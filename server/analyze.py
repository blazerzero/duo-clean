from pprint import pprint
import os
import json
import numpy as np
import pandas as pd
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

def aHeuristicAC(cfd, data):
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
    weights = dict()
    for lh in lhs:
        if '=' in lh:
            lh_key = lh.split('=')[0]
            lh_val = lh.split('=')[1]
            if lh_val.isnumeric():
                lh_val = int(lh_val)
            num_lh_val = len(data[data[lh_key] == lh_val])
            weights[lh] = wAC[lh_key] / num_lh_val
        else:
            weights[lh] = wAC[lh]
    return weights

def aHeuristicCombo(cfd, data):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    wUV = aHeuristicUV(cfd, data)
    wAC = aHeuristicAC(cfd, data)
    weights = {lh: wUV[lh] * wAC[lh] for lh in lhs}
    return weights

def sHeuristicUniform(cfd):
    return 0.5      # since the user can believe multiple FDs, we give each FD a 50/50 chance of being believed under sUniform

def sHeuristicSetRelation(cfd, all_cfds):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    lhs_set = set(lhs)
    subset_cfds = set([c.split(' => ')[0][1:-1] for c in all_cfds if lhs_set.issuperset(set(c.split(' => ')[0][1:-1].split(', ')))])
    superset_cfds = set([c.split(' => ')[0][1:-1] for c in all_cfds if set(c.split(' => ')[0][1:-1].split(', ')).issuperset(lhs_set)])

    all_related_cfd_set = subset_cfds | superset_cfds
    all_related_cfds = [c.split(', ') for c in all_related_cfd_set]
    all_related_cfds.append(lhs)
    all_related_cfds.sort(key=len)
    lhs_idx = all_related_cfds.index(lhs)
    weight = (len(all_related_cfds) - lhs_idx) / len(all_related_cfds)
    return weight


