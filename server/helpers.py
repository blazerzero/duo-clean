import random
from pprint import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np
import sys
import csv
import pickle
import math
import statistics
from collections import Counter

import analyze

class CellFeedback(object):
    def __init__(self, iter_num, marked, elapsed_time):
        self.iter_num = iter_num    # iteration number
        self.marked = marked            # whether or not the user marked the cell as noisy in this iteration
        self.elapsed_time = elapsed_time

class CFDWeightHistory(object):
    def __init__(self, iter_num, weight, elapsed_time):
        self.iter_num = iter_num
        self.weight = weight
        self.elapsed_time = elapsed_time

class CFDScore(object):
    def __init__(self, iter_num, score, elapsed_time):
        self.iter_num = iter_num
        self.score = score
        self.elapsed_time = elapsed_time

class StudyMetric(object):
    def __init__(self, iter_num, value, elapsed_time):
        self.iter_num = iter_num
        self.value = value
        self.elapsed_time = elapsed_time

# SAVE NOISE FEEDBACK FROM USER
def saveNoiseFeedback(data, feedback, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    current_time = pickle.load( open('./store/' + project_id + '/current_time.p', 'rb') )

    elapsed_time = current_time - start_time

    for idx in feedback.index:
        for col in feedback.columns:
            cell_metadata[int(idx)][col]['feedback_history'].append(CellFeedback(iter_num=current_iter, marked=bool(feedback.at[idx, col]), elapsed_time=elapsed_time))
    print('*** Latest feedback saved ***')
            
    # scoring function: score based on number of true errors correctly identified
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
        clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)    
    all_errors_found = 0
    all_errors_total = 0
    all_errors_marked = 0
    iter_errors_found = 0
    iter_errors_total = 0
    iter_errors_marked = 0

    for idx in data.index:
        for col in data.columns:
            if data.at[idx, col] != clean_dataset.at[idx, col]:
                all_errors_total += 1
                if idx in feedback.index:
                    iter_errors_total += 1
                    if bool(feedback.at[idx, col]) is True:
                        iter_errors_found += 1
                if len(cell_metadata[int(idx)][col]['feedback_history']) > 0 and cell_metadata[int(idx)][col]['feedback_history'][-1].marked is True:
                    all_errors_found += 1
            if len(cell_metadata[int(idx)][col]['feedback_history']) > 0 and cell_metadata[int(idx)][col]['feedback_history'][-1].marked is True:
                all_errors_marked += 1
                if idx in feedback.index:
                    iter_errors_marked += 1

    print('*** Score updated ***')

    project_info['true_pos'] = all_errors_found
    false_positives_full = all_errors_marked - all_errors_found
    project_info['false_pos'] = false_positives_full
    false_positives_iter = iter_errors_marked - iter_errors_found
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)
    print('*** Score saved ***')

    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
    print('*** Cell metadata updates saved ***')

    if all_errors_total > 0:
        true_error_pct_full = all_errors_found / all_errors_total
    else:
        true_error_pct_full = 0

    if iter_errors_total > 0:
        true_error_pct_iter = iter_errors_found / iter_errors_total
    else:
        true_error_pct_iter = 0

    if all_errors_marked > 0:
        error_accuracy_full = all_errors_found / all_errors_marked
    else:
        error_accuracy_full = 0

    if iter_errors_marked > 0:
        error_accuracy_iter = iter_errors_found / iter_errors_marked
    else:
        error_accuracy_iter = 0

    study_metrics['true_error_pct_full'].append(StudyMetric(iter_num=current_iter, value=true_error_pct_full, elapsed_time=elapsed_time))
    study_metrics['true_error_pct_iter'].append(StudyMetric(iter_num=current_iter, value=true_error_pct_iter, elapsed_time=elapsed_time))
    study_metrics['false_positives_full'].append(StudyMetric(iter_num=current_iter, value=false_positives_full, elapsed_time=elapsed_time))
    study_metrics['false_positives_iter'].append(StudyMetric(iter_num=current_iter, value=false_positives_iter, elapsed_time=elapsed_time))
    study_metrics['error_accuracy_full'].append(StudyMetric(iter_num=current_iter, value=error_accuracy_full, elapsed_time=elapsed_time))
    study_metrics['error_accuracy_iter'].append(StudyMetric(iter_num=current_iter, value=error_accuracy_iter, elapsed_time=elapsed_time))

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )


