import requests
import random
from pprint import pprint
import os
import json
import pandas as pd
import numpy as np
import sys
import pickle
import math
import scipy.special as sc
import scipy.stats.beta as betaD
import re

# class Hypothesis(object):
#     def __init__(self, fd, conf, support, vios, vio_pairs):
#         self.fd = fd
#         self.conf = conf
#         self.support = support
#         self.vios = vios
#         self.vio_pairs = vio_pairs

class FDMeta(object):
    def __init__(self, fd, theta, p_theta, a, b, support, vios, vio_pairs):
        self.lhs = fd.split(' => ')[0][1:-1].split(', ')
        self.rhs = fd.split(' => ')[1].split(', ')
        self.theta = theta
        self.theta_history = [theta]
        self.p_theta = p_theta
        self.p_theta_history = [p_theta]
        self.p_X_given_theta = None
        self.p_X_given_theta_history = []
        self.alpha = a
        self.alpha_history = [a]
        self.beta = b
        self.beta_history = [b]
        self.support = support
        self.vios = vios
        self.vio_pairs = vio_pairs

def buildFeedbackMap(data, feedback, header):
    feedbackMap = dict()
    rows = data.keys()
    cols = header
    for row in rows:
        tup = dict()
        for col in cols:
            trimmedCol = re.sub(r'/[\n\r]+/g', '', col)
            cell = next(f for f in feedback if f['row'] == int(data[row]['id']) and f['col'] == trimmedCol)
            tup[col] = cell['marked']
        feedbackMap[row] = tup
    return feedbackMap

def shuffleFDs(fds):
    return random.shuffle(fds)

def pTheta(theta, a, b):
    return (math.pow(theta, (a-1)) * math.pow((1-theta), (b-1))) / sc.beta(a, b)

