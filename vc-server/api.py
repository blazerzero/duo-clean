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

app = Flask(__name__)
CORS(app)
api = Api(app)

class Import(Resource):
    def get(self):
        return {'test': 'success!'}

    def post(self):
        newProjectID = 0
        existingProjects = [('0x' + d) for d in os.listdir('./store/') if os.path.isdir(os.path.join('./store/', d))]
        newDir = ''
        if (len(existingProjects) == 0):
            newProjectID = "{:08x}".format(1)
        else:
            projectIDList = [int(d, 0) for d in existingProjects]
            print(projectIDList)
            newProjectID = "{:08x}".format(max(projectIDList) + 1)
            print(newProjectID)
        newDir = './store/' + newProjectID + '/'
        try:
            os.mkdir(newDir)
        except OSError:
            print ('Unable to create a new directory for the project.')
            return { 'error': 'Unable to create a new directory for the project.' }
        importedFile = request.files['file']
        f = open(newDir+'data.csv', 'w')
        data = importedFile.read().decode('utf-8-sig').split('\n')
        header = data[0].split(',')
        for line in [l for l in data if len(l) > 0]:
            trimmedLineList = [tL.strip() for tL in line.split(',')]
            trimmedLine = ','.join(trimmedLineList)
            #print(trimmedLineList)
            #print(trimmedLine)
            f.write(trimmedLine + '\n')
            #f.write('\n')
        f.close()
        #f = open(newDir+'fdnum.txt', 'w')
        f.close()
        #p = subprocess.Popen(['./DFDrunner', newDir+'data.csv', newDir+'fdnum.txt'])
        #p.wait()

        # DFD runner
        # os.system('./DFDrunner ' + newDir + 'data.csv ' + newDir + 'fdnum.txt');

        returned_data = {
            'header': header,
            'project_id': newProjectID,
        }
        #response = {'test': 'success'}
        response = json.dumps(returned_data)
        pprint(response)
        return response, 201

api.add_resource(Import, '/import')

if __name__ == '__main__':
    app.run(debug=True)