# DISCOVER CFDs THAT BEST EXPLAIN THE FEEDBACK GIVEN BY THE USER
def explainFeedback(full_dataset, dirty_sample, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    current_time = pickle.load( open('./store/' + project_id + '/current_time.p', 'rb') )

    elapsed_time = current_time - start_time

    print('*** Cell metadata object loaded ***')

    dirty_sample = dirty_sample.applymap(str)
    prepped_sample = dirty_sample.copy(deep=True)

    marked_cols = list()
    
    for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            cell = cell_metadata[int(idx)][col]

            if len(cell['feedback_history']) >= 1 and cell['feedback_history'][-1].marked is True:
                marked_cols.append(idx)
                break
    
    prepped_sample = prepped_sample.drop(marked_cols)
    print(prepped_sample)
    print('*** Feedback reflected in \'repaired\' dataset ***')

    prepped_sample_fp = './store/' + project_id + '/mining_sample.csv'
    if os.path.exists(prepped_sample_fp):
        with open(prepped_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()

    rep_dict = list(prepped_sample.T.to_dict().values())
    rep_header = rep_dict[0].keys()
    with open(prepped_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, rep_header)
        writer.writeheader()
        writer.writerows(rep_dict)
    print('*** Mining dataset saved as CSV ***')

    # process = sp.Popen(['./xplode/CTane', dirty_sample_fp, rep_sample_fp, '0.8', str(math.ceil(0.5*len(dirty_sample.index)))], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})   # XPlode
    process = sp.Popen(['./data/cfddiscovery/CFDD', prepped_sample_fp, str(math.ceil(0.5*len(prepped_sample.index))), '0.5', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
    res = process.communicate()
    print('*** CFDD finished running ***')

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        print('*** FD meteadata object loaded ***')
        output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
        cfds = [c for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd']]
        print('*** FDs from CFDD extracted ***')
        accepted_cfds = [c for c in cfds if c['cfd'].split(' => ')[0] != '()' and c['cfd'] in cfd_metadata.keys()]
        print('FDs from CFDD:', accepted_cfds)
        for c in accepted_cfds:

            cfd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=c['conf'], elapsed_time=elapsed_time))
            complexity_bias = analyze.sHeuristicSetRelation(c['cfd'], [c['cfd'] for c in accepted_cfds])
            print('*** Complexity bias calculated ***')

            # System's weighted prior on rule confidence
            weighted_conf = 0
            for h in cfd_metadata[c['cfd']]['conf_history']:
                weighted_conf += (h.score / (current_iter - h.iter_num + 1))
            print('*** Weighted FD confidence calculated ***')

            weight = complexity_bias + weighted_conf
            cfd_metadata[c['cfd']]['weight'] = weight
        
        cfd_metadata = normalizeWeights(cfd_metadata)
        print('*** CFDD output processed and FD weights updated ***')

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        print('*** CFD metadata updates saved ***')
    
    else:
        print('[ERROR] There was an error running CFDD')    


# BUILD SAMPLE
def buildSample(data, sample_size, project_id, sampling_method, current_iter):
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )   
    modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    current_time = pickle.load( open('./store/' + project_id + '/current_time.p', 'rb') )

    elapsed_time = current_time - start_time
    
    # GET SAMPLE
    if (sampling_method == 'DUO'):
        print('DUO-INFORMED SAMPLING')
        s_out = returnTuples(data, sample_size, project_id)     # Y = set(s_out.index)
    else:
        print('RANDOM SAMPLING')
        s_out = data.sample(n=sample_size)      # Y = set(s_out.index)

    # MODELING METRICS
    if current_iter == 0:
        new_X = set(s_out.index)    # X is just being created --> X = set(s_out.index)
    else:
        new_X = modeling_metadata['X'][-1].value | set(s_out.index)     # X = X | set(s_out.index)
    modeling_metadata['X'].append(StudyMetric(iter_num=current_iter, value=new_X, elapsed_time=elapsed_time))
    modeling_metadata['Y'].append(StudyMetric(iter_num=current_iter, value=set(s_out.index), elapsed_time=elapsed_time))

    for cfd, cfd_m in cfd_metadata.items():
        # print(cfd)
        # p(X | h)
        if cfd not in modeling_metadata['p_X_given_h'].keys():  # cfd was just discovered in this iteration
            modeling_metadata['p_X_given_h'][cfd] = list()
        if set(new_X).issubset(cfd_m['support']):
            p_X_given_h = math.pow((1/len(new_X)), sample_size) # p(X | h) = PI_i (p(x_i | h)), where each x_i is in X
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=p_X_given_h, elapsed_time=elapsed_time))
        else:
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
    
        # I(y in h)
        for y in new_X:
            if y not in modeling_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
                modeling_metadata['y_in_h'][cfd][y] = list()
            if y in cfd_m['support']:   # FD is applicable to y
                if y not in cfd_m['vios']:    # y is clean w.r.t. the FD
                    modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
                
                # UPDATED CHECK FOR DETECTABILITY
                else:
                    vio_pairs = [i for i in cfd_m['vio_pairs'] if y in i]
                    if len(vio_pairs) == 0:     # y is dirty w.r.t the FD and does not pair with ANY other row in the dataset
                        modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
                    else:   # y is dirty w.r.t. the FD and DOES pair with some other row in the dataset
                        match_found = False
                        for x in new_X:
                            if len([i for i in vio_pairs if x in i and x != y]) > 0:
                                match_found = True
                                break
                        if match_found is False:    # y does not pair with any other tuple in X w.r.t. the FD and is not detectable YET
                            modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
                        else:   # y pairs with another tuple in X w.r.t. the FD and is detectable
                            modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
            else:   # FD is not applicable to y
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
    
    print('IDs of tuples in next sample:')
    for idx in s_out.index:
        print(idx)

    pickle.dump( modeling_metadata, open('./store/' + project_id + '/modeling_metadata.p', 'wb') )
    
    return s_out


