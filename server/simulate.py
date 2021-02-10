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
    def __init__(self, fd, a, b, support, vios, vio_pairs):
        self.lhs = fd.split(' => ')[0][1:-1].split(', ')
        self.rhs = fd.split(' => ')[1].split(', ')
        self.alpha = a
        self.alpha_history = [a]
        self.beta = b
        self.beta_history = [b]
        self.conf = (a / (a+b))
        self.support = support
        self.vios = vios
        self.vio_pairs = vio_pairs

def initialPrior(mu, variance):
    beta = (1 - mu) * ((mu * (1 - mu) / variance) - 1)
    alpha = (mu * beta) / (1 - mu)
    return alpha, beta

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

def run(s, b_type, decision_type, stat_calc):
    if b_type == 'oracle':
        p_max = 0.9
    elif b_type == 'informed':
        p_max = 0.9
    else:
        p_max = 0.5

    if s is None:
        s = '0'

    with open('./scenarios.json', 'r') as f:
        scenarios = json.load(f)
    scenario = scenarios[s]
    target_fd = scenario['target_fd']
    h_space = scenario['hypothesis_space']

    fd_metadata = dict()

    iter_num = 0
    
    for h in h_space:
        if h['cfd'] != target_fd:
            continue
        
        h['vio_pairs'] = set(tuple(vp) for vp in h['vio_pairs'])

        if b_type == 'oracle':
            # conf = next(i for i in scenario['clean_hypothesis_space'] if i['cfd'] == h['cfd'])['conf']
            mu = next(i for i in scenario['clean_hypothesis_space'] if i['cfd'] == h['cfd'])['conf']
            variance = 0.00000001
            alpha, beta = initialPrior(mu, variance)
            # alpha = 1
            # beta = 1
        if b_type == 'informed':
            mu = h['conf']
            variance = 0.01
            alpha, beta = initialPrior(mu, variance)
        else:
            alpha = 1
            beta = 1
        
        fd_m = FDMeta(
            fd=h['cfd'],
            a=alpha,
            b=beta,
            support=h['support'],
            vios=h['vios'],
            vio_pairs=h['vio_pairs']
        )
        print('iter:', iter_num)
        print('alpha:', fd_m.alpha)
        print('beta:', fd_m.beta)
        # for i in full_dirty_data.index:
        #     for j in full_dirty_data.index:
        #         if i == j:
        #             continue
        #         match = True
        #         for lh in fd_m.lhs:
        #             if full_dirty_data.at[i, lh] != full_dirty_data.at[j, lh]:
        #                 match = False
        #                 break

        #         if match is True and ((i, j) not in X and (j, i) not in X):
        #             if i < j:
        #                 X.add((i, j))
        #                 X_per_FD[h['cfd']].add((i, j))
        #             else:
        #                 X.add((j, i))
        #                 X_per_FD[h['cfd']].add((j, i))
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
        
        print('prepped data')
    except Exception as e:
        print(e)
        return

    print('initialized feedback object')
    msg = ''
    iter_num = 0

    pruned_X = set()
    marked_rows = set()

    max_marked = 1
    mark_prob = 0.5

    while msg != '[DONE]':
        iter_num += 1
        print('iter:', iter_num)
        feedbackMap = buildFeedbackMap(data, feedback, header)

        # p_X = 0

        # Bayesian behavior
        for fd, fd_m in fd_metadata.items():
            if fd != target_fd:
                continue

            # Step 1: update hyperparameters
            if b_type != 'oracle':
                # successes_X = set()
                # failures_X = set()
                successes = 0
                failures = 0

                for i in sample.index:
                    if i not in fd_m.vios:
                        successes += 1
                    else:
                        failures += 1

                print('successes:', successes)
                print('failures:', failures)

                fd_m.alpha += successes
                fd_m.alpha_history.append(fd_m.alpha)
                fd_m.beta += failures
                fd_m.beta_history.append(fd_m.beta)
                print('alpha:', fd_m.alpha)
                print('beta:', fd_m.beta)

        # Step 2: mark errors according to new beliefs
        # TODO: Upgrade q_t for consider multiple FDs
        fd_m = fd_metadata[target_fd]
        q_t = fd_m.alpha / (fd_m.alpha + fd_m.beta) if b_type != 'oracle' else fd_m.conf
        print('theta:', q_t)
        marked_vios = set()
        for row in data.keys():
            # for fd, fd_m in fd_metadata.items():      # NOTE: comment out temporarily
            if b_type == 'oracle':
                if stat_calc == 'precision':
                    q_t = mark_prob
                elif stat_calc == 'recall':
                    if len(marked_vios) > max_marked:
                        q_t = 0
                else:
                    continue
            else:
                if len([x for x in pruned_X if int(row) in x]) > 0:
                    continue

            if len([x for x in sample_X if int(row) in x]) > 0 and len([x for x in fd_m.vio_pairs if int(row) in x]) > 0:
                if decision_type == 'coin-flip':
                    decision = np.random.binomial(1, q_t)
                else:
                    decision = 1 if q_t >= p_max else 0
                    
                print(decision)
                if decision == 1:
                    for col in feedbackMap[row].keys():
                        feedbackMap[row][col] = True
                    marked_rows.add(int(row))
                    for x in [i for i in fd_m.vio_pairs if i in sample_X and row in i]:
                        marked_vios.add(x)
                    for x in [i for i in sample_X if int(row) in i]:
                        pruned_X.add(x)
                else:
                    for col in feedbackMap[row].keys():
                        feedbackMap[row][col] = False
                    if int(row) in marked_rows:
                        marked_rows.remove(int(row))
                    pruned_X = {x for x in pruned_X if int(row) not in x}
                    marked_vios = {(x, y) for (x, y) in marked_vios if x in sample.index and y in sample.index and int(row) not in (x, y)}
        print(marked_rows)

        # print(feedbackMap)
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
            if mark_prob < 0.9:
                mark_prob += 0.1
            elif mark_prob < 0.95:
                mark_prob += 0.01

        except Exception as e:
            print(e)
            msg = '[DONE]'

    pickle.dump( fd_metadata, open('./store/' + project_id + '/fd_metadata.p', 'wb') )

if __name__ == '__main__':
    s = sys.argv[1]
    b_type = sys.argv[2]
    decision_type = sys.argv[3]
    num_runs = int(sys.argv[4])
    stat_calc = None if len(sys.argv) < 6 else sys.argv[5]
    for i in range(0, num_runs):
        run(s, b_type, decision_type, stat_calc)