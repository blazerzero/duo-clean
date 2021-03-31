import copy
import itertools
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
import scipy.special as sc
from scipy.stats import beta as betaD
import re
from itertools import combinations

class CellFeedback(object):
    def __init__(self, iter_num, marked, elapsed_time):
        self.iter_num = iter_num    # iteration number
        self.marked = marked            # whether or not the user marked the cell as noisy in this iteration
        self.elapsed_time = elapsed_time

    def asdict(self):
        return {
            'iter_num': self.iter_num,
            'marked': self.marked,
            'elapsed_time': self.elapsed_time
        }

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

    def asdict(self):
        return {
            'iter_num': self.iter_num,
            'value': self.value,
            'elapsed_time': self.elapsed_time
        }

class FDMeta(object):
    def __init__(self, fd, a, b, support, vios, vio_pairs):
        self.lhs = fd.split(' => ')[0][1:-1].split(', ')
        self.rhs = fd.split(' => ')[1].split(', ')
        self.alpha = a
        self.alpha_history = [StudyMetric(iter_num=0, value=self.alpha, elapsed_time=0)]
        self.beta = b
        self.beta_history = [StudyMetric(iter_num=0, value=self.beta, elapsed_time=0)]
        self.conf = (a / (a+b))
        self.conf_history = [StudyMetric(iter_num=0, value=self.conf, elapsed_time=0)]
        self.support = support
        self.vios = vios
        self.vio_pairs = vio_pairs
        self.all_vios_found_history = []
        self.iter_vios_found_history = []
        self.iter_vios_total_history = []
        # self.alpha_err = alpha
        # self.alpha_err_history = [alpha]
        # self.beta_err = beta
        # self.beta_err_history = [beta]
    
    def asdict(self):
        # print([list(vp) for vp in self.vio_pairs])
        alpha_history = list()
        for a in self.alpha_history:
            alpha_history.append(a.asdict())

        beta_history = list()
        for b in self.beta_history:
            beta_history.append(b.asdict())

        return {
            'lhs': self.lhs,
            'rhs': self.rhs,
            'alpha': self.alpha,
            'alpha_history': alpha_history,
            'beta': self.beta,
            'beta_history': beta_history,
            'support': self.support,
            'vios': self.vios,
            'vio_pairs': [list(vp) for vp in self.vio_pairs],
            # 'all_vios_found_history': [a.asdict() for a in self.all_vios_found_history],
            # 'iter_vios_found_history': [i.asdict() for i in self.iter_vios_found_history],
            # 'iter_vios_total_history': [i.asdict() for i in self.iter_vios_total_history]
        }


