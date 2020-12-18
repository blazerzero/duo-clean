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
from scipy.stats import hmean
from scipy.special import comb
import re

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
                if str(idx) in feedback.index:
                    iter_errors_total += 1
                    if bool(feedback.at[str(idx), col]) is True:
                        iter_errors_found += 1
                if len(cell_metadata[idx][col]['feedback_history']) > 0 and cell_metadata[idx][col]['feedback_history'][-1].marked is True:
                    all_errors_found += 1
            if len(cell_metadata[idx][col]['feedback_history']) > 0 and cell_metadata[idx][col]['feedback_history'][-1].marked is True:
                all_errors_marked += 1
                if str(idx) in feedback.index:
                    iter_errors_marked += 1

    print('*** Score updated ***')

    project_info['true_pos'] = all_errors_found
    project_info['false_pos'] = all_errors_marked - all_errors_found
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

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )


# DISCOVER CFDs THAT BEST EXPLAIN THE FEEDBACK GIVEN BY THE USER
def explainFeedback(full_dataset, dirty_sample, project_id, current_iter, current_time, refresh):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)

    elapsed_time = current_time - start_time

    print('*** Cell metadata object loaded ***')

    dirty_sample = dirty_sample.applymap(str)
    prepped_sample = dirty_sample.copy(deep=True)

    marked_cols = list()

    h_space = project_info['scenario']['hypothesis_space']
    update_method = project_info['scenario']['update_method']

    if refresh == 1:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        for c in h_space:
            cfd_metadata[c['cfd']]['weight'] = cfd_metadata[c['cfd']]['weight_history'][-1].weight
        
        cfd_metadata = normalizeWeights(cfd_metadata)
        for c in h_space:
            cfd_metadata[c['cfd']]['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_metadata[c['cfd']]['weight'], elapsed_time=elapsed_time))

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        return
    
    # USER DATA
    for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            cell = cell_metadata[int(idx)][col]

            if len(cell['feedback_history']) >= 1 and cell['feedback_history'][-1].marked is True:
                marked_cols.append(idx)
                break
    
    prepped_sample = prepped_sample.drop(marked_cols)
    print('*** Feedback reflected in \'repaired\' dataset ***')

    prepped_sample_fp = './store/' + project_id + '/mining_sample.csv'
    if os.path.exists(prepped_sample_fp):
        with open(prepped_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()

    print('*** Feedback reflected in \'repaired\' dataset ***')

    rep_dict = list(prepped_sample.T.to_dict().values())
    print(rep_dict)
    if len(rep_dict) == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        for cfd, cfd_m in cfd_metadata.items():
            cfd_m['weight'] = cfd_m['weight_history'][-1].weight
        cfd_metadata = normalizeWeights(cfd_metadata)
        for cfd_m in cfd_metadata.values():
            cfd_m['score_history'].append(CFDScore(iter_num=current_iter, score=cfd_m['score'], elapsed_time=elapsed_time))
            cfd_m['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_m['weight'], elapsed_time=elapsed_time))
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        return

    rep_header = rep_dict[0].keys()
    with open(prepped_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, rep_header)
        writer.writeheader()
        writer.writerows(rep_dict)
    print('*** Mining dataset saved as CSV ***')

    # USER DATA
    process = sp.Popen(['./data/cfddiscovery/CFDD', prepped_sample_fp, str(len(prepped_sample.index)), '0.8', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
    # process = sp.Popen(['java -cp metanome-cli-1.1.0.jar:pyro-distro-1.0-SNAPSHOT-distro.jar de.metanome.cli.App --algorithm de.hpi.isg.pyro.algorithms.Pyro --algorithm-config maxArity:2,isFindFds:true,maxFdError:0.20,topKFds:5 --table-key inputFile --header $true --output print --separator , --tables ' + prepped_sample_fp], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   # PYRO
    res = process.communicate()
    print('*** Mining algorithm finished running ***')

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        print('*** FD meteadata object loaded ***')
        # output = res[0].decode('latin_1')
        # cfds = parseOutputPYRO(output)
        output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
        cfds = [c['cfd'] for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
        expanded_cfds = buildCompositionSpace(cfds, h_space, prepped_sample, None, project_info['scenario']['min_conf'], project_info['scenario']['max_ant'])
        # print(cfds)
        # print(cfd_metadata)
        print('*** FDs from mining algorithm extracted ***')
        accepted_cfds = [c['cfd'] for c in expanded_cfds if c['cfd'] in cfd_metadata.keys()]
        for cfd, cfd_m in cfd_metadata.items():
            if cfd in accepted_cfds:
                support, vios = getSupportAndVios(prepped_sample, None, cfd)
                if update_method == 'BAYESIAN':
                    cfd_m['weight'] = bayesianUpdateFD(cfd, prepped_sample, cfd['weight'], support, cfd_m['vios'], vios, None)
                else:
                    cfd_m['weight'] = reinforceFD(cfd, prepped_sample, cfd_m['weight'], support, vios, 1)
                    # wUV = analyze.aHeuristicUV(cfd, prepped_sample)
                    # wAC = analyze.aHeuristicAC(cfd)
                    # phaUV = np.mean([v for v in wUV.values()])
                    # phaAC = np.mean([v for v in wAC.values()])
                    # phsSR = analyze.sHeuristicSetRelation(cfd, [c['cfd'] for c in h_space]) # p(h | sSR)
                    # ph = hmean([phaUV, phaAC, phsSR])
                    # cfd_m['weight'] = cfd_m['score']
            else:
                cfd_m['weight'] = cfd_m['score_history'][-1].score

        cfd_metadata = normalizeWeights(cfd_metadata)
        for cfd_m in cfd_metadata.values():
            # cfd_m['score_history'].append(CFDScore(iter_num=current_iter, score=cfd_m['score'], elapsed_time=elapsed_time))
            cfd_m['weight_history'].append(CFDWeightHistory(iter_num=current_iter, weight=cfd_m['weight'], elapsed_time=elapsed_time))

        print('*** Mining output processed and FD weights updated ***')

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        print('*** CFD metadata updates saved ***')
    
    else:
        print('[ERROR] There was an error running CFDD')    


# BUILD SAMPLE
def buildSample(data, sample_size, project_id, current_iter, current_time):
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    all_vios = pickle.load( open('./store/' + project_id + '/all_vios.p', 'rb') )

    elapsed_time = current_time - start_time
    # print(elapsed_time)

    # with open('./store/' + project_id + '/project_info.json', 'r') as f:
    #     project_info = json.load(f)
    # diff = project_info['scenario']['diff']
    
    # GET SAMPLE
    s_out, vios = returnTuples(data, cfd_metadata, sample_size)

    # Y = getDirtyTuples(s_out, project_id)
    Y = vios
    print(Y)

    # MODELING METRICS
    if current_iter == 0:
        X = set()
    else:
        # prev_sample = pickle.load( open('./store/' + project_id + '/current_sample.p', 'rb') )
        prev_Y = pickle.load( open('./store/' + project_id + '/current_vios.p', 'rb') )
        # prev_sample_Y = getDirtyTuples(data.iloc[prev_sample], project_id)
        X = modeling_metadata['X'][-1].value | set(prev_Y)
    
    modeling_metadata['X'].append(StudyMetric(iter_num=current_iter, value=X, elapsed_time=elapsed_time))

    modeling_metadata['Y'].append(StudyMetric(iter_num=current_iter, value=Y, elapsed_time=elapsed_time))

    # USER DATA
    for cfd, cfd_m in cfd_metadata.items():
        # rhs = cfd.split(' => ')[1]
        # p(X | h)
        print(cfd)
        if cfd not in modeling_metadata['p_X_given_h'].keys():  # cfd was just discovered in this iteration
            modeling_metadata['p_X_given_h'][cfd] = list()
            modeling_metadata['p_X'][cfd] = list()
            modeling_metadata['p_h_given_X'][cfd] = list()
        print(cfd_m['vios'])
        if current_iter == 0:
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))    # At the start, there is no X, so p(h | X) is only influenced by p(h), so p(X | h) = 1 to remove its influence at this stage
        elif set(X).issubset(all_vios):
            print('subset!')
            print(X)
            print()
            p_X_given_h = math.pow((1/len(all_vios)), len(X)) # p(X | h) = PI_i (p(x_i | h)), where each x_i is in X
            
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=p_X_given_h, elapsed_time=elapsed_time))
        else:
            print('not subset!\n')
            modeling_metadata['p_X_given_h'][cfd].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
    
        # I(y in h)
        for y in Y:
            print('Y!')
            if y not in modeling_metadata['y_in_h'][cfd].keys():    # this is the first time the user will have been shown y
                modeling_metadata['y_in_h'][cfd][y] = list()
            if y in all_vios:
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=1, elapsed_time=elapsed_time))
            else:
                modeling_metadata['y_in_h'][cfd][y].append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))       

    print('IDs of tuples in next sample:', s_out.index)

    pickle.dump( modeling_metadata, open('./store/' + project_id + '/modeling_metadata.p', 'wb') )
    
    return s_out, vios

