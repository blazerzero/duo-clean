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
        scenario_id = request.form.get('scenario_id')     # USE THIS WHEN FRONTEND IS READY
        participant_name = request.form.get('participant_name')
        with open('scenarios.json', 'r') as f:
            scenarios_list = json.load(f)
            print(scenarios_list)
        scenario = scenarios_list[scenario_id]
        project_info = {
            'participant_name': participant_name,
            'scenario_id': scenario_id,
            'scenario': scenario,
            'score': 0
        }
        with open(new_project_dir + '/project_info.json', 'w') as f:
            json.dump(project_info, f)

        # Extract the header
        with open(scenario['dataset']) as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            data = list(reader)

        # Initialize iteration counter
        current_iter = 0

        # Initialize tuple metadata and value metadata objects
        tuple_metadata = dict()
        cell_metadata = dict()
        for idx in range(0, len(data)):

            # Tuple metadata
            tuple_metadata[idx] = dict()
            tuple_metadata[idx]['weight'] = 1/len(data)
            tuple_metadata[idx]['expl_freq'] = 0

            # Cell metadata
            cell_metadata[idx] = dict()
            for col in header:
                cell_metadata[idx][col] = dict()
                cell_metadata[idx][col]['feedback_history'] = list()
                
        # FD metadata
        fd_metadata = dict()

        # TODO: Initialize other metrics/metadata needed in study

        # Save metadata
        pickle.dump( tuple_metadata, open(new_project_dir + '/tuple_metadata.p', 'wb') )
        pickle.dump( cell_metadata, open(new_project_dir + '/cell_metadata.p', 'wb') )
        pickle.dump( fd_metadata, open(new_project_dir + '/fd_metadata.p', 'wb') )
        pickle.dump( current_iter, open(new_project_dir + '/current_iter.p', 'wb') )
        
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
        sample_size = 10
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
            
        data = pd.read_csv(project_info['scenario']['dataset'], keep_default_na=False)
        
        # Build sample and update tuple weights post-sampling
        s_out = helpers.buildSample(data, sample_size, project_id)

        # No changes have been made yet, so changes = False for every cell
        feedback = list()
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': False
                })

        leaderboard = helpers.buildLeaderboard(project_info['scenario_id'])
        
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'feedback': json.dumps(feedback),
            'leaderboard': json.dumps(leaderboard),
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
        feedback = json.loads(request.form.get('feedback'))
        is_new_feedback = request.form.get('is_new_feedback')
        feedback = pd.DataFrame.from_dict(feedback, orient='index')
        sample_size = 10

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        current_iter += 1
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        
        # with open(project_info['scenario']['dataset'], 'r+') as f:
        #     reader = csv.DictReader(f)
        #     data = list(reader)
        data = pd.read_csv(project_info['scenario']['dataset'], keep_default_na=False)

        # Save noise feedback
        if is_new_feedback is True:
            helpers.saveNoiseFeedback(data, feedback, project_id, current_iter)

        # Run CFD discovery algorithm to determine confidence of relevant CFD(s)
        # cfds = helpers.runCFDDiscovery(len(d_curr), project_id, current_iter)
        # if cfds is not None:
        #     for c in cfds:
        #        if scenario['cfd'] == c['cfd']:
        #             # If confidence threshold for relevant CFD(s) IS met, return completion message to user
        #             if c['conf'] >= scenario['conf_threshold']:
        #                 returned_data = {
        #                     'msg': '[DONE]'
        #                 }
        #                 response = json.dumps(returned_data)
        #                 pprint(response)
        #                 return response, 200, {'Access-Control-Allow-Origin': '*'}
        #             break

        # Confidence threshold for relevant CFD(s) IS NOT met, so build new sample based on tuple weights
        
        # Update tuple weights pre-sampling
        helpers.reinforceTuples(data, project_id, current_iter, is_new_feedback)

        # Build sample
        s_out = helpers.buildSample(data, sample_size, project_id)

        # Update tuple weights post-sampling
        # helpers.reinforceTuplesPostSample(s_out, project_id, current_iter)

        # Build changes map for front-end
        feedback = list()
        cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': bool(cell_metadata[idx][col]['feedback_history'][-1].marked) if len(cell_metadata[idx][col]['feedback_history']) > 0 else False
                })

        leaderboard = helpers.buildLeaderboard(project_info['scenario_id'])

        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'feedback': json.dumps(feedback),
            'leaderboard': json.dumps(leaderboard),
            'msg': '[SUCCESS]: Saved feedback and built new sample.'
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