def run(s, b_type):
    p_max = 0.9 if b_type == 'informed' else 0.5

    # if s == 0:
    #     master_data_fp = '../data/toy.csv'
    #     full_dirty_data_fp = '../data/dirty_toy.csv'
    # elif s % 4 == 1:
    #     master_data_fp = '../data/airport_1.csv'
    #     full_dirty_data_fp = '../data/dirty_airport_1.csv'
    # elif s % 4 == 2:
    #     master_data_fp = '../data/airport_2.csv'
    #     full_dirty_data_fp = '../data/dirty_airport_2.csv'
    # elif s % 4 == 3:
    #     master_data_fp = '../data/omdb_3.csv'
    #     full_dirty_data_fp = '../data/dirty_omdb_3.csv'
    # elif s % 4 == 0:
    #     master_data_fp = '../data/omdb_4.csv'
    #     full_dirty_data_fp = '../data/dirty_omdb_4.csv'
    # else:
    #     print('there was a problem determining the master data filepath. defaulting to example scenario')
    #     master_data_fp = '../data/toy.csv'
    #     full_dirty_data_fp = '../data/dirty_toy.csv'
    #     s = 0

    # full_dirty_data = pd.read_csv(full_dirty_data_fp, keep_default_na=False)
    with open('../scenarios.json', 'r') as f:
        scenarios = json.load(f)
    
    scenario = scenarios[s]
    h_space = scenario['hypothesis_space']
    # target_fds = scenario['cfds']
    # fds = [h['cfd'] for h in h_space]

    fd_metadata = dict()
    X = set()
    for h in h_space:
        h['vio_pairs'] = set(tuple(vp) for vp in h['vio_pairs'])
        if b_type == 'informed':
            mu = h['conf']
            a = 1
            b = a * (a - mu) / mu
            theta = h['conf']
        else:
            a = 1
            b = 1
            theta = 0.5
        
        p_theta = pTheta(theta, a, b)
        fd_m = FDMeta(
            fd=h['cfd'],
            theta=theta,
            p_theta=p_theta,
            a=a,
            b=b,
            support=h['support'],
            vios=h['vios'],
            vio_pairs=h['vio_pairs']
        )
        fd_metadata[h['cfd']] = fd_m
        X |= h['vio_pairs']

    header = None
    project_id = None

    try:
        r = requests.post('http://localhost:5000/duo/api/import', data={'scenario_id': str(s)})
        res = r.json()
        header = res['header']
        project_id = res['project_id']
    except Exception as e:
        print(e)

    print(project_id)

    data = None
    feedback = None
    sample_X = list()
    p_X = None

    try:
        print('before sample')
        r = requests.post('http://localhost:5000/duo/api/sample', data={'project_id': project_id})
        print('after sample')
        res = r.json()
        sample = r['sample']
        sample_X = r['sample_vios']
        data = json.loads(sample).values()
        print('parsed data')
        for row in data:
            for j in row.keys():
                if j == 'id':
                    continue

                if row[j] is None:
                    row[j] = ''
                elif type(row[j]) != 'str':
                    row[j] = str(row[j])
                if math.isnan(row[j]) is False and math.ceil(float(row[j]) - float(row[j])) == 0:
                    row[j] = str(math.ceil(row[j]))
        
        p_X = (math.factorial(len(sample_X)) * math.factorial(len(X) - len(sample_X))) / math.factorial(len(X))
        print('prepped data')
    except Exception as e:
        print(e)

    print('initialized feedback object')
    msg = ''
    iter_num = 0

    while msg != '[DONE]':
        iter_num += 1
        print('iter:', iter_num)
        feedbackMap = buildFeedbackMap(data, feedback, header)

        # Bayesian behavior
        user_X = set()

        # mark errors as see fit

        # update hyperparameters
        for _, fd_m in fd_metadata.items():
            p_X_given_theta = 1
            caught_X = set()
            missed_X = set()
            for x in [vio for vio in sample_X if vio in fd_m['vio_pairs']]:
                if x not in user_X:
                    p_X_given_theta *= fd_m['theta']
                    missed_X.add(x)
                else:
                    p_X_given_theta *= (1 - fd_m['theta'])
                    caught_X.add(x)
            
            fd_m['p_theta'] = (p_X_given_theta * fd_m['p_theta']) / p_X
            fd_m['p_theta_history'].append(fd_m['p_theta'])
            fd_m['alpha'] += len(caught_X)
            fd_m['alpha_history'].append(fd_m['alpha'])
            fd_m['beta'] += len(missed_X)
            fd_m['beta_history'].append(fd_m['beta'])

        feedback = dict()
        for f in feedbackMap.keys():
            feedback[data[f]['id']] = feedbackMap[f]

        is_new_feedback = False
        for idx in feedback.keys():
            for col in feedback[idx].keys():
                if feedback[idx][col] is True:
                    is_new_feedback = True
                    break
            if is_new_feedback is True:
                break
        
        formData = {
            'project_id': project_id,
            'feedback': feedback,
            'refresh': 0,
            'is_new_feedback': 1 if is_new_feedback is True else 0
        }

        try:
            r = requests.post('http://localhost:5000/duo/api/clean', data=formData)
            res = r.json()
            msg = res['msg']
            if msg != '[DONE]':
                sample = res['sample']
                sample_X = res['sample_vios']
                feedback = json.loads(feedback)
                data = json.loads(sample).values()

                for row in data:
                    for j in row.keys():
                        if j == 'id':
                            continue

                        if row[j] is None:
                            row[j] = ''
                        elif type(row[j]) != 'str':
                            row[j] = str(row[j])
                        if math.isnan(row[j]) is False and math.ceil(float(row[j]) - float(row[j])) == 0:
                            row[j] = str(math.ceil(row[j]))
        except Exception as e:
            print(e)
            msg = '[DONE]'

if __name__ == '__main__':
    s = int(sys.argv[2])
    b_type = sys.argv[3]
    run(s, b_type)