def returnTuples(data, fd_metadata, sample_size):
    chosen = list()
    fds = list(fd_metadata.keys())
    # weights = [f['weight'] for f in fd_metadata.values()]
    vios = set()
    while len(chosen) < sample_size:
        # if sampling_method == 'DUO':
        #     fd = random.choices(fds, weights=weights, k=1).pop()
        # else:
        fd = random.choice(fds)
        fd_m = fd_metadata[fd]
        if len(fd_m['vios']) > 0:
            tupSet = list()
            if sample_size - len(chosen) >= 3 and len(fd_m['vio_trios']) > 0:
                tupSet = random.choice(fd_m['vio_trios'])
            elif sample_size - len(chosen) >= 2 and len(fd_m['vio_pairs']) > 0:
                tupSet = random.choice(fd_m['vio_pairs'])
            elif sample_size - len(chosen) >= 1:
                tupSet = random.choices(fd_m['vios'], k=1)
        else:
            tupSet = random.choices(data.index, k=1)
        if tuple(tupSet) not in vios:
            vios.add(tuple(tupSet))
            for i in tupSet:
                if i not in chosen:
                    chosen.append(i)
        if len(chosen) >= sample_size:
            break
    s_out = data.iloc[chosen]
    return s_out, vios

def getDirtyTuples(s_out, project_id):
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    diff = project_info['scenario']['diff']
    dirty_tuples = list()
    for idx in s_out.index:
        print(idx)
        is_dirty = False
        for col in s_out.columns:
            if diff[str(idx)][col] is False:
                print('dirty')
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

