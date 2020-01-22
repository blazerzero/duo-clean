from flask import Flask, request, send_file
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
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

app = Flask(__name__)
CORS(app)
api = Api(app)


class Import(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Import test success!'}

    def post(self):
        newProjectID = 0
        existingProjects = [('0x' + d) for d in os.listdir('./store/') if os.path.isdir(os.path.join('./store/', d))]
        newDir = ''
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
            newDir += '00000001/'
            os.mkdir(newDir)
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

        #df = pd.read_csv(newDir + 'data.csv')

        returned_data = {
            'header': header,
            'project_id': newProjectID,
            'msg': '[SUCCESS] Successfully created new project with project ID = ' + newProjectID + '.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200


class Sample(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Sample test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        sample_size = int(request.form.get('sample_size'))
        existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        iteration_list = [int(d, 0) for d in existing_iters]
        current_iter = "{:08x}".format(max(iteration_list))
        data = pd.read_csv('./store/' + project_id + '/' + current_iter + '/data.csv', keep_default_na=False)
        tuple_metadata = pd.DataFrame(index=data.index, columns=['weight', 'expl_freq'])
        tuple_metadata['weight'] = 1
        tuple_metadata['expl_freq'] = 0
        value_metadata = dict()
        for idx in data.index:
            value_metadata[idx] = dict()
            for col in data.columns:
                value_metadata[idx][col]['history'] = [data.at[idx, col]]
                value_metadata[idx][col]['disagreement'] = 0
        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
        pickle.dump( value_metadata, open('./store/' + project_id + '/00000001/value_metadata.p', 'wb') )

        s_out = helpers.buildSample(data, min(sample_size, len(data.index)), project_id)   # SAMPLING FUNCTION GOES HERE; FOR NOW, BASIC SAMPLER

        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'msg': '[SUCCESS] Successfully retrieved sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200


class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Clean test success!'}

    def post(self):
        project_id = request.form.get('project_id')
        s_in = request.form.get('data')
        sample_size = int(request.form.get('sample_size'))

        existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        iteration_list = [int(d, 0) for d in existing_iters]
        current_iter = "{:08x}".format(max(iteration_list) + 1)
        prev_iter = "{:08x}".format(max(iteration_list))

        d_dirty = pd.read_csv('./store/' + project_id + '/' + prev_iter + '/data.csv', keep_default_na=False)
        d_rep = helpers.applyUserRepairs(d_dirty, s_in)
        os.mkdir('./store/' + project_id + '/' + current_iter + '/')
        os.mknod('./store/' + project_id + '/' + current_iter + '/applied_cfds.txt')
        d_rep.to_csv('./store/' + project_id + '/' + current_iter + '/data.csv', encoding='utf-8', index=False)
        top_cfds = helpers.discoverCFDs(project_id, current_iter)
        d_rep['cover'] = None

        if top_cfds is not None and isinstance(top_cfds, np.ndarray):
            helpers.addNewCfdsToList(top_cfds, project_id)
            picked_cfd_list = helpers.pickCfds(top_cfds, 1)
            #TODO: Build query from user repairs
            #picked_cfd_list = helpers.pickCfds(query, 1)

            if picked_cfd_list is not None:
                np.savetxt('./store/' + project_id + '/' + current_iter + '/applied_cfds.txt', picked_cfd_list,
                           fmt="%s")
                d_rep = helpers.buildCover(d_rep, picked_cfd_list)
                d_rep = helpers.applyCfdList(project_id, d_rep, picked_cfd_list)
            else:
                with open('./store/' + project_id + '/' + current_iter + '/applied_cfds.txt', 'w') as f:
                    print('No CFDs were applied.', file=f)

        d_rep = d_rep.drop(columns=['cover'])
        helpers.reinforceTuplesBasedOnContradiction(project_id, current_iter, d_rep)
        d_rep.to_csv('./store/' + project_id + '/' + current_iter + '/data.csv', encoding='utf-8', index=False)

        tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')

        for idx in d_rep.index:
            if idx in s_in.index:
                tuple_metadata.at[idx, 'expl_freq'] += 1
            else:
                tuple_metadata.at[idx, 'weight'] += (1 - (tuple_metadata.at[idx, 'expl_freq']/int('0x'+current_iter, 0)))    # reinforce tuple based on how frequently been explored

        #tuple_metadata['weight'] = tuple_metadata['weight'] / tuple_metadata['weight'].sum()
        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')

        s_out = helpers.buildSample(d_rep, sample_size, project_id)

        returned_data = {
            'sample': s_out.to_json(orient='index'),
            'msg': '[SUCCESS] Successfully applied and generalized repair and retrived new sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200


class Download(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Result test success!'}

    def post(self):
        project_id = request.form.get('project_id')

        existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if
                          os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        iteration_list = [int(d, 0) for d in existing_iters]
        latest_iter = "{:08x}".format(max(iteration_list))

        finalZip = BytesIO()

        with ZipFile(finalZip, 'w') as zf:
            zf.write('./store/' + project_id + '/' + latest_iter + '/data.csv')
            zf.write('./store/' + project_id + '/' + latest_iter + '/applied_cfds.txt')
        finalZip.seek(0)

        return send_file(finalZip, attachment_filename='charm_cleaned.zip', as_attachment=True)


api.add_resource(Import, '/import')
api.add_resource(Sample, '/sample')
api.add_resource(Clean, '/clean')
api.add_resource(Download, '/download')

if __name__ == '__main__':
    app.run(debug=True)
