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
        study_metrics, fd_metadata = helpers.deriveStats(
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