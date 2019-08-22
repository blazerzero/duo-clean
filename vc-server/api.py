from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort
from flask_cors import CORS
from random import sample

from helpers import map_csv

app = Flask(__name__)
CORS(app)
api = Api(app)

class Data(Resource):
    def get(self):
        return {'test': 'success!'}

    def post(self):
        parser = reqparse.RequestParser()
        args = parser.parse_args()
        imported_file = args['file']
        header, csv_data, relationships, maxOccurence = parse_csv(imported_file)
        sent_data = sample(csv_data, 10)
        response = {
            'header': header,
            'data': sent_data,
            'relationships': relationships,
            'maxOccurence': maxOccurence,
        }
        return response, 201

api.add_resource(Data, '/import')

if __name__ == '__main__':
    app.run(debug=True)