def checkForTermination(project_id, clean_h_space, current_iter):
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    top_fd = max(cfd_metadata, key=lambda x: cfd_metadata[x]['weight'])
    top_fd_conf = next(h for h in clean_h_space if h['cfd'] == top_fd)['conf']

    if current_iter >= 5:
        variance_delta = abs(np.var([fd_m['weight_history'][-1].weight for fd_m in cfd_metadata.values()]) - np.var([fd_m['weight_history'][-3].weight for fd_m in cfd_metadata.values()]))
        print("variance delta:", variance_delta)
        return top_fd_conf, variance_delta
    else:
        return top_fd_conf, None

# GET FD SUPPORT AND VIOLATIONS
def getSupportAndVios(dirty_data, clean_data, fd):
    lhs = fd.split(' => ')[0][1:-1]
    rhs = fd.split(' => ')[1]
    # print(lhs)
    # print(rhs)
    clean_patterns = None
    if clean_data is not None:
        clean_patterns = fd2cfd(clean_data, lhs, rhs)
        # ENFORCE ONE LHS TO RHS FOR CLEAN PATTERNS
        for l in clean_patterns.keys():
            if len(clean_patterns[l]) == 1:
                clean_patterns[l] = clean_patterns[l].pop()
            else:
                random_idx = random.randint(0, len(clean_patterns[l])-1)
                clean_patterns[l] = clean_patterns[l][random_idx]
    dirty_patterns = fd2cfd(dirty_data, lhs, rhs)
    # print(dirty_patterns)
    # print(clean_patterns)

    # IF DIRTY PATTERNS HAS >1 RHS TO 1 LHS, PICK CLEAN RHS
    for l in dirty_patterns.keys():
        if len(dirty_patterns[l]) == 1:
            dirty_patterns[l] = dirty_patterns[l].pop()
        else:
            if clean_patterns is not None and l in clean_patterns.keys() and clean_patterns[l] in dirty_patterns[l]:
                dirty_patterns[l] = clean_patterns[l]
            else:
                random_idx = random.randint(0, len(dirty_patterns[l])-1)
                dirty_patterns[l] = dirty_patterns[l][random_idx]
        
    # CODE TO BUILD COVER AND VIOLATION LIST
    support = list()
    violations = list()
    for idx in dirty_data.index:
        support.append(idx)
        applicable_lhs = ''
        for lh in lhs.split(', '):
            applicable_lhs += lh + '=' + str(dirty_data.at[idx, lh]) + ', '
        applicable_lhs = applicable_lhs[:-2]
        applicable_rhs = dirty_patterns[applicable_lhs]
        is_vio = False
        # rh = applicable_rhs.split('=')
        for rhs_piece in applicable_rhs.split(', '):
            rh = rhs_piece.split('=')
            if str(dirty_data.at[idx, rh[0]]) != str(rh[1]):
                is_vio = True
                break
        # if str(dirty_data.at[idx, rh[0]]) != str(rh[1]):
        if is_vio is True:
            violations.append(idx)
        
    return support, violations


