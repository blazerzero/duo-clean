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

from helpers import StudyMetric

def wHeuristicUniform(cfd):
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    weights = {lh: 1/len(lhs) for lh in lhs}
    return weights

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
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        bayes_modeling_metadata = modeling_metadata
        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        # P(h)        
        for cfd in bayes_modeling_metadata['p_h'].keys():
            # UNIFORM ATTRIBUTE WEIGHTS
            wUniform = wHeuristicUniform(cfd)   # p(h)
            phUniform = np.prod([v for _, v in wUniform])
            bayes_modeling_metadata['p_h']['hUniform'][cfd] = phUniform

        for heur in bayes_modeling_metadata['p_h'].keys():
            for it in range(1, iter_count+1):
                discovered_cfds = [cfd for cfd in bayes_modeling_metadata['p_X_given_h'].keys() if bayes_modeling_metadata['p_X_given_h'][cfd][0].iter_num == it]
                if len(discovered_cfds) == 0:
                    # P(Y in C | X)
                    bayes_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                    
                else:
                    p_h_given_X_list = list()
                    for h in discovered_cfds:
                        # p(h | X)
                        elem = [x.value for x in bayes_modeling_metadata['p_X_given_h'][cfd] if x.iter_num == it].pop()
                        elapsed_time = elem.elapsed_time
                        p_X_given_h = elem.value
                        p_h = bayes_modeling_metadata['p_h'][heur][h]
                        p_h_given_X = p_X_given_h * p_h
                        p_h_given_X_list.append({
                            'h': h,
                            'value': p_h_given_X
                        })
                    
                    # normalized p(h | X) such that sum of all p(h | X) = 1
                    p_h_given_X_list_sum = sum([x.value for x in p_h_given_X_list])
                    p_h_given_X_list = [{'h': x.h, 'value': x.value/p_h_given_X_list_sum} for x in p_h_given_X_list]

                    # p(Y in C | X)
                    p_Y_in_C_given_X = 1
                    for y in bayes_modeling_metadata['y_supp_h'][cfd].keys():
                        p_y_in_C_given_X = 0 # p(y in C | X)
                        for h, p_h_g_X in p_h_given_X_list:
                            i_y_supp_h = [x.value for x in bayes_modeling_metadata['y_supp_h'][cfd][y] if x.iter_num == it].pop()    # I(y in supp(h))
                            p_y_in_C_given_X += (i_y_supp_h * p_h_g_X)
                        p_Y_in_C_given_X *= p_y_in_C_given_X
                    
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
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        min_modeling_metadata = modeling_metadata
        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        
        # p(h)
        for cfd in min_modeling_metadata['p_h'].keys():
            # UNIFORM ATTRIBUTE WEIGHTS
            wUniform = wHeuristicUniform(cfd)
            phUniform = np.prod([v for _, v in wUniform])
            min_modeling_metadata['p_h']['hUniform'][cfd] = phUniform

        for heur in min_modeling_metadata['p_h'].keys():
            min_modeling_metadata['p_Y_in_C_given_X'][heur] = list()
            for it in range(1, iter_count+1):
                max_p_X_given_h = 0
                discovered_cfds = [cfd for cfd in min_modeling_metadata['p_X_given_h'].keys() if min_modeling_metadata['p_X_given_h'][cfd][0].iter_num == it]
                if len(discovered_cfds) == 0:
                    # P(Y in C | X)
                    min_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                    
                else:
                    # h_ML
                    for cfd in discovered_cfds:
                        curr_p_X_given_h = [x.value for x in min_modeling_metadata['p_X_given_h'][cfd] if x.iter_num == it].pop()
                        if max_p_X_given_h < curr_p_X_given_h:
                            max_p_X_given_h = curr_p_X_given_h
                            h_ML = cfd
                
                    # p(h_ML | X)
                    elem = [x.value for x in min_modeling_metadata['p_X_given_h'][cfd] if x.iter_num == it].pop()
                    elapsed_time = elem.elapsed_time
                    p_X_given_h = elem.value
                    p_h = min_modeling_metadata['p_h'][heur][h_ML]
                    p_h_ML_given_X = p_X_given_h * p_h

                    # p(Y in C | X)
                    p_Y_in_C_given_X = 1
                    for y in min_modeling_metadata['y_supp_h'][cfd].keys():
                        i_y_supp_h = [x.value for x in min_modeling_metadata['y_supp_h'][cfd][y] if x.iter_num == it].pop()    # I(y in supp(h))
                        p_y_in_C_given_X = i_y_supp_h * p_h_ML_given_X  # p(y in C | X)
                        p_Y_in_C_given_X *= p_y_in_C_given_X
                    min_modeling_metadata['p_Y_in_C_given_X'][heur].append(StudyMetric(iter_num=it, value=p_Y_in_C_given_X, elapsed_time=elapsed_time))

        pickle.dump( min_modeling_metadata, open('./store/' + project_id + '/min_modeling_metadata.p', 'wb') )