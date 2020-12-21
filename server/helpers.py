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

# RECORD USER FEEDBACK (FOR TRUE POS AND FALSE POS)
def recordFeedback():
    pass

# INTERPRET USER FEEDBACK AND UPDATE PROBABILITIES
def interpretFeedback(s_in, feedback, X, sample_X, project_id, target_fd=None):
    fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
    # start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )

    # Remove marked cells from consideration
    print(feedback)
    pruned_rows = list()
    for idx in feedback.index:
        for col in feedback.columns:
            if feedback.at[idx, col] is True:
                pruned_rows.append(idx)
                break

    pruned_sample_X = sample_X
    for row in pruned_rows:
        pruned_sample_X = filter(lambda x: row not in x, pruned_sample_X)

    print(len(X))
    print(len(pruned_sample_X))

    # p_sample_X = (math.factorial(len(pruned_sample_X)) * math.factorial(len(X) - len(pruned_sample_X))) / math.factorial(len(X))
    p_sample_X = math.factorial(len(pruned_sample_X))
    for i in range(0, len(pruned_sample_X)):
        p_sample_X /= (len(X) - i)

    # Calculate P(X | \theta_h) for each FD
    for fd, fd_m in fd_metadata.items():
        if fd != target_fd:
            continue
        p_X_given_theta = 1
        successes_X = set()
        failures_X = set()
        for x in pruned_sample_X:
            if x not in fd_m.vio_pairs:
                p_X_given_theta *= fd_m.theta
                successes_X.add(x)
            else:
                p_X_given_theta *= (1 - fd_m.theta)
                failures_X.add(x)
        
        # Calculate P(\theta_h | X) for each FD using previous p(\theta_h) and p(X)
        print(p_X_given_theta)
        print(fd_m.p_theta)
        print(p_sample_X)
        fd_m.p_theta = (p_X_given_theta * fd_m.p_theta) / p_sample_X
        fd_m.p_theta_history.append(fd_m.p_theta)
        fd_m.alpha += len(successes_X)
        fd_m.alpha_history.append(fd_m.alpha)
        fd_m.beta += len(failures_X)
        fd_m.beta_history.append(fd_m.beta)
        fd_m.theta = fd_m.alpha / (fd_m.alpha + fd_m.beta)
        fd_m.theta_history.append(fd_m.theta)

    pickle.dump( fd_metadata, open('./store/' + project_id + '/fd_metadata.p', 'wb') )

# BUILD SAMPLE
def buildSample(data, X, sample_size, project_id, current_iter, current_time):
    fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
    # modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
    start_time = pickle.load( open('./store/' + project_id + '/start_time.p', 'rb') )

    elapsed_time = current_time - start_time

    s_index, sample_X = returnTuples(data, X, sample_size)
    s_out = data.loc[s_index, :]

    # p_sample_X = (math.factorial(len(sample_X)) * math.factorial(len(X) - len(sample_X))) / math.factorial(len(X))

    # modeling_metadata['X'].append(StudyMetric(iter_num=current_iter, value=sample_X, elapsed_time=elapsed_time))
    # modeling_metadata['p_X'].append(StudyMetric(iter_num=current_iter, value=p_sample_X, elapsed_time=elapsed_time))

    print('IDs of tuples in next sample:', s_out.index)

    # pickle.dump( modeling_metadata, open('./store/' + project_id + '/modeling_metadata.p', 'wb') )
    
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

    composition_space = [{ 'cfd': h['cfd'], 'conf': h['conf'] } for h in h_space] if h_space is not None else list()
    for composed_fd in further_composed_fds:
        if clean_data is not None:
            support, vios = getSupportAndVios(dirty_data, clean_data, composed_fd)
            conf = (len(support) - len(vios)) / len(support)
            if conf >= min_conf and len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                composition_space.append({
                    'cfd': composed_fd,
                    'conf': conf
                })
        else:
            if len(composed_fd.split(' => ')[0][1:-1].split(', ')) <= max_ant:
                composition_space.append({
                    'cfd': composed_fd,
                    'conf': None
                })

    return composition_space

def pTheta(theta, a, b):
    return (math.pow(theta, (a-1)) * math.pow((1-theta), (b-1))) / sc.beta(a, b)