# RECORD USER FEEDBACK (FOR TRUE POS AND FALSE POS)
def recordFeedback(data, feedback, vio_pairs, project_id, current_iter, current_time):
    interaction_metadata = pickle.load( open('./store/' + project_id + '/interaction_metadata.p', 'rb') )
    study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )

    elapsed_time = current_time - start_time

    # for idx in feedback.index:
    #     for col in feedback.columns:
    for idx in data.index:
        if str(idx) in feedback.keys():
            for col in data.columns:
                interaction_metadata['feedback_history'][idx][col].append(CellFeedback(iter_num=current_iter, marked=bool(feedback[str(idx)][col]), elapsed_time=elapsed_time))
        else:
            for col in data.columns:
                interaction_metadata['feedback_history'][idx][col].append(CellFeedback(iter_num=current_iter, marked=interaction_metadata['feedback_history'][idx][col][-1].marked if current_iter > 1 else False, elapsed_time=elapsed_time))
            

    interaction_metadata['sample_history'].append(StudyMetric(iter_num=current_iter, value=[int(idx) for idx in feedback.keys()], elapsed_time=elapsed_time))
    print('*** Latest feedback saved ***')
            
    # scoring function: score based on number of true errors correctly identified
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
        clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
    
    iter_errors_found = 0
    iter_errors_total = 0
    iter_errors_marked = 0

    all_errors_found = 0
    all_errors_total = 0
    all_errors_marked = 0

    print(feedback)

    # Track errors caught in each iteration (short-term), medium-term, and cumulatively (long-term)
    mt_sample = set([int(i) for i in feedback.keys()])
    if current_iter > 1:
        mt_sample |= set(interaction_metadata['sample_history'][current_iter-2].value)
    all_sample = set([int(i) for i in feedback.keys()])
    for i in range(2, current_iter+1):
        all_sample |= set(interaction_metadata['sample_history'][current_iter-i].value)
    for idx in data.index:
        for col in data.columns:
            if data.at[idx, col] != clean_dataset.at[idx, col]:
                if str(idx) in feedback.keys():
                    iter_errors_total += 1
                    if bool(feedback[str(idx)][col]) is True:
                        iter_errors_found += 1
                if idx in all_sample:
                    all_errors_total += 1
                    if interaction_metadata['feedback_history'][int(idx)][col][-1].marked is True:
                        all_errors_found += 1
            if interaction_metadata['feedback_history'][int(idx)][col][-1].marked is True:
                if str(idx) in feedback.keys():
                    iter_errors_marked += 1
                if idx in all_sample:
                    all_errors_marked += 1

    print('*** Score updated ***')

    project_info['true_pos'] = all_errors_found
    project_info['false_pos'] = all_errors_marked - all_errors_found
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)
    print('*** Score saved ***')

    pickle.dump( interaction_metadata, open('./store/' + project_id + '/interaction_metadata.p', 'wb') )
    print('*** Interaction metadata updates saved ***')

    # ERRORS
    if iter_errors_marked > 0:
        iter_err_precision = iter_errors_found / iter_errors_marked
    else:
        iter_err_precision = 0
    
    if iter_errors_total > 0:
        iter_err_recall = iter_errors_found / iter_errors_total
    else:
        iter_err_recall = 0

    if iter_err_precision > 0 and iter_err_recall > 0:
        iter_err_f1 = 2 * (iter_err_precision * iter_err_recall) / (iter_err_precision + iter_err_recall)
    else:
        iter_err_f1 = 0

    if all_errors_marked > 0:
        all_err_precision = all_errors_found / all_errors_marked
    else:
        all_err_precision = 0
    
    if all_errors_total > 0:
        all_err_recall = all_errors_found / all_errors_total
    else:
        all_err_recall = 0

    if all_err_precision > 0 and all_err_recall > 0:
        all_err_f1 = 2 * (all_err_precision * all_err_recall) / (all_err_precision + all_err_recall)
    else:
        all_err_f1 = 0

    study_metrics['iter_err_precision'].append(StudyMetric(iter_num=current_iter, value=iter_err_precision, elapsed_time=elapsed_time))
    study_metrics['iter_err_recall'].append(StudyMetric(iter_num=current_iter, value=iter_err_recall, elapsed_time=elapsed_time))
    study_metrics['iter_err_f1'].append(StudyMetric(iter_num=current_iter, value=iter_err_f1, elapsed_time=elapsed_time))

    study_metrics['all_err_precision'].append(StudyMetric(iter_num=current_iter, value=all_err_precision, elapsed_time=elapsed_time))
    study_metrics['all_err_recall'].append(StudyMetric(iter_num=current_iter, value=all_err_recall, elapsed_time=elapsed_time))
    study_metrics['all_err_f1'].append(StudyMetric(iter_num=current_iter, value=all_err_f1, elapsed_time=elapsed_time))

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )

# INTERPRET USER FEEDBACK AND UPDATE PROBABILITIES
def interpretFeedback(s_in, feedback, X, sample_X, project_id, current_iter, current_time, target_fd=None):
    fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )

    elapsed_time = current_time - start_time
    # Remove marked cells from consideration
    print('*** about to interpret feedback ***')
    marked_rows = list()
    for idx in feedback.index:
        for col in feedback.columns:
            if bool(feedback.at[idx, col]) is True:
                marked_rows.append(int(idx))
                break

    # Calculate P(X | \theta_h) for each FD
    for fd, fd_m in fd_metadata.items():
        successes = 0
        failures = 0

        removed_pairs = set()
        sample_X_in_fd = {x for x in sample_X if x in fd_m.vio_pairs}
        for x, y in sample_X_in_fd:
            if x in marked_rows or y in marked_rows:
                removed_pairs.add((x, y))

        for i in s_in.index:
            if i in marked_rows:
                continue
            if i not in fd_m.vios:  # tuple is clean
                successes += 1
            else:
                if len([x for x in removed_pairs if i in x]) > 0:   # tuple is dirty but it's part of a vio that the user caught (i.e. they marked the wrong tuple as the error but still found the vio)
                    successes += 1
                else:   # tuple is dirty and they missed the vio, or the vio isn't in a pair in the sample
                    failures += 1

        print('successes:', successes)
        print('failures:', failures)
                
        fd_m.alpha += successes
        fd_m.alpha_history.append(StudyMetric(iter_num=current_iter, value=fd_m.alpha, elapsed_time=elapsed_time))
        fd_m.beta += failures
        fd_m.beta_history.append(StudyMetric(iter_num=current_iter, value=fd_m.beta, elapsed_time=elapsed_time))
        print('alpha:', fd_m.alpha)
        print('beta:', fd_m.beta)
        fd_m.conf = fd_m.alpha / (fd_m.alpha + fd_m.beta)
        fd_m.conf_history.append(StudyMetric(iter_num=current_iter, value=fd_m.conf, elapsed_time=elapsed_time))
        print('conf:', fd_m.conf)

    pickle.dump( fd_metadata, open('./store/' + project_id + '/fd_metadata.p', 'wb') )

