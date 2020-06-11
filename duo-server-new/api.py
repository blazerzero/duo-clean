from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS, cross_origin
from flask_csv import send_csv

import random
from pprint import pprint
import json
import os
import helpers
import time
import pandas as pd
import numpy as np
import pickle
import math
import shutil
import logging
import csv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)

logging.getLogger('flask_cors').level = logging.DEBUG

class Test(Resource):
    def get(self):
        return {'msg': '[SUCCESS] The server is live!'}

class Import(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        
        # Initialize a new project
        projects = [('0x' + d) for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
        if len(projects) == 0:
            new_project_id = '{:08x}'.format(1)
        else:
            project_ids = [int(d, 0) for d in projects]
            new_project_id = '{:08x}'.format(max(project_ids) + 1)
        new_project_dir = './store/' + new_project_id
        try:
            os.mkdir(new_project_dir)
        except OSError:
            returned_data = {
                'msg': '[ERROR] Unable to create a directory for this project.'
            }
            response = json.dumps(returned_data)
            pprint(response)
            return response, 500, {'Access-Control-Allow-Origin': '*'}

        # Read the scenario number and initialize the scenario accordingly
        # scenario_id = request.form.get('scenario_id')     # USE THIS WHEN FRONTEND IS READY
        scenario_id = "1" # TEMPORARY
        with open('scenarios.json', 'r') as f:
            scenarios_list = json.load(f)
        scenario = scenarios_list[scenario_id]
        with open(new_project_dir + '/scenario.json', 'w') as f:
            json.dump(scenario, f)

        # Read and save the imported dataset to the new project directory
        imported_file = request.files['file']
        f = open(new_project_dir + '/data.csv', 'w')
        imported_data = imported_file.read().decode('latin-1').split('\n')
        header = imported_data[0].split(',')
        header = [h.rstrip() for h in header]
        lines = [l for l in imported_data if len(l) > 0]
        for line in lines:
            f.write(line + '\n')
        f.close()
        shutil.copyfile(new_project_dir + '/data.csv', new_project_dir + '/in_progress.csv')

        # Initialize iteration counter
        current_iter = '00000000'

        # data = pd.read_csv(new_project_dir + '/in_progress.csv')
        # data.to_csv(new_project_dir + '/in_progress.csv', encoding='latin-1', index=False)
        with open(new_project_dir + '/in_progress.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            # with open(new_project_dir + '/in_progress.csv', 'w') as f:
            #     writer = csv.DictWriter(f, header)
            #     writer.writeheader()
            #     writer.writerows(data)

        # Initialize tuple metadata and value metadata objects
        tuple_metadata = dict()
        value_metadata = dict()
        for idx in range(0, len(data)):

            # Tuple metadata
            tuple_metadata[idx] = dict()
            tuple_metadata[idx]['weight'] = 1/len(data)
            tuple_metadata[idx]['expl_freq'] = 0
            tuple_metadata[idx]['noise_history'] = list()

            # Value metadata
            value_metadata[idx] = dict()
            for col in header:
                value_metadata[idx][col] = dict()
                value_metadata[idx][col]['history'] = list()
                value_metadata[idx][col]['history'].append(helpers.ValueHistory(data[idx][col], 'user', current_iter, False))
                # value_metadata[idx][col]['disagreement'] = 0
                
        # Initialize CFD metadata object
        cfd_metadata = dict()

        # Initialize other metrics/metadata needed in study

        # Save metadata
        pickle.dump( tuple_metadata, open(new_project_dir + '/tuple_metadata.p', 'wb') )
        pickle.dump( value_metadata, open(new_project_dir + '/value_metadata.p', 'wb') )
        pickle.dump( cfd_metadata, open(new_project_dir + '/cfd_metadata.p', 'wb') )
        pickle.dump( current_iter, open(new_project_dir + '/current_iter.p', 'wb') )

        # Calculate initial CFD confidence levels
        cfds = helpers.runCFDDiscovery(len(data), new_project_id, current_iter)
        #print("CFDs:")
        #pprint(cfds)
        
        # Return information to the user
        returned_data = {
            'header': header,
            'project_id': new_project_id,
            'msg': '[SUCCESS] Successfully created new project with project ID = ' + new_project_id + '.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        sample_size = int(request.form.get('sample_size'))
        data = pd.read_csv('./store/' + project_id + '/in_progress.csv', keep_default_na=False)
        
        # Build sample
        s_out = helpers.buildSample(data, sample_size, project_id)

        # No changes have been made yet, so changes = False for every cell
        changes = list()
        for idx in s_out.index:
            for col in s_out.columns:
                changes.append({
                    'row': idx,
                    'col': col,
                    'changed': False
                })
        
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps([]),
            'changes': json.dumps(changes),
            'msg': '[SUCCESS] Successfully built sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        sample = request.form.get('data')
        sample_size = int(request.form.get('sample_size'))

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        current_iter = '{:08x}'.format(int('0x' + current_iter, 0) + 1)

        with open('./store/' + project_id + '/scenario.json', 'r') as f:
            scenario = json.load(f)
        
        # d_prev = pd.read_csv('./store/' + project_id + '/in_progress.csv', keep_default_na=False)
        d_orig = pd.read_csv('./store/' + project_id + '/data.csv', keep_default_na=False)
        header = d_orig.columns
        with open('./store/' + project_id + '/in_progress.csv', 'r+') as f:
            reader = csv.DictReader(f)
            d_prev = list(reader)
            s_in = pd.read_json(sample, orient='index')
            f.seek(0)

            # Map any user-specified repairs from the sample to the full dataset
            d_curr = helpers.applyUserRepairs(d_prev, s_in, project_id, current_iter)
            # d_curr.to_csv('./store/' + project_id + '/in_progress.csv', 'latin-1', index=False)
            writer = csv.DictWriter(f, header)
            writer.writeheader()
            writer.writerows(d_curr)

        # Run CFD discovery algorithm to determine confidence of relevant CFD(s)
        cfds = helpers.runCFDDiscovery(len(d_curr), project_id, current_iter)
        for c in cfds:
            if scenario['cfd'] == c['cfd']:
                # If threshold IS met, return completion message to user
                if c['conf'] >= scenario['conf_threshold']:
                    returned_data = {
                        'msg': '[DONE]'
                    }
                    response = json.dumps(returned_data)
                    pprint(response)
                    return response, 200, {'Access-Control-Allow-Origin': '*'}
                break

        # If confidence threshold for relevant CFD(s) IS NOT met, build new sample based on tuple weights
        d_curr = pd.DataFrame(d_curr)
        s_out = helpers.buildSample(d_curr, sample_size, project_id)
        changes = list()
        for idx in s_out.index:
            for col in s_out.columns:
                changes.append({
                    'row': idx,
                    'col': col,
                    'changed': bool(s_out.at[idx, col] != d_orig.at[idx, col])
                })

        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps([]),
            'changes': json.dumps(changes),
            'msg': '[DONE]'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

api.add_resource(Test, '/duo/api/')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Clean, '/duo/api/clean')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')