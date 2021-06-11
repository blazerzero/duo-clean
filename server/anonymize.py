# Anonymizes participant details to hide PII

import json
import pickle
import copy
import numpy as np
from pkl2json import pkl2jsonRecursive
from api import User

def anonymize():
    users: dict[str, User] = pickle.load( open('./study-utils/users.p', 'rb') )
    with open('./study-utils/users.json', 'r') as f:
        users_json = json.load(f)
    anonymized_users: dict[str, User] = dict()
    for i, (email, user) in enumerate(users.items()):
        print(email)
        if '@anonymized.com' not in email and 'test' not in users_json[email]['background']:
            new_email = 'participant' + str(i+1) + '@anonymized.com'
            for run in user.runs:
                with open('./docker-out/' + run + '/project_info.json', 'r') as f:
                    project_info = json.load(f)
                project_info['email'] = new_email
                with open('./docker-out/' + run + '/project_info.json', 'w') as f:
                    json.dump(project_info, f)
            anonymized_users[new_email] = copy.deepcopy(users[email])
            anonymized_users[new_email].background = users_json[email]['background']
            # del users[email]
    pickle.dump( anonymized_users, open('./study-utils/users.p', 'wb') )
    pkl2jsonRecursive('real')

if __name__ == '__main__':
    anonymize()