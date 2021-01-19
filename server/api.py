from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS, cross_origin
from flask_csv import send_csv

import random
import json
import os
import time
import pandas as pd
import numpy as np
import pickle
import math
import shutil
import logging
import csv
from scipy.stats import hmean
from pprint import pprint

import helpers
import analyze

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
            pprint(returned_data)
            response = json.dumps(returned_data)
            return response, 500, {'Access-Control-Allow-Origin': '*'}

        print('*** Project initialized ***')

        # Read the scenario number and initialize the scenario accordingly
        scenario_id = request.form.get('scenario_id')
        if scenario_id is None:
            scenario_id = json.loads(request.data)['scenario_id']
        print(scenario_id)
        with open('scenarios.json', 'r') as f:
            scenarios_list = json.load(f)
        scenario = scenarios_list[scenario_id]
        project_info = {
            'scenario_id': scenario_id,
            'scenario': scenario,
            'score': 0,
            'true_pos': 0,
            'false_pos': 0
        }
        with open(new_project_dir + '/project_info.json', 'w') as f:
            json.dump(project_info, f, indent=4)

        print('*** Project info saved ***')

        # Extract the header
        '''with open(scenario['dirty_dataset']) as f:
            reader = csv.DictReader(f)
        header = reader.fieldnames
        data = list(reader)'''
        data = pd.read_csv(scenario['dirty_dataset'])
        header = [col for col in data.columns]

        # Initialize the iteration counter
        current_iter = 0

        # Initialize metadata objects
        interaction_metadata = dict()
        interaction_metadata['feedback_history'] = dict()
        interaction_metadata['sample_history'] = list()
        for idx in data.index:
            interaction_metadata['feedback_history'][int(idx)] = dict()
            for col in header:
                # interaction_metadata[idx][col] = dict()
                interaction_metadata['feedback_history'][int(idx)][col] = list()

        X = set()
        
        fd_metadata = dict()
        # target_fd = scenario['target_fd']
        # target_fd = '(owner, ownertype) => type, manager'
        h_space = scenario['hypothesis_space']
        for h in h_space:
            # if h['cfd'] != target_fd:
            #     continue

            h['vio_pairs'] = set(tuple(vp) for vp in h['vio_pairs'])
            mu = h['conf']
            variance = 0.0025
            
            alpha, beta = helpers.initialPrior(mu, variance)
            fd_m = helpers.FDMeta(
                fd=h['cfd'],
                a=alpha,
                b=beta,
                support=h['support'],
                vios=h['vios'],
                vio_pairs=h['vio_pairs'],
            )

            print('iter: 0'),
            print('alpha:', fd_m.alpha)
            print('beta:', fd_m.beta)

            for i in data.index:
                for j in data.index:
                    if i == j:
                        continue

                    X |= h['vio_pairs']
                    
                    match = True if i not in h['vios'] and j not in h['vios'] else False

                    # match = True
                    # for lh in fd_m.lhs:
                    #     if data.at[i, lh] != data.at[j, lh]:
                    #         match = False
                    #         break

                    if match is True and ((i, j) not in X and (j, i) not in X):
                        if i < j:
                            X.add((i, j))
                        else:
                            X.add((j, i)) 

            fd_metadata[h['cfd']] = fd_m

        print(len(X))
        current_iter += 1

        study_metrics = dict()
        study_metrics['vio_precision'] = list()
        study_metrics['vio_recall'] = list()
        study_metrics['vio_f1'] = list()
        study_metrics['err_precision'] = list()
        study_metrics['err_recall'] = list()
        study_metrics['err_f1'] = list()
        pickle.dump( study_metrics, open(new_project_dir + '/study_metrics.p', 'wb') )

        pickle.dump( interaction_metadata, open(new_project_dir + '/interaction_metadata.p', 'wb') )
        pickle.dump( fd_metadata, open(new_project_dir + '/fd_metadata.p', 'wb') )
        pickle.dump( current_iter, open(new_project_dir + '/current_iter.p', 'wb') )
        pickle.dump( X, open(new_project_dir + '/X.p', 'wb') )

        print('*** Metadata and objects initialized and saved ***')

        # Return information to the user
        returned_data = {
            'header': header,
            'project_id': new_project_id,
            'scenario_desc': scenario['description'],
            'msg': '[SUCCESS] Successfully created new project with project ID = ' + new_project_id + '.'
        }
        response = json.dumps(returned_data)
        return response, 201, {'Access-Control-Allow-Origin': '*'}

