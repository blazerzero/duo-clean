from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS, cross_origin
# from flask_restful.utils import cors

from flask_csv import send_csv
from random import sample
from pprint import pprint
from zipfile import ZipFile
from io import BytesIO
import json
import os
import subprocess
import helpers
import time
import pandas as pd
import numpy as np
import pickle
import math
import shutil
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)

logging.getLogger('flask_cors').level = logging.DEBUG

class TestLive(Resource):
    def get(self):
        return {'msg': '[SUCCESS] The server is live'}

class TestCORSLive(Resource):
    def get(self):
        return {'msg': '[SUCCESS] The server is live with CORS!'}

class Import(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        existingProjects = [('0x' + d) for d in os.listdir('./store/') if os.path.isdir(os.path.join('./store/', d))]

        # Initialize a new project
        if len(existingProjects) == 0:
            newProjectID = "{:08x}".format(1)
        else:
            projectIDList = [int(d, 0) for d in existingProjects]
            print(projectIDList)
            newProjectID = "{:08x}".format(max(projectIDList) + 1)
            print(newProjectID)
        newDir = './store/' + newProjectID + '/'
        try:
            os.mkdir(newDir)
            open(newDir + 'applied_cfds.txt', 'w').close()
        except OSError:
            print ('[ERROR] Unable to create a new directory for the project.')
            return {'msg': '[ERROR] Unable to create a new directory for the project.'}

        # Read and save the imported dataset to the project directory
        importedFile = request.files['file']
        f = open(newDir + 'data.csv', 'w')
        data = importedFile.read().decode('utf-8-sig').split('\n')
        header = data[0].split(',')
        for line in [l for l in data if len(l) > 0]:
            trimmedLineList = [tL.strip() for tL in line.split(',')]
            trimmedLine = ','.join(trimmedLineList)
            f.write(trimmedLine + '\n')
        f.close()
        shutil.copyfile(newDir + 'data.csv', newDir + 'before.csv')

        returned_data = {
            'header': header,
            'project_id': newProjectID,
            'msg': '[SUCCESS] Successfully created new project with project ID = ' + newProjectID + '.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Sample test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        sample_size = int(request.form.get('sample_size'))
        data = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)
        tuple_metadata = pd.DataFrame(index=data.index, columns=['weight', 'expl_freq'])    # Initialize tuple metadata DataFrame
        tuple_metadata['weight'] = 1            # Initialize tuple weights
        tuple_metadata['expl_freq'] = 0         # Initialize exploration frequency of all tuples
        value_metadata = dict()                 # Initialize value metadata dictionary
        cfd_metadata = list()                   # Initialize CFD metadata object
        cfd_applied_map = dict()

        current_iter = '00000000'       # Initial data is considered iteration 0
        for idx in data.index:
            value_metadata[idx] = dict()        # Initialize column dictionary for this row
            for col in data.columns:
                value_metadata[idx][col] = dict()               # Initialize dictionary for this cell
                value_metadata[idx][col]['history'] = list()    # Initialize cell value history list
                value_metadata[idx][col]['history'].append(helpers.ValueHistory(data.at[idx, col], 'user', None, current_iter, False))        # Add initial value to cell history list
                value_metadata[idx][col]['disagreement'] = 0    # Initialize cell value disagreement to 0

        s_out = data.sample(n=sample_size)

        # Diff object for experiments
        diffs = dict()
        diffs['cells'] = list()
        diffs['tups'] = list()
        pickle.dump( diffs, open('./store/' + project_id + '/diffs.p', 'wb') )
        # helpers.calcDiffs(data, './test/team-clean.csv', project_id, 'system', current_iter)

        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
        pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        pickle.dump( cfd_applied_map, open('./store/' + project_id + '/cfd_applied_map.p', 'wb') )

        # No changes have been made yet, so changes = False for every cell
        changes = dict()
        for i in s_out.index:
            for j in s_out.columns:
                changes[(i, j)] = False

        # Represent in serializable format
        changes = [{'row': k[0], 'col': k[1], 'repaired': v} for k, v in changes.items()]

        # Return this data to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps([]),
            'changes': json.dumps(changes),
            'msg': '[SUCCESS] Successfully retrieved sample.'
        }

        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Clean test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        s_in = request.form.get('data')
        sample_size = int(request.form.get('sample_size'))

        current_iter = pickle.load(open('./store/' + project_id + '/current_iter.p', 'rb'))
        current_iter = "{:08x}".format(int('0x'+current_iter, 0)+1)     # Increment the current iteration number
        cfd_applied_map = pickle.load(open('./store/' + project_id + '/cfd_applied_map.p', 'rb'))

        d_dirty = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)
        s_df = pd.read_json(s_in, orient='index')

        # Map the user's cell repairs to the respective cells in the full dataset
        d_rep, changed_ids = helpers.applyUserRepairs(d_dirty, s_df, project_id, current_iter)
        # helpers.calcDiffs(d_rep, './test/team-clean.csv', project_id, 'user', current_iter)

        d_rep.to_csv('./store/' + project_id + '/after.csv', encoding='utf-8', index=False)     # Save the user-repaired full dataset as a csv file (for XPlode)
        top_cfds = helpers.discoverCFDs(project_id)         # Run XPlode to discover new CFDs for before and after-repair versions of the dataset
        d_rep['cover'] = None                               # Initialize the cover for each row

        print(top_cfds)

        # Initialize dictionary in CFD applied map for this iteration
        cfd_applied_map[current_iter] = dict()
        for idx in d_rep.index:
            cfd_applied_map[current_iter][idx] = dict()
            for col in d_rep.columns:
                cfd_applied_map[current_iter][idx][col] = list()  # initialize the CFD mapping for each cell

        # Initialize a dictionary of the contradictions that occur during cleaning
        contradictions = dict()
        changes = dict()
        for i in d_rep.index:
            for j in d_rep.columns:
                changes[(i, j)] = False

        if top_cfds is not None and isinstance(top_cfds, np.ndarray):
            # Build query
            query = ''
            for idx in changed_ids:
                for col in s_df.columns:
                    query += (col + '=' + s_df.at[idx, col] + ' ')
            query = query[:-1]

            # Format query for updating receiver
            tokenized_query = query.split(' ')
            formatted_query = []
            for q in tokenized_query:
                word = "('" + q + "')"
                formatted_query.append(word)

            helpers.updateReceiver(top_cfds, project_id, current_iter, formatted_query)       # Update receiver with new CFDs
            picked_cfd_list, picked_cfd_id_list = helpers.pickCfds(project_id, formatted_query, 3)  # Get CFDs from receiver

            if picked_cfd_list is not None and len(picked_cfd_list) > 0:
                with open('./store/' + project_id + '/applied_cfds.txt', 'a') as f:
                    np.savetxt(f, [c['cfd'] for c in picked_cfd_list], fmt="%s")
                patterns = dict()
                value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
                d_rep['cover'] = np.empty(len(d_rep.index), dtype=str)
                for c in picked_cfd_list:
                    lhs = c['cfd'].split(' => ')[0][1:-1]
                    rhs = c['cfd'].split(' => ')[1]
                    print(lhs)
                    print(rhs)
                    patterns.update(helpers.fd2cfd(d_rep, lhs, rhs, value_metadata, current_iter))      # Variable CFD to constant CFD conversion
                    d_rep = helpers.buildCover(d_rep, lhs, rhs, patterns)   # Build the CFD cover for this iteration
                d_dirty['cover'] = d_rep['cover']
                d_rep, cfd_applied_map, contradictions, changes = helpers.applyCfdList(project_id, d_dirty, picked_cfd_list, picked_cfd_id_list, cfd_applied_map, current_iter)
            else:
                pass

        d_rep = d_rep.drop(columns=['cover'])
        helpers.reinforceTuplesBasedOnContradiction(project_id, current_iter, d_rep)
        d_rep.to_csv('./store/' + project_id + '/before.csv', encoding='utf-8', index=False)

        # helpers.calcDiffs(d_rep, './test/team-clean.csv', project_id, 'system', current_iter)

        tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')

        # reinforce tuples based on how frequently they have been explored
        for idx in d_rep.index:
            if idx in s_df.index:
                tuple_metadata.at[idx, 'expl_freq'] += 1
            else:
                # Reinforce based on the percentage of iterations the tuple has been sampled in
                tuple_metadata.at[idx, 'weight'] += (1 - (tuple_metadata.at[idx, 'expl_freq']/int('0x'+current_iter, 0)))

        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')

        # Generate a new sample
        s_out = helpers.buildSample(d_rep, sample_size, project_id, cfd_applied_map, current_iter)

        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        pickle.dump( cfd_applied_map, open('./store/' + project_id + '/cfd_applied_map.p', 'wb') )

        # Serialize these objects to return to the user
        contradictions = [{'row': k[0], 'col': k[1]} for k, v in contradictions.items()]
        changes = [{'row': k[0], 'col': k[1], 'repaired': v} for k, v in changes.items()]

        # Return this data to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps(contradictions),
            'changes': json.dumps(changes),
            'msg': '[SUCCESS] Successfully applied and generalized repair and retrived new sample.'
        }

        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


api.add_resource(TestLive, '/duo/api/test')
api.add_resource(TestCORSLive, '/duo/api/testcors')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Clean, '/duo/api/clean')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