# BUILD SAMPLE
def buildSample(data, X, sample_size, project_id, current_iter, current_time):
    fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    target_fd = project_info['scenario']['target_fd']
    alt_h_list = project_info['scenario']['alt_h']
    tfd_conf = next(i for i in project_info['scenario']['hypothesis_space'] if i['cfd'] == target_fd)['conf']
    tfd_m = fd_metadata[target_fd]
    alt_fd_m = dict()
    for h in alt_h_list:
        alt_fd_m[h] = fd_metadata[h]
    alt_h_vio_pairs = set()
    for _, h in alt_fd_m.items():
        alt_h_vio_pairs |= h.vio_pairs

    elapsed_time = current_time - start_time

    sample_X = set()
    s_out = None
    tfd_X = [x for x in X if x in tfd_m.vio_pairs]
    target_h_sample_ratio = project_info['scenario']['target_h_sample_ratio']
    alt_h_sample_ratio = project_info['scenario']['alt_h_sample_ratio']
    s_index, sample_X = returnTuples(data, tfd_X, sample_size, list(alt_h_vio_pairs), target_h_sample_ratio, alt_h_sample_ratio, current_iter)
    s_out = data.loc[s_index, :]

    print('IDs of tuples in next sample:', s_out.index)
    
    return s_out, sample_X


# RETURN TUPLES AND VIOS FOR SAMPLE
def returnTuples(data, X, sample_size, alt_h_vio_pairs, target_h_sample_ratio, alt_h_sample_ratio, current_iter):
    s_out = list()
    X_tups = list(itertools.chain(*X))
    alt_X_tups = list(itertools.chain(*alt_h_vio_pairs))
    viable_X = [(x, y) for (x, y) in X if x not in alt_X_tups and y not in alt_X_tups]
    viable_alt_X = [(x, y) for (x, y) in alt_h_vio_pairs if x not in X_tups and y not in X_tups]
    viable_rem = [x for x in data.index if x not in X_tups and x not in alt_X_tups]
    if len(viable_alt_X) > math.ceil(alt_h_sample_ratio * sample_size):
        alt_vios_out = random.sample(population=viable_alt_X, k=math.ceil(alt_h_sample_ratio * sample_size))
    else:
        alt_vios_out = viable_alt_X
    for (x, y) in alt_vios_out:
        if x not in s_out:
            s_out.append(x)
        if y not in s_out:
            s_out.append(y)
    if len(viable_X) > math.ceil(target_h_sample_ratio * sample_size):
        target_vios_out = random.sample(population=viable_X, k=math.ceil(target_h_sample_ratio * sample_size))
    else:
        target_vios_out = viable_X
    for (x, y) in target_vios_out:
        if x not in s_out:
            s_out.append(x)
        if y not in s_out:
            s_out.append(y)
        # if len(s_out) >= sample_size:
        #     break
    for i in range(0, math.ceil((1-target_h_sample_ratio-alt_h_sample_ratio)*sample_size)):
        other_tups = random.sample(population=viable_rem, k=2)
        if other_tups[0] not in s_out and other_tups[1] not in s_out:
            s_out.append(other_tups[0])
            s_out.append(other_tups[1])
    # other_tups_out = random.sample(population=viable_rem, k=2)
    # if len(s_out) < sample_size:
        # for i in other_tups_out:
            # if i not in s_out:
                # s_out.append(i)
            # if len(s_out) >= sample_size:
            #     break
    random.shuffle(s_out)
    sample_X = set()
    for i1 in s_out:
        for i2 in s_out:
            tup = (i1, i2) if i1 < i2 else (i2, i1)
            if tup in X:
                sample_X.add(tup)
    return s_out, sample_X


# GET THE USER'S TRUE POSITIVE AND FALSE POSITIVE COUNTS
def getUserScores(project_id):
    with open('./store/' + project_id + '/project_info.json') as f:
        project_info = json.load(f)
    return project_info['true_pos'], project_info['false_pos']


# GET FD SUPPORT AND VIOLATIONS
def getSupportAndVios(dirty_data, clean_data, fd):
    lhs = fd.split(' => ')[0][1:-1]
    rhs = fd.split(' => ')[1]
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
        
    # BUILD COVER AND VIOLATION LIST
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
        for rhs_piece in applicable_rhs.split(', '):
            rh = rhs_piece.split('=')
            if str(dirty_data.at[idx, rh[0]]) != str(rh[1]):
                is_vio = True
                break
        if is_vio is True:
            violations.append(idx)
        
    return support, violations


