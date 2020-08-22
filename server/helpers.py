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

class CellFeedback(object):
    def __init__(self, iter_num, marked):
        self.iter_num = iter_num    # iteration number
        self.marked = marked            # whether or not the user marked the cell as noisy in this iteration

'''class CFDConfidenceHistory(object):
    def __init__(self, iter_num, conf):
        self.iter_num = iter_num
        self.conf = conf'''

class CFDWeightHistory(object):
    def __init__(self, iter_num,weight):
        self.iter_num = iter_num
        self.weight = weight

class CFDScore(object):
    def __init__(self, iter_num, score):
        self.iter_num = iter_num
        self.score = score

class StudyMetric(object):
    def __init__(self, iter_num, value):
        self.iter_num = iter_num
        self.value = value

# SAVE NOISE FEEDBACK FROM USER
def saveNoiseFeedback(data, feedback, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
    for idx in feedback.index:
        for col in feedback.columns:
            cell_metadata[int(idx)][col]['feedback_history'].append(CellFeedback(iter_num=current_iter, marked=bool(feedback.at[idx, col])))
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

    project_info['score'] = all_errors_found
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)
    print('*** Score saved ***')

    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
    print('*** Cell metadata updates saved ***')

    true_error_pct_full = all_errors_found / all_errors_total
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

    study_metrics['true_error_pct_full'].append(StudyMetric(iter_num=current_iter, value=true_error_pct_full))
    study_metrics['true_error_pct_iter'].append(StudyMetric(iter_num=current_iter, value=true_error_pct_iter))
    study_metrics['error_accuracy_full'].append(StudyMetric(iter_num=current_iter, value=error_accuracy_full))
    study_metrics['error_accuracy_iter'].append(StudyMetric(iter_num=current_iter, value=error_accuracy_iter))

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )

    return true_error_pct_full


# DISCOVER CFDS THAT COULD APPLY OVER DATASET AND THEIR CONFIDENCES
'''def runCFDDiscovery(num_rows, project_id, current_iter):
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
        return None'''