# CONVERT FD OR PARTIAL CFD TO FULL CFD
def fd2cfd(data, lhs, rhs):
    patterns = dict()
    mappings = dict()
    # print(lhs)
    # print(rhs)

    # Gather all the possible patterns present in the dataset for each pure FD or partial CFD
    for idx in data.index:
        lhspattern = ''
        rhspattern = ''
        for clause in lhs.split(', '):
            if '=' in clause:
                lhspattern += clause + ', '
            else:
                lhspattern += clause + '=' + str(data.at[idx, clause]) + ', '
        lhspattern = lhspattern[:-2]

        for clause in rhs.split(', '):
            if '=' in clause:
                rhspattern += clause + ', '
            else:
                rhspattern += clause + '=' + str(data.at[idx, clause]) + ', '
        rhspattern = rhspattern[:-2]

        if lhspattern in patterns.keys():
            patterns[lhspattern].append(rhspattern)
            if (lhspattern, rhspattern) in mappings.keys():
                mappings[(lhspattern, rhspattern)].append(idx)
            else:
                mappings[(lhspattern, rhspattern)] = [idx]
        else:
            patterns[lhspattern] = [rhspattern]
            mappings[(lhspattern, rhspattern)] = [idx]

    # Pick RHS patterns for each LHS from these candidates
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [k for k, v in get_mode.items() if v == max(list(counts.values()))]

    return patterns

def parseOutputPYRO(output):
    keyword = 'Results:\n'
    _, keyword, after = output.partition(keyword)
    unformatted_fds = after.split('\n')
    formatted_fds = list()
    for c in unformatted_fds:
        if '->' not in c:
            continue
        lhs_attrs = [x.split('.')[-1] for x in c.split('->')[0][1:-1].split(', ')]
        rhs = c.split('->')[1].split('.')[-1]
        lhs = ', '.join(lhs_attrs)
        fd = '(' + lhs + ') => ' + rhs
        formatted_fds.append(fd)
    return formatted_fds

def reinforceFD(fd, data, score, support, vios, r):
    for idx in data.index:
        if idx in support:
            score += r
            if idx not in vios:
                score += r
    return score

def bayesianUpdateFD(fd, data, weight, support, vios, sample_vios, all_vios):
    p_X_given_h = 1
    for sv in sample_vios:
        if sv in vios:
            p_X_given_h *= (1 - weight)
        else:
            p_X_given_h *= weight

    p_X = 1
    for vios in sample_vios:
        # TODO: Calculate p(X) given that we have vio trios, pairs, AND singles, and depending on sample size available, some may not be able to be added
        pass

    weight = (weight * p_X_given_h) / p_X
    return weight