# CONVERT FD OR PARTIAL CFD TO FULL CFD
def fd2cfd(data, lhs, rhs):
    patterns = dict()
    mappings = dict()

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

    composition_space = [{ 'cfd': h['cfd'] } for h in h_space] if h_space is not None else list()
    for composed_fd in further_composed_fds:
        if clean_data is not None:
            support, vios = getSupportAndVios(dirty_data, clean_data, composed_fd)
            conf = (len(support) - len(vios)) / len(support)
            if conf >= min_conf and len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                composition_space.append({
                    'cfd': composed_fd
                })
        else:
            if len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                composition_space.append({
                    'cfd': composed_fd
                })

    return composition_space

def initialPrior(mu, variance):
    if mu == 1:
        mu = 0.9999
    beta = (1 - mu) * ((mu * (1 - mu) / variance) - 1)
    alpha = (mu * beta) / (1 - mu)
    return abs(alpha), abs(beta)

def getPairs(data, support, vios, fd):
    vio_pairs = set()
    all_pairs = set()
    lhs = fd.split(' => ')[0][1:-1].split(', ')
    rhs = fd.split(' => ')[1].split(', ')
    for idx1 in support:
        for idx2 in support:
            if idx1 == idx2:
                continue
            pair = (idx1, idx2) if idx2 > idx1 else (idx2, idx1)
            all_pairs.add(pair)
            match = True
            for lh in lhs:
                if data.at[idx1, lh] != data.at[idx2, lh]:
                    match = False
                    break
            if match is True:
                for rh in rhs:
                    if data.at[idx1, rh] != data.at[idx2, rh]:
                        vio_pairs.add(pair)
                        break
    return list(all_pairs), list(vio_pairs)   

def vioStats(curr_sample, t_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset):
    vios_marked = set()
    vios_total = set()
    vios_found = set()
    for x, y in vio_pairs:
        if x not in t_sample or y not in t_sample:
            continue
        if x not in curr_sample and y not in curr_sample:
            continue
        vios_total.add((x, y))

        x_marked = False
        for rh in rhs:
            if feedback[str(x)][rh] is True:
                x_marked = True
                break
        y_marked = False
        for rh in rhs:
            if feedback[str(y)][rh] is True:
                y_marked = True
                break
        if x_marked == y_marked and x_marked is False:
            continue
        vios_marked.add((x,y))
        vios_found.add((x,y))
    
    for x in curr_sample:
        vios_w_x = {i for i in vios_marked if x in i}
        if len(vios_w_x) == 0:
            marked = True
            for rh in rhs:
                if feedback[str(x)][rh] is False:
                    marked = False
                    break
            if marked is True:
                vios_marked.add((x,x))

    return vios_marked, vios_found, vios_total

def pkl2Json(project_id):
    files = os.listdir('./store/' + project_id + '/')
    for f in files:
        print('./store/' + project_id + '/' + f)
        if '.p' in f:
            obj = pickle.load( open('./store/' + project_id + '/' + f, 'rb') )
            if type(obj) == dict:
                if f == 'fd_metadata.p':
                    for k in obj.keys():
                        obj[k] = obj[k].asdict()
                elif f == 'interaction_metadata.p':
                    for idx in obj['feedback_history'].keys():
                        for col in obj['feedback_history'][idx].keys():
                            obj['feedback_history'][idx][col] = [i.asdict() for i in obj['feedback_history'][idx][col]]
                    obj['sample_history'] = [i.asdict() for i in obj['sample_history']]
                elif f == 'study_metrics.p':
                    for idx in obj.keys():
                        obj[idx] = [i.asdict() for i in obj[idx]]

                with open('./store/' + project_id + '/' + f.split('.')[0] + '.json', 'w') as fp:
                    json.dump(obj, fp, ensure_ascii=False, indent=4)

def checkForTermination(project_id):
    pkl2Json(project_id)
    with open('./store/' + project_id + '/study_metrics.json', 'r') as f:
        study_metrics = json.load(f)
    with open('./store/' + project_id + '/fd_metadata.json', 'r') as f:
        fd_metadata = json.load(f)
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    with open('./store/' + project_id + '/interaction_metadata.json', 'r') as f:
        interaction_metadata = json.load(f)
    dirty_dataset = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
    clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
    target_fd = project_info['scenario']['target_fd']

    h_space = project_info['scenario']['hypothesis_space']
    clean_h_space = project_info['scenario']['clean_hypothesis_space']
    study_metrics, fd_metadata = deriveStats(
        interaction_metadata,
        fd_metadata,
        h_space,
        study_metrics,
        dirty_dataset,
        clean_dataset,
        target_fd
    )

    with open('./store/' + project_id + '/study_metrics.json', 'w') as f:
        json.dump(study_metrics, f, indent=4)
    with open('./store/' + project_id + '/fd_metadata.json', 'w') as f:
        json.dump(fd_metadata, f, indent=4)

    if (len(study_metrics['st_vios_marked'][-1]['value']) == 0):
        return False
    
    st_vio_precision = [i['value'] for i in study_metrics['st_vio_precision']]
    st_vio_recall = [i['value'] for i in study_metrics['st_vio_recall']]
    if (st_vio_precision[-1] >= 0.8 and abs(st_vio_precision[-1] - st_vio_precision[-2]) <= 0.1 and abs(st_vio_precision[-2] - st_vio_precision[-3]) <= 0.1):
        if (st_vio_recall[-1] >= 0.6 and (abs(st_vio_recall[-1] - st_vio_recall[-2]) <= 0.1 and abs(st_vio_precision[-2] - st_vio_precision[-3]) <= 0.1)):
            return True
        elif (st_vio_recall[-1] >= 0.5 and (abs(st_vio_recall[-1] - st_vio_recall[-2]) <= 0.05 and abs(st_vio_precision[-2] - st_vio_precision[-3]) <= 0.05)):
            return True
        else:
            return False
    else:
        return False

