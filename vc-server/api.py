from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api, reqparse, abort
# from flask_restful.utils import cors
from flask_cors import CORS, cross_origin
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
        data = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)                                              # read in the data
        tuple_metadata = pd.DataFrame(index=data.index, columns=['weight', 'expl_freq'])                                                # initialize tuple metadata DataFrame
        tuple_metadata['weight'] = 1                                                                                                    # initialize tuple weights to 1
        tuple_metadata['expl_freq'] = 0                                                                                                 # initialize exploration frequency of tuples to 0
        value_metadata = dict()                                                                                                         # initialize value metadata fictionary

        current_iter = '00000000'                                                                                                       # initial data is considered iteration 0
        for idx in data.index:                                                                                                          # for each row in the dataset
            value_metadata[idx] = dict()                                                                                                    # initialize dictionary for this row
            for col in data.columns:                                                                                                        # for each column in the dataset
                value_metadata[idx][col] = dict()                                                                                               # initialize dictionary for this cell
                value_metadata[idx][col]['history'] = list()                                                                                    # initialize cell value history list
                value_metadata[idx][col]['history'].append(helpers.ValueHistory(data.at[idx, col], 'system', None, current_iter, False))        # add initial value to cell history list
                value_metadata[idx][col]['disagreement'] = 0                                                                                    # initialize cell value disagreement to 0 as there is no disagreement currently

        s_out = data.sample(n=sample_size)                                                                                              # get sample for user

        diffs = dict()
        diffs['cells'] = list()
        diffs['tups'] = list()
        pickle.dump( diffs, open('./store/' + project_id + '/diffs.p', 'wb') )
        helpers.calcDiffs(data, './test/team-clean.csv', project_id, 'system', current_iter)

        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')                                                         # save the tuple metadata DataFrame
        pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )                                        # save the value metadata object
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )                                            # save the current iteration number

        # return this data to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps([]),
            'msg': '[SUCCESS] Successfully retrieved sample.'
        }
        response = json.dumps(returned_data)                                                                                            # stringify returned data
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Clean test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        s_in = request.form.get('data')
        sample_size = int(request.form.get('sample_size'))

        current_iter = pickle.load(open('./store/' + project_id + '/current_iter.p', 'rb'))                 # load the current iteration number
        current_iter = "{:08x}".format(int('0x'+current_iter, 0)+1)                                         # new iteration, so increment the current iteration number

        d_dirty = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)               # read in dirty data as DataFrame
        s_df = pd.read_json(s_in, orient='index')                                                           # turn sample into DataFrame
        d_rep, changed_ids = helpers.applyUserRepairs(d_dirty, s_df, project_id, current_iter)              # map the user's cell repairs to the respective cells in the full dataset
        helpers.calcDiffs(d_rep, './test/team-clean.csv', project_id, 'user', current_iter)
        d_rep.to_csv('./store/' + project_id + '/after.csv', encoding='utf-8', index=False)                 # save the user-repaired full dataset as a csv file (for XPlode)
        top_cfds = helpers.discoverCFDs(project_id)                                                         # run XPlode to discover new CFDs for before and after-repair versions of the dataset
        d_rep['cover'] = None                                                                               # initialize the cover for each row

        # CFD applied map holds info on which CFD was applied (or None if no CFD was applied) to each cell in each iteration
        if os.path.isfile('./store/' + project_id + '/cfd_applied_map.p'):
            cfd_applied_map = pickle.load( open('./store/' + project_id + '/cfd_applied_map.p', 'rb') )     # CFD applied map exists, so load it
        else:
            cfd_applied_map = dict()                                                                        # initialize CFD applied map
        print(top_cfds)

        # initialize dictionary in CFD applied map for this iteration
        cfd_applied_map[current_iter] = dict()
        for idx in d_rep.index:
            cfd_applied_map[current_iter][idx] = dict()
            for col in d_rep.columns:
                cfd_applied_map[current_iter][idx][col] = None                                              # initialize the CFD mapping for each cell to None

        contradictions = dict()                                                                             # initialize a dictionary of the contradictions that occur during cleaning

        if top_cfds is not None and isinstance(top_cfds, np.ndarray):                                       # XPlode successfully returned a non-empty array of discovered CFDs
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

            helpers.addNewCfdsToList(top_cfds, project_id, current_iter, formatted_query)                                                               # Update receiver with new CFDs
            picked_cfd_list, picked_cfd_id_list = helpers.pickCfds(project_id, formatted_query, 3)                                                      # Get CFDs from receiver

            if picked_cfd_list is not None and len(picked_cfd_list) > 0:                                                                                # Successfully got CFDs from receiver
                with open('./store/' + project_id + '/applied_cfds.txt', 'a') as f:
                    np.savetxt(f, [c['cfd'] for c in picked_cfd_list], fmt="%s")                                                                            # Print selected CFDs into applied_cfds.txt
                patterns = dict()
                value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
                d_rep['cover'] = np.empty(len(d_rep.index), dtype=str)
                for c in picked_cfd_list:
                    lhs = c['cfd'].split(' => ')[0][1:-1]
                    rhs = c['cfd'].split(' => ')[1]
                    print(lhs)
                    print(rhs)
                    patterns.update(helpers.fd2cfd(d_rep, lhs, rhs, value_metadata, current_iter))

                    #TODO: Integrate patterns into buildCover and applyCfd
                    d_rep = helpers.buildCover(d_rep, lhs, rhs, patterns)                                                                                      # Build the CFD cover for this iteration
                d_dirty['cover'] = d_rep['cover']
                d_rep, cfd_applied_map, contradictions = helpers.applyCfdList(project_id, d_dirty, picked_cfd_list, picked_cfd_id_list, cfd_applied_map, current_iter)    # Apply the selected CFDs to the dataset
            else:
                pass
                #with open('./store/' + project_id + '/applied_cfds.txt', 'w') as f:
                #    print('No CFDs were applied.', file=f)

        d_rep = d_rep.drop(columns=['cover'])
        helpers.reinforceTuplesBasedOnContradiction(project_id, current_iter, d_rep)                                        # reinforce data tuples based on contradiction metrics for each individual cell
        d_rep.to_csv('./store/' + project_id + '/before.csv', encoding='utf-8', index=False)                                # save the cleaned dataset as a CSV file (this is the new "before" file for the next iteration)

        helpers.calcDiffs(d_rep, './test/team-clean.csv', project_id, 'system', current_iter)

        tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')                                      # load the tuple metadata DataFrame

        # reinforce tuples based on how frequently they have been explored prior to this iteration
        for idx in d_rep.index:                                                                                             # for each row in the dataset
            if idx in s_df.index:                                                                                               # if this row was in the sample
                tuple_metadata.at[idx, 'expl_freq'] += 1                                                                            # increment the exploration frequency of this tuple
            else:                                                                                                               # if this row was NOT in the sample
                tuple_metadata.at[idx, 'weight'] += (1 - (tuple_metadata.at[idx, 'expl_freq']/int('0x'+current_iter, 0)))           # reinforce the weight of this tuple by incorporating how its exploration frequency compares to the total number of iterations

        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')                                             # save the tuple metadata DataFrame

        s_out = helpers.buildSample(d_rep, sample_size, project_id, cfd_applied_map, current_iter)                          # generate a new sample

        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )                                # save the current iteration number
        pickle.dump( cfd_applied_map, open('./store/' + project_id + '/cfd_applied_map.p', 'wb') )                          # save the updated cell/CFD map

        contradictions = [{'row': k[0], 'col': k[1]} for k, v in contradictions.items()]                                    # convert keys of contradiction tracker into a serializable format; meeting criterion 2 of Roth and Erev 1995

        # return this data to the user
        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'contradictions': json.dumps(contradictions),
            'msg': '[SUCCESS] Successfully applied and generalized repair and retrived new sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200, {'Access-Control-Allow-Origin': '*'}


class Download(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Result test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        finalZip = BytesIO()

        # with ZipFile(finalZip, 'w') as zf:
        #    zf.write('./store/' + project_id + '/after.csv')
            # zf.write('./store/' + project_id + '/applied_cfds.txt')
        # finalZip.seek(0)

        #return send_file(finalZip, attachment_filename='charm_cleaned.zip', as_attachment=True), 200, {'Access-Control-Allow-Origin': '*'}
        return send_file('./store/' + project_id + '/after.csv', attachment_filename='charm_cleaned.csv', as_attachment=True), 200, {'Access-Control-Allow-Origin': '*'}


api.add_resource(TestLive, '/duo/api/test')
api.add_resource(TestCORSLive, '/duo/api/testcors')
api.add_resource(Import, '/duo/api/import')
api.add_resource(Sample, '/duo/api/sample')
api.add_resource(Clean, '/duo/api/clean')
api.add_resource(Download, '/duo/api/download')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