def bayes(sampling_method):
    with open('scenarios.json') as f:
        all_scenarios = json.load(f)
    scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario_id = project_info['scenario_id']
        if scenario_id not in scenario_ids:
            break
       
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        bayes_modeling_metadata = modeling_metadata
        bayes_modeling_metadata['p_Y_in_C_given_X'] = dict()
        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        p_h = dict()
        p_h['aUNI'] = dict()
        p_h['aUV'] = dict()
        p_h['aAC'] = dict()
        p_h['aCOMBO'] = dict()
        p_h['sUNI'] = dict()
        p_h['sSR'] = dict()
        bayes_modeling_metadata['p_h'] = dict()
        bayes_modeling_metadata['p_h']['aUNI-sUNI'] = dict()
        bayes_modeling_metadata['p_h']['aUNI-sSR'] = dict()
        bayes_modeling_metadata['p_h']['aUV-sUNI'] = dict()
        bayes_modeling_metadata['p_h']['aUV-sSR'] = dict()
        bayes_modeling_metadata['p_h']['aAC-sUNI'] = dict()
        bayes_modeling_metadata['p_h']['aAC-sSR'] = dict()
        bayes_modeling_metadata['p_h']['aCOMBO-sUNI'] = dict()
        bayes_modeling_metadata['p_h']['aCOMBO-sSR'] = dict()

        all_cfds = cfd_metadata.keys()

        # p(h)        
        for cfd in all_cfds:
            # UNIFORM ATTRIBUTE WEIGHTS
            wUniform = aHeuristicUniform(cfd)   # attribute weights (aUniform)
            wUV = aHeuristicUV(cfd, data)       # attribute weights (aUV)
            wAC = aHeuristicAC(cfd, data) # attribute weights (aAC)
            wCombo = aHeuristicCombo(cfd, data) # attribute weights (aCombo = aUV * aAC)

            # p(h | [heuristic]) = PI_i w(a_i), where a_i is an attribute in the LHS of h
            phaUniform = np.prod([v for _, v in wUniform.items()])   # p(h | aUniform)
            phaUV = np.prod([v for _, v in wUV.items()])     # p(h | aUV)
            phaAC = np.prod([v for _, v in wAC.items()])     # p(h | aAC)
            phaCombo = np.prod([v for _, v in wCombo.items()])   # p(h | aCombo)
            phsUniform = sHeuristicUniform(cfd)
            phsSetRelation = sHeuristicSetRelation(cfd, all_cfds)
            p_h['aUNI'][cfd] = phaUniform
            p_h['aUV'][cfd] = phaUV
            p_h['aAC'][cfd] = phaAC
            p_h['aCOMBO'][cfd] = phaCombo
            p_h['sUNI'][cfd] = phsUniform
            p_h['sSR'][cfd] = phsSetRelation

            bayes_modeling_metadata['p_h']['aUNI-sUNI'][cfd] = p_h['aUNI'][cfd] * p_h['sUNI'][cfd]
            bayes_modeling_metadata['p_h']['aUNI-sSR'][cfd] = p_h['aUNI'][cfd] * p_h['sSR'][cfd]
            bayes_modeling_metadata['p_h']['aUV-sUNI'][cfd] = p_h['aUV'][cfd] * p_h['sUNI'][cfd]
            bayes_modeling_metadata['p_h']['aUV-sSR'][cfd] = p_h['aUV'][cfd] * p_h['sSR'][cfd]
            bayes_modeling_metadata['p_h']['aAC-sUNI'][cfd] = p_h['aAC'][cfd] * p_h['sUNI'][cfd]
            bayes_modeling_metadata['p_h']['aAC-sSR'][cfd] = p_h['aAC'][cfd] * p_h['sSR'][cfd]
            bayes_modeling_metadata['p_h']['aCOMBO-sUNI'][cfd] = p_h['aCOMBO'][cfd] * p_h['sUNI'][cfd]
            bayes_modeling_metadata['p_h']['aCOMBO-sSR'][cfd] = p_h['aCOMBO'][cfd] * p_h['sSR'][cfd]

        for heur in bayes_modeling_metadata['p_h'].keys():
            bayes_modeling_metadata['p_Y_in_C_given_X'][heur] = list()
            for it in range(1, iter_count+1):
                elapsed_time = bayes_modeling_metadata['Y'][it].elapsed_time

                # Get all FDs/CFDs that have were known by the system in this iteration
                discovered_cfds = [cfd for cfd in bayes_modeling_metadata['p_X_given_h'].keys() if it in [x.iter_num for x in bayes_modeling_metadata['p_X_given_h'][cfd]]]
                
                if len(discovered_cfds) == 0:   # no FDs discovered yet
                    # P(Y in C | X) = 0
                    bayes_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                    
                else:
                    p_h_given_X_list = list()
                    # p(h | X) for each h
                    for h in discovered_cfds:
                        elem = [x for x in bayes_modeling_metadata['p_X_given_h'][h] if x.iter_num == it].pop()     # p(X | h) for this iteration
                        p_X_given_h = elem.value
                        p_h = bayes_modeling_metadata['p_h'][heur][h]   # p(h)
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
                            i_y_supp_h = bayes_modeling_metadata['y_supp_h'][h][y]  # I(y in supp(h))
                            p_y_in_C_given_X += (i_y_supp_h * p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                            
                        p_Y_in_C_given_X *= p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
                        print('p(Y in C | X) =', p_Y_in_C_given_X)
                    
                    bayes_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=p_Y_in_C_given_X, elapsed_time=elapsed_time))

        pickle.dump( bayes_modeling_metadata, open('./store/' + project_id + '/bayes_modeling_metadata.p', 'wb') )


