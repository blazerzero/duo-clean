from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from random import sample
from pprint import pprint
import json
import os
import subprocess
import helpers
import time
import pandas as pd
import numpy as np

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
            open(newDir + 'discovered_cfds.txt', 'w').close()
            newDir += '00000001/'
            os.mkdir(newDir)
        except OSError:
            print ('[ERROR] Unable to create a new directory for the project.')
            return {'msg': '[ERROR] Unable to create a new directory for the project.'}
        importedFile = request.files['file']
        f = open(newDir+'data.csv', 'w')
        data = importedFile.read().decode('utf-8-sig').split('\n')
        header = data[0].split(',')
        for line in [l for l in data if len(l) > 0]:
            trimmedLineList = [tL.strip() for tL in line.split(',')]
            trimmedLine = ','.join(trimmedLineList)
            f.write(trimmedLine + '\n')
        f.close()

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
        print(request.form)
        print(request.form.get('project_id'))
        project_id = request.form.get('project_id')
        sample_size = int(request.form.get('sample_size'))
        existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        iteration_list = [int(d, 0) for d in existing_iters]
        print(iteration_list)
        current_iter = "{:08x}".format(max(iteration_list))
        print(current_iter)
        data = pd.read_csv('./store/' + project_id + '/' + current_iter + '/data.csv')
        s_out = helpers.buildSample(data, min(sample_size, len(data.index))).to_json(orient='index')   # SAMPLING FUNCTION GOES HERE; FOR NOW, BASIC SAMPLER

        returned_data = {
            'sample': s_out,
            'msg': '[SUCCESS] Successfully retrieved sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200


class Clean(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Clean test success!'}

    def post(self):
        print(request.form)
        print(request.form.get('project_id'))
        print(request.form.get('data'))
        print(request.form.get('sample_size'))

        print('About to read form data');

        project_id = request.form.get('project_id')
        s_in = request.form.get('data')
        sample_size = int(request.form.get('sample_size'))

        print('Read form data')

        existing_iters = [('0x' + f) for f in os.listdir('./store/' + project_id + '/') if os.path.isdir(os.path.join('./store/' + project_id + '/', f))]
        iteration_list = [int(d, 0) for d in existing_iters]
        print(iteration_list)
        current_iter = "{:08x}".format(max(iteration_list))
        print(current_iter)

        d_dirty = pd.read_csv('./store/' + project_id + '/' + current_iter + '/data.csv')
        print(d_dirty)
        d_rep = helpers.applyUserRepairs(d_dirty, s_in)
        print('here')
        current_iter = "{:08x}".format(int('0x'+current_iter, 0) + 1)
        print('here1')
        os.mkdir('./store/' + project_id + '/' + current_iter + '/')
        d_rep.to_csv('./store/' + project_id + '/' + current_iter + '/data.csv', encoding='utf-8', index=False)
        print('about to discover CFDs')
        top_cfds = helpers.discoverCFDs(project_id, current_iter)
        #discovered_cfds = helpers.addNewCfdsToList(top_cfds, project_id)
        helpers.addNewCfdsToList(top_cfds, project_id) # TODO; TEMPORARY IMPLEMENTATION

        #d_rep = helpers.buildCover(d_rep, discovered_cfds)
        d_rep = helpers.buildCover(d_rep, top_cfds)

        picked_cfd_list = helpers.pickCfds(top_cfds, 1)      # TODO; TEMPORARY IMPLEMENTATION
        if picked_cfd_list is not None:
            d_rep = helpers.applyCfdList(d_rep, picked_cfd_list)

        d_rep = d_rep.drop(columns=['cover'])

        d_rep.to_csv('./store/' + project_id + '/' + current_iter + '/data.csv', encoding='utf-8', index=False)
        np.savetxt('./store/' + project_id + '/' + current_iter + '/top_cfds.txt', top_cfds, fmt="%s")

        s_out = helpers.buildSample(d_rep, sample_size).to_json(orient='index')     # TODO; TEMPORARY IMPLEMENTATION

        returned_data = {
            'sample': s_out,
            'msg': '[SUCCESS] Successfully applied and generalized repair and retrived new sample.'
        }
        response = json.dumps(returned_data)
        pprint(response)
        return response, 200


class Result(Resource):
    def get(self):
        return {'msg': '[SUCCESS] Result test success!'}

    def post(self):
        print(request.form)
        print(request.form.get('project_id'))


api.add_resource(Import, '/import')
api.add_resource(Sample, '/sample')
api.add_resource(Clean, '/clean')
api.add_resource(Result, '/result')

if __name__ == '__main__':
    app.run(debug=True)
