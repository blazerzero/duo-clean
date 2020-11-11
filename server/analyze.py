from pprint import pprint
import os
import json
import numpy as np
import pandas as pd
from scipy.stats import hmean
import matplotlib.pyplot as plt
import sys
import csv
import pickle
import math
import statistics
from operator import attrgetter
from collections import Counter

class PHGivenX(object):
    def __init__(self, h, value):
        self.h = h
        self.value = value

class StudyMetric(object):
    def __init__(self, iter_num, value, elapsed_time):
        self.iter_num = iter_num
        self.value = value
        self.elapsed_time = elapsed_time

def aHeuristicUniform(cfd):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    weights = {lh: 0.5 for lh in lhs}
    return weights

def aHeuristicUV(cfd, data):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    weights = dict()
    for lh in lhs:
        numUV = len(set(data[lh])) if '=' not in lh else 1
        weights[lh] = numUV / len(data.index)
    return weights

def aHeuristicAC(cfd):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    wAC = {
        'type': 0.4,
        'region': 0.6,
        'facilityname': 0.9,
        'owner': 0.9,
        'ownertype': 0.5,
        'manager': 0.75,
        'listingnumber': 0.9,
        'title': 0.8,
        'year': 0.3,
        'rating': 0.75,
        'director': 0.6,
        'userrating': 0.1
    }
    weights = {lh: wAC[lh] for lh in lhs}
    # for lh in lhs:
    #     if '=' in lh:
    #         lh_key = lh.split('=')[0]
    #         lh_val = lh.split('=')[1].replace('\n', '').replace('\t', '').replace('\r', '')
    #         if lh_val.isnumeric():
    #             lh_val = int(lh_val)
    #         num_lh_val = len(data[data[lh_key] == lh_val])
    #         weights[lh] = wAC[lh_key] / num_lh_val
    #     else:
    #         weights[lh] = wAC[lh]
    return weights

def aHeuristicCombo(cfd, data):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    wUV = aHeuristicUV(cfd, data)
    wAC = aHeuristicAC(cfd)
    weights = {lh: hmean([wUV[lh], wAC[lh]]) for lh in lhs}
    return weights

def sHeuristicUniform(cfd):
    return 1      # sUniform assumes the structure of the FD w.r.t. to similar FDs does not affect its chance of being believed by the user

def sHeuristicSetRelation(cfd, all_cfds):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    lhs_set = set(lhs)
    subset_cfds = set([c.split(' => ')[0][1:-1] for c in all_cfds if lhs_set.issuperset(set(c.split(' => ')[0][1:-1].split(', ')))])
    superset_cfds = set([c.split(' => ')[0][1:-1] for c in all_cfds if set(c.split(' => ')[0][1:-1].split(', ')).issuperset(lhs_set)])

    similar_cfd_set = lhs_set | subset_cfds | superset_cfds
    similar_cfds = [c.split(', ') for c in similar_cfd_set]
    similar_cfds.sort(key=len)
    lhs_idx = similar_cfds.index(lhs)
    weight = (len(similar_cfds) - lhs_idx) / len(similar_cfds)
    return weight

