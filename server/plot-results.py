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

import helpers

def derive_stats(interaction_metadata, fd_metadata, h_space, study_metrics, dirty_dataset, clean_dataset):
    feedback_history = interaction_metadata['feedback_history']
    study_metrics['iter_vio_recall'] = list()
    study_metrics['all_vio_recall'] = list()
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
            # fd_metadata[h['cfd']] = dict()
            # fd_metadata[h['cfd']]['lhs'] = h['cfd'].split(' => ')[0][1:-1].split(', ')
            # fd_metadata[h['cfd']]['rhs'] = h['cfd'].split(' => ')[1].split(', ')
            # print(h)
            # fd_metadata[h['cfd']]['support'] = h['support']
            # fd_metadata[h['cfd']]['vios'] = h['vios']
            # fd_metadata[h['cfd']]['vio_pairs'] = h['vio_pairs']
        fd_metadata[h['cfd']]['alpha'] = alpha
        fd_metadata[h['cfd']]['beta'] = beta
        fd_metadata[h['cfd']]['alpha_history'] = [{ 'iter_num': 0, 'value': alpha, 'elapsed_time': 0 }]
        fd_metadata[h['cfd']]['beta_history'] = [{ 'iter_num': 0, 'value': beta, 'elapsed_time': 0 }]
        conf = alpha / (alpha + beta)
        fd_metadata[h['cfd']]['conf'] = conf
        fd_metadata[h['cfd']]['conf_history'] = [{ 'iter_num': 0, 'value': conf, 'elapsed_time': 0 }]

    iters = range(1, len(interaction_metadata['sample_history'])+1)
    for i in iters:
        all_vios_found = set()
        all_vios_total = set()
        all_vios_marked = set()
        iter_vios_found = set()
        iter_vios_total = set()
        iter_vios_marked = set()

        all_errors_found = 0
        all_errors_total = 0
        all_errors_marked = 0
        iter_errors_found = 0
        iter_errors_total = 0
        iter_errors_marked = 0

        sample = interaction_metadata['sample_history'][i-1]['value']
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
                    all_errors_total += 1
                    if idx in sample:
                        iter_errors_total += 1
                        if feedback[str(idx)][col] is True:
                            iter_errors_found += 1
                    if feedback[str(idx)][col] is True:
                        all_errors_found += 1
                if feedback[str(idx)][col] is True:
                    all_errors_marked += 1
                    if idx in sample:
                        iter_errors_marked += 1

        marked_rows = [r for r in marked_rows]
        
        for h in h_space:
            successes = 0
            failures = 0

            fd = h['cfd']
            if fd not in fd_metadata.keys():
                continue
            fd_m = fd_metadata[fd]

            removed_pairs = set()
            sample_X_in_fd = {(x, y) for (x, y) in fd_m['vio_pairs'] if x in sample and y in sample}
            for x, y in sample_X_in_fd:
                if x in marked_rows or y in marked_rows:
                    removed_pairs.add((x, y))
            
            for ix in sample:
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

            # print(fd_m['alpha'])
            # print(fd_m['beta'])
            
            fd_m['alpha_history'].append({ 'iter_num': i, 'value': fd_m['alpha'], 'elapsed_time': elapsed_time })
            fd_m['beta_history'].append({ 'iter_num': i, 'value': fd_m['beta'], 'elapsed_time': elapsed_time })

            fd_m['conf'] = fd_m['alpha'] / (fd_m['alpha'] + fd_m['beta'])
            # print(fd_m['conf'])
            fd_m['conf_history'].append({ 'iter_num': i, 'value': fd_m['conf'], 'elapsed_time': elapsed_time })

            # print(h)
            if 'vio_pairs' not in h.keys():
                continue
            vio_pairs = h['vio_pairs']
            rhs = fd.split(' => ')[1].split(', ')
            # study_metrics['iter_vio_recall'][fd] = list()
            
            all_vios_total |= set([tuple(vp) for vp in vio_pairs])
            for x, y in vio_pairs:
                if x not in sample or y not in sample:
                    continue
                iter_vios_total.add((x, y))
                caught = True
                for rh in rhs:
                    if feedback[str(x)][rh] is False and feedback[str(y)][rh] is False:
                        caught = False
                        break
                if caught is True:
                    all_vios_found.add((x, y))
                    iter_vios_found.add((x, y))

        print(iter_vios_total)
        print(iter_vios_found)
        print(all_vios_total)
        print(all_vios_found, '\n')
        
        if len(iter_vios_total) > 0:
            iter_vio_recall = len(iter_vios_found) / len(iter_vios_total)
        else:
            iter_vio_recall = 0

        if len(all_vios_total) > 0:
            all_vio_recall = len(all_vios_found) / len(all_vios_total)
        else:
            all_vio_recall = 0

        if iter_errors_marked > 0:
            iter_err_precision = iter_errors_found / iter_errors_marked
        else:
            iter_err_precision = 0
        
        if iter_errors_total > 0:
            iter_err_recall = iter_errors_found / iter_errors_total
        else:
            iter_err_recall = 0

        if iter_err_precision > 0 and iter_err_recall > 0:
            iter_err_f1 = 2 * (iter_err_precision * iter_err_recall) / (iter_err_precision + iter_err_recall)
        else:
            iter_err_f1 = 0

        if all_errors_marked > 0:
            all_err_precision = all_errors_found / all_errors_marked
        else:
            all_err_precision = 0
        
        if all_errors_total > 0:
            all_err_recall = all_errors_found / all_errors_total
        else:
            all_err_recall = 0

        if all_err_precision > 0 and all_err_recall > 0:
            all_err_f1 = 2 * (all_err_precision * all_err_recall) / (all_err_precision + all_err_recall)
        else:
            all_err_f1 = 0

        print(iter_err_precision)
        print(iter_err_recall)
        print(iter_err_f1)
        print(all_err_precision)
        print(all_err_recall)
        print(all_err_f1)
        print(iter_vio_recall)
        print(all_vio_recall, '\n')

        study_metrics['iter_err_precision'].append({ 'iter_num': int(i), 'value': iter_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_recall'].append({ 'iter_num': int(i), 'value': iter_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['iter_err_f1'].append({ 'iter_num': int(i), 'value': iter_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['all_err_precision'].append({ 'iter_num': int(i), 'value': all_err_precision, 'elapsed_time': elapsed_time })
        study_metrics['all_err_recall'].append({ 'iter_num': int(i), 'value': all_err_recall, 'elapsed_time': elapsed_time })
        study_metrics['all_err_f1'].append({ 'iter_num': int(i), 'value': all_err_f1, 'elapsed_time': elapsed_time })
        study_metrics['iter_vio_recall'].append({ 'iter_num': int(i), 'value': iter_vio_recall, 'elapsed_time': elapsed_time })
        study_metrics['all_vio_recall'].append({ 'iter_num': int(i), 'value': all_vio_recall, 'elapsed_time': elapsed_time})
    return study_metrics, fd_metadata

# def derive_conf(fd_metadata, study_metrics):
#     for fd_m in fd_metadata.values():
#         fd_m['conf'] = fd_m['alpha'] / (fd_m['alpha'] + fd_m['beta'])
#         fd_m['conf_history'] = list()
#         for i in range(0, len(fd_m['alpha_history'])):
#             alpha = fd_m['alpha_history'][i]
#             beta = fd_m['beta_history'][i]
#             if i == 0:
#                 iter_num = 0
#                 elapsed_time = 0.0
#             else:
#                 iter_num = study_metrics['iter_err_precision'][i-1]['iter_num']
#                 elapsed_time = study_metrics['iter_err_precision'][i-1]['elapsed_time']
#             conf = alpha / (alpha + beta)
#             fd_m['conf_history'].append({ 'iter_num': iter_num, 'value': conf, 'elapsed_time': elapsed_time })
#     return fd_metadata

def calc_conf_distance(fd_metadata, h_space, study_metrics):
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
    for i in range(0, len(times)):
        avg_conf_d = np.prod([cd[i]['value'] for cd in conf_distance.values()]) / len(conf_distance.keys())
        avg_conf_distance.append({ 'iter_num': i+1, 'value': avg_conf_d, 'elapsed_time': times[i] })      
    return conf_distance, avg_conf_distance

def plot_results(run_type, project_ids, x_axis):
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

    # with open('./scenarios.json', 'r') as f:
    #     scenarios = json.load(f)

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

        h_space = project_info['scenario']['hypothesis_space']
        clean_h_space = project_info['scenario']['clean_hypothesis_space']
        if len([k for k in study_metrics.keys() if 'iter' in k]) == 0:
            study_metrics, fd_metadata = derive_stats(
                interaction_metadata,
                fd_metadata,
                h_space,
                study_metrics,
                dirty_dataset,
                clean_dataset
            )
            study_metrics['iter_err_precision'] = study_metrics.pop('precision')
            study_metrics['iter_err_recall'] = study_metrics.pop('recall')
            study_metrics['iter_err_f1'] = study_metrics.pop('f1')
        # if 'iter_conf' not in fd_metadata.keys():
        #     fd_metadata = derive_conf(fd_metadata, study_metrics)

        conf_distance, avg_conf_distance = calc_conf_distance(fd_metadata, clean_h_space, study_metrics)

        if x_axis == 'iter':
            ax1.plot([i['iter_num'] for i in study_metrics['iter_err_precision']], [i['value'] for i in study_metrics['iter_err_precision']])
            ax2.plot([i['iter_num'] for i in study_metrics['iter_err_recall']], [i['value'] for i in study_metrics['iter_err_recall']])
            ax3.plot([i['iter_num'] for i in study_metrics['iter_err_f1']], [i['value'] for i in study_metrics['iter_err_f1']])
            ax4.plot([i['iter_num'] for i in study_metrics['iter_vio_recall']], [i['value'] for i in study_metrics['iter_vio_recall']])
            ax5.plot([i['iter_num'] for i in study_metrics['all_vio_recall']], [i['value'] for i in study_metrics['all_vio_recall']])
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
            ax4.plot([i['elapsed_time'] for i in study_metrics['iter_vio_recall']], [i['value'] for i in study_metrics['iter_vio_recall']])
            ax5.plot([i['elapsed_time'] for i in study_metrics['all_vio_recall']], [i['value'] for i in study_metrics['all_vio_recall']])
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
    ax4.set_title('Vio-Catching Recall per Iteration')
    ax5.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax5.set_ylabel('Recall')
    ax5.set_title('Cumulative Violation-Catching Recall')
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
    fig1.savefig(path + '/iter-err-precision.jpg')
    fig2.savefig(path + '/iter-err-recall.jpg')
    fig3.savefig(path + '/iter-err-f1.jpg')
    fig4.savefig(path + '/iter-vio-recall.jpg')
    fig5.savefig(path + '/cumulative-vio-recall.jpg')
    fig6.savefig(path + '/target-fd-system-conf-gtruth-distance.jpg')
    fig7.savefig(path + '/avg-system-conf-gtruthdistance.jpg')
    fig8.savefig(path + '/cumulative-err-precision.jpg')
    fig9.savefig(path + '/cumulative-err-recall.jpg')
    fig10.savefig(path + '/cumulative-err-f1.jpg')
    plt.clf()

if __name__ == '__main__':
    plot_results(sys.argv[1], sys.argv[2:-1], sys.argv[-1])