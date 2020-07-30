import random
from pprint import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np
import sys
import pickle
import math
import statistics
from collections import Counter

# sys.path.insert(0, './charm/keywordSearch/')
# import charm

# CELL VALUE HISTORY OBJECT
# class ValueHistory(object):
#     def __init__(self, value, iter_num, changed):
#         self.value = value      # the value
#         self.agent = agent      # who set this cell to this value at this point, user or system
#         self.cfd_applied = cfd_applied      # the CFD that resulted in this value
#         self.iter_num = iter_num                # the iteration number for this value
#         self.changed = changed              # whether this value is a change from the previous state

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

# MAP USER-SUBMITTED REPAIRS FROM SAMPLE TO FULL DATASET
# def applyUserModFeedback(d_prev, s_in, project_id, current_iter):
#     d_curr = d_prev
#     cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )

#     for idx in s_in.index:
#         for col in s_in.columns:
#             if d_curr[idx][col] != s_in.at[idx, col]:
#                 d_curr[idx][col] = s_in.at[idx, col]
#                 cell_metadata[idx][col]['history'].append(ValueHistory(value=s_in.at[idx, col], iter_num=current_iter, changed=True))
#             else:
#                 cell_metadata[idx][col]['history'].append(ValueHistory(value=d_curr[idx][col], iter_num=current_iter, changed=False))

#     pickle.dump( cell_metadata, open('./store/' + project_id + '/cell_metadata.p', 'wb') )
#     return d_curr


# SAVE NOISE FEEDBACK FROM USER
def saveNoiseFeedback(data, feedback, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'rb') )
    print(feedback)
    for idx in feedback.index:
        for col in feedback.columns:
            cell_metadata[int(idx)][col]['feedback_history'].append(CellFeedback(marked=feedback.at[idx, col], iter_num=current_iter))
            
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
        clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
    
    # scoring function: score based on number of true errors correctly identified
    score = 0
    for idx in data.index:
        for col in data.columns:
            if data.at[idx, col] != clean_dataset[idx, col] and cell_metadata[int(idx)][col]['feedback_history'][-1].marked is True:
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
def explainFeedback(sample, project_id, current_iter):
    cell_metadata = pickle.load( open('./store/' + project_id + '/cell_metadata.p', 'wb') )
    
    dirty_data = sample
    dirty_dataset_fp = './store/' + project_id + 'temp_dirty_sample.csv'
    dirty_data.to_csv(dirty_dataset_fp, index=False)
    
    rep_data = dirty_data
    for idx in dirty_data.index:
        for col in dirty_data.columns:
            if cell_metadata[int(idx)][col]['feedback_history'][-1].marked is True:
                rep_data.at[idx, col] = np.nan
                
    rep_dataset_fp = './store/' + project_id + 'temp_feedback_sample.csv'
    rep_data.to_csv(rep_dataset_fp, index=False)
    
    process = sp.Popen(['./xplode/CTane', dirty_dataset_fp, rep_dataset_fp, str(0.7*len(dirty_data.index)), '0.7'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    res = process.communicate()
    print('res:', res[0])

    if process.returncode == 0:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        output = res[0].decode('latin_1').replace(',]', ']')
        cfds = json.loads(output)['cfds']
        for c in cfds:
            if c['cfd'] not in cfd_metadata.keys():
                cfd_metadata[c['cfd']] = dict()
                cfd_metadata[c['cfd']]['history'] = list()
            cfd_metadata[c['cfd']]['history'].append(CFDScore(iter_num=current_iter, score=c['score']))

        pickle.load( cfd_metadata, open('./store' + project_id + 'cfd_metadata.p', 'wb') )
    
    else:
        print('[ERROR] There was an error running XPlode')    
    

# UPDATE TUPLE WEIGHTS BASED ON INTERACTION STATISTICS
def reinforceTuplesBasedOnInteraction(data, project_id, current_iter, is_new_feedback):
    if is_new_feedback is False:
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
            if cell_metadata[idx][col]['feedback_history'][-1].marked:
                cell_entropy_list = list()
                for val in data[col].unique():
                    p = len([v for v in data[col] if v == val].to_list()) / len(data.index)
                    cell_entropy = (p * math.log(p))
                    cell_entropy_list.append(cell_entropy)
                average_cell_entropy = statistics.mean(cell_entropy_list)
                entropy -= average_cell_entropy
            else:
                p = len([v for v in data[col] if v == data.at[idx, col]].to_list()) / len(data.index)
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
    if is_new_feedback is False:
        return

    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )

    for cfd in cfd_metadata.keys():
        # Bias towards simpler rules
        lhs = cfd.split(' => ')[0][1:-1].split(', ')
        num_attributes = len(lhs) + 1
        complexity_bias = 1 / num_attributes

        # System's weighted prior on rule confidence
        weighted_conf = 0
        for h in cfd['history']:
            weighted_conf += (h.score / (current_iter - h.iter_num + 1))

        cfd['weight'] = complexity_bias + weighted_conf
    
    cfd_metadata = normalizeWeights(cfd_metadata)

    for cfd in cfd_metadata.keys():
        # Update tuple weights based on whether tuple violates CFD and confidence of the CFD
        lhs = cfd.split(' => ')[0][1:-1].split(', ')
        rhs = cfd.split(' => ')[1]

        patterns = fd2cfd(data, lhs, rhs)
        cover, violations = buildCover(data, lhs, rhs, patterns)
        for idx in cover:
            reinforcement_decision = random.random()
            if reinforcement_decision <= cfd['weight']:     # ensures that CFDs with higher weight influence the sample more
                tuple_metadata[idx]['weight'] += 0.5
            if idx in violations:
                tuple_metadata[idx]['weight'] += 0.5

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
                lhspattern += clause + '=' + data.at[idx, clause] + ', '
        lhspattern = lhspattern[:-2]
        if '=' in rhs:
            rhspattern = rhs
        else:
            rhspattern = rhs + '=' + data.at[idx, rhs]
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
            random_idx = random.randint(0, len(patterns[key]))
            patterns[key] = patterns[key][random_idx]

    return patterns


# BUILD COVER AND VIOLATIONS
def buildCover(data, lhs, rhs, patterns):
    cover = list()
    violations = list()
    for idx in data.index():
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
                for lh in lhs:
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
    tuple_metadata = pickle.load( open('./store/' + project_id + '/tuple_metadata.p', 'rb') )
    
    s_out = data.sample(n=sample_size, random_state=1)
    for idx in s_out.index:
        tuple_metadata[idx]['expl_freq'] += 1
        
    pickle.dump( tuple_metadata, open('./store/' + project_id + '/tuple_metadata.p', 'wb') )
    
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
    #TODO: DUO-specific weight modifications
    s_out = returnTuples(data, sample_size, project_id)
    return s_out


# RETURN TUPLES BASED ON WEIGHT
def returnTuples(data, sample_size, project_id):
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