def bayes(sampling_method):
    # with open('scenarios.json') as f:
    #     all_scenarios = json.load(f)
    # scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        if scenario['sampling_method'] != sampling_method:
            continue
        print("project id:", project_id)
        print("scenario id:", project_info['scenario_id'])
        data = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
        data = data.replace(r'\\n\\t\\r','', regex=True) 

        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        # gt_metadata = pickle.load( open('./store/' + project_id + '/gt_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        # clean_fd_metadata = pickle.load( open('./store/' + project_id + '/clean_fd_metadata.p', 'rb') )
        
        bayes_modeling_metadata = modeling_metadata
        # gt_bayes_metadata = gt_metadata

        bayes_modeling_metadata['p_Y_in_C_given_X'] = dict()
        # gt_bayes_metadata['p_Y_in_C_given_X'] = dict()

        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        # p_h = dict()
        # p_h['aUNI'] = dict()
        # p_h['aUV'] = dict()
        # p_h['aAC'] = dict()
        # p_h['aCOMBO'] = dict()
        # p_h['sUNI'] = dict()
        # p_h['sSR'] = dict()
        bayes_modeling_metadata['p_h'] = dict()
        # gt_bayes_metadata['p_h'] = dict()
        # bayes_modeling_metadata['p_h']['aUNI-sUNI'] = dict()
        # bayes_modeling_metadata['p_h']['aUNI-sSR'] = dict()
        # bayes_modeling_metadata['p_h']['aUV-sUNI'] = dict()
        # bayes_modeling_metadata['p_h']['aUV-sSR'] = dict()
        # bayes_modeling_metadata['p_h']['aAC-sUNI'] = dict()
        # bayes_modeling_metadata['p_h']['aAC-sSR'] = dict()
        # bayes_modeling_metadata['p_h']['aCOMBO-sUNI'] = dict()
        bayes_modeling_metadata['p_h']['aCOMBO-sSR'] = dict()
        # gt_bayes_metadata['p_h']['aCOMBO-sSR'] = dict()

        # all_cfds = cfd_metadata.keys()

        # p(h)        
        # for cfd in all_cfds:
            # UNIFORM ATTRIBUTE WEIGHTS
            # wUniform = aHeuristicUniform(cfd)   # attribute weights (aUniform)
            # wUV = aHeuristicUV(cfd, data)       # attribute weights (aUV)
            # wAC = aHeuristicAC(cfd, data) # attribute weights (aAC)
            # wCombo = aHeuristicCombo(cfd, data) # attribute weights (aCombo = aUV * aAC)

            # p(h | [heuristic]) = PI_i w(a_i), where a_i is an attribute in the LHS of h
            # phaUniform = np.prod([v for _, v in wUniform.items()])   # p(h | aUniform)
            # phaUV = np.prod([v for _, v in wUV.items()])     # p(h | aUV)
            # phaAC = np.prod([v for _, v in wAC.items()])     # p(h | aAC)
            # phaCombo = np.prod([v for _, v in wCombo.items()])   # p(h | aCombo)
            # phsUniform = sHeuristicUniform(cfd)
            # phsSetRelation = sHeuristicSetRelation(cfd, all_cfds)
            # p_h['aUNI'][cfd] = phaUniform
            # p_h['aUV'][cfd] = phaUV
            # p_h['aAC'][cfd] = phaAC
            # p_h['aCOMBO'][cfd] = phaCombo
            # p_h['sUNI'][cfd] = phsUniform
            # p_h['sSR'][cfd] = phsSetRelation

            # bayes_modeling_metadata['p_h']['aUNI-sUNI'][cfd] = p_h['aUNI'][cfd] * p_h['sUNI'][cfd]
            # bayes_modeling_metadata['p_h']['aUNI-sSR'][cfd] = p_h['aUNI'][cfd] * p_h['sSR'][cfd]
            # bayes_modeling_metadata['p_h']['aUV-sUNI'][cfd] = p_h['aUV'][cfd] * p_h['sUNI'][cfd]
            # bayes_modeling_metadata['p_h']['aUV-sSR'][cfd] = p_h['aUV'][cfd] * p_h['sSR'][cfd]
            # bayes_modeling_metadata['p_h']['aAC-sUNI'][cfd] = p_h['aAC'][cfd] * p_h['sUNI'][cfd]
            # bayes_modeling_metadata['p_h']['aAC-sSR'][cfd] = p_h['aAC'][cfd] * p_h['sSR'][cfd]
            # bayes_modeling_metadata['p_h']['aCOMBO-sUNI'][cfd] = p_h['aCOMBO'][cfd] * p_h['sUNI'][cfd]
            # bayes_modeling_metadata['p_h']['aCOMBO-sSR'][cfd] = p_h['aCOMBO'][cfd] * p_h['sSR'][cfd]
            # gt_bayes_metadata['p_h']['aCOMBO-sSR'][cfd] = p_h['aCOMBO'][cfd] * p_h['sSR'][cfd]

        # for heur in bayes_modeling_metadata['p_h'].keys():
        # print(heur)
        bayes_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'] = list()
        # gt_bayes_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'] = list()
        for it in range(1, iter_count+1):
            elapsed_time = bayes_modeling_metadata['Y'][it-1].elapsed_time

            # Get all FDs/CFDs that have were known by the system in this iteration
            discovered_cfds = [cfd for cfd, cfd_m in cfd_metadata.items()]
            
            if len(discovered_cfds) == 0:   # no FDs discovered yet
                # P(Y in C | X) = 0
                bayes_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                continue
                
            p_h_given_X_list = list()
            # p(h | X) for each h
            for h in discovered_cfds:
                elem = next(x for x in bayes_modeling_metadata['p_X_given_h'][h] if x.iter_num == it)     # p(X | h) for this iteration
                # print(elem.value)
                p_X_given_h = elem.value
                # print(it)
                # print(cfd_metadata[h]['weight_history'][it-1].iter_num)
                p_h = cfd_metadata[h]['weight_history'][it-1].weight    # p(h)
                p_h_given_X = p_X_given_h * p_h     # p(h | X)
                p_h_given_X_list.append(PHGivenX(h=h, value=p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            p_h_given_X_list_sum = sum([x.value for x in p_h_given_X_list])
            p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/p_h_given_X_list_sum) if x.value > 0 else 0)) for x in p_h_given_X_list]

            # p(Y in C | X)
            p_Y_in_C_given_X = 1
            for y in bayes_modeling_metadata['Y'][it-1].value:
                p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in p_h_given_X_list:
                    h = phgx.h
                    p_h_given_X = phgx.value    # p(h | X)
                    i_y_in_h = next(i for i in bayes_modeling_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    p_y_in_C_given_X += (i_y_in_h * p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                    
                p_Y_in_C_given_X *= p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
            print('p(Y in C | X) =', p_Y_in_C_given_X)
            
            bayes_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=p_Y_in_C_given_X, elapsed_time=elapsed_time))

            # GROUND TRUTH
            # Get all FDs/CFDs that have were known by the system in this iteration
            '''clean_discovered_cfds = [cfd for cfd, cfd_m in clean_fd_metadata.items()]
            
            if len(clean_discovered_cfds) == 0:   # no FDs discovered yet
                # P(Y in C | X) = 0
                gt_bayes_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                continue
            clean_p_h_given_X_list = list()
            for h in clean_discovered_cfds:
                clean_elem = next(x for x in gt_bayes_metadata['p_X_given_h'][h] if x.iter_num == it)     # p(X | h) for this iteration
                clean_p_X_given_h = clean_elem.value
                clean_p_h = clean_fd_metadata[h]['weight_history'][it-1].weight     # p(h)
                clean_p_h_given_X = clean_p_X_given_h * clean_p_h     # p(h | X)
                clean_p_h_given_X_list.append(PHGivenX(h=h, value=clean_p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            clean_p_h_given_X_list_sum = sum([x.value for x in clean_p_h_given_X_list])
            clean_p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/clean_p_h_given_X_list_sum) if x.value > 0 else 0)) for x in clean_p_h_given_X_list]

            # p(Y in C | X)
            clean_p_Y_in_C_given_X = 1
            for y in gt_bayes_metadata['Y'][it-1].value:
                clean_p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in clean_p_h_given_X_list:
                    h = phgx.h
                    clean_p_h_given_X = phgx.value    # p(h | X)
                    clean_i_y_in_h = next(i for i in gt_bayes_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    clean_p_y_in_C_given_X += (clean_i_y_in_h * clean_p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                    
                clean_p_Y_in_C_given_X *= clean_p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
            print('GROUND TRUTH p(Y in C | X) =', clean_p_Y_in_C_given_X)
            
            gt_bayes_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=clean_p_Y_in_C_given_X, elapsed_time=elapsed_time))'''

        pickle.dump( bayes_modeling_metadata, open('./store/' + project_id + '/bayes_modeling_metadata.p', 'wb') )
        # pickle.dump( gt_bayes_metadata, open('./store/' + project_id + '/gt_bayes_metadata.p', 'wb') )


