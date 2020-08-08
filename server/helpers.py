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
    def __init__(self, marked, iter_num):
        self.marked = marked            # whether or not the user marked the cell as noisy in this iteration
        self.iter_num = iter_num    # iteration number

class CFDConfidenceHistory(object):
    def __init__(self, iter_num, conf):
        self.iter_num = iter_num
        self.conf = conf

class CFDScore(object):
    def __init__(self, iter_num, score):
        self.iter_num = iter_num
        self.score = score

# SAVE NOISE FEEDBACK FROM USER
def saveNoiseFeedback(data, feedback, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    for idx in feedback.index:
        for col in feedback.columns:
            cell_metadata[int(idx)][col]['feedback_history'].append(CellFeedback(marked=bool(feedback.at[idx, col]), iter_num=current_iter))
            
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
        clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
    
    # scoring function: score based on number of true errors correctly identified
    score = 0
    for idx in data.index:
        for col in data.columns:
            if data.at[idx, col] != clean_dataset.at[idx, col] and len(cell_metadata[int(idx)][col]['feedback_history']) > 0 and cell_metadata[int(idx)][col]['feedback_history'][-1].marked is True:
                score += 1

    project_info['score'] = score
    with open('./store/' + project_id + '/project_info.json', 'w') as f:
        json.dump(project_info, f)

    pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') ) 


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


# DISCOVER CFDs THAT BEST EXPLAIN THE FEEDBACK GIVEN BY THE USER
def explainFeedback(dirty_sample, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    
    rep_sample = dirty_sample.copy(deep=True)
    
    for idx in dirty_sample.index:
        for col in dirty_sample.columns:
            cell = cell_metadata[int(idx)][col]
            if current_iter > 1 and len(cell['feedback_history']) > 1 and cell['feedback_history'][-1].iter_num == current_iter and cell['feedback_history'][-2].marked is True:
                dirty_sample.at[idx, col] = 'N/A'

            if len(cell['feedback_history']) >= 1 and cell['feedback_history'][-1].marked is True:
                rep_sample.at[idx, col] = 'N/A'

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

    process = sp.Popen(['./xplode/CTane', dirty_sample_fp, rep_sample_fp, '0.5', str(0.7*len(dirty_sample.index))], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    res = process.communicate()

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        output = res[0].decode('latin_1').replace(',]', ']')
        cfds = json.loads(output)['cfds']
        print('cfds from xplode:', cfds)
        accepted_cfds = [c for c in cfds if c['cfd'].split(' => ')[0] != '()']
        for c in accepted_cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDScore(iter_num=current_iter, score=c['score']))

        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
    
    else:
        print('[ERROR] There was an error running XPlode')    
    

# UPDATE TUPLE WEIGHTS BASED ON INTERACTION STATISTICS
def reinforceTuplesBasedOnInteraction(data, project_id, current_iter, is_new_feedback):
    if is_new_feedback == 0:
        return
    
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    for idx in data.index:

        # Evaluate exploration frequency
        expl_score = current_iter / (tuple_metadata[idx]['expl_freq'] + 1)

        # Entropy and feedback consistency
        feedback_consistency = 0
        entropy = 0
        for col in data.columns:
            if len(cell_metadata[idx][col]['feedback_history']) > 0 and cell_metadata[idx][col]['feedback_history'][-1].marked:
                cell_entropy_list = list()
                for val in data[col].unique():
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

        reinforcement_value = expl_score + entropy + feedback_consistency
                
        tuple_metadata[idx]['weight'] += reinforcement_value

    tuple_metadata = normalizeWeights(tuple_metadata)

    print('Tuple weights:')
    pprint([v['weight'] for _, v in tuple_metadata.items()])
    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )


# REINFORCE TUPLES BASED ON DEPENDENCIES
def reinforceTuplesBasedOnDependencies(data, project_id, current_iter, is_new_feedback):
    if is_new_feedback == 0:
        return

    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )

    for cfd, cfd_m in cfd_metadata.items():
        # Bias towards simpler rules
        lhs = cfd.split(' => ')[0][1:-1].split(', ')
        num_attributes = len(lhs) + 1
        complexity_bias = 1 / num_attributes

        # System's weighted prior on rule confidence
        weighted_conf = 0
        for h in cfd_m['history']:
            weighted_conf += (h.score / (current_iter - h.iter_num + 1))

        cfd_m['weight'] = complexity_bias + weighted_conf

    cfd_metadata = normalizeWeights(cfd_metadata)
    print('cfd weights post-duo:', [cfd_m['weight'] for _, cfd_m in cfd_metadata.items()])

    for cfd, cfd_m in cfd_metadata.items():
        # Update tuple weights based on whether tuple violates CFD and confidence of the CFD
        lhs = cfd.split(' => ')[0][1:-1]
        rhs = cfd.split(' => ')[1]

        patterns = fd2cfd(data, lhs, rhs)
        cover, violations = buildCover(data, lhs, rhs, patterns)
        for idx in cover:
            reinforcement_decision = random.random()
            if reinforcement_decision <= cfd_m['weight']:     # ensures that CFDs with higher weight influence the sample more
                tuple_metadata[idx]['weight'] += 1
            if idx in violations:
                tuple_metadata[idx]['weight'] += 1

    tuple_metadata = normalizeWeights(tuple_metadata)

    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )


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

    # Pick RHS patterns for each LHS from these candidates
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [key for key, v in get_mode.items() if v == max(list(counts.values()))]

        # If there is only one top RHS pattern for this LHS, pick it
        if len(patterns[key]) == 1:
            patterns[key] = patterns[key].pop()
        else:
            random_idx = random.randint(0, len(patterns[key])-1)
            patterns[key] = patterns[key][random_idx]

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
                        applicable_lhs += lh + '=' + data.at[idx, lh] + ', '
                applicable_lhs = applicable_lhs[:-2]
                applicable_rhs = patterns[applicable_lhs]
                rh = applicable_rhs.split('=')
                if data.at[idx, rh[0]] != rh[1]:
                    violations.append(idx)

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

