from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from random import sample
from pprint import pprint
import json
import os
import helpers
import time

app = Flask(__name__)
CORS(app)
api = Api(app)

class Import(Resource):
    def get(self):
        return {'test': 'success!'}

    def post(self):
        existingProjects = [('0x' + d) for d in os.listdir('./store/') if os.path.isdir(os.path.join('./store/', d))]
        newDir = ''
        if (len(existingProjects) == 0):
            newDir = './store/00000001/'
        else:
            projectHexes = [int(d, 0) for d in existingProjects]
            print(projectHexes)
            newProjectHex = "{:08x}".format(max(projectHexes) + 1)
            print(newProjectHex)
            newDir = './store/' + newProjectHex + '/'
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
            f.write(line)
            f.write('\n')
        f.close()
        #f = open(newDir+'fdnum.txt', 'w')
        f.close()
        #p = subprocess.Popen(['./DFDrunner', newDir+'data.csv', newDir+'fdnum.txt'])
        #p.wait()

        # DFD runner
        #os.system('./DFDrunner ' + newDir + 'data.csv ' + newDir + 'fdnum.txt');

        # TANE runner
        os.system('./TANErunner ' + newDir + 'data.csv ' + newDir + 'fdnum.txt');

        #tane.runTANE('../data.csv', 'r')
        #print('done finding FDs')
        resF = open(newDir+'fdnum.txt', 'r')
        res = resF.read()
        resLines = res.split('\n')
        resF.close()
        fdFile = open(newDir+'fdlist.csv', 'a')
        convertedRes = list()
        for row in [r for r in resLines if len(r) > 0]:
            #print(row)
            lhsRow = filter(lambda a: a != ',', row.split(' -> ')[0].split(' '))
            #print(lhsRow)
            #print(row.split(' -> ')[1])
            rhsRow = row.split(' -> ')[1]
            #time.sleep(3)
            lhs = list()
            for colNum in lhsRow:
                lhs.append(header[int(colNum)-1])
            #key = tuple(lhs)
            rhs = header[int(rhsRow)-1]
            convertedRes.append((lhs, rhs))
            l = '('
            for e in [atr for atr in lhs if atr != ',']:
                l += e
                l += ' '
            l = l[:-1]
            l += '), '
            l += rhs
            fdFile.write(l + '\n')
        fdFile.close()
        #print(header)
            #convertedRes.append((lhs, rhs))
        #dataJSON = request.data.decode('utf8').replace("'", '"')
        #data = json.loads(dataJSON)
        #print(data['formData'])
        #importedFile = request.form['file']
        #print('got file')
        #header, csv_data, relationships, maxOccurence = helpers.map_csv(importedFile)
        #print('mapped values')

        sent_data = sample(convertedRes, 10)
        #print('got sample')
        returned_data = {
            'header': header,
            'data': sent_data,
        }
        #response = {'test': 'success'}
        response = json.dumps(returned_data)
        pprint(response)
        return response, 201

api.add_resource(Import, '/import')

if __name__ == '__main__':
    app.run(debug=True)
