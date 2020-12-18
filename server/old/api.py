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
import analyze
from scipy.stats import hmean

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

        print("*** Project initialized ***")

        # Read the scenario number and initialize the scenario accordingly
        scenario_id = request.form.get('scenario_id')
        if scenario_id is None:
            scenario_id = json.loads(request.data)['scenario_id']
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
        with open(scenario['dirty_dataset']) as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            data = list(reader)

        df = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)

        # Initialize iteration counter
        current_iter = 0

        # Initialize tuple metadata and value metadata objects
        tuple_metadata = dict()
        cell_metadata = dict()
        for idx in range(0, len(data)):

            # Tuple metadata
            tuple_metadata[idx] = dict()
            tuple_metadata[idx]['weight'] = 1/len(data)

            # Cell metadata
            cell_metadata[idx] = dict()
            for col in header:
                cell_metadata[idx][col] = dict()
                cell_metadata[idx][col]['feedback_history'] = list()
                
        # FD metadata
        cfd_metadata = dict()
        h_space = scenario['hypothesis_space']
        for h in h_space:
            cfd_metadata[h['cfd']] = dict()

            wUV = analyze.aHeuristicUV(h['cfd'], df)
            wAC = analyze.aHeuristicAC(h['cfd'])
            # phaUV = np.prod([v for v in wUV.values()])
            # phaAC = np.prod([v for v in wAC.values()])
            phaUV = np.mean([v for v in wUV.values()])
            phaAC = np.mean([v for v in wAC.values()])
            phsSR = analyze.sHeuristicSetRelation(h['cfd'], [c['cfd'] for c in h_space]) # p(h | sSR)
            ph = hmean([phaUV, phaAC, phsSR])
            
            cfd_metadata[h['cfd']]['conf'] = h['conf']
            cfd_metadata[h['cfd']]['score'] = 1
            cfd_metadata[h['cfd']]['weight'] = cfd_metadata[h['cfd']]['score'] * ph

            cfd_metadata[h['cfd']]['support'] = h['support']
            cfd_metadata[h['cfd']]['vios'] = h['vios']
            cfd_metadata[h['cfd']]['vio_pairs'] = h['vio_pairs']
            cfd_metadata[h['cfd']]['vio_trios'] = h['vio_trios']
        
        cfd_metadata = helpers.normalizeWeights(cfd_metadata)
        for _, cfd_m in cfd_metadata.items():
            cfd_m['score_history'] = list()
            cfd_m['score_history'].append(helpers.CFDScore(iter_num=current_iter, score=cfd_m['score'], elapsed_time=0))
            cfd_m['weight_history'] = list()
            cfd_m['weight_history'].append(helpers.CFDWeightHistory(iter_num=current_iter, weight=cfd_m['weight'], elapsed_time=0))

        # Initialize other metrics/metadata needed in study
        study_metrics = dict()
        study_metrics['precision'] = list()
        study_metrics['recall'] = list()
        study_metrics['f1'] = list()

        start_time = time.time()

        modeling_metadata = dict()
        modeling_metadata['p_X_given_h'] = dict()
        modeling_metadata['p_X'] = dict()
        modeling_metadata['p_h_given_X'] = dict()
        modeling_metadata['X'] = list()
        modeling_metadata['Y'] = list()
        modeling_metadata['y_in_h'] = dict()
        for cfd in cfd_metadata.keys():
            modeling_metadata['y_in_h'][cfd] = dict()

        print('*** Metadata and study metric objects initialized ***')

        # Save metadata
        pickle.dump( tuple_metadata, open(new_project_dir + '/tuple_metadata.p', 'wb') )
        pickle.dump( cell_metadata, open(new_project_dir + '/cell_metadata.p', 'wb') )
        pickle.dump( cfd_metadata, open(new_project_dir + '/cfd_metadata.p', 'wb') )
        pickle.dump( current_iter, open(new_project_dir + '/current_iter.p', 'wb') )
        pickle.dump( study_metrics, open(new_project_dir + '/study_metrics.p', 'wb') )
        pickle.dump( start_time, open(new_project_dir + '/start_time.p', 'wb') )
        pickle.dump( modeling_metadata, open(new_project_dir + '/modeling_metadata.p', 'wb') )

        print('*** Metadata and study metric objects saved ***')

        # Return information to the user
        returned_data = {
            'header': header,
            'project_id': new_project_id,
            'scenario_desc': scenario['description'],
            'msg': '[SUCCESS] Successfully created new project with project ID = ' + new_project_id + '.'
        }
        response = json.dumps(returned_data)
        # pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        if project_id is None:
            project_id = json.loads(request.data)['project_id']
        sample_size = 10
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

        current_time = time.time()
        pickle.dump( current_time, open('./store/' + project_id + '/current_time.p', 'wb') )

        print('*** Project info loaded ***')
            
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        # sampling_method = project_info['scenario']['sampling_method']
        
        # Build sample and update tuple weights post-sampling
        start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
        current_iter = 0
        s_out, vios = helpers.buildSample(data, sample_size, project_id, current_iter, start_time) # TODO: Update sampling strategy
        s_index = s_out.index
        pickle.dump( s_index, open('./store/' + project_id + '/current_sample.p', 'wb') )
        pickle.dump( vios, open('./store/' + project_id + '/current_vios.p', 'wb') )

        # print('*** Sample built and saved with ' + sampling_method + ' ***')

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
        
        s_out.insert(0, 'id', s_out.index, True)

        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'sample_vios': [list(v) for v in vios],
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
            pprint(returned_data)
            response = json.dumps(returned_data)
            return response, 200, {'Access-Control-Allow-Origin': '*'}
            
        s_index = pickle.load( open('./store/' + project_id + '/current_sample.p', 'rb') )
        vios = pickle.load( open('./store/' + project_id + '/current_vios.p', 'rb') )

        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        s_out = data.loc[s_index, :]

        # Build changes map for front-end
        feedback = list()
        cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': bool(cell_metadata[int(idx)][col]['feedback_history'][-1].marked) if len(cell_metadata[int(idx)][col]['feedback_history']) > 0 else False
                })

        print('*** Feedback object created ***')

        true_pos, false_pos = helpers.getUserScores(project_id)
        
        print('*** Leaderboard created ***')

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        clean_h_space = project_info['scenario']['clean_hypothesis_space']

        top_fd_conf, variance_delta = helpers.checkForTermination(project_id, clean_h_space, current_iter)
        conf_threshold = (0.85 / len(project_info['scenario']['cfds']))
        
        if current_iter >= 25 or (top_fd_conf >= conf_threshold and variance_delta is not None and variance_delta < 0.01):
            msg = '[DONE]'
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'

        header = s_out.columns.tolist()
        s_out.insert(0, 'id', s_out.index, True)

        # Return information to the user
        returned_data = {
            'header': header,
            'sample': s_out.to_json(orient='index'),
            'sample_vios': [list(v) for v in vios],
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
            print(req)
            project_id = req['project_id']
            feedback = req['feedback']
            is_new_feedback = req['is_new_feedback']
            refresh = req['refresh']
        else:
            feedback = json.loads(request.form.get('feedback'))
            is_new_feedback = int(request.form.get('is_new_feedback'))
            refresh = int(request.form.get('refresh'))

        feedback = pd.DataFrame.from_dict(feedback, orient='index')
        sample_size = 10

        print('*** Necessary objects loaded ***')

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        current_iter += 1

        current_time = pickle.load( open('./store/' + project_id + '/current_time.p', 'rb') )
        current_time = time.time()

        print('*** Iteration counter updated ***')

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)

        print('*** Project info loaded ***')
        
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)

        print('*** Loaded dirty dataset ***')

        # Save noise feedback
        if is_new_feedback == 1 and refresh == 0:
            print('*** NEW FEEDBACK! ***')
            helpers.saveNoiseFeedback(data, feedback, project_id, current_iter, current_time)
        print('*** Feedback saved ***')
        s_in = data.iloc[feedback.index]
        print('*** Extracted sample from dataset ***')
        if is_new_feedback == 1 and refresh == 0:
            helpers.explainFeedback(data, s_in, project_id, current_iter, current_time, 0)
        else:
            helpers.explainFeedback(data, s_in, project_id, current_iter, current_time, 1)
        print('*** Mining completed and FD/CFD weights updated ***')
        
        # Update tuple weights pre-sampling
        # sampling_method = project_info['scenario']['sampling_method']
        print('*** Sampling method retrieved ***')

        # Build sample
        s_out, vios = helpers.buildSample(data, sample_size, project_id, current_iter, current_time)
        s_index = s_out.index
        pickle.dump( s_index, open('./store/' + project_id + '/current_sample.p', 'wb') )
        pickle.dump( vios, open('./store/' + project_id + '/current_vios.p', 'wb') )

        print('*** New sample created and saved ***')

        # Build feedback map for front-end
        feedback = list()
        cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
        for idx in s_out.index:
            for col in s_out.columns:
                feedback.append({
                    'row': idx,
                    'col': col,
                    'marked': bool(cell_metadata[int(idx)][col]['feedback_history'][-1].marked) if len(cell_metadata[int(idx)][col]['feedback_history']) > 0 else False
                })

        print('*** Feedback object created ***')

        true_pos, false_pos = helpers.getUserScores(project_id)

        print('*** User scores retrieved ***')

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        clean_h_space = project_info['scenario']['clean_hypothesis_space']
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )

        top_fd_conf, variance_delta = helpers.checkForTermination(project_id, clean_h_space, current_iter)
        conf_threshold = (0.85 / len(project_info['scenario']['cfds']))

        # if refresh == 0 and (current_iter >= 25 or (top_fd_conf >= conf_threshold and variance_delta is not None and variance_delta < 0.01)):
        if refresh == 0 and current_iter >= 25:
            msg = '[DONE]'
            top_fd = max(cfd_metadata, key=lambda x: cfd_metadata[x]['weight'])
            concerned_fd_conf = next(h for h in clean_h_space if h['cfd'] == top_fd)['conf'] if top_fd in [k['cfd'] for k in clean_h_space] else None
            project_info['flagged'] = True if concerned_fd_conf is None or concerned_fd_conf < conf_threshold else False
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'

        s_out.insert(0, 'id', s_out.index, True)

        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        pickle.dump( current_time, open('./store/' + project_id + '/current_time.p', 'wb') )
        with open('./store/' + project_id + '/project_info.json', 'w') as f:
            json.dump(project_info, f)
        
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'sample_vios': [list(v) for v in vios],
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
