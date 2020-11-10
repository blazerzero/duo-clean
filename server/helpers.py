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
def saveNoiseFeedback(data, feedback, project_id, current_iter, current_time):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )

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
    project_info['false_pos'] = all_errors_marked - all_errors_found
    # false_positives_iter = iter_errors_marked - iter_errors_found
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)
    print('*** Score saved ***')

    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
    print('*** Cell metadata updates saved ***')

    if iter_errors_marked > 0:
        precision = iter_errors_found / iter_errors_marked
    else:
        precision = 0
    
    if iter_errors_total > 0:
        recall = iter_errors_found / iter_errors_total
    else:
        recall = 0

    if precision > 0 and recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0

    study_metrics['precision'].append(StudyMetric(iter_num=current_iter, value=precision, elapsed_time=elapsed_time))
    study_metrics['recall'].append(StudyMetric(iter_num=current_iter, value=recall, elapsed_time=elapsed_time))
    study_metrics['f1'].append(StudyMetric(iter_num=current_iter, value=f1, elapsed_time=elapsed_time))

    '''if all_errors_total > 0:
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
    study_metrics['error_accuracy_iter'].append(StudyMetric(iter_num=current_iter, value=error_accuracy_iter, elapsed_time=elapsed_time))'''

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )


# DISCOVER CFDs THAT BEST EXPLAIN THE FEEDBACK GIVEN BY THE USER
def explainFeedback(full_dataset, dirty_sample, project_id, current_iter, current_time, refresh):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    # master_diff = pd.DataFrame.from_dict(project_info['scenario']['diff'], orient='index')

    elapsed_time = current_time - start_time

    print('*** Cell metadata object loaded ***')

    dirty_sample = dirty_sample.applymap(str)
    prepped_sample = dirty_sample.copy(deep=True)
    # master_prepped_sample = dirty_sample.copy(deep=True)

    marked_cols = list()
    # master_marked_cols = list()

    h_space = project_info['scenario']['hypothesis_space']

    if refresh == 1:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        # clean_fd_metadata = pickle.load( open('./store/' + project_id + '/clean_fd_metadata.p', 'rb') )
        for c in h_space:
            # cfd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=cfd_metadata[c['cfd']]['conf_history'][-1].score, elapsed_time=elapsed_time))
            # wCOMBO = analyze.aHeuristicCombo(c['cfd'], full_dataset)
            # phaCOMBO = np.prod([v for _, v in wCOMBO.items()])  # p(h | aCOMBO)
            # phsSR = analyze.sHeuristicSetRelation(c['cfd'], [c['cfd'] for c in h_space]) # p(h | sSR)
            # print('*** Complexity bias calculated ***')

            # System's weighted prior on rule confidence
            # weight = 0
            # for h in cfd_metadata[c['cfd']]['conf_history']:
            #     weight += (h.score / (current_iter - h.iter_num + 1))
            # print('*** Weighted FD confidence calculated ***')

            # weight = complexity_bias + weighted_conf
            cfd_metadata[c['cfd']]['weight'] = cfd_metadata[c['cfd']]['weight_history'][-1].weight
            
            # clean_fd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=clean_fd_metadata[c['cfd']]['conf_history'][-1].score, elapsed_time=elapsed_time))
            # wCOMBO = analyze.aHeuristicCombo(c['cfd'], full_dataset)
            # phaCOMBO = np.prod([v for _, v in wCOMBO.items()])  # p(h | aCOMBO)
            # phsSR = analyze.sHeuristicSetRelation(c['cfd'], [c['cfd'] for c in h_space]) # p(h | sSR)
            # System's weighted prior on rule confidence
            # weight = 0
            # for h in clean_fd_metadata[c['cfd']]['conf_history']:
            #     weight += (h.score / (current_iter - h.iter_num + 1))

            # weight = complexity_bias + weighted_conf
            # clean_fd_metadata[c['cfd']]['weight'] = clean_fd_metadata[c['cfd']]['weight_history'][-1].weight
        
        cfd_metadata = normalizeWeights(cfd_metadata)
        # clean_fd_metadata = normalizeWeights(clean_fd_metadata)
        for c in h_space:
            cfd_metadata[c['cfd']]['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_metadata[c['cfd']]['weight'], elapsed_time=elapsed_time))
            # clean_fd_metadata[c['cfd']]['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=clean_fd_metadata[c['cfd']]['weight'], elapsed_time=elapsed_time))

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        # pickle.dump( clean_fd_metadata, open('./store/' + project_id + '/clean_fd_metadata.p', 'wb') )
        return
    
    # USER DATA
    for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            cell = cell_metadata[int(idx)][col]

            if len(cell['feedback_history']) >= 1 and cell['feedback_history'][-1].marked is True:
                marked_cols.append(idx)
                break

    # GROUND TRUTH
    '''for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            if master_diff.at[str(idx), col] is False:
                master_marked_cols.append(idx)
                break'''
    
    prepped_sample = prepped_sample.drop(marked_cols)
    # print(prepped_sample)
    print('*** Feedback reflected in \'repaired\' dataset ***')

    prepped_sample_fp = './store/' + project_id + '/mining_sample.csv'
    if os.path.exists(prepped_sample_fp):
        with open(prepped_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()

    # master_prepped_sample = master_prepped_sample.drop(master_marked_cols)
    # print(master_prepped_sample)
    print('*** Feedback reflected in \'repaired\' dataset ***')

    '''master_prepped_sample_fp = './store/' + project_id + '/gt_mining_sample.csv'
    if os.path.exists(master_prepped_sample_fp):
        with open(master_prepped_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()'''

    rep_dict = list(prepped_sample.T.to_dict().values())
    rep_header = rep_dict[0].keys()
    with open(prepped_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, rep_header)
        writer.writeheader()
        writer.writerows(rep_dict)
    print('*** Mining dataset saved as CSV ***')

    '''master_rep_dict = list(master_prepped_sample.T.to_dict().values())
    master_rep_header = master_rep_dict[0].keys()
    with open(master_prepped_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, master_rep_header)
        writer.writeheader()
        writer.writerows(master_rep_dict)
    print('*** Mining dataset saved as CSV ***')'''

    # GROUND TRUTH
    '''clean_process = sp.Popen(['./data/cfddiscovery/CFDD', master_prepped_sample_fp, str(math.ceil(0.8*len(master_prepped_sample.index))), '0.8', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
    clean_res = clean_process.communicate()

    if clean_process.returncode == 0:
        clean_fd_metadata = pickle.load( open('./store/' + project_id + '/clean_fd_metadata.p', 'rb') )
        clean_output = clean_res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
        clean_cfds = [c for c in json.loads(clean_output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
        clean_accepted_cfds = [c for c in clean_cfds if c['cfd'] in clean_fd_metadata.keys()]
        for c in h_space:
            if c['cfd'] in [ac['cfd'] for ac in clean_accepted_cfds]:
                ac = next(a for a in clean_accepted_cfds if a['cfd'] == c['cfd'])
                clean_fd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=ac['conf'], elapsed_time=elapsed_time))
            else:
                clean_fd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=clean_fd_metadata[c['cfd']]['conf_history'][-1].score, elapsed_time=elapsed_time))
            
            wCOMBO = analyze.aHeuristicCombo(c['cfd'], full_dataset)
            phaCOMBO = np.prod([v for _, v in wCOMBO.items()])  # p(h | aCOMBO)
            phsSR = analyze.sHeuristicSetRelation(c['cfd'], [c['cfd'] for c in h_space]) # p(h | sSR)
            # System's weighted prior on rule confidence
            weight = 0
            for h in clean_fd_metadata[c['cfd']]['conf_history']:
                weight += (h.score / (current_iter - h.iter_num + 1))

            # weight = complexity_bias + weighted_conf
            clean_fd_metadata[c['cfd']]['weight'] = weight * phaCOMBO * phsSR   # weight * p(h | aCOMBO-sSR)
            # clean_fd_metadata[c['cfd']]['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=weight, elapsed_time=elapsed_time))
        
        clean_fd_metadata = normalizeWeights(clean_fd_metadata)
        for cfd_m in clean_fd_metadata.values():
            cfd_m['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_m['weight'], elapsed_time=elapsed_time))
        print('ground truth weights:', [cfd_m['weight_history'][-1].weight for cfd_m in clean_fd_metadata.values()])

        pickle.dump( clean_fd_metadata, open('./store/' + project_id + '/clean_fd_metadata.p', 'wb') )

    else:
        print('[ERROR] There was an error running CFDD') '''

    # USER DATA
    process = sp.Popen(['./data/cfddiscovery/CFDD', prepped_sample_fp, str(math.ceil(0.8*len(prepped_sample.index))), '0.8', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
    res = process.communicate()
    print('*** CFDD finished running ***')

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        print('*** FD meteadata object loaded ***')
        output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
        cfds = [c for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
        print('*** FDs from CFDD extracted ***')
        accepted_cfds = [c for c in cfds if c['cfd'] in cfd_metadata.keys()]
        for c in h_space:
            if c['cfd'] in [ac['cfd'] for ac in accepted_cfds]:
                ac = next(a for a in accepted_cfds if a['cfd'] == c['cfd'])
                cfd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=ac['conf'], elapsed_time=elapsed_time))
            else:
                cfd_metadata[c['cfd']]['conf_history'].append(CFDScore(iter_num=current_iter, score=cfd_metadata[c['cfd']]['conf_history'][-1].score, elapsed_time=elapsed_time))
            
            wCOMBO = analyze.aHeuristicCombo(c['cfd'], full_dataset)
            phaCOMBO = np.prod([v for _, v in wCOMBO.items()])  # p(h | aCOMBO)
            phsSR = analyze.sHeuristicSetRelation(c['cfd'], [c['cfd'] for c in h_space]) # p(h | sSR)
            # print('*** Complexity bias calculated ***')

            # System's weighted prior on rule confidence
            weight = 0
            for h in cfd_metadata[c['cfd']]['conf_history']:
                weight += (h.score / (current_iter - h.iter_num + 1))
            # print('*** Weighted FD confidence calculated ***')

            # weight = complexity_bias + weighted_conf
            cfd_metadata[c['cfd']]['weight'] = weight * phaCOMBO * phsSR    # weight * p(h | aCOMBO-sSR)
            # cfd_metadata[c['cfd']]['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=weight, elapsed_time=elapsed_time))
        
        cfd_metadata = normalizeWeights(cfd_metadata)
        for cfd_m in cfd_metadata.values():
            print(cfd_m['weight'])
            cfd_m['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_m['weight'], elapsed_time=elapsed_time))
        print('user weights:', [cfd_m['weight_history'][-1].weight for cfd_m in cfd_metadata.values()])

        print('*** CFDD output processed and FD weights updated ***')

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        print('*** CFD metadata updates saved ***')
    
    else:
        print('[ERROR] There was an error running CFDD')    


# BUILD SAMPLE
def buildSample(data, sample_size, project_id, sampling_method, current_iter, current_time):
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    # clean_fd_metadata = pickle.load( open('./store/' + project_id + '/clean_fd_metadata.p', 'rb') )
    modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
    # gt_metadata = pickle.load( open('./store/' + project_id + '/gt_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )

    elapsed_time = current_time - start_time
    print(elapsed_time)
    
    # GET SAMPLE
    if (sampling_method == 'DUO'):
        print('DUO-INFORMED SAMPLING')
        s_out = returnTuples(data, sample_size, project_id)     # Y = set(s_out.index)
    else:
        print('RANDOM SAMPLING')
        s_out = data.sample(n=sample_size)      # Y = set(s_out.index)

    dirty_tuples = getDirtyTuples(s_out, project_id)

    # MODELING METRICS
    if current_iter == 0:
        new_X = dirty_tuples    # X is just being created --> X = set(s_out.index)
    else:
        new_X = modeling_metadata['X'][-1].value | dirty_tuples     # X = X | set(s_out.index)
    
    modeling_metadata['X'].append(StudyMetric(iter_num=current_iter, value=new_X, elapsed_time=elapsed_time))
    # gt_metadata['X'].append(StudyMetric(iter_num=current_iter, value=new_X, elapsed_time=elapsed_time))

    modeling_metadata['Y'].append(StudyMetric(iter_num=current_iter, value=dirty_tuples, elapsed_time=elapsed_time))
    # gt_metadata['Y'].append(StudyMetric(iter_num=current_iter, value=set(s_out.index), elapsed_time=elapsed_time))

    # USER DATA
    for cfd, cfd_m in cfd_metadata.items():
        # p(X | h)
        if cfd not in modeling_metadata['p_X_given_h'].keys():  # cfd was just discovered in this iteration
            modeling_metadata['p_X_given_h'][cfd] = list()
        if set(new_X).issubset(cfd_m['vios']):
            p_X_given_h = math.pow((1/len(new_X)), sample_size) # p(X | h) = PI_i (p(x_i | h)), where each x_i is in X
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=p_X_given_h, elapsed_time=elapsed_time))
        else:
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
    
        # I(y in h)
        for y in new_X:
            if y not in modeling_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
                modeling_metadata['y_in_h'][cfd][y] = list()
            if y in cfd_m['vios']:
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
            else:
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
            '''if y not in modeling_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
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
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))'''

    # GROUND TRUTH
    '''for cfd, cfd_m in clean_fd_metadata.items():
        # p(X | h)
        if cfd not in gt_metadata['p_X_given_h'].keys():  # cfd was just discovered in this iteration
            gt_metadata['p_X_given_h'][cfd] = list()
        if set(new_X).issubset(cfd_m['support']):
            p_X_given_h = math.pow((1/len(new_X)), sample_size) # p(X | h) = PI_i (p(x_i | h)), where each x_i is in X
            gt_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=p_X_given_h, elapsed_time=elapsed_time))
        else:
            gt_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
    
        # I(y in h)
        for y in new_X:
            # if y not in gt_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
            #     gt_metadata['y_in_h'][cfd][y] = list()
            # if y in cfd_m['support'] and y not in cfd_m['vios']:
            #     gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
            # else:
            #     gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
            if y not in gt_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
                gt_metadata['y_in_h'][cfd][y] = list()
            if y in cfd_m['support']:   # FD is applicable to y
                if y not in cfd_m['vios']:    # y is clean w.r.t. the FD
                    gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
                
                # UPDATED CHECK FOR DETECTABILITY
                else:
                    vio_pairs = [i for i in cfd_m['vio_pairs'] if y in i]
                    if len(vio_pairs) == 0:     # y is dirty w.r.t the FD and does not pair with ANY other row in the dataset
                        gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
                    else:   # y is dirty w.r.t. the FD and DOES pair with some other row in the dataset
                        match_found = False
                        for x in new_X:
                            if len([i for i in vio_pairs if x in i and x != y]) > 0:
                                match_found = True
                                break
                        if match_found is False:    # y does not pair with any other tuple in X w.r.t. the FD and is not detectable YET
                            gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
                        else:   # y pairs with another tuple in X w.r.t. the FD and is detectable
                            gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
            else:   # FD is not applicable to y
                gt_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))'''
        

    print('IDs of tuples in next sample:', s_out.index)

    pickle.dump( modeling_metadata, open('./store/' + project_id + '/modeling_metadata.p', 'wb') )
    # pickle.dump( gt_metadata, open('./store/' + project_id + '/gt_metadata.p', 'wb') )
    
    return s_out

# RETURN TUPLES BASED ON WEIGHT
def returnTuples(data, sample_size, project_id):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    tuple_weights = [v['weight'] for v in tuple_metadata.values()]
    cfd_weights = [v['weight'] for v in cfd_metadata.values()]
    print(cfd_metadata.keys())
    print(cfd_weights)
    chosen_tuples = list()
    
    # print('IDs of tuples in next sample:')
    while len(chosen_tuples) < sample_size:
        fd = random.choices(list(cfd_metadata.keys()), weights=cfd_weights, k=1).pop()
        # if fd not in chosen_fds:
        cfd_m = cfd_metadata[fd]
        if len(cfd_m['vios']) > 0:
            if len(cfd_m['vio_trios']) > 0 and sample_size - len(chosen_tuples) >= 3:
                returned_tuple1, returned_tuple2, returned_tuple3 = random.choice(cfd_m['vio_pairs'])
                if returned_tuple1 not in chosen_tuples and returned_tuple2 not in chosen_tuples and returned_tuple3 not in chosen_tuples:
                    chosen_tuples.append(returned_tuple1)
                    chosen_tuples.append(returned_tuple2)
                    chosen_tuples.append(returned_tuple3)
            elif len(cfd_m['vio_pairs']) > 0 and sample_size - len(chosen_tuples) >= 2:
                returned_tuple1, returned_tuple2 = random.choice(cfd_m['vio_pairs'])
                if returned_tuple1 not in chosen_tuples and returned_tuple2 not in chosen_tuples:
                    chosen_tuples.append(returned_tuple1)
                    chosen_tuples.append(returned_tuple2)
            else:
                returned_tuple = random.choices(data.index, weights=tuple_weights, k=1)[0]
                if returned_tuple not in chosen_tuples:
                    chosen_tuples.append(returned_tuple1)
        # if len(cfd_m['vio_pairs']) == 0:
            # returned_tuple1 = pickSingleTuple(tuple_weights)
            # returned_tuple2 = pickSingleTuple(tuple_weights)
            # returned_tuples = random.choices(data.index, weights=tuple_weights, k=3)
            # returned_tuple1 = returned_tuples[0]
            # returned_tuple2 = returned_tuples[1]

        '''if returned_tuple1 not in chosen_tuples and returned_tuple2 not in chosen_tuples:
            chosen_tuples.append(returned_tuple1)
            chosen_tuples.append(returned_tuple2)'''
            # print(returned_tuple1)
            # print(returned_tuple2)

        if len(chosen_tuples) >= len(tuple_weights):
            break
    
    # print(data)
    # print(chosen_tuples)
    s_out = data.iloc[chosen_tuples]
    return s_out

def getDirtyTuples(s_out, project_id):
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    h_space = project_info['scenario']['hypothesis_space']
    dirty_tuples = list()
    for idx in s_out.index:
        is_dirty = False
        for h in h_space:
            if idx in h['vios']:
                is_dirty = True
                break
        if is_dirty is True:
            dirty_tuples.append(idx)
    return set(dirty_tuples)

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

def getHSpaceConfDelta(project_id, current_iter):
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    if current_iter >= 5:
        h_space_conf_delta = 0
        for fd_m in cfd_metadata.values():
            fd_conf_delta = abs(fd_m['conf_history'][-1].score - fd_m['conf_history'][-3].score)
            print(fd_conf_delta)
            h_space_conf_delta += fd_conf_delta
        h_space_conf_delta /= len(cfd_metadata.keys())
        print("delta h:", h_space_conf_delta)
        return h_space_conf_delta
    else:
        return None