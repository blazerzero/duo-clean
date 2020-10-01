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

class HeuristicClassifier(object):
    def __init__(self, values, color):
        self.values = values
        self.color = color

def plot_bayes(sampling_method):
    with open('scenarios.json') as f:
        all_scenarios = json.load(f)
    scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    bayes_lists_s1 = list()
    bayes_lists_s2 = list()
    bayes_lists_s3 = list()
    bayes_lists_s4 = list()
    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario_id = project_info['scenario_id']
        if scenario_id not in scenario_ids:
            break

        bayes_modeling_metadata = pickle.load( open('./store/' + project_id + '/bayes_modeling_metadata.p', 'rb') )
        for heur, p_Y_in_C_given_X in bayes_modeling_metadata['p_Y_in_C_given_X'].items():
            if heur == 'hUniform':
                color = 'b'
            else:
                color = 'grey'

            if scenario_id == '1':
                bayes_lists_s1.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '2':
                bayes_lists_s2.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '3':
                bayes_lists_s3.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '4':
                bayes_lists_s4.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))

    fig = plt.figure()

    sp = fig.add_subplot(111)
    sp.set_ylabel(r'p(Y $\in C | X)')
    sp1 = fig.add_subplot(241)
    sp2 = fig.add_subplot(242)
    sp3 = fig.add_subplot(243)
    sp4 = fig.add_subplot(244)
    sp1.set_title('Scenario 1')
    sp2.set_xlabel('Iteration #')
    sp2.set_title('Scenario 2')
    sp2.set_xlabel('Iteration #')
    sp3.set_title('Scenario 3')
    sp3.set_xlabel('Iteration #')
    sp4.set_title('Scenario 4')
    sp4.set_xlabel('Iteration #')

    for b in bayes_lists_s1:
        sp1.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in bayes_lists_s2:
        sp2.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in bayes_lists_s3:
        sp3.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in bayes_lists_s4:
        sp4.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)

    fig.savefig('./plots/bayes-' + sampling_method + '.jpg')
    plt.clf()
    print('[SUCCESS]')

def plot_min(sampling_method):
    with open('scenarios.json') as f:
        all_scenarios = json.load(f)
    scenario_ids = [k for k, s in all_scenarios.items() if s['sampling_method'] == sampling_method]

    min_lists_s1 = list()
    min_lists_s2 = list()
    min_lists_s3 = list()
    min_lists_s4 = list()
    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    for project_id in project_ids:
        with open('./store/' + project_id + '/project_info.json') as f:
            project_info = json.load(f)
        scenario_id = project_info['scenario_id']
        if scenario_id not in scenario_ids:
            break

        min_modeling_metadata = pickle.load( open('./store/' + project_id + '/min_modeling_metadata.p', 'rb') )
        for heur, p_Y_in_C_given_X in min_modeling_metadata['p_Y_in_C_given_X'].items():
            if heur == 'hUniform':
                color = 'b'
            else:
                color = 'grey'

            if scenario_id == '1':
                min_lists_s1.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '2':
                min_lists_s2.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '3':
                min_lists_s3.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))
            elif scenario_id == '4':
                min_lists_s4.append(HeuristicClassifier(values=p_Y_in_C_given_X, color=color))

    fig = plt.figure()

    sp = fig.add_subplot(111)
    sp.set_ylabel(r'p(Y $\in C | X)')
    sp1 = fig.add_subplot(241)
    sp2 = fig.add_subplot(242)
    sp3 = fig.add_subplot(243)
    sp4 = fig.add_subplot(244)
    sp1.set_title('Scenario 1')
    sp2.set_xlabel('Iteration #')
    sp2.set_title('Scenario 2')
    sp2.set_xlabel('Iteration #')
    sp3.set_title('Scenario 3')
    sp3.set_xlabel('Iteration #')
    sp4.set_title('Scenario 4')
    sp4.set_xlabel('Iteration #')

    for b in min_lists_s1:
        sp1.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in min_lists_s2:
        sp2.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in min_lists_s3:
        sp3.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)
    for b in min_lists_s4:
        sp4.plot([i for i in range(0, len(b.values) + 1)], b.values, color=b.color)

    fig.savefig('./plots/min-' + sampling_method + '.jpg')
    plt.clf()
    print('[SUCCESS]')

def plot_error_metrics():
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

    return '[SUCCESS]'
