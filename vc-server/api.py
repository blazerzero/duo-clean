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
import shutil

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
            #os.mknod(newDir + 'applied_cfds.txt')
            open(newDir + 'applied_cfds.txt', 'w').close()
        #    newDir += '00000001/'
        #    os.mkdir(newDir)
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
        #current_iter = "{:08x}".format(max(iteration_list))
        data = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)
        tuple_metadata = pd.DataFrame(index=data.index, columns=['weight', 'expl_freq'])
        tuple_metadata['weight'] = 1
        tuple_metadata['expl_freq'] = 0
        value_metadata = dict()
        for idx in data.index:
            value_metadata[idx] = dict()
            for col in data.columns:
                value_metadata[idx][col] = dict()
                #value_metadata[idx][col]['history'] = [(data.at[idx, col], None)]
                value_metadata[idx][col]['history'] = list()
                value_metadata[idx][col]['history'].append(helpers.ValueHistory(data.at[idx, col], 'system', None, '00000000', False))
                value_metadata[idx][col]['disagreement'] = 0

        s_out = data.sample(n=sample_size)
        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
        pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )

        current_iter = '00000001'
        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
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

        #existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        #iteration_list = [int(d, 0) for d in existing_iters]
        current_iter = pickle.load(open('./store/' + project_id + '/current_iter.p', 'rb'))

        #prev_iter = "{:08x}".format(max(iteration_list))

        d_dirty = pd.read_csv('./store/' + project_id + '/before.csv', keep_default_na=False)
        d_rep, changed_ids = helpers.applyUserRepairs(d_dirty, s_in, project_id, current_iter)
        current_iter = "{:08x}".format(int('0x'+current_iter, 0)+1)
        #os.mkdir('./store/' + project_id + '/' + current_iter + '/')
        d_rep.to_csv('./store/' + project_id + '/after.csv', encoding='utf-8', index=False)
        top_cfds = helpers.discoverCFDs(project_id, current_iter)
        d_rep['cover'] = None

        cfd_applied_map = None
        if os.path.isfile('./store/' + project_id + '/cfd_applied_map.p'):
            cfd_applied_map = list()
        else:
            cfd_applied_map = pickle.load( open('./store/' + project_id + '/cfd_applied_map.p', 'rb') )
        print('here')
        cfd_applied_map.append(dict())
        print('Initialize CFD applied map for this iteration')
        print(top_cfds)
        for idx in d_rep.index:
            cfd_applied_map[-1][idx] = dict()
            for col in d_rep.columns:
                cfd_applied_map[-1][idx][col] = None

        if top_cfds is not None and isinstance(top_cfds, np.ndarray):
            helpers.addNewCfdsToList(top_cfds, project_id, current_iter)
            #picked_cfd_list, picked_cfd_id_list = helpers.pickCfds(top_cfds, 1)
            #TODO: Build query from user repairs
            query = ''
            for idx in changed_ids:
                for col in s_in.columns:
                    query += (col + '=' + s_in.at[idx, col] + ' ')
            query = query[:-1]
            picked_cfd_list, picked_cfd_id_list = helpers.pickCfds(query, 1)

            if picked_cfd_list is not None:
                np.savetxt('./store/' + project_id + '/applied_cfds.txt', np.array(picked_cfd_list),
                           fmt="%s")
                d_rep = helpers.buildCover(d_rep, picked_cfd_list)
                d_rep, cfd_applied_map = helpers.applyCfdList(project_id, d_rep, picked_cfd_list, picked_cfd_id_list, current_iter)
            else:
                with open('./store/' + project_id + '/applied_cfds.txt', 'w') as f:
                    print('No CFDs were applied.', file=f)

        d_rep = d_rep.drop(columns=['cover'])
        helpers.reinforceTuplesBasedOnContradiction(project_id, current_iter, d_rep, cfd_applied_map)
        d_rep.to_csv('./store/' + project_id + '/before.csv', encoding='utf-8', index=False)

        tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')

        for idx in d_rep.index:
            if idx in s_in.index:
                tuple_metadata.at[idx, 'expl_freq'] += 1
            else:
                tuple_metadata.at[idx, 'weight'] += (1 - (tuple_metadata.at[idx, 'expl_freq']/int('0x'+current_iter, 0)))    # reinforce tuple based on how frequently been explored

        #tuple_metadata['weight'] = tuple_metadata['weight'] / tuple_metadata['weight'].sum()
        tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')

        s_out = helpers.buildSample(d_rep, sample_size, project_id, cfd_applied_map, current_iter)

        pickle.dump( current_iter, open('./store/' + project_id + '/current_iter.p', 'wb') )
        pickle.dump( cfd_applied_map, open('./store/' + project_id + '/cfd_applied_map.p', 'wb') )

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
