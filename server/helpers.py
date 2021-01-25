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
        # self.all_vios_found_history = []
        # self.iter_vios_found_history = []
        # self.iter_vios_total_history = []
        # self.alpha_err = alpha
        # self.alpha_err_history = [alpha]
        # self.beta_err = beta
        # self.beta_err_history = [beta]
    
    def asdict(self):
        print([list(vp) for vp in self.vio_pairs])
        return {
            'lhs': self.lhs,
            'rhs': self.rhs,
            'alpha': self.alpha,
            'alpha_history': self.alpha_history,
            'beta': self.beta,
            'beta_history': self.beta_history,
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
    
    all_vios_found = set()
    all_vios_total = set()
    # all_vios_marked = 0
    iter_vios_found = set()
    iter_vios_total = set()
    
    all_errors_found = 0
    all_errors_total = 0
    all_errors_marked = 0
    iter_errors_found = 0
    iter_errors_total = 0
    iter_errors_marked = 0

    # Track vios caught in each iteration
    for fd_m in fd_metadata.values():
        fd_m.all_vios_found_history.append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
        fd_m.iter_vios_found_history.append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
        fd_m.iter_vios_total_history.append(StudyMetric(iter_num=current_iter, value=0, elapsed_time=elapsed_time))
        
        all_vios_total |= fd_m.vio_pairs
        for i, j in fd_m.vio_pairs:
            if str(i) in feedback.keys() and str(j) in feedback.keys():
                iter_vios_total.add((i, j))
                fd_m.iter_vios_total_history[-1].value += 1
            caught = True
            for rh in fd_m.rhs:
                if feedback[str(i)][rh] is False and feedback[str(j)][rh] is False:
                    caught = False
                    break
            if caught is True:
                all_vios_found.add((i, j))
                fd_m.all_vios_found_history[-1].value += 1
                if str(i) in feedback.keys() and str(j) in feedback.keys():
                    iter_vios_found.add((i, j))
                    fd_m.iter_vios_found_history[-1].value += 1

    # Track errors caught in each iteration
    for idx in data.index:
        for col in data.columns:
            if data.at[idx, col] != clean_dataset.at[idx, col]:
                all_errors_total += 1
                if str(idx) in feedback.keys():
                    iter_errors_total += 1
                    if bool(feedback[str(idx)][col]) is True:
                        iter_errors_found += 1
                if interaction_metadata['feedback_history'][int(idx)][col][-1].marked is True:
                    all_errors_found += 1
            if interaction_metadata['feedback_history'][int(idx)][col][-1].marked is True:
                all_errors_marked += 1
                if str(idx) in feedback.keys():
                    iter_errors_marked += 1

    print('*** Score updated ***')

    project_info['true_pos'] = all_errors_found
    project_info['false_pos'] = all_errors_marked - all_errors_found
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)
    print('*** Score saved ***')

    pickle.dump( interaction_metadata, open('./store/' + project_id + '/interaction_metadata.p', 'wb') )
    print('*** Interaction metadata updates saved ***')

    # VIOLATIONS
    # if iter_vios_marked > 0:
    #     vio_precision = iter_vios_found / iter_vios_marked
    # else:
    #     vio_precision = 0
    
    if len(iter_vios_total) > 0:
        iter_vio_recall = len(iter_vios_found) / len(iter_vios_total)
    else:
        iter_vio_recall = 0

    if len(all_vios_total) > 0:
        all_vio_recall = len(all_vios_found) / len(all_vios_total)
    else:
        all_vio_recall = 0

    # if vio_precision > 0 and vio_recall > 0:
    #     vio_f1 = 2 * (vio_precision * vio_recall) / (vio_precision + vio_recall)
    # else:
    #     vio_f1 = 0

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

    # study_metrics['vio_precision'].append(StudyMetric(iter_num=current_iter, value=vio_precision, elapsed_time=elapsed_time))
    study_metrics['iter_vio_recall'].append(StudyMetric(iter_num=current_iter, value=iter_vio_recall, elapsed_time=elapsed_time))
    study_metrics['all_vio_recall'].append(StudyMetric(iter_num=current_iter, value=all_vio_recall, elapsed_time=elapsed_time))
    # study_metrics['vio_f1'].append(StudyMetric(iter_num=current_iter, value=vio_f1, elapsed_time=elapsed_time))

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
    # print(feedback)
    print('*** about to interpret feedback ***')
    marked_rows = list()
    for idx in feedback.index:
        for col in feedback.columns:
            if bool(feedback.at[idx, col]) is True:
                marked_rows.append(int(idx))
                break

    # print(sample_X)
    # pruned_s_in = s_in.drop([int(i) for i in pruned_rows])
    # pruned_sample_X = sample_X
    # for row in pruned_rows:
    #     pruned_sample_X = {x for x in pruned_sample_X if int(row) not in x}
        # print(sample_X)

    # print(len(X))
    # print(len(sample_X))

    # Calculate P(X | \theta_h) for each FD
    for fd, fd_m in fd_metadata.items():
        # if target_fd is not None and fd != target_fd:
        #     continue
        
        # successes_X = set()
        # failures_X = set()
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

        # print('successes:', len(successes_X))
        # print('failures:', len(failures_X))
        print('successes:', successes)
        print('failures:', failures)
                
        # fd_m.alpha += len(successes_X)
        fd_m.alpha += successes
        fd_m.alpha_history.append(StudyMetric(iter_num=current_iter, value=fd_m.alpha, elapsed_time=elapsed_time))
        # fd_m.beta += len(failures_X)
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

    elapsed_time = current_time - start_time

    s_index, sample_X = returnTuples(data, X, sample_size)
    s_out = data.loc[s_index, :]

    print('IDs of tuples in next sample:', s_out.index)
    
    return s_out, sample_X


# RETURN TUPLES AND VIOS FOR SAMPLE
def returnTuples(data, X, sample_size):
    s_out = random.sample(population=list(data.index), k=sample_size)
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
            # print(conf)
            if conf >= min_conf and len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                # print('here')
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
    beta = (1 - mu) * ((mu * (1 - mu) / variance) - 1)
    alpha = (mu * beta) / (1 - mu)
    return alpha, beta

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

    # for v in vios:
    #     for idx in support:
    #         if idx == v:
    #             continue
    #         match = True
    #         for lh in lhs:
    #             if data.at[idx, lh] != data.at[v, lh]:
    #                 match = False   # idx and v do not have the same LHS
    #                 break
    #         if match is True:   # if idx and v have the same LHS
    #             pair = (idx, v) if v > idx else (v, idx)
    #             all_pairs.append(pair)
    #             vio_pair = None
    #             for rh in rhs:
    #                 if data.at[idx, rh] != data.at[v, rh]:
    #                     vio_pair = (idx, v) if v > idx else (v, idx)
    #                     break
    #             if vio_pair is not None and vio_pair not in vio_pairs:
    #                 vio_pairs.append(vio_pair)

    # return all_pairs, vio_pairs