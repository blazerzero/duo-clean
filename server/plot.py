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
from collections import Counter

class PlotData(object):
    def __init__(self, values, color):
        self.values = values
        self.color = color

class StudyMetric(object):
    def __init__(self, iter_num, value, elapsed_time):
        self.iter_num = iter_num
        self.value = value
        self.elapsed_time = elapsed_time

def plot_modeling(scenario_id, modeling_method, sampling_method, x_axis):
    # with open('scenarios.json') as f:
    #     all_scenarios = json.load(f)
    # scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]
    scenario_ids = ["1", "2", "3", "4"]

    # lists_s1 = list()
    # lists_s2 = list()
    # lists_s3 = list()
    # lists_s4 = list()
    preds = list()
    f1s = list()
    # f1_s2 = list()
    # f1_s3 = list()
    # f1_s4 = list()
    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        # scenario_id = project_info['scenario_id']
        if project_info['scenario_id'] != scenario_id or scenario['sampling_method'] != sampling_method:
            continue
        print("project id:", project_id)

        modeling_metadata = pickle.load( open('./store/' + project_id + '/' + modeling_method + '_modeling_metadata.p', 'rb') )
        #gt_metadata = pickle.load( open('./store/' + project_id + '/gt_' + modeling_method + '_metadata.p', 'rb') )
        study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
        
        # for heur, p_Y_in_C_given_X in modeling_metadata['p_Y_in_C_given_X'].items():
        for p_Y_in_C_given_X in modeling_metadata['p_Y_in_C_given_X']:
            # print(heur)
            # if heur != 'aCOMBO-sSR':
            #     continue
            print([x.value for x in p_Y_in_C_given_X])
            '''if heur == 'aUNI-sUNI':
                color = 'royalblue'
            elif heur == 'aUNI-sSR':
                color = 'green'
            elif heur == 'aUV-sUNI':
                color = 'red'
            elif heur == 'aUV-sSR':
                color = 'cyan'
            elif heur == 'aAC-sUNI':
                color = 'magenta'
            elif heur == 'aAC-sSR':
                color = 'darkorange'
            elif heur == 'aCOMBO-sUNI':
                color = 'navy'
            elif heur == 'aCOMBO-sSR':'''
            # color = 'green'

            preds.append(PlotData(values=p_Y_in_C_given_X, color='green'))
            f1s.append(PlotData(values=study_metrics['f1'], color='blue'))
            '''if scenario_id == scenario_ids[0]:
                lists_s1.append(PlotData(values=p_Y_in_C_given_X, color='green'))
                f1_s1.append(PlotData(values=study_metrics['f1'], color='blue'))
            elif scenario_id == scenario_ids[1]:
                lists_s2.append(PlotData(values=p_Y_in_C_given_X, color='green'))
                f1_s2.append(PlotData(values=study_metrics['f1'], color='blue'))
            elif scenario_id == scenario_ids[2]:
                lists_s3.append(PlotData(values=p_Y_in_C_given_X, color='green'))
                f1_s3.append(PlotData(values=study_metrics['f1'], color='blue'))
            elif scenario_id == scenario_ids[3]:
                lists_s4.append(PlotData(values=p_Y_in_C_given_X, color='green'))
                f1_s4.append(PlotData(values=study_metrics['f1'], color='blue'))'''

        '''for heur, p_Y_in_C_given_X in gt_metadata['p_Y_in_C_given_X'].items():
            # print(heur)
            if heur != 'aCOMBO-sSR':
                continue

            if scenario_id == scenario_ids[0]:
                lists_s1.append(PlotData(values=p_Y_in_C_given_X, color='blue'))
            elif scenario_id == scenario_ids[1]:
                lists_s2.append(PlotData(values=p_Y_in_C_given_X, color='blue'))
            elif scenario_id == scenario_ids[2]:
                lists_s3.append(PlotData(values=p_Y_in_C_given_X, color='blue'))
            elif scenario_id == scenario_ids[3]:
                lists_s4.append(PlotData(values=p_Y_in_C_given_X, color='blue'))'''

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    ax1.set_ylabel('p(Y in C | X)')
    ax2.set_ylabel('F1 score')
    '''ax1[0,1].set_ylabel('p(Y in C | X)')
    ax2[0,1].set_ylabel('F1 score')
    ax1[1,0].set_ylabel('p(Y in C | X)')
    ax2[1,0].set_ylabel('F1 score')
    ax1[1,1].set_ylabel('p(Y in C | X)')
    ax2[1,1].set_ylabel('F1 score')'''
    ax1.set_title('Scenario ' + scenario_id)
    ax1.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1.set_yticks(np.arange(0.0, 1.25, 0.25))
    ax2.set_yticks(np.arange(0.0, 1.25, 0.25))
    ax1.set_ylim([0, None])
    ax2.set_ylim([0, None])
    '''ax1[0,1].set_title('Scenario ' + scenario_ids[1])
    ax1[0,1].set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1[0,1].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax2[0,1].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax1[0,1].set_ylim([0, None])
    ax2[0,1].set_ylim([0, None])
    ax1[1,0].set_title('Scenario ' + scenario_ids[2])
    ax1[1,0].set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1[1,0].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax2[1,0].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax1[1,0].set_ylim([0, None])
    ax2[1,0].set_ylim([0, None])
    ax1[1,1].set_title('Scenario ' + scenario_ids[3])
    ax1[1,1].set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1[1,1].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax2[1,1].set_yticks(np.arange(0.0, 1.25, 0.25))
    ax1[1,1].set_ylim([0, None])
    ax2[1,1].set_ylim([0, None])'''

    if x_axis == 'iter':
        for b in preds:
            ax1.set_xticks(np.arange(0, 36, 6.0))
            ax1.plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        '''for b in lists_s2:
            ax1[0,1].set_xticks(np.arange(0, 36, 6.0))
            ax1[0,1].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        for b in lists_s3:
            ax1[1,0].set_xticks(np.arange(0, 36, 6.0))
            ax1[1,0].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        for b in lists_s4:
            ax1[1,1].set_xticks(np.arange(0, 36, 6.0))
            ax1[1,1].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)'''

        for b in f1s:
            # ax2[0,0].set_xticks(np.arange(0, 36, 6.0))
            ax2.plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        '''for b in f1_s2:
            # ax2[0,1].set_xticks(np.arange(0, 36, 6.0))
            ax2[0,1].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        for b in f1_s3:
            # ax2[1,0].set_xticks(np.arange(0, 36, 6.0))
            ax2[1,0].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)
        for b in f1_s4:
            # ax2[1,1].set_xticks(np.arange(0, 36, 6.0))
            ax2[1,1].plot([i for i in range(1, len(b.values) + 1)], [x.value for x in b.values], color=b.color)'''
            
    elif x_axis == 'time':
        for b in preds:
            ax1.plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        '''for b in lists_s2:
            ax1[0,1].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        for b in lists_s3:
            ax1[1,0].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        for b in lists_s4:
            ax1[1,1].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)'''

        for b in f1s:
            # ax2[0,0].set_xticks(np.arange(0, 36, 6.0))
            ax2.plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        '''for b in f1_s2:
            # ax2[0,1].set_xticks(np.arange(0, 36, 6.0))
            ax2[0,1].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        for b in f1_s3:
            # ax2[1,0].set_xticks(np.arange(0, 36, 6.0))
            ax2[1,0].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)
        for b in f1_s4:
            # ax2[1,1].set_xticks(np.arange(0, 36, 6.0))
            ax2[1,1].plot([x.elapsed_time for x in b.values], [x.value for x in b.values], color=b.color)'''

    fig.tight_layout()
    fig.savefig('./plots/scenario-' + scenario_id + '-' + modeling_method + '-' + sampling_method + '-' + x_axis + '.jpg')
    plt.clf()
    print('[SUCCESS]')