def max_likelihood(sampling_method):
    # with open('scenarios.json') as f:
    #     all_scenarios = json.load(f)
    # scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        if scenario['sampling_method'] != sampling_method:
            continue
        
        data = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
        data = data.replace(r'\\n\\t\\r','', regex=True) 
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        # gt_metadata = pickle.load( open('./store/' + project_id + '/gt_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        # clean_fd_metadata = pickle.load( open('./store/' + project_id + '/clean_fd_metadata.p', 'rb') )
        
        min_modeling_metadata = modeling_metadata
        # gt_min_metadata = gt_metadata

        min_modeling_metadata['p_Y_in_C_given_X'] = dict()
        # gt_min_metadata['p_Y_in_C_given_X'] = dict()

        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        # p_h = dict()
        # p_h['aUNI'] = dict()
        # p_h['aUV'] = dict()
        # p_h['aAC'] = dict()
        # p_h['aCOMBO'] = dict()
        # p_h['sUNI'] = dict()
        # p_h['sSR'] = dict()
        # min_modeling_metadata['p_h'] = dict()
        # min_modeling_metadata['p_h']['aUNI-sUNI'] = dict()
        # min_modeling_metadata['p_h']['aUNI-sSR'] = dict()
        # min_modeling_metadata['p_h']['aUV-sUNI'] = dict()
        # min_modeling_metadata['p_h']['aUV-sSR'] = dict()
        # min_modeling_metadata['p_h']['aAC-sUNI'] = dict()
        # min_modeling_metadata['p_h']['aAC-sSR'] = dict()
        # min_modeling_metadata['p_h']['aCOMBO-sUNI'] = dict()
        # min_modeling_metadata['p_h']['aCOMBO-sSR'] = dict()

        # all_cfds = cfd_metadata.keys()

        # p(h)        
        # for cfd in all_cfds:
            # UNIFORM ATTRIBUTE WEIGHTS
            # wUniform = aHeuristicUniform(cfd)   # attribute weights (aUniform)
            # wUV = aHeuristicUV(cfd, data)       # attribute weights (aUV)
            # wAC = aHeuristicAC(cfd, data) # attribute weights (aAC)
            # wCombo = aHeuristicCombo(cfd, data) # attribute weights (aCombo = aUV * aAC)

            # p(h | [heuristic]) = PI_i w(a_i), where a_i is an attribute in the LHS of h
            # phaUniform = np.prod([v for _, v in wUniform.items()])   # p(h | aUniform)
            # phaUV = np.prod([v for _, v in wUV.items()])     # p(h | aUV)
            # phaAC = np.prod([v for _, v in wAC.items()])     # p(h | aAC)
            # phaCombo = np.prod([v for _, v in wCombo.items()])   # p(h | aCombo)
            # phsUniform = sHeuristicUniform(cfd)
            # phsSetRelation = sHeuristicSetRelation(cfd, all_cfds)
            # p_h['aUNI'][cfd] = phaUniform
            # p_h['aUV'][cfd] = phaUV
            # p_h['aAC'][cfd] = phaAC
            # p_h['aCOMBO'][cfd] = phaCombo
            # p_h['sUNI'][cfd] = phsUniform
            # p_h['sSR'][cfd] = phsSetRelation

            # min_modeling_metadata['p_h']['aUNI-sUNI'][cfd] = p_h['aUNI'][cfd] * p_h['sUNI'][cfd]
            # min_modeling_metadata['p_h']['aUNI-sSR'][cfd] = p_h['aUNI'][cfd] * p_h['sSR'][cfd]
            # min_modeling_metadata['p_h']['aUV-sUNI'][cfd] = p_h['aUV'][cfd] * p_h['sUNI'][cfd]
            # min_modeling_metadata['p_h']['aUV-sSR'][cfd] = p_h['aUV'][cfd] * p_h['sSR'][cfd]
            # min_modeling_metadata['p_h']['aAC-sUNI'][cfd] = p_h['aAC'][cfd] * p_h['sUNI'][cfd]
            # min_modeling_metadata['p_h']['aAC-sSR'][cfd] = p_h['aAC'][cfd] * p_h['sSR'][cfd]
            # min_modeling_metadata['p_h']['aCOMBO-sUNI'][cfd] = p_h['aCOMBO'][cfd] * p_h['sUNI'][cfd]
            # min_modeling_metadata['p_h']['aCOMBO-sSR'][cfd] = p_h['aCOMBO'][cfd] * p_h['sSR'][cfd]

        # for heur in min_modeling_metadata['p_h'].keys():
        min_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'] = list()
        # gt_min_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'] = list()

        for it in range(1, iter_count+1):
            elapsed_time = min_modeling_metadata['Y'][it-1].elapsed_time
            curr_X = min_modeling_metadata['X'][it-1].value

            # Get all FDs/CFDs that have were known by the system in this iteration
            discovered_cfds = [cfd for cfd in cfd_metadata.keys()]
            
            if len(discovered_cfds) == 0:   # no FDs discovered yet
                # P(Y in C | X)
                min_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                continue
                
            # find smallest h's
            small_cfds = set()
            # find all h that support X
            x_in_h = dict()
            for h in discovered_cfds:
                x_in_h[h] = list()
                for x in curr_X:
                    x_in_h_val = next(v for v in min_modeling_metadata['y_in_h'][h][x] if v.iter_num == it).value
                    x_in_h[h].append(x_in_h_val)
            # x_in_h = {h:  for h in discovered_cfds}
            supporting_cfds = [h for h in discovered_cfds if 0 not in x_in_h[h]]

            # find smallest h (think subset/superset) of these h's
            for cfd in supporting_cfds:
                lhs = cfd.split(' => ')[0][1:-1].split(', ')
                lhs_set = set(lhs)
                subset_cfds = [c for c in supporting_cfds if lhs_set.issuperset(set(c.split(' => ')[0][1:-1].split(', ')))]
                if len(subset_cfds) > 0:
                    small_h = min(subset_cfds, key=len)
                else:
                    small_h = cfd
                small_cfds.add(small_h)
                
            # find smallest h (think subset/superset) of these h's
            if len(small_cfds) > 1:
                smallest_cfd = max(small_cfds, key=lambda x: min_modeling_metadata['p_h']['aCOMBO-sSR'][x])
            else:
                smallest_cfd = next(iter(small_cfds))

            lhs = smallest_cfd.split(' => ')[0][1:-1].split(', ')
            lhs_set = set(lhs)
            # get all hypotheses that are more complex than the "smallest" FD determined above
            generalized_cfds = [c for c in supporting_cfds if set(c.split(' => ')[0][1:-1].split(', ')).issuperset(lhs_set)]

            p_h_given_X_list = list()
            # p(h | X) for each h
            for h in generalized_cfds:
                elem = next(x for x in min_modeling_metadata['p_X_given_h'][h] if x.iter_num == it)     # p(X | h) for this iteration
                p_X_given_h = elem.value
                p_h = cfd_metadata[h]['weight_history'][it-1].weight    # p(h)
                p_h_given_X = p_X_given_h * p_h     # p(h | X)
                p_h_given_X_list.append(PHGivenX(h=h, value=p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            p_h_given_X_list_sum = sum([x.value for x in p_h_given_X_list])
            p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/p_h_given_X_list_sum) if x.value > 0 else 0)) for x in p_h_given_X_list]

            # p(Y in C | X)
            p_Y_in_C_given_X = 1
            for y in min_modeling_metadata['Y'][it-1].value:
                p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in p_h_given_X_list:
                    h = phgx.h
                    p_h_given_X = phgx.value    # p(h | X)
                    i_y_in_h = next(i for i in min_modeling_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    p_y_in_C_given_X += (i_y_in_h * p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                    
                p_Y_in_C_given_X *= p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
            print('p(Y in C | X) =', p_Y_in_C_given_X)

            # GROUND TRUTH
            # find smallest h's
            '''clean_small_cfds = set()
            # find all h that support X
            clean_x_in_h = dict()
            for h in scenario['clean_hypothesis_space']:
                clean_x_in_h[h['cfd']] = list()
                for x in curr_X:
                    clean_x_in_h_val = next(v for v in gt_min_metadata['y_in_h'][h['cfd']][x] if v.iter_num == it).value
                    clean_x_in_h[h['cfd']].append(clean_x_in_h_val)
            # x_in_h = {h:  for h in discovered_cfds}
            clean_supporting_cfds = [h['cfd'] for h in scenario['clean_hypothesis_space'] if 0 not in clean_x_in_h[h['cfd']]]

            # find smallest h (think subset/superset) of these h's
            for cfd in clean_supporting_cfds:
                clean_lhs = cfd.split(' => ')[0][1:-1].split(', ')
                clean_lhs_set = set(clean_lhs)
                clean_subset_cfds = [c for c in clean_supporting_cfds if clean_lhs_set.issuperset(set(c.split(' => ')[0][1:-1].split(', ')))]
                if len(clean_subset_cfds) > 0:
                    clean_small_h = min(clean_subset_cfds, key=len)
                else:
                    clean_small_h = cfd
                clean_small_cfds.add(clean_small_h)
                
            # find smallest h (think subset/superset) of these h's
            if len(clean_small_cfds) > 1:
                clean_smallest_cfd = max(clean_small_cfds, key=lambda x: gt_min_metadata['p_h']['aCOMBO-sSR'][x])
            else:
                clean_smallest_cfd = next(iter(clean_small_cfds))

            clean_lhs = clean_smallest_cfd.split(' => ')[0][1:-1].split(', ')
            clean_lhs_set = set(clean_lhs)
            # get all hypotheses that are more complex than the "smallest" FD determined above
            clean_generalized_cfds = [c for c in clean_supporting_cfds if set(c.split(' => ')[0][1:-1].split(', ')).issuperset(clean_lhs_set)]

            clean_p_h_given_X_list = list()
            # p(h | X) for each h
            for h in clean_generalized_cfds:
                clean_elem = next(x for x in gt_min_metadata['p_X_given_h'][h] if x.iter_num == it)     # p(X | h) for this iteration
                clean_p_X_given_h = clean_elem.value
                clean_p_h = clean_fd_metadata[h]['weight_history'][it-1].weight     # p(h)
                clean_p_h_given_X = clean_p_X_given_h * clean_p_h     # p(h | X)
                clean_p_h_given_X_list.append(PHGivenX(h=h, value=clean_p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            clean_p_h_given_X_list_sum = sum([x.value for x in clean_p_h_given_X_list])
            clean_p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/clean_p_h_given_X_list_sum) if x.value > 0 else 0)) for x in clean_p_h_given_X_list]

            # p(Y in C | X)
            clean_p_Y_in_C_given_X = 1
            for y in gt_min_metadata['Y'][it-1].value:
                clean_p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in clean_p_h_given_X_list:
                    h = phgx.h
                    clean_p_h_given_X = phgx.value    # p(h | X)
                    clean_i_y_in_h = next(i for i in gt_min_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    clean_p_y_in_C_given_X += (clean_i_y_in_h * clean_p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                    
                clean_p_Y_in_C_given_X *= clean_p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
            print('GROUND TRUTH p(Y in C | X) =', clean_p_Y_in_C_given_X)'''
            
            min_modeling_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=p_Y_in_C_given_X, elapsed_time=elapsed_time))
            # gt_min_metadata['p_Y_in_C_given_X']['aCOMBO-sSR'].append(StudyMetric(iter_num=it, value=clean_p_Y_in_C_given_X, elapsed_time=elapsed_time))

        pickle.dump( min_modeling_metadata, open('./store/' + project_id + '/min_modeling_metadata.p', 'wb') )
        # pickle.dump( gt_min_metadata, open('./store/' + project_id + '/gt_min_metadata.p', 'wb') )

if __name__ == '__main__':
    if len(sys.argv) > 2:
        if sys.argv[2] != 'RANDOM-PURE' and sys.argv[2] != 'DUO':
            print('must specify RANDOM-PURE or DUO sampling method')
        elif sys.argv[1] == 'bayes':
            bayes(sys.argv[2])
        elif sys.argv[1] == 'min':
            max_likelihood(sys.argv[2])
        else:
            print('must specify bayes or min modeling method')
    else:
        print('must specify bayes or min modeling method')
