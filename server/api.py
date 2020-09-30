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
            pprint(returned_data)
            response = json.dumps(returned_data)
            return response, 500, {'Access-Control-Allow-Origin': '*'}

        print("*** Project initialized ***")

        # Read the scenario number and initialize the scenario accordingly
        scenario_id = request.form.get('scenario_id')
        participant_name = request.form.get('participant_name')
        with open('scenarios.json', 'r') as f:
            scenarios_list = json.load(f)
        scenario = scenarios_list[scenario_id]
        project_info = {
            'participant_name': participant_name,
            'scenario_id': scenario_id,
            'scenario': scenario,
            'score': 0
        }
        with open(new_project_dir + '/project_info.json', 'w') as f:
            json.dump(project_info, f)

        print('*** Project info saved ***')

        # Extract the header
        with open(scenario['dirty_dataset']) as f:
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
        cfd_metadata = dict()

        # Initialize other metrics/metadata needed in study
        study_metrics = dict()
        study_metrics['true_error_pct_full'] = list()
        study_metrics['true_error_pct_iter'] = list()
        study_metrics['false_positives_full'] = list()
        study_metrics['false_positives_iter'] = list()
        study_metrics['cfd_confidence'] = dict()
        for cfd in scenario['cfds']:
            study_metrics['cfd_confidence'][cfd] = list()
        study_metrics['error_accuracy_full'] = list()
        study_metrics['error_accuracy_iter'] = list()

        start_time = time.time()

        modeling_metadata = dict()
        modeling_metadata['p_X_given_h'] = dict()
        modeling_metadata['X'] = list()
        modeling_metadata['y_supp_h'] = dict()

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

        current_time = time.time()
        pickle.dump( current_time, open('./store/' + project_id + '/current_time.p', 'wb') )

        print('*** Project info loaded ***')
            
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        sampling_method = project_info['scenario']['sampling_method']
        
        # Build sample and update tuple weights post-sampling
        s_out = helpers.buildSample(data, sample_size, project_id, sampling_method, current_iter=0)
        s_out_dict = list(s_out.T.to_dict().values())
        s_out_header = s_out_dict[0].keys()
        with open('./store/' + project_id + '/current_sample.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, s_out_header)
            writer.writeheader()
            writer.writerows(s_out_dict)

        print('*** Sample built and saved with ' + sampling_method + ' ***')

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

        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'feedback': json.dumps(feedback),
            'true_pos': 0,
            'false_pos': 0,
            'msg': '[SUCCESS] Successfully built sample.'
        }
        pprint(returned_data)
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Resume(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        s_out = pd.read_csv('./store/' + project_id + '/current_sample.csv', keep_default_na=False)

        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

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
        study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )

        if current_iter == 30 or (len(study_metrics['true_error_pct_full']) > 0 and study_metrics['true_error_pct_full'][-1].value >= 0.9):
            msg = '[DONE]'
        else:
            msg = '[SUCCESS] Successfully built sample.'

        # Return information to the user
        returned_data = {
            'header': s_out.columns.tolist(),
            'sample': s_out.to_json(orient='index'),
            'feedback': json.dumps(feedback),
            'true_pos': true_pos,
            'false_pos': false_pos,
            'msg': msg,
            'scenario_id': project_info['scenario_id'],
            'scenario_desc': project_info['scenario']['description']
        }
        pprint(returned_data)
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] This endpoint is live!'}

    def post(self):
        project_id = request.form.get('project_id')
        feedback = json.loads(request.form.get('feedback'))
        is_new_feedback = int(request.form.get('is_new_feedback'))
        feedback = pd.DataFrame.from_dict(feedback, orient='index')
        sample_size = 10

        print('*** Necessary objects loaded ***')

        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        current_iter += 1
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )

        print('*** Iteration counter updated ***')

        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)

        print('*** Project info loaded ***')
        
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)

        print('*** Loaded dirty dataset ***')

        # Save noise feedback
        percentage_errors_found = 0
        if is_new_feedback == 1:
            print('*** NEW FEEDBACK! ***')
            percentage_errors_found = helpers.saveNoiseFeedback(data, feedback, project_id, current_iter)
            print('*** Noise feedback saved ***')
            s_in = data.iloc[feedback.index]
            print('*** Extracted sample from dataset ***')
            helpers.explainFeedback(s_in, project_id, current_iter)
            helpers.buildCovers(data, project_id, current_iter)
            print('*** XPlode completed and FD/CFD weights updated ***')

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
        sampling_method = project_info['scenario']['sampling_method']
        print('*** Sampling method retrieved ***')
        # if sampling_method != 'RANDOM-PURE':
        #     helpers.reinforceTuplesBasedOnInteraction(data, project_id, current_iter, is_new_feedback)
        #     print('*** Tuples reinforced based on interaction metrics ***')
        # if sampling_method == 'DUO':
        #     helpers.reinforceTuplesBasedOnDependencies(data, project_id, current_iter, is_new_feedback, project_info)
        #     print('*** Tuples reinforced based on FD/CFD weights ***')

        # Build sample
        s_out = helpers.buildSample(data, sample_size, project_id, sampling_method, current_iter)
        s_out_dict = list(s_out.T.to_dict().values())
        s_out_header = s_out_dict[0].keys()
        with open('./store/' + project_id + '/current_sample.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, s_out_header)
            writer.writeheader()
            writer.writerows(s_out_dict)

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

        print('*** Leaderboard created ***')

        if current_iter == 30 or percentage_errors_found >= 0.9:
            msg = '[DONE]'
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'feedback': json.dumps(feedback),
            'true_pos': true_pos,
            'false_pos': false_pos,
            'msg': msg
        }
        pprint(returned_data)
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

api.add_resource(Test, '/duo/api/')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Resume, '/duo/api/resume')
api.add_resource(Clean, '/duo/api/clean')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
