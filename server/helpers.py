import random
from pprint import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np
import sys
import pickle
from math import isnan
from collections import Counter

# sys.path.insert(0, './charm/keywordSearch/')
# import charm

# CELL VALUE HISTORY OBJECT
class ValueHistory(object):
    def __init__(self, value, iter_num, changed):
        self.value = value      # the value
        # self.agent = agent      # who set this cell to this value at this point, user or system
        # self.cfd_applied = cfd_applied      # the CFD that resulted in this value
        self.iter_num = iter_num                # the iteration number for this value
        self.changed = changed              # whether this value is a change from the previous state

class CellStatistic(object):
    def __init__(self, vocc, vspr, vdis, iter_num):
        self.vocc = vocc            # value occurrence
        self.vspr = vspr            # value spread
        self.vdis = vdis            # value disagreement
        self.iter_num = iter_num    # iteration number

# TUPLE NOISE HISTORY OBJECT
class TupleNoiseHistory(object):
    def __init__(self, noisy, iter_num):
        self.noisy = noisy          # whether or not the tuple is noisy at iteration = iter_num
        self.iter_num = iter_num    # iteration number

class CFDConfidenceHistory(object):
    def __init__(self, iter_num, conf):
        self.iter_num = iter_num
        self.conf = conf

# MAP USER-SUBMITTED REPAIRS FROM SAMPLE TO FULL DATASET
def applyUserModFeedback(d_prev, s_in, project_id, current_iter):
    d_curr = d_prev
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )

    for idx in s_in.index:
        for col in s_in.columns:
            if d_curr[idx][col] != s_in.at[idx, col]:
                d_curr[idx][col] = s_in.at[idx, col]
                cell_metadata[idx][col]['history'].append(ValueHistory(value=s_in.at[idx, col], iter_num=current_iter, changed=True))
            else:
                cell_metadata[idx][col]['history'].append(ValueHistory(value=d_curr[idx][col], iter_num=current_iter, changed=False))

    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
    return d_curr

# APPLY NOISE FEEDBACK FROM USER
def applyNoiseFeedback(data, noisy_tuples, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )

    for idx in range(0, len(data)):
        if idx in noisy_tuples.keys():
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(noisy=noisy_tuples[idx], iter_num=current_iter))
        else:
            tuple_metadata[idx]['noise_history'].append(TupleNoiseHistory(noisy=False, iter_num=current_iter))

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

# DISCOVER CFDS THAT COULD APPLY OVER DATASET AND THEIR CONFIDENCES
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
        for c in cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDConfidenceHistory(iter_num=current_iter, conf=c['conf']))
        
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
    
        return cfds
    
    else:
        return None

# UPDATE TUPLE WEIGHTS BASED ON INTERACTION STATISTICS
def reinforceTuples(data, project_id, current_iter):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    iter_num = int('0x' + current_iter, 0)
    for idx in data.index:
        reinforcementValue = 0

        # Evaluate exploration frequency
        expl_score = (iter_num - tuple_metadata[idx]['expl_freq']) / iter_num
        for col in data.columns:

            # Occurrence of null value in cell
            occur_null = 0
            if data.at[idx, col] == '' or isnan(data.at[idx, col]):
                occur_null = (1 / len(data.columns))

            # Value occurrence
            vocc_prev = cell_metadata[idx][col]['stats'][-1].vocc
            vocc_curr = len(set([vh.value for vh in cell_metadata[idx][col]['history']]))
            vocc_delta = vocc_curr - vocc_prev

            # Value spread
            vspr_curr = vocc_curr / iter_num

            # Value disagreement (overall and delta)
            cell_history = Counter([vh.value for vh in cell_metadata[idx][col]['history']])
            num_occurrences_mode = cell_history.most_common(1)[0][1]
            vdis_prev = cell_metadata[idx][col]['stats'][-1].vdis
            vdis_curr = 1 - (num_occurrences_mode/len(cell_metadata[idx][col]['history']))
            vdis_delta = vdis_curr - vdis_prev
            # cell_metadata[idx][col]['disagreement'] = vdis_curr
            cell_metadata[idx][col]['stats'].append(CellStatistic(vocc=vocc_curr, vspr=vspr_curr, vdis=vdis_curr, iter_num=current_iter))

            # Stops weight underflow
            if vdis_delta < 0:
                vdis_delta = 0

            # Check if the user changed the value of the cell from the last iteration
            latest_value = cell_metadata[idx][col]['history'][-1]
            user_mod_score = 0
            if latest_value.changed == True:
                user_mod_score = (1 / len(data.columns))

            reinforcementValue += (occur_null + vocc_delta + vspr_curr + vdis_curr + vdis_delta + user_mod_score)

        reinforcementValue += expl_score

        # Based on noise feedback
        for nh in tuple_metadata[idx]['noise_history']:
            if nh.noisy == True:
                reinforcementValue += (nh.iter_num / len(tuple_metadata[idx]['noise_history']))
                
        tuple_metadata.at[idx, 'weight'] += reinforcementValue

    tuple_metadata = normalizeTupleWeights(tuple_metadata)

    print('Tuple weights:')
    pprint([v['weight'] for _, v in tuple_metadata.items()])
    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
        
# BUILD PROBABILISTIC SAMPLE
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

# SELECT ONE TUPLE TO ADD TO SAMPLE
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

# UPDATE TUPLE WEIGHTS BASED ON EXPLORATION
# def reinforceTuplesPostSample(sample, project_id, current_iter):
#     tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
#     iter_num = int('0x' + current_iter, 0)

    # Based on exploration frequency of each tuple
#     for idx in sample.index:
#         expl_freq = tuple_metadata[idx]['expl_freq']
#         tuple_metadata[idx]['weight'] += (1 - expl_freq/(iter_num+1))

#     tuple_metadata = normalizeTupleWeights(tuple_metadata)
    
#     print('Tuple weights:')
#     pprint([v['weight'] for _, v in tuple_metadata.items()])

#     pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )

# NORMALIZE TUPLE WEIGHTS BETWEEN 0 AND 1
def normalizeTupleWeights(tm_unnormalized):
    tm_normalized = tm_unnormalized
    tm_weight_sum = sum([v['weight'] for _, v in tm_unnormalized.items()])
    for idx in tm_normalized.keys():
        tm_normalized[idx]['weight'] = tm_normalized[idx]['weight'] / tm_weight_sum

    return tm_normalized
