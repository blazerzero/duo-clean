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
from scipy.stats import beta as betaD
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
    cols = header
    for row in data.keys():
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

def run(s, b_type, decision_type):
    p_max = 0.9 if b_type == 'informed' else 0.5

    if int(s) == 0:
        full_dirty_data_fp = '../data/dirty_toy.csv'
    elif int(s) % 4 == 1:
        full_dirty_data_fp = '../data/dirty_airport_1.csv'
    elif int(s) % 4 == 2:
        full_dirty_data_fp = '../data/dirty_airport_2.csv'
    elif int(s) % 4 == 3:
        full_dirty_data_fp = '../data/dirty_omdb_3.csv'
    elif int(s) % 4 == 0:
        full_dirty_data_fp = '../data/dirty_omdb_4.csv'
    else:
        print('there was a problem determining the master data filepath. defaulting to example scenario')
        full_dirty_data_fp = '../data/dirty_toy.csv'
        s = '0'

    full_dirty_data = pd.read_csv(full_dirty_data_fp, keep_default_na=False)
    with open('../scenarios.json', 'r') as f:
        scenarios = json.load(f)
    scenario = scenarios[s]
    # h_space = scenario['hypothesis_space']
    target_fd = scenario['target_fd']
    h_space = [s for s in scenario['hypothesis_space'] if s['cfd'] == target_fd]    # NOTE: for one-FD step only

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
        for i in full_dirty_data.index:
            for j in full_dirty_data.index:
                if i == j:
                    continue
                match = True
                for lh in fd_m.lhs:
                    if full_dirty_data.at[i, lh] != full_dirty_data.at[j, lh]:
                        match = False
                        break

                if match is True and ((i, j) not in X and (j, i) not in X):
                    if i < j:
                        X.add((i, j))
                    else:
                        X.add((j, i)) 
        fd_metadata[h['cfd']] = fd_m

    header = None
    project_id = None

    try:
        r = requests.post('http://localhost:5000/duo/api/import', data={'scenario_id': str(s)})
        res = json.loads(r.json())
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
        res = json.loads(r.json())

        sample = res['sample']
        print('extracted sample')
        sample_X = set(tuple(x) for x in res['X'])
        print('got vios')
        data = json.loads(sample)
        feedback = json.loads(res['feedback'])
        print('parsed data')
        for row in data.keys():
            for j in data[row].keys():
                if j == 'id':
                    continue
                if data[row][j] is None:
                    data[row][j] = ''
                elif type(data[row][j]) != 'str':
                    data[row][j] = str(data[row][j])
        
        # p_X = (math.factorial(len(sample_X)) * math.factorial(len(X) - len(sample_X))) / math.factorial(len(X))
        p_X = math.factorial(len(sample_X))
        for i in range(0, len(sample_X)):
            p_X /= (len(X) - i)
        print('prepped data')
    except Exception as e:
        print(e)

    print('initialized feedback object')
    msg = ''
    iter_num = 0

    pruned_rows_per_FD = dict()
    while msg != '[DONE]':
        iter_num += 1
        print('iter:', iter_num)
        feedbackMap = buildFeedbackMap(data, feedback, header)

        # Bayesian behavior
        for fd, fd_m in fd_metadata.items():

            # Step 1: update hyperparameters
            p_X_given_theta = 1
            successes_X = set()
            failures_X = set()

            # NOTE: Conditions for adding to successes/failures needs verifying
            for x in sample_X:
                if x not in fd_m.vio_pairs:
                    p_X_given_theta *= fd_m.theta
                    successes_X.add(x)
                else:
                    p_X_given_theta *= (1 - fd_m.theta)
                    failures_X.add(x)
            print(p_X_given_theta)
            print(fd_m.p_theta)
            print(p_X)
            fd_m.p_theta = (p_X_given_theta * fd_m.p_theta) / p_X
            fd_m.p_theta_history.append(fd_m.p_theta)
            fd_m.alpha += len(successes_X)
            fd_m.alpha_history.append(fd_m.alpha)
            fd_m.beta += len(failures_X)
            fd_m.beta_history.append(fd_m.beta)
            fd_m.theta = fd_m.alpha / (fd_m.alpha + fd_m.beta)
            fd_m.theta_history.append(fd_m.theta)

            # Step 2: mark errors according to new beliefs
            for row in data.keys():
                p_t_in_C_given_theta = 1
                for x in sample_X:
                    if row in x:
                        p_t_in_C_given_theta *= fd_m.theta
                    else:
                        p_t_in_C_given_theta *= (1 - fd_m.theta)
                # print(p_t_in_C_given_theta)
                if decision_type == 'coin-flip':    # weighted coin flip-based decisions
                    decision = np.random.binomial(1, p_t_in_C_given_theta)
                else:   # threshold-based decisions
                    decision = 1 if p_t_in_C_given_theta >= p_max else 0
                if decision == 0:   # user thinks tuple is NOT clean
                    if fd not in pruned_rows_per_FD.keys() or row not in pruned_rows_per_FD[fd]:
                        for rh in fd_m.rhs:
                            feedbackMap[row][rh] = True
                else:   # user thinks tuple IS clean
                    for rh in fd_m.rhs:
                        feedbackMap[row][rh] = False

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
        
        print('built new feedback map')

        formData = {
            'project_id': project_id,
            'feedback': json.dumps(feedback),
            'refresh': 0,
            'is_new_feedback': 1 if is_new_feedback is True else 0
        }

        try:
            r = requests.post('http://localhost:5000/duo/api/clean', data=formData)
            res = json.loads(r.json())
            msg = res['msg']
            if msg != '[DONE]':
                sample = res['sample']
                sample_X = set(tuple(x) for x in res['X'])
                feedback = json.loads(res['feedback'])
                data = json.loads(sample)

                for row in data.keys():
                    for j in data[row].keys():
                        if j == 'id':
                            continue

                        if data[row][j] is None:
                            data[row][j] = ''
                        elif type(data[row][j]) != 'str':
                            data[row][j] = str(data[row][j])
                
                # p_X = (math.factorial(len(sample_X)) * math.factorial(len(X) - len(sample_X))) / math.factorial(len(X))
                p_X = math.factorial(len(sample_X))
                for i in range(0, len(sample_X)):
                    p_X /= (len(X) - i)

        except Exception as e:
            print(e)
            msg = '[DONE]'

    pickle.dump( fd_metadata, open('../store/' + project_id + '/simulated_user_fd_metadata.p', 'wb') )

if __name__ == '__main__':
    s = sys.argv[1]
    b_type = sys.argv[2]
    decision_type = sys.argv[3]
    run(s, b_type, decision_type)