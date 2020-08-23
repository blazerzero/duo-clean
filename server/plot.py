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

def plot():
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
    fig.savefig('cfd_confidence_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_cfd_confs_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Confidence of FD/CFD')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('FD/CFD Confidence: RANDOM-UB')
    fig.savefig('cfd_confidence_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_cfd_confs_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Confidence of FD/CFD')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('FD/CFD Confidence: DUO')
    fig.savefig('cfd_confidence_duo.jpg')
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
    fig.savefig('tep_full_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_tep_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Total Errors Identified: RANDOM-UB')
    fig.savefig('tep_full_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_tep_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Total Errors Identified: DUO')
    fig.savefig('tep_full_duo.jpg')
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
    fig.savefig('tep_iter_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_tep_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Errors Identified Per Iteration: RANDOM-UB')
    fig.savefig('tep_iter_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_tep_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('%% of Total Errors Identified')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('%% of Errors Identified Per Iteration: DUO')
    fig.savefig('tep_iter_duo.jpg')
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
    fig.savefig('eacc_full_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_eacc_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Total Error Accuracy: RANDOM-UB')
    fig.savefig('eacc_full_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_eacc_full_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Total Error Accuracy: DUO')
    fig.savefig('eacc_full_duo.jpg')
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
    fig.savefig('eacc_iter_random_pure.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in random_ub_eacc_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'r-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Error Accuracy Per Iteration: RANDOM-UB')
    fig.savefig('eacc_iter_random_ub.jpg')
    plt.clf()

    fig = plt.figure()
    for conf_list in duo_eacc_iter_lists:
        plt.plot([c.iter_num for c in conf_list], [c.value for c in conf_list], 'g-')
    plt.xlabel('Iteration #')
    plt.ylabel('Error Accuracy (%%)')
    plt.xticks(np.arange(0, 30, 6))
    plt.yticks(np.arange(0.0, 1.0, 0.2))
    plt.title('Error Accuracy Per Iteration: DUO')
    fig.savefig('eacc_iter_duo.jpg')
    plt.clf()

    return '[SUCCESS]'