class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        if project_id is None:
            # print(request.data)
            project_id = json.loads(request.data)['project_id']
        sample_size = 10
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

        start_time = time.time()
        pickle.dump( start_time, open('./store/' + project_id + '/start_time.p', 'wb') )

        print('*** Project info loaded ***')

        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        
        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        X = pickle.load( open('./store/' + project_id + '/X.p', 'rb') )
        
        # Build sample and X_t
        s_out, sample_X = helpers.buildSample(data, X, sample_size, project_id, current_iter, start_time)
        s_index = s_out.index
        pickle.dump( s_index, open('./store/' + project_id + '/current_sample.p', 'wb') )
        pickle.dump( sample_X, open('./store/' + project_id + '/current_X.p', 'wb') )    

        # Build initial feedback map for frontend
        feedback = list()
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': False
                })

        print('*** Feedback object created ***')
        print(len(sample_X))
        
        s_out.insert(0, 'id', s_out.index, True)
        print(s_out.index)

        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'X': [list(v) for v in sample_X],
            'feedback': json.dumps(feedback),
            'true_pos': 0,
            'false_pos': 0,
            'msg': '[SUCCESS] Successfully built sample.'
        }
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Resume(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        projects = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
        if project_id not in projects:
            returned_data = {
                'msg': '[INVALID PROJECT ID]'
            }
            response = json.dumps(returned_data)
            return response, 200, {'Access-Control-Allow-Origin': '*'}
            
        s_index = pickle.load( open('./store/' + project_id + '/current_sample.p', 'rb') )
        sample_X = pickle.load( open('./store/' + project_id + '/current_X.p', 'rb') )

        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        s_out = data.loc[s_index, :]

        feedback = list()
        interaction_metadata = pickle.load( open('./store/' + project_id + '/interaction_metadata.p', 'rb') )
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': bool(interaction_metadata['feedback_history'][int(idx)][col][-1].marked) if len(interaction_metadata['feedback_history'][int(idx)][col]) > 0 else False
                })

        print('*** Feedback object created ***')

        true_pos, false_pos = helpers.getUserScores(project_id)
        
        print('*** Leaderboard created ***')

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        clean_h_space = project_info['scenario']['clean_hypothesis_space']

        # top_fd_conf, variance_delta = helpers.checkForTermination(project_id, clean_h_space, current_iter)
        # conf_threshold = (0.85 / len(project_info['scenario']['cfds']))
        
        # if current_iter >= 25 or (top_fd_conf >= conf_threshold and variance_delta is not None and variance_delta < 0.01):
        if current_iter >= 25:
            msg = '[DONE]'
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'

        header = s_out.columns.tolist()
        s_out.insert(0, 'id', s_out.index, True)

        # Return information to the user
        returned_data = {
            'header': header,
            'sample': s_out.to_json(orient='index'),
            'X': [list(v) for v in sample_X],
            'feedback': json.dumps(feedback),
            'true_pos': true_pos,
            'false_pos': false_pos,
            'msg': msg,
            'scenario_id': project_info['scenario_id'],
            'scenario_desc': project_info['scenario']['description']
        }
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        if project_id is None:
            req = json.loads(request.data)
            # print(req)
            project_id = req['project_id']
            feedback_dict = req['feedback']
        else:
            feedback_dict = json.loads(request.form.get('feedback'))

        print(project_id)
        # print(feedback)

        feedback = pd.DataFrame.from_dict(feedback_dict, orient='index')
        sample_size = 10

        print('*** Necessary objects loaded ***')

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        print(current_iter)
        # current_time = pickle.load( open('./store/' + project_id + '/current_time.p', 'rb') )
        current_time = time.time()

        curr_sample_X = pickle.load( open('./store/' + project_id + '/current_X.p', 'rb') )
        X = pickle.load( open('./store/' + project_id + '/X.p', 'rb') )

        print('*** Iteration counter updated ***')

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)

        print('*** Project info loaded ***')
        
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)

        print('*** Loaded dirty dataset ***')

        s_in = data.iloc[feedback.index]
        print('*** Extracted sample from dataset ***')
        helpers.recordFeedback(data, feedback_dict, curr_sample_X, project_id, current_iter, current_time)
        target_fd = project_info['scenario']['target_fd'] # NOTE: For current sims only
        # target_fd = '(owner, ownertype) => type, manager'
        helpers.interpretFeedback(s_in, feedback, X, curr_sample_X, project_id, target_fd)
        print('*** FD weights updated ***')

        current_iter += 1
        s_out, new_sample_X = helpers.buildSample(data, X, sample_size, project_id, current_iter, current_time)
        s_index = s_out.index
        pickle.dump( s_index, open('./store/' + project_id + '/current_sample.p', 'wb') )
        pickle.dump( new_sample_X, open('./store/' + project_id + '/current_X.p', 'wb') )

        # Build feedback map for front-end
        feedback = list()
        interaction_metadata = pickle.load( open('./store/' + project_id + '/interaction_metadata.p', 'rb') )
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': bool(interaction_metadata['feedback_history'][int(idx)][col][-1].marked) if len(interaction_metadata['feedback_history'][int(idx)][col]) > 0 else False
                })

        print('*** Feedback object created ***')

        true_pos, false_pos = helpers.getUserScores(project_id)

        print('*** User scores retrieved ***')

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        clean_h_space = project_info['scenario']['clean_hypothesis_space']
        # cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )

        # top_fd_conf, variance_delta = helpers.checkForTermination(project_id, clean_h_space, current_iter)
        # conf_threshold = (0.85 / len(project_info['scenario']['cfds']))

        # if refresh == 0 and (current_iter >= 25 or (top_fd_conf >= conf_threshold and variance_delta is not None and variance_delta < 0.01)):
        # if current_iter > 25:
        if current_iter > 100:
            msg = '[DONE]'
            # top_fd = max(cfd_metadata, key=lambda x: cfd_metadata[x]['weight'])
            # concerned_fd_conf = next(h for h in clean_h_space if h['cfd'] == top_fd)['conf'] if top_fd in [k['cfd'] for k in clean_h_space] else None
            # project_info['flagged'] = True if concerned_fd_conf is None or concerned_fd_conf < conf_threshold else False
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'

        s_out.insert(0, 'id', s_out.index, True)
        print(s_out.index)

        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        # pickle.dump( current_time, open('./store/' + project_id + '/current_time.p', 'wb') )
        with open('./store/' + project_id + '/project_info.json', 'w') as f:
            json.dump(project_info, f)

        # print(X)
        print(new_sample_X)
        
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'X': [list(v) for v in new_sample_X],
            'feedback': json.dumps(feedback),
            'true_pos': true_pos,
            'false_pos': false_pos,
            'msg': msg
        }
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


api.add_resource(Test, '/duo/api/')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Resume, '/duo/api/resume')
api.add_resource(Clean, '/duo/api/clean')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')