def deriveStats(interaction_metadata, fd_metadata, h_space, study_metrics, dirty_dataset, clean_dataset, target_fd):
    feedback_history = interaction_metadata['feedback_history']
    study_metrics['st_vio_precision'] = list()
    study_metrics['lt_vio_precision'] = list()
    study_metrics['mt_vio_precision'] = list()
    study_metrics['mt_2_vio_precision'] = list()
    study_metrics['mt_3_vio_precision'] = list()
    study_metrics['st_vio_recall'] = list()
    study_metrics['lt_vio_recall'] = list()
    study_metrics['mt_vio_recall'] = list()
    study_metrics['mt_2_vio_recall'] = list()
    study_metrics['mt_3_vio_recall'] = list()
    study_metrics['st_vio_f1'] = list()
    study_metrics['lt_vio_f1'] = list()
    study_metrics['mt_vio_f1'] = list()
    study_metrics['mt_2_vio_f1'] = list()
    study_metrics['mt_3_vio_f1'] = list()
    study_metrics['iter_err_precision'] = list()
    study_metrics['iter_err_recall'] = list()
    study_metrics['iter_err_f1'] = list()
    study_metrics['all_err_precision'] = list()
    study_metrics['all_err_recall'] = list()
    study_metrics['all_err_f1'] = list()

    study_metrics['st_vios_marked'] = list()
    study_metrics['mt_vios_marked'] = list()
    study_metrics['mt_2_vios_marked'] = list()
    study_metrics['mt_3_vios_marked'] = list()
    study_metrics['lt_vios_marked'] = list()
    study_metrics['st_vios_found'] = list()
    study_metrics['mt_vios_found'] = list()
    study_metrics['mt_2_vios_found'] = list()
    study_metrics['mt_3_vios_found'] = list()
    study_metrics['lt_vios_found'] = list()
    study_metrics['st_vios_total'] = list()
    study_metrics['mt_vios_total'] = list()
    study_metrics['mt_2_vios_total'] = list()
    study_metrics['mt_3_vios_total'] = list()
    study_metrics['lt_vios_total'] = list()

    study_metrics['iter_errors_marked'] = list()
    study_metrics['iter_errors_found'] = list()
    study_metrics['iter_errors_total'] = list()
    study_metrics['all_errors_marked'] = list()
    study_metrics['all_errors_found'] = list()
    study_metrics['all_errors_total'] = list()

    for h in h_space:
        if h['cfd'] not in fd_metadata.keys():
            continue

        mu = h['conf']
        variance = 0.0025
        alpha, beta = initialPrior(mu, variance)
        conf = alpha / (alpha + beta)
        
        fd_metadata[h['cfd']]['alpha'] = alpha
        fd_metadata[h['cfd']]['beta'] = beta
        fd_metadata[h['cfd']]['conf'] = conf

        fd_metadata[h['cfd']]['alpha_history'] = [{ 'iter_num': 0, 'value': alpha, 'elapsed_time': 0 }]
        fd_metadata[h['cfd']]['beta_history'] = [{ 'iter_num': 0, 'value': beta, 'elapsed_time': 0 }]
        fd_metadata[h['cfd']]['conf_history'] = [{ 'iter_num': 0, 'value': conf, 'elapsed_time': 0 }]

    iters = range(1, len(interaction_metadata['sample_history'])+1)
    for i in iters:
        st_vios_found = set()
        st_vios_total = set()
        st_vios_marked = set()
        mt_vios_found = set()
        mt_vios_total = set()
        mt_vios_marked = set()
        mt_2_vios_found = set()
        mt_2_vios_total = set()
        mt_2_vios_marked = set()
        mt_3_vios_found = set()
        mt_3_vios_total = set()
        mt_3_vios_marked = set()
        lt_vios_found = set()
        lt_vios_total = set()
        lt_vios_marked = set()

        iter_errors_found = 0
        iter_errors_total = 0
        iter_errors_marked = 0
        all_errors_found = 0
        all_errors_total = 0
        all_errors_marked = 0

        curr_sample = interaction_metadata['sample_history'][i-1]['value']
        mt_sample = set(curr_sample)
        mt_2_sample = set(curr_sample)
        mt_3_sample = set(curr_sample)
        if i > 1:
            mt_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            mt_2_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            mt_3_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            if i > 2:
                mt_2_sample |= set(interaction_metadata['sample_history'][i-3]['value'])
                mt_3_sample |= set(interaction_metadata['sample_history'][i-3]['value'])
                if i > 3:
                    mt_3_sample |= set(interaction_metadata['sample_history'][i-4]['value'])
        lt_sample = set(curr_sample)
        for ix in range(2, i+1):
            lt_sample |= set(interaction_metadata['sample_history'][i-ix]['value'])
        elapsed_time = interaction_metadata['sample_history'][i-1]['elapsed_time']

        feedback = dict()
        marked_rows = set()
        for x in feedback_history.keys():
            feedback[x] = dict()
            for y in feedback_history[x].keys():
                feedback[x][y] = feedback_history[x][y][i-1]['marked']
                if feedback[x][y] is True and x not in marked_rows:
                    marked_rows.add(x)

        for idx in dirty_dataset.index:
            for col in dirty_dataset.columns:
                if dirty_dataset.at[idx, col] != clean_dataset.at[idx, col]:
                    if idx in curr_sample:
                        iter_errors_total += 1
                        if feedback[str(idx)][col] is True:
                            iter_errors_found += 1
                    if idx in lt_sample:
                        all_errors_total += 1
                        if feedback[str(idx)][col] is True:
                            all_errors_found += 1
                if feedback[str(idx)][col] is True:
                    if idx in curr_sample:
                        iter_errors_marked += 1
                    if idx in lt_sample:
                        all_errors_marked += 1

        marked_rows = [r for r in marked_rows]
        
        for h in h_space:
            successes = 0
            failures = 0

            fd = h['cfd']
            if fd not in fd_metadata.keys():
                continue
            fd_m = fd_metadata[fd]

            removed_pairs = set()
            sample_X_in_fd = {(x, y) for (x, y) in fd_m['vio_pairs'] if x in curr_sample and y in curr_sample}
            for x, y in sample_X_in_fd:
                if x in marked_rows or y in marked_rows:
                    removed_pairs.add((x, y))
            
            for ix in curr_sample:
                if ix in marked_rows:
                    continue
                if i not in fd_m['vios']:
                    successes += 1
                else:
                    if len([x for x in removed_pairs if ix in x]) > 0:
                        successes += 1
                    else:
                        failures += 1

            fd_m['alpha'] += successes
            fd_m['beta'] += failures
            fd_m['conf'] = fd_m['alpha'] / (fd_m['alpha'] + fd_m['beta'])
            
            fd_m['alpha_history'].append({ 'iter_num': i, 'value': fd_m['alpha'], 'elapsed_time': elapsed_time })
            fd_m['beta_history'].append({ 'iter_num': i, 'value': fd_m['beta'], 'elapsed_time': elapsed_time })
            fd_m['conf_history'].append({ 'iter_num': i, 'value': fd_m['conf'], 'elapsed_time': elapsed_time })

            if fd != target_fd:
                continue
            vio_pairs = h['vio_pairs']
            rhs = fd.split(' => ')[1].split(', ')
            
            # Check if the violation was caught for short-term memory
            fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = vioStats(curr_sample, curr_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
            st_vios_marked |= fd_st_vios_marked
            st_vios_found |= fd_st_vios_found
            st_vios_total |= fd_st_vios_total
            print('vios found:', st_vios_found)
            print('vios marked:', st_vios_marked)
            print('vios total:', st_vios_total)

        # Medium-term memory violation calculations
        if i > 1:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = vioStats(curr_sample, mt_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_vios_marked |= fd_st_vios_marked
                mt_vios_found |= fd_st_vios_found
                mt_vios_total |= fd_st_vios_total
        else:
            mt_vios_marked = copy.deepcopy(st_vios_marked)
            mt_vios_found = copy.deepcopy(st_vios_found)
            mt_vios_total = copy.deepcopy(st_vios_total)

        if i > 2:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = vioStats(curr_sample, mt_2_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_2_vios_marked |= fd_st_vios_marked
                mt_2_vios_found |= fd_st_vios_found
                mt_2_vios_total |= fd_st_vios_total
        else:
            mt_2_vios_marked = copy.deepcopy(mt_vios_marked)
            mt_2_vios_found = copy.deepcopy(mt_vios_found)
            mt_2_vios_total = copy.deepcopy(mt_vios_total)

        if i > 3:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = vioStats(curr_sample, mt_3_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_3_vios_marked |= fd_st_vios_marked
                mt_3_vios_found |= fd_st_vios_found
                mt_3_vios_total |= fd_st_vios_total
        else:
            mt_3_vios_marked = copy.deepcopy(mt_2_vios_marked)
            mt_3_vios_found = copy.deepcopy(mt_2_vios_found)
            mt_3_vios_total = copy.deepcopy(mt_2_vios_total)
                
        # Long-term memory violation calculations
        if i > 1:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = vioStats(curr_sample, lt_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                lt_vios_marked |= fd_st_vios_marked
                lt_vios_found |= fd_st_vios_found
                lt_vios_total |= fd_st_vios_total
        else:
            lt_vios_marked = copy.deepcopy(st_vios_marked)
            lt_vios_found = copy.deepcopy(st_vios_found)
            lt_vios_total = copy.deepcopy(st_vios_total)

        # Short, mid, and long-term violation precision, recall, and F1
        if len(st_vios_total) > 0:
            st_vio_recall = len(st_vios_found) / len(st_vios_total)
        else:
            st_vio_recall = 1
        
        print('recall:', st_vio_recall)

        if len(lt_vios_total) > 0:
            lt_vio_recall = len(lt_vios_found) / len(lt_vios_total)
        else:
            lt_vio_recall = 1

        if len(mt_vios_total) > 0:
            mt_vio_recall = len(mt_vios_found) / len(mt_vios_total)
        else:
            mt_vio_recall = 1

        if len(mt_2_vios_total) > 0:
            mt_2_vio_recall = len(mt_2_vios_found) / len(mt_2_vios_total)
        else:
            mt_2_vio_recall = 1

        if len(mt_3_vios_total) > 0:
            mt_3_vio_recall = len(mt_3_vios_found) / len(mt_3_vios_total)
        else:
            mt_3_vio_recall = 1

        if len(st_vios_marked) > 0:
            st_vio_precision = len(st_vios_found) / len(st_vios_marked)
        else:
            st_vio_precision = 1

        print('precision:', st_vio_precision)

        if len(lt_vios_marked) > 0:
            lt_vio_precision = len(lt_vios_found) / len(lt_vios_marked)
        else:
            lt_vio_precision = 1

        if len(mt_vios_marked) > 0:
            mt_vio_precision = len(mt_vios_found) / len(mt_vios_marked)
        else:
            mt_vio_precision = 1

        if len(mt_2_vios_marked) > 0:
            mt_2_vio_precision = len(mt_2_vios_found) / len(mt_2_vios_marked)
        else:
            mt_2_vio_precision = 1

        if len(mt_3_vios_marked) > 0:
            mt_3_vio_precision = len(mt_3_vios_found) / len(mt_3_vios_marked)
        else:
            mt_3_vio_precision = 1

        if st_vio_precision > 0 or st_vio_recall > 0:
            st_vio_f1 = 2 * (st_vio_precision * st_vio_recall) / (st_vio_precision + st_vio_recall)
        else:
            st_vio_f1 = 1
        
        print('f1:', st_vio_f1, '\n')

        if lt_vio_precision > 0 or lt_vio_recall > 0:
            lt_vio_f1 = 2 * (lt_vio_precision * lt_vio_recall) / (lt_vio_precision + lt_vio_recall)
        else:
            lt_vio_f1 = 1

        if mt_vio_precision > 0 or mt_vio_recall > 0:
            mt_vio_f1 = 2 * (mt_vio_precision * mt_vio_recall) / (mt_vio_precision + mt_vio_recall)
        else:
            mt_vio_f1 = 1

        if mt_2_vio_precision > 0 or mt_2_vio_recall > 0:
            mt_2_vio_f1 = 2 * (mt_2_vio_precision * mt_2_vio_recall) / (mt_2_vio_precision + mt_2_vio_recall)
        else:
            mt_2_vio_f1 = 1

        if mt_3_vio_precision > 0 or mt_3_vio_recall > 0:
            mt_3_vio_f1 = 2 * (mt_3_vio_precision * mt_3_vio_recall) / (mt_3_vio_precision + mt_3_vio_recall)
        else:
            mt_3_vio_f1 = 1

        # Short and long-term error precision, recall, and F1
        if iter_errors_marked > 0:
            iter_err_precision = iter_errors_found / iter_errors_marked
        else:
            iter_err_precision = 1
        
        if iter_errors_total > 0:
            iter_err_recall = iter_errors_found / iter_errors_total
        else:
            iter_err_recall = 1

        if iter_err_precision > 0 or iter_err_recall > 0:
            iter_err_f1 = 2 * (iter_err_precision * iter_err_recall) / (iter_err_precision + iter_err_recall)
        else:
            iter_err_f1 = 1

        if all_errors_marked > 0:
            all_err_precision = all_errors_found / all_errors_marked
        else:
            all_err_precision = 1
        
        if all_errors_total > 0:
            all_err_recall = all_errors_found / all_errors_total
        else:
            all_err_recall = 1

        if all_err_precision > 0 or all_err_recall > 0:
            all_err_f1 = 2 * (all_err_precision * all_err_recall) / (all_err_precision + all_err_recall)
        else:
            all_err_f1 = 1

        study_metrics['iter_err_precision'].append({ 'iter_num': int(i), 'value': iter_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_recall'].append({ 'iter_num': int(i), 'value': iter_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_f1'].append({ 'iter_num': int(i), 'value': iter_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['all_err_precision'].append({ 'iter_num': int(i), 'value': all_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['all_err_recall'].append({ 'iter_num': int(i), 'value': all_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['all_err_f1'].append({ 'iter_num': int(i), 'value': all_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_recall'].append({ 'iter_num': int(i), 'value': st_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_recall'].append({ 'iter_num': int(i), 'value': mt_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_recall'].append({ 'iter_num': int(i), 'value': mt_2_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_recall'].append({ 'iter_num': int(i), 'value': mt_3_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_recall'].append({ 'iter_num': int(i), 'value': lt_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_precision'].append({ 'iter_num': int(i), 'value': st_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_precision'].append({ 'iter_num': int(i), 'value': mt_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_precision'].append({ 'iter_num': int(i), 'value': mt_2_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_precision'].append({ 'iter_num': int(i), 'value': mt_3_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_precision'].append({ 'iter_num': int(i), 'value': lt_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_f1'].append({ 'iter_num': int(i), 'value': st_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_f1'].append({ 'iter_num': int(i), 'value': mt_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_f1'].append({ 'iter_num': int(i), 'value': mt_2_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_f1'].append({ 'iter_num': int(i), 'value': mt_3_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_f1'].append({ 'iter_num': int(i), 'value': lt_vio_f1, 'elapsed_time': elapsed_time })

        study_metrics['st_vios_marked'].append({ 'iter_num': int(i), 'value': list(st_vios_marked), 'elapsed_time': elapsed_time })
        study_metrics['mt_vios_marked'].append({ 'iter_num': int(i), 'value': list(mt_vios_marked), 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vios_marked'].append({ 'iter_num': int(i), 'value': list(mt_2_vios_marked), 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vios_marked'].append({ 'iter_num': int(i), 'value': list(mt_3_vios_marked), 'elapsed_time': elapsed_time })
        study_metrics['lt_vios_marked'].append({ 'iter_num': int(i), 'value': list(lt_vios_marked), 'elapsed_time': elapsed_time })
        study_metrics['st_vios_found'].append({ 'iter_num': int(i), 'value': list(st_vios_found), 'elapsed_time': elapsed_time })
        study_metrics['mt_vios_found'].append({ 'iter_num': int(i), 'value': list(mt_vios_found), 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vios_found'].append({ 'iter_num': int(i), 'value': list(mt_2_vios_found), 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vios_found'].append({ 'iter_num': int(i), 'value': list(mt_3_vios_found), 'elapsed_time': elapsed_time })
        study_metrics['lt_vios_found'].append({ 'iter_num': int(i), 'value': list(lt_vios_found), 'elapsed_time': elapsed_time })
        study_metrics['st_vios_total'].append({ 'iter_num': int(i), 'value': list(st_vios_total), 'elapsed_time': elapsed_time })
        study_metrics['mt_vios_total'].append({ 'iter_num': int(i), 'value': list(mt_vios_total), 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vios_total'].append({ 'iter_num': int(i), 'value': list(mt_2_vios_total), 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vios_total'].append({ 'iter_num': int(i), 'value': list(mt_3_vios_total), 'elapsed_time': elapsed_time })
        study_metrics['lt_vios_total'].append({ 'iter_num': int(i), 'value': list(lt_vios_total), 'elapsed_time': elapsed_time })

        study_metrics['iter_errors_marked'].append({ 'iter_num': int(i), 'value': iter_errors_marked, 'elapsed_time': elapsed_time })
        study_metrics['iter_errors_found'].append({ 'iter_num': int(i), 'value': iter_errors_found, 'elapsed_time': elapsed_time })
        study_metrics['iter_errors_total'].append({ 'iter_num': int(i), 'value': iter_errors_total, 'elapsed_time': elapsed_time })
        study_metrics['all_errors_marked'].append({ 'iter_num': int(i), 'value': all_errors_marked, 'elapsed_time': elapsed_time })
        study_metrics['all_errors_found'].append({ 'iter_num': int(i), 'value': all_errors_found, 'elapsed_time': elapsed_time })
        study_metrics['all_errors_total'].append({ 'iter_num': int(i), 'value': all_errors_total, 'elapsed_time': elapsed_time })
    return study_metrics, fd_metadata