def buildCompositionSpace(fds, h_space, dirty_data, clean_data, min_conf, max_ant):
    composed_fds = set(fds)
    composed_combos = set()
    for fd1 in fds:
        for fd2 in fds:
            if fd1 == fd2 or (fd1, fd2) in composed_combos or (fd2, fd1) in composed_combos:
                continue
            fd1_lhs = set(fd1.split(' => ')[0][1:-1].split(', '))
            fd1_rhs = set(fd1.split(' => ')[1].split(', '))
            fd2_lhs = set(fd2.split(' => ')[0][1:-1].split(', '))
            fd2_rhs = set(fd2.split(' => ')[1].split(', '))

            if not fd1_rhs.isdisjoint(fd2_lhs) or not fd2_rhs.isdisjoint(fd1_lhs):
                continue

            composed_fd_lhs_set = fd1_lhs | fd2_lhs
            if len(composed_fd_lhs_set) > max_ant:
                continue
            
            composed_fd_lhs = '(' + ', '.join(composed_fd_lhs_set) + ')'

            if h_space is not None: # H space already exists, so match the LHS with a currently existing FD if possible
                try:
                    matching_fd = next(h['cfd'] for h in h_space if composed_fd_lhs_set == set(h['cfd'].split(' => ')[0][1:-1].split(', ')))
                    matching_fd_lhs = matching_fd.split(' => ')[0]  # Ensures the LHS is in an order that does not throw off future calculations
                    composed_fd_lhs = matching_fd_lhs
                except StopIteration:
                    pass

            composed_fd_rhs_set = fd1_rhs | fd2_rhs
            composed_fd_rhs = ', '.join(composed_fd_rhs_set)

            if h_space is not None: # H space already exists, so match the RHS with a currently existing FD if possible
                try:
                    matching_fd = next(h['cfd'] for h in h_space if composed_fd_lhs_set == set(h['cfd'].split(' => ')[0][1:-1].split(', ')) and composed_fd_rhs_set == set(h['cfd'].split(' => ')[1].split(', ')))
                    matching_fd_rhs = matching_fd.split(' => ')[1]    # Ensures the RHS is in an order that does not throw off future calculations
                    composed_fd_rhs = matching_fd_rhs
                except StopIteration:
                    pass

            composed_fd = composed_fd_lhs + ' => ' + composed_fd_rhs
            
            try:    # Prune duplicates from space of composed FDs
                _ = next(h for h in composed_fds if composed_fd_lhs_set == set(h.split(' => ')[0][1:-1].split(', ')) and composed_fd_rhs_set == set(h.split(' => ')[1].split(', ')))
                pass
            except StopIteration:
                composed_fds.add(composed_fd)

            composed_combos.add((fd1, fd2))

    further_composed_fds = set(composed_fds)
    for fd1 in composed_fds:
        for fd2 in composed_fds:
            if fd1 == fd2 or (fd1, fd2) in composed_combos or (fd2, fd1) in composed_combos:
                continue
            fd1_lhs = set(fd1.split(' => ')[0][1:-1].split(', '))
            fd1_rhs = set(fd1.split(' => ')[1].split(', '))
            fd2_lhs = set(fd2.split(' => ')[0][1:-1].split(', '))
            fd2_rhs = set(fd2.split(' => ')[1].split(', '))

            if not fd1_rhs.isdisjoint(fd2_lhs) or not fd2_rhs.isdisjoint(fd1_lhs):
                continue

            composed_fd_lhs_set = fd1_lhs | fd2_lhs
            if len(composed_fd_lhs_set) > max_ant:
                continue
            
            composed_fd_lhs = '(' + ', '.join(composed_fd_lhs_set) + ')'

            if h_space is not None: # H space already exists, so match the LHS with a currently existing FD if possible
                try:
                    matching_fd = next(h['cfd'] for h in h_space if composed_fd_lhs_set == set(h['cfd'].split(' => ')[0][1:-1].split(', ')))
                    matching_fd_lhs = matching_fd.split(' => ')[0]  # Ensures the LHS is in an order that does not throw off future calculations
                    composed_fd_lhs = matching_fd_lhs
                except StopIteration:
                    pass

            composed_fd_rhs_set = fd1_rhs | fd2_rhs
            composed_fd_rhs = ', '.join(composed_fd_rhs_set)

            if h_space is not None: # H space already exists, so match the RHS with a currently existing FD if possible
                try:
                    matching_fd = next(h['cfd'] for h in h_space if composed_fd_lhs_set == set(h['cfd'].split(' => ')[0][1:-1].split(', ')) and composed_fd_rhs_set == set(h['cfd'].split(' => ')[1].split(', ')))
                    matching_fd_rhs = matching_fd.split(' => ')[1]    # Ensures the RHS is in an order that does not throw off future calculations
                    composed_fd_rhs = matching_fd_rhs
                except StopIteration:
                    pass

            composed_fd = composed_fd_lhs + ' => ' + composed_fd_rhs
            
            try:    # Prune duplicates from space of composed FDs
                _ = next(h for h in further_composed_fds if composed_fd_lhs_set == set(h.split(' => ')[0][1:-1].split(', ')) and composed_fd_rhs_set == set(h.split(' => ')[1].split(', ')))
                pass
            except StopIteration:
                further_composed_fds.add(composed_fd)

            composed_combos.add((fd1, fd2))

    # print(composed_fds)


    composition_space = [{ 'cfd': h['cfd'], 'conf': h['conf'] } for h in h_space] if h_space is not None else list()
    for composed_fd in further_composed_fds:
        # if composed_fd != '(manager) => owner':
        #     continue
        # print(composed_fd)
        if clean_data is not None:
            support, vios = getSupportAndVios(dirty_data, clean_data, composed_fd)
            # print(support)
            # print(vios)
            conf = (len(support) - len(vios)) / len(support)
            # print(conf)
            if conf >= min_conf and len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                # print(composed_fd)
                composition_space.append({
                    'cfd': composed_fd,
                    'conf': conf
                })
        else:
            if len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                # print(composed_fd)
                composition_space.append({
                    'cfd': composed_fd,
                    'conf': None
                })

    return composition_space