# DISCOVER CFDs THAT BEST EXPLAIN THE FEEDBACK GIVEN BY THE USER
def explainFeedback(dirty_sample, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    print('*** Cell metadata object loaded ***')

    dirty_sample = dirty_sample.applymap(str)
    
    rep_sample = dirty_sample.copy(deep=True)
    
    for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            cell = cell_metadata[int(idx)][col]
            if current_iter > 1 and len(cell['feedback_history']) > 1 and cell['feedback_history'][-1].iter_num == current_iter and cell['feedback_history'][-2].marked is True:
                dirty_sample.at[idx, col] = 'N/A'

            if len(cell['feedback_history']) >= 1 and cell['feedback_history'][-1].marked is True:
                rep_sample.at[idx, col] = 'N/A'
    print('*** Feedback reflected in \'repaired\' dataset ***')

    if dirty_sample.equals(rep_sample):
        return

    dirty_sample_fp = './store/' + project_id + '/temp_sample_w_o_feedback.csv'
    rep_sample_fp = './store/' + project_id + '/temp_sample_w_feedback.csv'
    if os.path.exists('./store/' + project_id + '/temp_sample_w_o_feedback.csv'):
        with open(dirty_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()
    if os.path.exists('./store/' + project_id + '/temp_sample_w_feedback.csv'):
        with open(rep_sample_fp, 'r+') as f:
            f.seek(0)
            f.truncate()

    d_dict = list(dirty_sample.T.to_dict().values())
    d_header = d_dict[0].keys()
    with open(dirty_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, d_header)
        writer.writeheader()
        writer.writerows(d_dict)

    rep_dict = list(rep_sample.T.to_dict().values())
    rep_header = rep_dict[0].keys()
    with open(rep_sample_fp, 'w', newline='') as f:
        writer = csv.DictWriter(f, rep_header)
        writer.writeheader()
        writer.writerows(rep_dict)
    print('*** Dirty and repaired datasets saved as CSV for XPlode ***')

    process = sp.Popen(['./xplode/CTane', dirty_sample_fp, rep_sample_fp, '0.5', str(0.5*len(dirty_sample.index))], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    res = process.communicate()
    print('*** XPlode finished ***')

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        print('*** CFD meteadata object loaded ***')
        output = res[0].decode('latin_1').replace(',]', ']')
        cfds = json.loads(output)['cfds']
        print('*** CFDs from XPlode extracted ***')
        print('cfds from xplode:', cfds)
        accepted_cfds = [c for c in cfds if c['cfd'].split(' => ')[0] != '()']
        for c in accepted_cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
                cfd_metadata[c['cfd']]['weight_history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDScore(iter_num=current_iter, score=c['score']))
        print('*** XPlode output processed ***')

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
        print('*** CFD metadata updates saved ***')
    
    else:
        print('[ERROR] There was an error running XPlode')    
    

# UPDATE TUPLE WEIGHTS BASED ON INTERACTION STATISTICS
def reinforceTuplesBasedOnInteraction(data, project_id, current_iter, is_new_feedback):
    if is_new_feedback == 0:
        return
    
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    print('*** Metadata objects loaded ***')
    for idx in data.index:

        # Evaluate exploration frequency
        expl_score = current_iter / (tuple_metadata[idx]['expl_freq'] + 1)
        print('*** Exploration score calculated ***')

        # Entropy and feedback consistency
        feedback_consistency = 0
        entropy = 0
        for col in data.columns:
            if len(cell_metadata[idx][col]['feedback_history']) > 0 and cell_metadata[idx][col]['feedback_history'][-1].marked:
                cell_entropy_list = list()
                for val in [d for d in data[col].unique() if d != 'N/A']:
                    p = len([v for v in data[col] if v == val]) / len(data.index)
                    cell_entropy = (p * math.log(p))
                    cell_entropy_list.append(cell_entropy)
                average_cell_entropy = statistics.mean(cell_entropy_list)
                entropy -= average_cell_entropy
            else:
                p = len([v for v in data[col] if v == data.at[idx, col]]) / len(data.index)
                entropy -= (p * math.log(p))
            
            for i in range(1, len(cell_metadata[idx][col]['feedback_history'])):
                if cell_metadata[idx][col]['feedback_history'][i].marked != cell_metadata[idx][col]['feedback_history'][i-1].marked:
                    feedback_consistency += 1/(current_iter-i)
        # print('*** Exploration score and feedback consistency score calculated ***')

        reinforcement_value = expl_score + entropy + feedback_consistency
        # print('*** Reinforcement value calculated ***')
                
        tuple_metadata[idx]['weight'] += reinforcement_value
        # print('*** Tuple weight updated ***')

    tuple_metadata = normalizeWeights(tuple_metadata)
    print('*** Tuple weights normalized ***')

    print('Tuple weights:')
    pprint([v['weight'] for _, v in tuple_metadata.items()])
    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    print('*** Tuple metadata updates saved ***')


# REINFORCE TUPLES BASED ON DEPENDENCIES
def reinforceTuplesBasedOnDependencies(data, project_id, current_iter, is_new_feedback, project_info):
    if is_new_feedback == 0:
        return

    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    print('*** Metadata objects loaded ***')

    for cfd, cfd_m in cfd_metadata.items():
        # Bias towards simpler rules
        lhs = cfd.split(' => ')[0][1:-1].split(', ')
        num_attributes = len(lhs) + 1
        complexity_bias = 1 / num_attributes
        print('*** Complexity bias calculated ***')

        # System's weighted prior on rule confidence
        weighted_conf = 0
        for h in cfd_m['history']:
            weighted_conf += (h.score / (current_iter - h.iter_num + 1))
        print('*** Weighted CFD confidence calculated ***')

        cfd_m['weight'] = complexity_bias + weighted_conf
        # cfd_m['weight_history'].append(CFDWeightHistory(iter_num=h.iter_num, weight=(complexity_bias + weighted_conf)))
        print('*** CFD weight updated ***')
    
    cfd_metadata = normalizeWeights(cfd_metadata)
    for cfd, cfd_m in cfd_metadata.items():
        cfd_m['weight_history'].append(CFDWeightHistory(iter_num=h.iter_num, weight=cfd_m['weight']))
    print('*** CFD weights normalized and saved in history ***')
    print('cfd weights post-duo:', [cfd_m['weight'] for _, cfd_m in cfd_metadata.items()])

    pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )

    if len(cfd_metadata_keys()) == 0:
        return

    cfd_weights = {k: v['weight'] for k, v in cfd_metadata.items()}
    cfd = pickSingleTuple(cfd_weights)

    # for cfd, cfd_m in cfd_metadata.items():
    # Update tuple weights based on whether tuple violates CFD and confidence of the CFD
    cfd_m = cfd_metadata[cfd]
    lhs = cfd.split(' => ')[0][1:-1]
    rhs = cfd.split(' => ')[1]

    patterns = fd2cfd(data, lhs, rhs)
    print('*** Transformed FD into CFD pattern set ***')
    cover, violations = buildCover(data, lhs, rhs, patterns)
    print('*** Calculate cover and violating tuples for CFD ***')
    for idx in cover:
        # reinforcement_decision = random.random()
        # if reinforcement_decision <= cfd_m['weight']:     # ensures that CFDs with higher weight influence the sample more
        tuple_metadata[idx]['weight'] += 1
        if idx in violations:
            tuple_metadata[idx]['weight'] += 1
        # print('*** Tuple weight updated ***')

    tuple_metadata = normalizeWeights(tuple_metadata)
    print('*** Tuple weights normalized ***')

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    print('*** Metadata updates saved ***')

    study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
    for cfd in project_info['scenario']['cfds']:
        if cfd in cfd_metadata.keys():
            study_metrics['cfd_confidence'][cfd].append(StudyMetric(iter_num=current_iter, value=cfd_metadata[cfd]['weight']))

    pickle.dump( study_metrics, open('./store/' + project_id + '/study_metrics.p', 'wb') )


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
        if '=' in rhs:
            rhspattern = rhs
        else:
            rhspattern = rhs + '=' + str(data.at[idx, rhs])
        if lhspattern in patterns.keys():
            patterns[lhspattern].append(rhspattern)
            if (lhspattern, rhspattern) in mappings.keys():
                mappings[(lhspattern, rhspattern)].append(idx)
            else:
                mappings[(lhspattern, rhspattern)] = [idx]
        else:
            patterns[lhspattern] = [rhspattern]
            mappings[(lhspattern, rhspattern)] = [idx]
    print('*** Patterns and mappings built ***')

    # Pick RHS patterns for each LHS from these candidates
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [k for k, v in get_mode.items() if v == max(list(counts.values()))]
        pprint('All RHS patterns for' + key + ':' + repr(patterns[key]))

        # If there is only one top RHS pattern for this LHS, pick it
        if len(patterns[key]) == 1:
            patterns[key] = patterns[key].pop()
        else:
            random_idx = random.randint(0, len(patterns[key])-1)
            patterns[key] = patterns[key][random_idx]
        print('*** RHS pattern picked ***')

    return patterns


# BUILD COVER AND VIOLATIONS
def buildCover(data, lhs, rhs, patterns):
    cover = list()
    violations = list()
    for idx in data.index:
        applies = True
        for lh in lhs.split(', '):

            # If this element of the CFD is constant
            if '=' in lh:
                lh = np.array(lh.split('='))
                if data.at[idx, lh[0]] != lh[1]:     # CFD does not apply to this row
                    applies = False
                    break

        # If this CFD applies to this row
        if applies:
            cover.append(idx)
            if lhs.count('=') == len(lhs.split(', ')) and '=' in rhs:
                rh = np.array(rhs.split('='))
                if data.at[idx, rh[0]] != rh[1]:
                    violations.append(idx)
            elif lhs.count('=') == len(lhs.split(', ')) and '=' not in rhs:
                rh_attribute = rhs.split('=')[0]
                applicable_rhv = patterns[lhs].split('=')[1]
                if data.at[idx, rh_attribute] != applicable_rhv:
                    violations.append(idx)
            elif lhs.count('=') < len(lhs.split(', ')):
                applicable_lhs = ''
                for lh in lhs.split(', '):
                    if '=' in lh:
                        applicable_lhs += lh + ', '
                    else:
                        applicable_lhs += lh + '=' + str(data.at[idx, lh]) + ', '
                applicable_lhs = applicable_lhs[:-2]
                applicable_rhs = patterns[applicable_lhs]
                rh = applicable_rhs.split('=')
                if data.at[idx, rh[0]] != rh[1]:
                    violations.append(idx)
    pprint('Cover for (' + lhs + ') => ' + rhs + ':' + repr(cover))
    pprint('Violations for (' + lhs + ') => ' + rhs + ':' + repr(violations))
    print('*** Cover and violations built ***')
    return cover, violations

# BUILD SAMPLE
def buildSample(data, sample_size, project_id, sampling_method):
    if sampling_method == 'RANDOM-PURE':
        return samplingRandomPure(data, sample_size, project_id)
    elif sampling_method == 'RANDOM-UB':
        return samplingRandomUB(data, sample_size, project_id)
    elif sampling_method == 'DUO':
        return samplingDuo(data, sample_size, project_id)
    else:
        return samplingRandomPure(data, sample_size, project_id)
    

# BUILD PURELY RANDOM SAMPLE
def samplingRandomPure(data, sample_size, project_id):
    print('Sampling method: RANDOM-PURE')
    s_out = returnTuples(data, sample_size, project_id)
    print('IDs of tuples in next sample:')
    for idx in s_out.index:
        print(idx)
    return s_out


# BUILD PROBABILISTIC SAMPLE BASED SOLELY ON METRICS FROM FEEDBACK AND TUPLES SHOWN
def samplingRandomUB(data, sample_size, project_id):
    print('Sampling method: RANDOM-UB')
    s_out = returnTuples(data, sample_size, project_id)
    return s_out


# BUILD PROBABILISTIC SAMPLE BASED ON INTERACTION METRICS AND ACTIVE LEARNING
# OF FDs/CFDs BY SYSTEM
def samplingDuo(data, sample_size, project_id):
    print('Sampling method: DUO')
    s_out = returnTuples(data, sample_size, project_id)
    return s_out


# RETURN TUPLES BASED ON WEIGHT
def returnTuples(data, sample_size, project_id):
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    tuple_weights = {k: v['weight'] for k, v in tuple_metadata.items()}
    chosen_tuples = list()
    
    print('IDs of tuples in next sample:')
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


# NORMALIZE WEIGHTS BETWEEN 0 AND 1
def normalizeWeights(m_unnormalized):
    m_normalized = m_unnormalized
    m_weight_sum = sum([v['weight'] for _, v in m_unnormalized.items()])
    for k in m_normalized.keys():
        m_normalized[k]['weight'] = m_normalized[k]['weight'] / m_weight_sum

    return m_normalized


# BUILD LEADERBOARD
def buildLeaderboard(scenario_id):
    leaderboard = list()
    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        if project_info['scenario_id'] == scenario_id:
            leaderboard.append({
                'project_id': project_id,
                'name': project_info['participant_name'],
                'score': project_info['score']
            })
    sortedLeaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)
    sortedLeaderboardWithRank = [{
        'rank': idx+1,
        'name': l['name'],
        'score': l['score']
    } for idx, l in enumerate(sortedLeaderboard)]
    return sortedLeaderboardWithRank

