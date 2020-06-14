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
        self.iter_num = iter_num                # the iteration number for this value
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
            if d_curr[idx][col] != s_in.at[idx, col]:
                d_curr[idx][col] = s_in.at[idx, col]
                value_metadata[idx][col]['history'].append(ValueHistory(s_in.at[idx, col], 'user', current_iter, True))
            else:
                value_metadata[idx][col]['history'].append(ValueHistory(s_in.at[idx, col], 'user', current_iter, False))

    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )
    return d_curr

def applyNoiseFeedback(data, noisy_tuples, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )

    for idx in range(0, len(data)):
        if idx in noisy_tuples.keys():
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(noisy_tuples[idx], current_iter))
        else:
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(False, current_iter))

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

def runCFDDiscovery(num_rows, project_id, current_iter):
    fp = './store/' + project_id + '/in_progress.csv'

    process = sp.Popen(['./data/cfddiscovery/CFDD', fp, str(0.7*num_rows), '0.7', '4'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    res = process.communicate()
    print('res:', res[0])

    if process.returncode == 0 and '[ERROR]' not in res[0].decode('latin-1'):
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        output = res[0].decode('latin-1')
        polished_output = output.replace(',]', ']')
        cfds = json.loads(polished_output)['cfds']
        # output = json.loads(res[0].decode('latin-1'))
        # cfds = output['cfds']
        for c in cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDConfidenceHistory(current_iter, c['conf']))
        
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
    
        return cfds
    
    else:
        return None

def reinforceTuplesPreSample(data, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
    for idx in data.index:
        reinforcementValue = 0
        for col in data.columns:
            vspr_prev = len(set([vh.value for vh in value_metadata[idx][col]['history'] if int('0x' + vh.iter_num, 0) < int('0x' + current_iter, 0)]))
            vspr_curr = len(set([vh.value for vh in value_metadata[idx][col]['history']]))
            vspr_delta = vspr_curr - vspr_prev

            historical_values = Counter([vh.value for vh in value_metadata[idx][col]['history']])
            num_occurrences_mode = historical_values.most_common(1)[0][1]
            vdis_prev = value_metadata[idx][col]['disagreement']
            vdis_curr = 1 - (num_occurrences_mode/vspr_curr)
            vdis_delta = vdis_curr - vdis_prev
            value_metadata[idx][col]['disagreement'] = vdis_curr

            if vdis_delta < 0:
                vdis_delta = 0

            curr_value = [h for h in historical_values if h[0] == data.at[idx, col]].pop()
            prev_value = [h for h in historical_values if h[0] == value_metadata[idx][col]['history'][-2].value].pop()

            if curr_value != prev_value:
                reinforcementValue += (1 / len(data.columns))

            reinforcementValue += (vspr_delta + vdis_curr + vdis_delta)

        for nh in tuple_metadata[idx]['noise_history']:
            if nh.noisy == True:
                reinforcementValue += (int('0x' + nh.iter_num, 0) / len(tuple_metadata[idx]['noise_history']))
                
        tuple_metadata.at[idx, 'weight'] += reinforcementValue

    tuple_metadata = normalizeTupleWeights(tuple_metadata)

    print('Tuple weights:')
    pprint([v['weight'] for _, v in tuple_metadata.items()])
    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )
        

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

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

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

def reinforceTuplesPostSample(sample, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    iter_num = int('0x' + current_iter, 0)

    for idx in sample.index:
        expl_freq = tuple_metadata[idx]['expl_freq']
        tuple_metadata[idx]['weight'] += (1 - expl_freq/(iter_num+1))

    tuple_metadata = normalizeTupleWeights(tuple_metadata)
    
    print('Tuple weights:')
    pprint([v['weight'] for _, v in tuple_metadata.items()])

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

def normalizeTupleWeights(tm_unnormalized):
    tm_normalized = tm_unnormalized
    tm_weight_sum = sum([v['weight'] for _, v in tm_unnormalized.items()])
    for idx in tm_normalized.keys():
        tm_normalized[idx]['weight'] = tm_normalized[idx]['weight'] / tm_weight_sum

    return tm_normalized
