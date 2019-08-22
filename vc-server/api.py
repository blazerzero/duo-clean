from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from random import sample
from pprint import pprint
import json

import helpers

app = Flask(__name__)
CORS(app)
api = Api(app)

class Data(Resource):
    def get(self):
        return {'test': 'success!'}

    def post(self):
        imported_file = request.files['file']
        #dataJSON = request.data.decode('utf8').replace("'", '"')
        #data = json.loads(dataJSON)
        #print(data['formData'])
        #imported_file = request.form['file']
        #print('got file')
        header, csv_data, relationships, maxOccurence = helpers.map_csv(imported_file)
        #print('mapped values')
        sent_data = sample(csv_data, 10)
        #print('got sample')
        returned_data = {
            'header': header,
            'data': sent_data,
            'relationships': repr(relationships),
            'maxOccurence': maxOccurence,
        }
        #response = {'test': 'success'}
        response = json.dumps(returned_data)
        pprint(response)
        return response, 201

api.add_resource(Data, '/import')

if __name__ == '__main__':
    app.run(debug=True)
