import random
from pprint import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np
import sys
import pickle
from collections import Counter

sys.path.insert(0, './charm/keywordSearch/')
import charm

class ValueHistory(object):
    def __init__(self, value, agent, iter_num, changed):
        self.value = value      # the value
        self.agent = agent      # who set this cell to this value at this point, user or system
        # self.cfd_applied = cfd_applied      # the CFD that resulted in this value
        self.iter = iter_num                # the iteration number for this value
        self.changed = changed              # whether this value is a change from the previous state

class TupleNoiseHistory(object):
    def __init__(self, noisy, iter_num):
        self.noisy = noisy
        self.iter_num = iter_num

class CFDConfidenceHistory(object):
    def __init__(self, iter_num, conf):
        self.iter_num = iter_num
        self.conf = conf

def applyUserRepairs(d_prev, s_in, project_id, current_iter):
    d_curr = d_prev
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )

    for idx in s_in.index:
        for col in s_in.columns:
            if d_curr.at[idx, col] != s_in.at[idx, col]:
                d_curr.at[idx, col] = s_in.at[idx, col]
                value_metadata[idx][col]['history'].append(ValueHistory(s_in.at[idx, col], 'user', current_iter, True))
            else:
                value_metadata[idx][col]['history'].append(ValueHistory(s_in.at[idx, col], 'user', current_iter, False))

    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )
    return d_curr

def applyNoiseFeedback(data, noisy_tuples, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )

    for idx in data.index:
        if idx in noisy_tuples.keys():
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(noisy_tuples[idx], current_iter))
        else:
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(False, current_iter))

    pickle.dumps( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

def runCFDDiscovery(data, project_id, current_iter):
    fp = './store/' + project_id + '/in_progress.csv'

    process = sp.Popen(['./data/cfddiscovery/CFDD', fp, str(0.7*len(data.index)), '0.7', '4'])
    res = process.communicate()

    if process.returncode == 0 and '[ERROR]' not in res[0]:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        output = json.loads(res[0].decode('latin-1'))
        cfds = output['cfds']
        for c in cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDConfidenceHistory(current_iter, c['conf']))
        
        pickle.dumps( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
    
        return cfds
    
    else:
        return None
        

def buildSample(data, sample_size, project_id):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    tuple_weights = {k: v['weight'] for k, v in tuple_metadata.items()}
    chosen_tuples = list()

    while len(chosen_tuples) < sample_size:
        returned_tuple = pickSingleTuple(tuple_weights)
        if returned_tuple not in chosen_tuples:
            chosen_tuples.append(returned_tuple)
            tuple_metadata[returned_tuple]['expl_freq'] += 1
        if len(chosen_tuples) >= len(tuple_weights.keys()):
            break

    s_out = data.iloc[chosen_tuples]
    return s_out

def pickSingleTuple(tuple_weights):
    chance = random.uniform(0, 1)
    cumulative = 0
    total = sum(tuple_weights.values())
    for id, weight in tuple_weights.items():
        cumulative += weight/total
        if cumulative > chance:
            tup = id
            del (id, weight)
            print(tup)
            return tup