if __name__ == '__main__':
    if len(sys.argv) == 5:
        plot_modeling(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print('must specify scenario id, modeling method, sampling method, and x axis')




################
# IGNORE BELOW #
#       |      #
#       |      #
#       V      #
################





'''def plot_error_metrics():
    with open('scenarios.json') as f:
        scenarios = json.load(f)
    random_pure_scenarios = [k for k, s in scenarios.items() if s['sampling_method'] == 'RANDOM-PURE']
    random_ub_scenarios = [k for k, s in scenarios.items() if s['sampling_method'] == 'RANDOM-UB']
    duo_scenarios = [k for k, s in scenarios.items() if s['sampling_method'] == 'DUO']

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    random_pure_cfd_confs_lists = list()
    random_ub_cfd_confs_lists = list()
    duo_cfd_confs_lists = list()

    random_pure_tep_full_lists = list()
    random_ub_tep_full_lists = list()
    duo_tep_full_lists = list()

    random_pure_tep_iter_lists = list()
    random_ub_tep_iter_lists = list()
    duo_tep_iter_lists = list()

    random_pure_eacc_full_lists = list()
    random_ub_eacc_full_lists = list()
    duo_eacc_full_lists = list()

    random_pure_eacc_iter_lists = list()
    random_ub_eacc_iter_lists = list()
    duo_eacc_iter_lists = list()
    
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        study_metrics = pickle.load( open('./store/' + project_id + '/study_metrics.p', 'rb') )
        tep_full = study_metrics['true_error_pct_full']
        tep_iter = study_metrics['true_error_pct_iter']
        eacc_full = study_metrics['error_accuracy_full']
        eacc_iter = study_metrics['error_accuracy_iter']
        if project_info['scenario_id'] in random_pure_scenarios:
            random_pure_tep_full_lists.append(tep_full)
            random_pure_tep_iter_lists.append(tep_iter)
            random_pure_eacc_full_lists.append(eacc_full)
            random_pure_eacc_iter_lists.append(eacc_iter)
        elif project_info['scenario_id'] in random_ub_scenarios:
            random_ub_tep_full_lists.append(tep_full)
            random_ub_tep_iter_lists.append(tep_iter)
            random_ub_eacc_full_lists.append(eacc_full)
            random_ub_eacc_iter_lists.append(eacc_iter)
        elif project_info['scenario_id'] in duo_scenarios:
            duo_tep_full_lists.append(tep_full)
            duo_tep_iter_lists.append(tep_iter)
            duo_eacc_full_lists.append(eacc_full)
            duo_eacc_iter_lists.append(eacc_iter)
        else:
            return None

        for cfd in project_info['scenario']['cfds']:
            cfd_weights = study_metrics['cfd_confidence'][cfd]
            if project_info['scenario_id'] in random_pure_scenarios:
                random_pure_cfd_confs_lists.append(cfd_weights)
            elif project_info['scenario_id'] in random_ub_scenarios:
                random_ub_cfd_confs_lists.append(cfd_weights)
            elif project_info['scenario_id'] in duo_scenarios:
                duo_cfd_confs_lists.append(cfd_weights)
            else:
                return None

    # FD/CFD confidence
    fig = plt.figure()
    for conf_list in random_pure_cfd_confs_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'b-')
    plt.xlabel('Iteration #')
    plt.ylabel('Confidence of FD/CFD')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('FD/CFD Confidence: RANDOM-PURE')
    fig.savefig('./plots/cfd_confidence_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_cfd_confs_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Confidence of FD/CFD')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('FD/CFD Confidence: RANDOM-UB')
    fig.savefig('./plots/cfd_confidence_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_cfd_confs_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Confidence of FD/CFD')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('FD/CFD Confidence: DUO')
    fig.savefig('./plots/cfd_confidence_duo.jpg')
    plt.clf()

    # True error percentage (total)
    fig = plt.figure()
    for conf_list in random_pure_tep_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'b-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Total Errors Identified: RANDOM-PURE')
    fig.savefig('./plots/tep_full_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_tep_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Total Errors Identified: RANDOM-UB')
    fig.savefig('./plots/tep_full_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_tep_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Total Errors Identified: DUO')
    fig.savefig('./plots/tep_full_duo.jpg')
    plt.clf()

    # True error percentage (per iteration)
    fig = plt.figure()
    for conf_list in random_pure_tep_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'b-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Errors in Sample Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Errors Identified Per Iteration: RANDOM-PURE')
    fig.savefig('./plots/tep_iter_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_tep_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Errors Identified Per Iteration: RANDOM-UB')
    fig.savefig('./plots/tep_iter_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_tep_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Errors Identified Per Iteration: DUO')
    fig.savefig('./plots/tep_iter_duo.jpg')
    plt.clf()

    # Error accuracy (total)
    fig = plt.figure()
    for conf_list in random_pure_eacc_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'b-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Total Error Accuracy: RANDOM-PURE')
    fig.savefig('./plots/eacc_full_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_eacc_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Total Error Accuracy: RANDOM-UB')
    fig.savefig('./plots/eacc_full_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_eacc_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Total Error Accuracy: DUO')
    fig.savefig('./plots/eacc_full_duo.jpg')
    plt.clf()

    # Error accuracy (per iteration)
    fig = plt.figure()
    for conf_list in random_pure_eacc_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'b-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Error Accuracy Per Iteration: RANDOM-PURE')
    fig.savefig('./plots/eacc_iter_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_eacc_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Error Accuracy Per Iteration: RANDOM-UB')
    fig.savefig('./plots/eacc_iter_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_eacc_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Error Accuracy Per Iteration: DUO')
    fig.savefig('./plots/eacc_iter_duo.jpg')
    plt.clf()

    '''