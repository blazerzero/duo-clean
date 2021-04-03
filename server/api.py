import json, os, time, pickle, math, logging
from pprint import pprint
from random import shuffle
from datetime import datetime

from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS, cross_origin
from flask_csv import send_csv

import pandas as pd
import numpy as np
from rich.console import Console

import helpers, analyze

console = Console()

# Flask configs
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)
logging.getLogger('flask_cors').level = logging.DEBUG

class User(object):
    def __init__(self):
        with open('scenarios-for-study.json', 'r') as f:
            data = json.load(f)
        self.scenarios = data['scenarios']
        shuffle(self.scenarios)
        self.start_time = datetime.now()
        self.done = list()
        self.pre_survey = dict()
        self.post_questionnaire = dict()
        console.log(self.scenarios)
    
    def asdict(self):
        return {
            'scenarios': self.scenarios,
            'start_time': self.start_time,
            'done': self.done,
            'post_questionnaire': self.post_questionnaire
        }

# Test endpoint to check if the server is live
class Test(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api is live!'}

# Start/resume the study for a particular user
# If the specified email is already associated with a run, resume study
# If the specified email is new, begin a new run
class Start(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api/start is live!'}
    
    def post(self):
        # Get the provided email
        email = request.form.get('email')
        if email is None:
            email = json.loads(request.data)['email']
        print('Email:', email)
        
        # Load the users list
        try:
            users = pickle.load( open('./study-utils/users.p', 'rb') )
        except:
            users = dict()
        
        if email in users.keys():   # Get the already existing user
            user = users[email]
            console.log(user.scenarios)
            scenarios_left = [s for s in user.scenarios if s not in user.done]
            status_code = 200
            response = {
                'scenarios': scenarios_left
            }
        else:   # Store the user in the users list
            user = User()
            users[email] = user
            status_code = 201
            response = {
                'scenarios': user.scenarios
            }
        
        pickle.dump( users, open('./study-utils/users.p', 'wb') )
        
        # Return
        return response, status_code, {'Access-Control-Allow-Origin': '*'}

class Import(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api/import is live!'}

    def post(self):
        # Initialize a new project
        projects = [('0x' + d) for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
        if len(projects) == 0:
            new_project_id = '{:08x}'.format(1)
        else:
            project_ids = [int(d, 0) for d in projects]
            new_project_id = '{:08x}'.format(max(project_ids) + 1)
        new_project_dir = './store/' + new_project_id
        
        # Save the new project
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
        email = request.form.get('email')
        answers = request.form.get('answers')
        if scenario_id is None or email is None or answers is None:
            scenario_id = json.loads(request.data)['scenario_id']
            email = json.loads(request.data)['email']
            answers = json.loads(request.data)['answers']
        print(scenario_id)
        with open('scenarios.json', 'r') as f:
            scenarios_list = json.load(f)
        scenario = scenarios_list[scenario_id]
        target_fd = scenario['target_fd']
        project_info = {
            'email': email,
            'scenario_id': scenario_id,
            'scenario': scenario
        }

        # Get the user from the users list
        try:
            users = pickle.load( open('./study-utils/users.p', 'rb'))
        except:
            return {'msg': '[ERROR] users does not exist'}, 400, {'Access-Control-Allow-Origin': '*'}
        
        # Save the user's questionnaire responses
        if email not in users.keys():
            return {'msg': '[ERROR] no user exists with this email'}, 400, {'Access-Control-Allow-Origin': '*'}
        
        user = users[email]
        user.pre_survey = answers
        user.scenarios = user.scenarios[1:]
        users[email] = user

        # Save the users object updates
        pickle.dump( users, open('./study-utils/users.p', 'wb') )

        with open(new_project_dir + '/project_info.json', 'w') as f:
            json.dump(project_info, f, indent=4)

        print('*** Project info saved ***')

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

        # X = set()
        
        # Initialize hypothesis parameters
        fd_metadata = dict()
        h_space = scenario['hypothesis_space']
        for h in h_space:

            # Calculate the mean and variance
            h['vio_pairs'] = set(tuple(vp) for vp in h['vio_pairs'])
            mu = h['conf']
            if mu == 1:
                mu = 0.99999
            variance = 0.0025
            
            # Calculate alpha and beta
            alpha, beta = helpers.initialPrior(mu, variance)
            
            # Initialize the FD metadata object
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
            print('conf:', h['conf'])

            # # Build the
            # for i in data.index:
            #     for j in data.index:
            #         if i == j:
            #             continue

            #         X |= h['vio_pairs']
                    
            #         match = True if i not in h['vios'] and j not in h['vios'] else False

            #         if match is True and ((i, j) not in X and (j, i) not in X):
            #             if i < j:
            #                 X.add((i, j))
            #             else:
            #                 X.add((j, i)) 

            fd_metadata[h['cfd']] = fd_m

        # print(len(X))
        current_iter += 1

        study_metrics = dict()
        study_metrics['iter_err_precision'] = list()
        study_metrics['iter_err_recall'] = list()
        study_metrics['iter_err_f1'] = list()
        study_metrics['all_err_precision'] = list()
        study_metrics['all_err_recall'] = list()
        study_metrics['all_err_f1'] = list()
        pickle.dump( study_metrics, open(new_project_dir + '/study_metrics.p', 'wb') )

        pickle.dump( interaction_metadata, open(new_project_dir + '/interaction_metadata.p', 'wb') )
        pickle.dump( fd_metadata, open(new_project_dir + '/fd_metadata.p', 'wb') )
        pickle.dump( current_iter, open(new_project_dir + '/current_iter.p', 'wb') )
        pickle.dump( fd_metadata[target_fd].vio_pairs, open(new_project_dir + '/X.p', 'wb') )

        print('*** Metadata and objects initialized and saved ***')

        # Return information to the user
        returned_data = {
            'header': header,
            'project_id': new_project_id,
            'description': scenario['description']
        }
        response = json.dumps(returned_data)
        return response, 201, {'Access-Control-Allow-Origin': '*'}

# Get the first sample for a scenario interaction
class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api/sample is live!'}
    
    def post(self):
        # Get the project ID
        project_id = request.form.get('project_id')
        if project_id is None:
            # print(request.data)
            project_id = json.loads(request.data)['project_id']
        sample_size = 10
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)

        # Calculate the start time of the interaction
        start_time = time.time()
        pickle.dump( start_time, open('./store/' + project_id + '/start_time.p', 'wb') )

        print('*** Project info loaded ***')

        # Get data
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        X = pickle.load( open('./store/' + project_id + '/X.p', 'rb') )
        
        # Build sample
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

        # Add ID to s_out (for use on frontend)
        s_out.insert(0, 'id', s_out.index, True)

        # Return information to the user
        response = {
            'sample': s_out.to_json(orient='index'),
            'X': [list(v) for v in sample_X],
            'feedback': json.dumps(feedback),
            'true_pos': 0,
            'false_pos': 0,
            'msg': '[SUCCESS] Successfully built sample.'
        }
        return response, 200, {'Access-Control-Allow-Origin': '*'}

# Take in and analyze user feedback, and return a new sample
class Feedback(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api/feedback is live!'}
    
    def post(self):
        # Get the project ID for the interaction and the user's feedback object
        project_id = request.form.get('project_id')
        if project_id is None:
            req = json.loads(request.data)
            project_id = req['project_id']
            feedback_dict = req['feedback']
        else:
            feedback_dict = json.loads(request.form.get('feedback'))

        print(project_id)

        feedback = pd.DataFrame.from_dict(feedback_dict, orient='index')
        sample_size = 10

        print('*** Necessary objects loaded ***')

        # Get the current iteration count and current time
        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        print(current_iter)
        current_time = time.time()

        curr_sample_X = pickle.load( open('./store/' + project_id + '/current_X.p', 'rb') )
        X = pickle.load( open('./store/' + project_id + '/X.p', 'rb') )

        print('*** Iteration counter updated ***')

        # Get the project info
        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)

        print('*** Project info loaded ***')
        
        # Load the dataset
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)

        print('*** Loaded dirty dataset ***')

        # Record the user's feedback and analyze it
        s_in = data.iloc[feedback.index]
        print('*** Extracted sample from dataset ***')
        helpers.recordFeedback(data, feedback_dict, curr_sample_X, project_id, current_iter, current_time)
        target_fd = project_info['scenario']['target_fd'] # NOTE: For current sims only
        helpers.interpretFeedback(s_in, feedback, X, curr_sample_X, project_id, current_iter, current_time)

        # Build a new sample
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

        # Check if the scenario is done
        if current_iter <= 5:
            terminate = False
        else:
            terminate = helpers.checkForTermination(project_id)
        if current_iter > 15 or terminate is True:
            msg = '[DONE]'
        else:
            msg = '[SUCCESS]: Saved feedback and built new sample.'

        s_out.insert(0, 'id', s_out.index, True)
        print(s_out.index)

        # Save object updates
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        with open('./store/' + project_id + '/project_info.json', 'w') as f:
            json.dump(project_info, f)

        print(new_sample_X)
        
        # Return information to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'X': [list(v) for v in new_sample_X],
            'feedback': json.dumps(feedback),
            'msg': msg
        }
        response = json.dumps(returned_data)
        return response, 200, {'Access-Control-Allow-Origin': '*'}

# Store the user's responses to the post-interaction questionnaire
class PostInteraction(Resource):
    def get(self):
        return {'msg': '[SUCCESS] /duo/api/post-interaction is live!'}

    def post(self):
        # Get the provided email and scenario number
        email = request.form.get('email')
        scenario_id = request.form.get('scenario_id')
        answers = request.form.get('answers')
        if email is None or scenario_id is None or answers is None:
            email = json.loads(request.data)['email']
            scenario_id = json.loads(request.data)['scenario_id']
            answers = json.loads(request.data)['answers']
        
        # Get the user from the users list
        try:
            users = pickle.load( open('./study-utils/users.p', 'rb'))
        except:
            return {'msg': '[ERROR] users does not exist'}, 400, {'Access-Control-Allow-Origin': '*'}
        
        # Save the user's questionnaire responses
        user = users[email]
        user.post_questionnaire[str(scenario_id)] = answers
        users[email] = user
        
        # Save the users object updates
        pickle.dump( users, open('./study-utils/users.p', 'wb') )

        # Done
        return '', 201, {'Access-Control-Allow-Origin': '*'}

api.add_resource(Test, '/duo/api')
api.add_resource(Start, '/duo/api/start')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Feedback, '/duo/api/feedback')
api.add_resource(PostInteraction, '/duo/api/post-interaction')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')