# BUILD PROBABILISTIC SAMPLE BASED ON VIOLATIONS OF FDs
def samplingDuo(data, sample_size, project_id):
    print('Sampling method: DUO')
    s_out = returnTuples(data, sample_size, project_id)
    return s_out


# RETURN TUPLES BASED ON WEIGHT
def returnTuples(data, sample_size, project_id):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    tuple_weights = {k: v['weight'] for k, v in tuple_metadata.items()}
    cfd_weights = {k: v['weight'] for k, v in cfd_metadata.items()}
    chosen_tuples = list()
    # chosen_fds = list()
    
    print('IDs of tuples in next sample:')
    while len(chosen_tuples) < sample_size:
        fd = pickSingleTuple(cfd_weights)
        # if fd not in chosen_fds:
        cfd_m = cfd_metadata[fd]
        if len(cfd_m['vios']) <= 1 or len(cfd_m['vio_pairs']) == 0:
            returned_tuple1 = pickSingleTuple(tuple_weights)
            returned_tuple2 = pickSingleTuple(tuple_weights)
        else:
            returned_tuple1, returned_tuple2 = random.choice(cfd_m['vio_pairs'])

        if returned_tuple1 not in chosen_tuples and returned_tuple2 not in chosen_tuples:
            chosen_tuples.append(returned_tuple1)
            chosen_tuples.append(returned_tuple2)
            print(returned_tuple1)
            print(returned_tuple2)
            
        # returned_tuple1 = random.choice(cfd_m['support'])
        # if returned_tuple1 not in chosen_tuples:
        #     chosen_tuples.append(returned_tuple1)
        #     returned_tuple2 = random.choice(cfd_m['support'])
        #     if returned_tuple2 not in chosen_tuples:
        #         chosen_tuples.append(returned_tuple2)
        #         print(returned_tuple1)
        #         print(returned_tuple2)
        #         chosen_fds.append(fd)

        if len(chosen_tuples) >= len(tuple_weights.keys()):
            break
    
    print(data)
    print(chosen_tuples)
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
            # print(tup)
            return tup


# NORMALIZE WEIGHTS BETWEEN 0 AND 1
def normalizeWeights(m_unnormalized):
    m_normalized = m_unnormalized
    m_weight_sum = sum([v['weight'] for _, v in m_unnormalized.items()])
    for k in m_normalized.keys():
        m_normalized[k]['weight'] = m_normalized[k]['weight'] / m_weight_sum

    return m_normalized


# GET THE USER'S TRUE POSITIVE AND FALSE POSITIVE COUNTS
def getUserScores(project_id):
    with open('./store/' + project_id + '/project_info.json') as f:
        project_info = json.load(f)
    return project_info['true_pos'], project_info['false_pos']
