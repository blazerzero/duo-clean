import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn
import sys
import pickle
import math
import scipy.stats as st
import scipy.special as sc
import copy

import helpers

def deriveStats(interaction_metadata, fd_metadata, h_space, study_metrics, dirty_dataset, clean_dataset, target_fd):
    feedback_history = interaction_metadata['feedback_history']
    study_metrics['st_vio_precision'] = list()
    study_metrics['lt_vio_precision'] = list()
    study_metrics['mt_vio_precision'] = list()
    study_metrics['mt_2_vio_precision'] = list()
    study_metrics['mt_3_vio_precision'] = list()
    study_metrics['st_vio_recall'] = list()
    study_metrics['lt_vio_recall'] = list()
    study_metrics['mt_vio_recall'] = list()
    study_metrics['mt_2_vio_recall'] = list()
    study_metrics['mt_3_vio_recall'] = list()
    study_metrics['st_vio_f1'] = list()
    study_metrics['lt_vio_f1'] = list()
    study_metrics['mt_vio_f1'] = list()
    study_metrics['mt_2_vio_f1'] = list()
    study_metrics['mt_3_vio_f1'] = list()
    study_metrics['iter_err_precision'] = list()
    study_metrics['iter_err_recall'] = list()
    study_metrics['iter_err_f1'] = list()
    study_metrics['all_err_precision'] = list()
    study_metrics['all_err_recall'] = list()
    study_metrics['all_err_f1'] = list()

    for h in h_space:
        if h['cfd'] not in fd_metadata.keys():
            continue

        mu = h['conf']
        variance = 0.0025
        alpha, beta = helpers.initialPrior(mu, variance)
        conf = alpha / (alpha + beta)
        
        fd_metadata[h['cfd']]['alpha'] = alpha
        fd_metadata[h['cfd']]['beta'] = beta
        fd_metadata[h['cfd']]['conf'] = conf

        fd_metadata[h['cfd']]['alpha_history'] = [{ 'iter_num': 0, 'value': alpha, 'elapsed_time': 0 }]
        fd_metadata[h['cfd']]['beta_history'] = [{ 'iter_num': 0, 'value': beta, 'elapsed_time': 0 }]
        fd_metadata[h['cfd']]['conf_history'] = [{ 'iter_num': 0, 'value': conf, 'elapsed_time': 0 }]

    iters = range(1, len(interaction_metadata['sample_history'])+1)
    for i in iters:
        st_vios_found = set()
        st_vios_total = set()
        st_vios_marked = set()
        mt_vios_found = set()
        mt_vios_total = set()
        mt_vios_marked = set()
        mt_2_vios_found = set()
        mt_2_vios_total = set()
        mt_2_vios_marked = set()
        mt_3_vios_found = set()
        mt_3_vios_total = set()
        mt_3_vios_marked = set()
        lt_vios_found = set()
        lt_vios_total = set()
        lt_vios_marked = set()

        iter_errors_found = 0
        iter_errors_total = 0
        iter_errors_marked = 0
        all_errors_found = 0
        all_errors_total = 0
        all_errors_marked = 0

        curr_sample = interaction_metadata['sample_history'][i-1]['value']
        mt_sample = set(curr_sample)
        mt_2_sample = set(curr_sample)
        mt_3_sample = set(curr_sample)
        if i > 1:
            mt_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            mt_2_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            mt_3_sample |= set(interaction_metadata['sample_history'][i-2]['value'])
            if i > 2:
                mt_2_sample |= set(interaction_metadata['sample_history'][i-3]['value'])
                mt_3_sample |= set(interaction_metadata['sample_history'][i-3]['value'])
                if i > 3:
                    mt_3_sample |= set(interaction_metadata['sample_history'][i-4]['value'])
        lt_sample = set(curr_sample)
        for ix in range(2, i+1):
            lt_sample |= set(interaction_metadata['sample_history'][i-ix]['value'])
        elapsed_time = interaction_metadata['sample_history'][i-1]['elapsed_time']

        feedback = dict()
        marked_rows = set()
        for x in feedback_history.keys():
            feedback[x] = dict()
            for y in feedback_history[x].keys():
                feedback[x][y] = feedback_history[x][y][i-1]['marked']
                if feedback[x][y] is True and x not in marked_rows:
                    marked_rows.add(x)

        for idx in dirty_dataset.index:
            for col in dirty_dataset.columns:
                if dirty_dataset.at[idx, col] != clean_dataset.at[idx, col]:
                    if idx in curr_sample:
                        iter_errors_total += 1
                        if feedback[str(idx)][col] is True:
                            iter_errors_found += 1
                    if idx in lt_sample:
                        all_errors_total += 1
                        if feedback[str(idx)][col] is True:
                            all_errors_found += 1
                if feedback[str(idx)][col] is True:
                    if idx in curr_sample:
                        iter_errors_marked += 1
                    if idx in lt_sample:
                        all_errors_marked += 1

        marked_rows = [r for r in marked_rows]
        
        for h in h_space:
            successes = 0
            failures = 0

            fd = h['cfd']
            if fd not in fd_metadata.keys():
                continue
            fd_m = fd_metadata[fd]

            removed_pairs = set()
            sample_X_in_fd = {(x, y) for (x, y) in fd_m['vio_pairs'] if x in curr_sample and y in curr_sample}
            for x, y in sample_X_in_fd:
                if x in marked_rows or y in marked_rows:
                    removed_pairs.add((x, y))
            
            for ix in curr_sample:
                if ix in marked_rows:
                    continue
                if i not in fd_m['vios']:
                    successes += 1
                else:
                    if len([x for x in removed_pairs if ix in x]) > 0:
                        successes += 1
                    else:
                        failures += 1

            fd_m['alpha'] += successes
            fd_m['beta'] += failures
            fd_m['conf'] = fd_m['alpha'] / (fd_m['alpha'] + fd_m['beta'])
            
            fd_m['alpha_history'].append({ 'iter_num': i, 'value': fd_m['alpha'], 'elapsed_time': elapsed_time })
            fd_m['beta_history'].append({ 'iter_num': i, 'value': fd_m['beta'], 'elapsed_time': elapsed_time })
            fd_m['conf_history'].append({ 'iter_num': i, 'value': fd_m['conf'], 'elapsed_time': elapsed_time })

            if fd != target_fd:
                continue
            vio_pairs = h['vio_pairs']
            rhs = fd.split(' => ')[1].split(', ')
            
            # Check if the violation was caught for short-term memory
            fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = helpers.vioStats(curr_sample, curr_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
            st_vios_marked |= fd_st_vios_marked
            st_vios_found |= fd_st_vios_found
            st_vios_total |= fd_st_vios_total
            print('vios found:', st_vios_found)
            print('vios marked:', st_vios_marked)
            print('vios total:', st_vios_total)

        # Medium-term memory violation calculations
        if i > 1:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = helpers.vioStats(curr_sample, mt_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_vios_marked |= fd_st_vios_marked
                mt_vios_found |= fd_st_vios_found
                mt_vios_total |= fd_st_vios_total
        else:
            mt_vios_marked = copy.deepcopy(st_vios_marked)
            mt_vios_found = copy.deepcopy(st_vios_found)
            mt_vios_total = copy.deepcopy(st_vios_total)

        if i > 2:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = helpers.vioStats(curr_sample, mt_2_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_2_vios_marked |= fd_st_vios_marked
                mt_2_vios_found |= fd_st_vios_found
                mt_2_vios_total |= fd_st_vios_total
        else:
            mt_2_vios_marked = copy.deepcopy(mt_vios_marked)
            mt_2_vios_found = copy.deepcopy(mt_vios_found)
            mt_2_vios_total = copy.deepcopy(mt_vios_total)

        if i > 3:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = helpers.vioStats(curr_sample, mt_3_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                mt_3_vios_marked |= fd_st_vios_marked
                mt_3_vios_found |= fd_st_vios_found
                mt_3_vios_total |= fd_st_vios_total
        else:
            mt_3_vios_marked = copy.deepcopy(mt_2_vios_marked)
            mt_3_vios_found = copy.deepcopy(mt_2_vios_found)
            mt_3_vios_total = copy.deepcopy(mt_2_vios_total)
                
        # Long-term memory violation calculations
        if i > 1:
            for h in h_space:
                fd = h['cfd']
                if fd != target_fd:
                    continue
                vio_pairs = h['vio_pairs']
                rhs = fd.split(' => ')[1].split(', ')
                
                fd_st_vios_marked, fd_st_vios_found, fd_st_vios_total = helpers.vioStats(curr_sample, lt_sample, feedback, vio_pairs, rhs, dirty_dataset, clean_dataset)
                lt_vios_marked |= fd_st_vios_marked
                lt_vios_found |= fd_st_vios_found
                lt_vios_total |= fd_st_vios_total
        else:
            lt_vios_marked = copy.deepcopy(st_vios_marked)
            lt_vios_found = copy.deepcopy(st_vios_found)
            lt_vios_total = copy.deepcopy(st_vios_total)

        # Short, mid, and long-term violation precision, recall, and F1
        if len(st_vios_total) > 0:
            st_vio_recall = len(st_vios_found) / len(st_vios_total)
        else:
            st_vio_recall = 1

        if len(lt_vios_total) > 0:
            lt_vio_recall = len(lt_vios_found) / len(lt_vios_total)
        else:
            lt_vio_recall = 1

        if len(mt_vios_total) > 0:
            mt_vio_recall = len(mt_vios_found) / len(mt_vios_total)
        else:
            mt_vio_recall = 1

        if len(mt_2_vios_total) > 0:
            mt_2_vio_recall = len(mt_2_vios_found) / len(mt_2_vios_total)
        else:
            mt_2_vio_recall = 1

        if len(mt_3_vios_total) > 0:
            mt_3_vio_recall = len(mt_3_vios_found) / len(mt_3_vios_total)
        else:
            mt_3_vio_recall = 1

        if len(st_vios_marked) > 0:
            st_vio_precision = len(st_vios_found) / len(st_vios_marked)
        else:
            st_vio_precision = 1

        print('precision:', st_vio_precision, '\n')

        if len(lt_vios_marked) > 0:
            lt_vio_precision = len(lt_vios_found) / len(lt_vios_marked)
        else:
            lt_vio_precision = 1

        if len(mt_vios_marked) > 0:
            mt_vio_precision = len(mt_vios_found) / len(mt_vios_marked)
        else:
            mt_vio_precision = 1

        if len(mt_2_vios_marked) > 0:
            mt_2_vio_precision = len(mt_2_vios_found) / len(mt_2_vios_marked)
        else:
            mt_2_vio_precision = 1

        if len(mt_3_vios_marked) > 0:
            mt_3_vio_precision = len(mt_3_vios_found) / len(mt_3_vios_marked)
        else:
            mt_3_vio_precision = 1

        if st_vio_precision > 0 or st_vio_recall > 0:
            st_vio_f1 = 2 * (st_vio_precision * st_vio_recall) / (st_vio_precision + st_vio_recall)
        else:
            st_vio_f1 = 1

        if lt_vio_precision > 0 or lt_vio_recall > 0:
            lt_vio_f1 = 2 * (lt_vio_precision * lt_vio_recall) / (lt_vio_precision + lt_vio_recall)
        else:
            lt_vio_f1 = 1

        if mt_vio_precision > 0 or mt_vio_recall > 0:
            mt_vio_f1 = 2 * (mt_vio_precision * mt_vio_recall) / (mt_vio_precision + mt_vio_recall)
        else:
            mt_vio_f1 = 1

        if mt_2_vio_precision > 0 or mt_2_vio_recall > 0:
            mt_2_vio_f1 = 2 * (mt_2_vio_precision * mt_2_vio_recall) / (mt_2_vio_precision + mt_2_vio_recall)
        else:
            mt_2_vio_f1 = 1

        if mt_3_vio_precision > 0 or mt_3_vio_recall > 0:
            mt_3_vio_f1 = 2 * (mt_3_vio_precision * mt_3_vio_recall) / (mt_3_vio_precision + mt_3_vio_recall)
        else:
            mt_3_vio_f1 = 1

        # Short and long-term error precision, recall, and F1
        if iter_errors_marked > 0:
            iter_err_precision = iter_errors_found / iter_errors_marked
        else:
            iter_err_precision = 1
        
        if iter_errors_total > 0:
            iter_err_recall = iter_errors_found / iter_errors_total
        else:
            iter_err_recall = 1

        if iter_err_precision > 0 or iter_err_recall > 0:
            iter_err_f1 = 2 * (iter_err_precision * iter_err_recall) / (iter_err_precision + iter_err_recall)
        else:
            iter_err_f1 = 1

        if all_errors_marked > 0:
            all_err_precision = all_errors_found / all_errors_marked
        else:
            all_err_precision = 1
        
        if all_errors_total > 0:
            all_err_recall = all_errors_found / all_errors_total
        else:
            all_err_recall = 1

        if all_err_precision > 0 or all_err_recall > 0:
            all_err_f1 = 2 * (all_err_precision * all_err_recall) / (all_err_precision + all_err_recall)
        else:
            all_err_f1 = 1

        study_metrics['iter_err_precision'].append({ 'iter_num': int(i), 'value': iter_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_recall'].append({ 'iter_num': int(i), 'value': iter_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_f1'].append({ 'iter_num': int(i), 'value': iter_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['all_err_precision'].append({ 'iter_num': int(i), 'value': all_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['all_err_recall'].append({ 'iter_num': int(i), 'value': all_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['all_err_f1'].append({ 'iter_num': int(i), 'value': all_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_recall'].append({ 'iter_num': int(i), 'value': st_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_recall'].append({ 'iter_num': int(i), 'value': mt_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_recall'].append({ 'iter_num': int(i), 'value': mt_2_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_recall'].append({ 'iter_num': int(i), 'value': mt_3_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_recall'].append({ 'iter_num': int(i), 'value': lt_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_precision'].append({ 'iter_num': int(i), 'value': st_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_precision'].append({ 'iter_num': int(i), 'value': mt_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_precision'].append({ 'iter_num': int(i), 'value': mt_2_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_precision'].append({ 'iter_num': int(i), 'value': mt_3_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_precision'].append({ 'iter_num': int(i), 'value': lt_vio_precision, 'elapsed_time': elapsed_time })
        study_metrics['st_vio_f1'].append({ 'iter_num': int(i), 'value': st_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_vio_f1'].append({ 'iter_num': int(i), 'value': mt_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_2_vio_f1'].append({ 'iter_num': int(i), 'value': mt_2_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['mt_3_vio_f1'].append({ 'iter_num': int(i), 'value': mt_3_vio_f1, 'elapsed_time': elapsed_time })
        study_metrics['lt_vio_f1'].append({ 'iter_num': int(i), 'value': lt_vio_f1, 'elapsed_time': elapsed_time })
    return study_metrics, fd_metadata

def calcConfDistance(fd_metadata, h_space, interaction_metadata):
    conf_distance = dict()
    for fd, fd_m in fd_metadata.items():
        conf_distance[fd] = list()
        true_conf = next(f for f in h_space if f['cfd'] == fd)['conf']
        times = list()
        for conf_d in fd_m['conf_history']:
            # print(conf_d)
            iter_num = conf_d['iter_num']
            elapsed_time = conf_d['elapsed_time']
            times.append(elapsed_time)
            dist = abs(true_conf - conf_d['value'])
            conf_distance[fd].append({ 'iter_num': iter_num, 'value': dist, 'elapsed_time': elapsed_time })

    avg_conf_distance = list()
    times = [i['elapsed_time'] for i in interaction_metadata['sample_history']]
    for i in range(0, len(times)):
        avg_conf_d = np.prod([cd[i]['value'] for cd in conf_distance.values()]) / len(conf_distance.keys())
        avg_conf_distance.append({ 'iter_num': i+1, 'value': avg_conf_d, 'elapsed_time': times[i] })      
    return conf_distance, avg_conf_distance

def plotResults(run_type, project_ids, x_axis):
    fig1, ax1 = plt.subplots()  # Error precision (iterative)
    fig2, ax2 = plt.subplots()  # Error recall (iterative)
    fig3, ax3 = plt.subplots()  # Error F1-score (iterative)
    fig4, ax4 = plt.subplots()  # Violation recall per iteration
    fig5, ax5 = plt.subplots()  # Violation recall (cumulative)
    fig6, ax6 = plt.subplots()  # Confidence distance per FD
    fig7, ax7 = plt.subplots()  # Average confidence distance
    fig8, ax8 = plt.subplots()  # Error precision (cumulative)
    fig9, ax9 = plt.subplots()  # Error recall (cumulative)
    fig10, ax10 = plt.subplots()  # Error F1-score (cumulative)
    if x_axis == 'iter':
        ax1.set_xticks(np.arange(0, 30, 5))
        ax2.set_xticks(np.arange(0, 30, 5))
        ax3.set_xticks(np.arange(0, 30, 5))
        ax4.set_xticks(np.arange(0, 30, 5))
        ax5.set_xticks(np.arange(0, 30, 5))
        ax6.set_xticks(np.arange(0, 30, 5))
        ax7.set_xticks(np.arange(0, 30, 5))
        ax8.set_xticks(np.arange(0, 30, 5))
        ax9.set_xticks(np.arange(0, 30, 5))
        ax10.set_xticks(np.arange(0, 30, 5))
    ax1.set_ylim([0, 1])
    ax2.set_ylim([0, 1])
    ax3.set_ylim([0, 1])
    ax4.set_ylim([0, 1])
    ax5.set_ylim([0, 1])
    ax8.set_ylim([0, 1])
    ax9.set_ylim([0, 1])
    ax10.set_ylim([0, 1])

    for project_id in project_ids:
        pathstart = './docker-out/' if run_type == 'real' else './store/'

        with open(pathstart + project_id + '/study_metrics.json', 'r') as f:
            study_metrics = json.load(f)
        with open(pathstart + project_id + '/fd_metadata.json', 'r') as f:
            fd_metadata = json.load(f)
        with open(pathstart + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        with open(pathstart + project_id + '/interaction_metadata.json', 'r') as f:
            interaction_metadata = json.load(f)
        dirty_dataset = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
        clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
        target_fd = project_info['scenario']['target_fd']

        h_space = project_info['scenario']['hypothesis_space']
        clean_h_space = project_info['scenario']['clean_hypothesis_space']
        # if len([k for k in study_metrics.keys() if 'lt_vio' in k]) == 0:
        study_metrics, fd_metadata = deriveStats(
            interaction_metadata,
            fd_metadata,
            h_space,
            study_metrics,
            dirty_dataset,
            clean_dataset,
            target_fd
        )

        with open(pathstart + project_id + '/study_metrics.json', 'w') as f:
            json.dump(study_metrics, f)
        with open(pathstart + project_id + '/fd_metadata.json', 'w') as f:
            json.load(fd_metadata, f)

        conf_distance, avg_conf_distance = calcConfDistance(fd_metadata, clean_h_space, interaction_metadata)

        if x_axis == 'iter':
            ax1.plot([i['iter_num'] for i in study_metrics['iter_err_precision']], [i['value'] for i in study_metrics['iter_err_precision']])
            ax2.plot([i['iter_num'] for i in study_metrics['iter_err_recall']], [i['value'] for i in study_metrics['iter_err_recall']])
            ax3.plot([i['iter_num'] for i in study_metrics['iter_err_f1']], [i['value'] for i in study_metrics['iter_err_f1']])
            ax4.plot([i['iter_num'] for i in study_metrics['st_vio_recall']], [i['value'] for i in study_metrics['st_vio_recall']])
            ax5.plot([i['iter_num'] for i in study_metrics['lt_vio_recall']], [i['value'] for i in study_metrics['lt_vio_recall']])
            for fd, conf_d in conf_distance.items():
                if fd != project_info['scenario']['target_fd']:
                    continue
                ax6.plot([i['iter_num'] for i in conf_d], [i['value'] for i in conf_d])
            ax7.plot([i['iter_num'] for i in avg_conf_distance], [i['value'] for i in avg_conf_distance])
            ax8.plot([i['iter_num'] for i in study_metrics['all_err_precision']], [i['value'] for i in study_metrics['all_err_precision']])
            ax9.plot([i['iter_num'] for i in study_metrics['all_err_recall']], [i['value'] for i in study_metrics['all_err_recall']])
            ax10.plot([i['iter_num'] for i in study_metrics['all_err_f1']], [i['value'] for i in study_metrics['all_err_f1']])
        else:
            ax1.plot([i['elapsed_time'] for i in study_metrics['iter_err_precision']], [i['value'] for i in study_metrics['iter_err_precision']])
            ax2.plot([i['elapsed_time'] for i in study_metrics['iter_err_recall']], [i['value'] for i in study_metrics['iter_err_recall']])
            ax3.plot([i['elapsed_time'] for i in study_metrics['iter_err_f1']], [i['value'] for i in study_metrics['iter_err_f1']])
            ax4.plot([i['elapsed_time'] for i in study_metrics['st_vio_recall']], [i['value'] for i in study_metrics['st_vio_recall']])
            ax5.plot([i['elapsed_time'] for i in study_metrics['lt_vio_recall']], [i['value'] for i in study_metrics['lt_vio_recall']])
            for fd, conf_d in conf_distance.items():
                if fd != project_info['scenario']['target_fd']:
                    continue
                ax6.plot([i['elapsed_time'] for i in conf_d], [i['value'] for i in conf_d])
            ax7.plot([i['elapsed_time'] for i in avg_conf_distance], [i['value'] for i in avg_conf_distance])
            ax8.plot([i['elapsed_time'] for i in study_metrics['all_err_precision']], [i['value'] for i in study_metrics['all_err_precision']])
            ax9.plot([i['elapsed_time'] for i in study_metrics['all_err_recall']], [i['value'] for i in study_metrics['all_err_recall']])
            ax10.plot([i['elapsed_time'] for i in study_metrics['all_err_f1']], [i['value'] for i in study_metrics['all_err_f1']])
    
    ax1.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1.set_ylabel('Precision')
    ax1.set_title('Error-Marking Precision per Iteration')
    ax2.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax2.set_ylabel('Recall')
    ax2.set_title('Error-Marking Recall per Iteration')
    ax3.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax3.set_ylabel('F1-Score')
    ax3.set_title('Error-Marking F1-Score per Iteration')
    ax4.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax4.set_ylabel('Recall')
    ax4.set_title('Short-Term Vio-Catching Recall')
    ax5.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax5.set_ylabel('Recall')
    ax5.set_title('Long-Term Violation-Catching Recall')
    ax6.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax6.set_ylabel('Confidence Distance')
    ax6.set_title('Distance Btwn System FD Conf and Ground Truth - Target FD')
    ax7.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax7.set_ylabel('Confidence Distance')
    ax7.set_title('Average Distance Btwn System FD Conf and Ground Truth')
    ax8.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax8.set_ylabel('Precision')
    ax8.set_title('Cumulative Error-Marking Precision')
    ax9.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax9.set_ylabel('Recall')
    ax9.set_title('Cumulative Error-Marking Recall')
    ax10.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax10.set_ylabel('F1-Score')
    ax10.set_title('Cumulative Error-Marking F1-Score')
    fig1.tight_layout()
    fig2.tight_layout()
    fig3.tight_layout()
    fig4.tight_layout()
    fig5.tight_layout()
    fig6.tight_layout()
    fig7.tight_layout()
    fig8.tight_layout()
    fig9.tight_layout()
    fig10.tight_layout()
    if len(project_ids) > 1:
        path = './plots/cumulative'
    else:
        project_id = project_ids[0]
        path = './plots/' + project_id
    if not os.path.exists(path):
        os.mkdir(path)
    fig1.savefig(path + '/st-err-precision.jpg')
    fig2.savefig(path + '/st-err-recall.jpg')
    fig3.savefig(path + '/st-err-f1.jpg')
    fig4.savefig(path + '/st-vio-recall.jpg')
    fig5.savefig(path + '/lt-vio-recall.jpg')
    fig6.savefig(path + '/target-fd-system-conf-gtruth-distance.jpg')
    fig7.savefig(path + '/avg-system-conf-gtruthdistance.jpg')
    fig8.savefig(path + '/lt-err-precision.jpg')
    fig9.savefig(path + '/lt-err-recall.jpg')
    fig10.savefig(path + '/lt-err-f1.jpg')
    plt.clf()

if __name__ == '__main__':
    plotResults(sys.argv[1], sys.argv[2:-1], sys.argv[-1])