def max_likelihood(sampling_method):
    with open('scenarios.json') as f:
        all_scenarios = json.load(f)
    scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario_id = project_info['scenario_id']
        if scenario_id not in scenario_ids:
            break
        
        data = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        min_modeling_metadata = modeling_metadata
        min_modeling_metadata['p_Y_in_C_given_X'] = dict()
        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        p_h = dict()
        p_h['aUNI'] = dict()
        p_h['aUV'] = dict()
        p_h['aAC'] = dict()
        p_h['aCOMBO'] = dict()
        p_h['sUNI'] = dict()
        p_h['sSR'] = dict()
        min_modeling_metadata['p_h'] = dict()
        min_modeling_metadata['p_h']['aUNI-sUNI'] = dict()
        min_modeling_metadata['p_h']['aUNI-sSR'] = dict()
        min_modeling_metadata['p_h']['aUV-sUNI'] = dict()
        min_modeling_metadata['p_h']['aUV-sSR'] = dict()
        min_modeling_metadata['p_h']['aAC-sUNI'] = dict()
        min_modeling_metadata['p_h']['aAC-sSR'] = dict()
        min_modeling_metadata['p_h']['aCOMBO-sUNI'] = dict()
        min_modeling_metadata['p_h']['aCOMBO-sSR'] = dict()

        all_cfds = cfd_metadata.keys()

        # p(h)        
        for cfd in all_cfds:
            # UNIFORM ATTRIBUTE WEIGHTS
            wUniform = aHeuristicUniform(cfd)   # attribute weights (aUniform)
            wUV = aHeuristicUV(cfd, data)       # attribute weights (aUV)
            wAC = aHeuristicAC(cfd, data) # attribute weights (aAC)
            wCombo = aHeuristicCombo(cfd, data) # attribute weights (aCombo = aUV * aAC)

            # p(h | [heuristic]) = PI_i w(a_i), where a_i is an attribute in the LHS of h
            phaUniform = np.prod([v for _, v in wUniform.items()])   # p(h | aUniform)
            phaUV = np.prod([v for _, v in wUV.items()])     # p(h | aUV)
            phaAC = np.prod([v for _, v in wAC.items()])     # p(h | aAC)
            phaCombo = np.prod([v for _, v in wCombo.items()])   # p(h | aCombo)
            phsUniform = sHeuristicUniform(cfd)
            phsSetRelation = sHeuristicSetRelation(cfd, all_cfds)
            p_h['aUNI'][cfd] = phaUniform
            p_h['aUV'][cfd] = phaUV
            p_h['aAC'][cfd] = phaAC
            p_h['aCOMBO'][cfd] = phaCombo
            p_h['sUNI'][cfd] = phsUniform
            p_h['sSR'][cfd] = phsSetRelation

            min_modeling_metadata['p_h']['aUNI-sUNI'][cfd] = p_h['aUNI'][cfd] * p_h['sUNI'][cfd]
            min_modeling_metadata['p_h']['aUNI-sSR'][cfd] = p_h['aUNI'][cfd] * p_h['sSR'][cfd]
            min_modeling_metadata['p_h']['aUV-sUNI'][cfd] = p_h['aUV'][cfd] * p_h['sUNI'][cfd]
            min_modeling_metadata['p_h']['aUV-sSR'][cfd] = p_h['aUV'][cfd] * p_h['sSR'][cfd]
            min_modeling_metadata['p_h']['aAC-sUNI'][cfd] = p_h['aAC'][cfd] * p_h['sUNI'][cfd]
            min_modeling_metadata['p_h']['aAC-sSR'][cfd] = p_h['aAC'][cfd] * p_h['sSR'][cfd]
            min_modeling_metadata['p_h']['aCOMBO-sUNI'][cfd] = p_h['aCOMBO'][cfd] * p_h['sUNI'][cfd]
            min_modeling_metadata['p_h']['aCOMBO-sSR'][cfd] = p_h['aCOMBO'][cfd] * p_h['sSR'][cfd]

        for heur in min_modeling_metadata['p_h'].keys():
            min_modeling_metadata['p_Y_in_C_given_X'][heur] = list()
            for it in range(1, iter_count+1):
                elapsed_time = min_modeling_metadata['Y'][it].elapsed_time

                # Get all FDs/CFDs that have were known by the system in this iteration
                discovered_cfds = [cfd for cfd in min_modeling_metadata['p_X_given_h'].keys() if it in [x.iter_num for x in min_modeling_metadata['p_X_given_h'][cfd]]]
                
                if len(discovered_cfds) == 0:   # no FDs discovered yet
                    # P(Y in C | X)
                    min_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                    
                else:
                    # find h_ML and p(X | h_ML)
                    max_p_X_given_h = 0
                    h_ML = None
                    for cfd in discovered_cfds:
                        curr_p_X_given_h = [x.value for x in min_modeling_metadata['p_X_given_h'][cfd] if x.iter_num == it].pop()   # p(X | h) for this cfd in this iteration
                        if max_p_X_given_h <= curr_p_X_given_h:     # if an FD is found with a higher p(X | h)
                            max_p_X_given_h = curr_p_X_given_h      # update p(X | h_ML)
                            h_ML = cfd  # update h_ML
                
                    # p(h_ML | X)
                    p_h_ML = min_modeling_metadata['p_h'][heur][h_ML]   # p(h_ML)
                    p_h_ML_given_X = max_p_X_given_h * p_h_ML   # p(h_ML | X) = p(X | h_ML) * p(h_ML)

                    # p(Y in C | X)
                    p_Y_in_C_given_X = 1
                    for y in min_modeling_metadata['Y'][it-1].value:
                        i_y_supp_h_ML = min_modeling_metadata['y_supp_h'][h_ML][y]  # I(y in supp(h_ML))
                        p_y_in_C_given_X = i_y_supp_h_ML * p_h_ML_given_X   # p(y in C | X) = I(y in supp(h_ML)) * p(h_ML | X)
                        p_Y_in_C_given_X *= p_y_in_C_given_X    # incorporating each y in Y into p(Y in C | X)
                        print('p(Y in C | X) =', p_Y_in_C_given_X)
                    
                    min_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=p_Y_in_C_given_X, elapsed_time=elapsed_time))

        pickle.dump( min_modeling_metadata, open('./store/' + project_id + '/min_modeling_metadata.p', 'wb') )
