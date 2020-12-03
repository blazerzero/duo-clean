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
        'userrating': 0.1,
        'name': 0.8,
        'areacode': 0.7,
        'phone': 0.5,
        'state': 0.4,
        'zip': 0.3
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

def bayes(scenario_id):

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        if project_info['scenario_id'] != scenario_id:
            continue
        print("project id:", project_id)
        print("scenario id:", project_info['scenario_id'])
        
        data = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
        data = data.replace(r'\\n\\t\\r','', regex=True) 

        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        
        bayes_modeling_metadata = modeling_metadata

        bayes_modeling_metadata['pred_accuracy'] = list()

        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        for it in range(0, iter_count):
            elapsed_time = bayes_modeling_metadata['Y'][it].elapsed_time

            # Get all FDs/CFDs that have were known by the system in this iteration
            discovered_cfds = [cfd for cfd, cfd_m in cfd_metadata.items()]
            
            if len(discovered_cfds) == 0:   # no FDs discovered yet
                bayes_modeling_metadata['pred_accuracy'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                continue
                
            p_h_given_X_list = list()
            print('iter:', it)
            # p(h | X) for each h
            for h in discovered_cfds:
                p_X_given_h = next(x for x in bayes_modeling_metadata['p_X_given_h'][h] if x.iter_num == it).value     # p(X | h) for this iteration
                p_h = cfd_metadata[h]['weight_history'][it].weight    # p(h)
                print('p(h) for ' + h + ': ' + str(p_h))
                p_h_given_X = p_X_given_h * p_h     # p(h | X)
                p_h_given_X_list.append(PHGivenX(h=h, value=p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            p_h_given_X_list_sum = sum([x.value for x in p_h_given_X_list])
            p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/p_h_given_X_list_sum) if p_h_given_X_list_sum > 0 else 0)) for x in p_h_given_X_list]

            # p(Y in C | X)
            p_y_in_C_given_X_list = list()
            for y in bayes_modeling_metadata['Y'][it].value:
                p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in p_h_given_X_list:
                    h = phgx.h
                    p_h_given_X = phgx.value    # p(h | X)
                    i_y_in_h = next(i for i in bayes_modeling_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    p_y_in_C_given_X += (i_y_in_h * p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)
                print('individual p(y in C | X):', p_y_in_C_given_X)
                p_y_in_C_given_X_list.append(p_y_in_C_given_X)
            if len(p_y_in_C_given_X_list) > 0:
                # pred_accuracy = len([y for y in p_y_in_C_given_X_list if y >= 0.5]) / len(p_y_in_C_given_X_list)
                pred_accuracy = hmean(p_y_in_C_given_X_list)
            else:
                pred_accuracy = 0
            print('combined p(y in C | X):', pred_accuracy, '\n')
            
            bayes_modeling_metadata['pred_accuracy'].append(StudyMetric(iter_num=it, value=pred_accuracy, elapsed_time=elapsed_time))
            # print(bayes_modeling_metadata['pred_accuracy'])

        print('--------\n')
        pickle.dump( bayes_modeling_metadata, open('./store/' + project_id + '/bayes_modeling_metadata.p', 'wb') )


def max_likelihood(scenario_id):

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        if project_info['scenario_id'] != scenario_id:
            continue
        print("project id:", project_id)
        print("scenario id:", project_info['scenario_id'])
        
        data = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
        data = data.replace(r'\\n\\t\\r','', regex=True) 
        
        modeling_metadata = pickle.load( open('./store/' + project_id + '/modeling_metadata.p', 'rb') )
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        
        min_modeling_metadata = modeling_metadata

        min_modeling_metadata['pred_accuracy'] = list()

        iter_count = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )

        for it in range(0, iter_count):
            elapsed_time = min_modeling_metadata['Y'][it].elapsed_time
            curr_X = min_modeling_metadata['X'][it].value

            # Get all FDs/CFDs that have were known by the system in this iteration
            discovered_cfds = [cfd for cfd in cfd_metadata.keys()]
            if len(discovered_cfds) == 0:   # no FDs discovered yet
                # P(Y in C | X)
                min_modeling_metadata['pred_accuracy'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                continue
                
            # find smallest h's
            small_cfds = set()
            # find all h that support X
            x_in_h = dict()
            for h in discovered_cfds:
                x_in_h[h] = list()
                for x in curr_X:
                    x_in_h_val = 1 if x in cfd_metadata[h]['vios'] else 0
                    x_in_h[h].append(x_in_h_val)
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
                smallest_cfd = max(small_cfds, key=lambda h: cfd_metadata[h]['weight_history'][it].weight)
            else:
                try:
                    smallest_cfd = next(iter(small_cfds))
                except StopIteration:
                    min_modeling_metadata['pred_accuracy'].append(StudyMetric(iter_num=it, value=0, elapsed_time=elapsed_time))
                    continue

            lhs = smallest_cfd.split(' => ')[0][1:-1].split(', ')
            lhs_set = set(lhs)
            # get all hypotheses that are more complex than the "smallest" FD determined above
            generalized_cfds = [c for c in supporting_cfds if set(c.split(' => ')[0][1:-1].split(', ')).issuperset(lhs_set)]

            p_h_given_X_list = list()
            print('iter:', it)
            # p(h | X) for each h
            for h in generalized_cfds:
                p_X_given_h = next(x for x in min_modeling_metadata['p_X_given_h'][h] if x.iter_num == it).value     # p(X | h) for this iteration
                p_h = cfd_metadata[h]['weight_history'][it].weight    # p(h)
                print('p(h) for ' + h + ': ' + str(p_h))
                p_h_given_X = p_X_given_h * p_h     # p(h | X)
                p_h_given_X_list.append(PHGivenX(h=h, value=p_h_given_X))
            
            # normalized p(h | X) such that sum of all p(h | X) = 1
            p_h_given_X_list_sum = sum([x.value for x in p_h_given_X_list])
            p_h_given_X_list = [PHGivenX(h=x.h, value=((x.value/p_h_given_X_list_sum) if p_h_given_X_list_sum > 0 else 0)) for x in p_h_given_X_list]

            # p(Y in C | X)
            p_y_in_C_given_X_list = list()
            for y in min_modeling_metadata['Y'][it].value:
                p_y_in_C_given_X = 0 # p(y in C | X)
                for phgx in p_h_given_X_list:
                    h = phgx.h
                    p_h_given_X = phgx.value    # p(h | X)
                    i_y_in_h = next(i for i in min_modeling_metadata['y_in_h'][h][y] if i.iter_num == it).value  # I(y in supp(h))
                    p_y_in_C_given_X += (i_y_in_h * p_h_given_X)  # p(y in C | X) = I(y in supp(h)) * p(h | X)   
                print('individual p(y in C | X):', p_y_in_C_given_X)
                p_y_in_C_given_X_list.append(p_y_in_C_given_X)
            if len(p_y_in_C_given_X_list) > 0:
                # pred_accuracy = len([y for y in p_y_in_C_given_X_list if y >= 0.5]) / len(p_y_in_C_given_X_list)
                pred_accuracy = hmean(p_y_in_C_given_X_list)
            else:
                pred_accuracy = 0
            print('combined p(y in C | X):', pred_accuracy, '\n')

            min_modeling_metadata['pred_accuracy'].append(StudyMetric(iter_num=it, value=pred_accuracy, elapsed_time=elapsed_time))

        print('--------\n')
        pickle.dump( min_modeling_metadata, open('./store/' + project_id + '/min_modeling_metadata.p', 'wb') )
        # pickle.dump( gt_min_metadata, open('./store/' + project_id + '/gt_min_metadata.p', 'wb') )

def main(args=sys.argv):
    if len(args) > 2:
        if args[2] == 'bayes':
            bayes(args[1])
        elif args[2] == 'min':
            max_likelihood(args[1])
        else:
            print('must specify bayes or min modeling method')
    else:
        print('must specify bayes or min modeling method')

if __name__ == '__main__':
    main(sys.argv)
