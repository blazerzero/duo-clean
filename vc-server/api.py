from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from random import sample
from pprint import pprint
import json
from './TANE/' import tane

import helpers

app = Flask(__name__)
CORS(app)
api = Api(app)

class Import(Resource):
    def get(self):
        return {'test': 'success!'}

    def post(self):
        imported_file = request.files['file']
        f = open('data.csv', 'w')
        data = imported_file.read().decode('utf-8-sig')
        header = data.split('\n')[0]
        f.write(lines)
        f.close()
        tane.runTANE('../data.csv', 'r')
        resF = open('TANE/result.txt')
        res = resF.read()
        resLines = res.split('\n')
        resF.close()
        fdFile = open('fd.csv', 'a')
        convertedRes = list()
        for row in resLines:
            lhsRow = row.split(' -> ')[0].split(' ')
            rhs = row.split(' -> ')[1].pop()
            lhs = list()
            for colNum in lhsRow:
                lhs.append(header[colNum-1])
            #key = tuple(lhs)
            convertedRes.append((lhs, rhs))
            fdFile.write((lhs, rhs))
        fdFile.close()
            #convertedRes.append((lhs, rhs))
        #dataJSON = request.data.decode('utf8').replace("'", '"')
        #data = json.loads(dataJSON)
        #print(data['formData'])
        #imported_file = request.form['file']
        #print('got file')
        #header, csv_data, relationships, maxOccurence = helpers.map_csv(imported_file)
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
