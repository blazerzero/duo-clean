import copy
import pandas as pd
import numpy as np
import scipy as sp
import sys
import helpers
import json
import matplotlib.pyplot as plt
from rich.console import Console
import os
import statstests
from itertools import zip_longest

console = Console()

s_index = {
    8: '1',
    11: '2',
    13: '3',
    14: '4',
    15: '5'
}

def extract_fd(item):
    return item['cfd']

def eval_user_h(project_id, run_type):
    pathstart = './docker-out/' if run_type == 'real' else './store/'
    with open(pathstart + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    scenario = project_info['scenario']
    scenario_id = project_info['scenario_id']
    data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
    clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
    target_fd = scenario['target_fd']
    h_space = scenario['hypothesis_space']
    with open(pathstart + project_id + '/interaction_metadata.json', 'r') as f:
        interaction_metadata = json.load(f)
    with open(pathstart + project_id + '/fd_metadata.json', 'r') as f:
        fd_metadata = json.load(f)
    with open(pathstart + project_id + '/study_metrics.json', 'r') as f:
        study_metrics = json.load(f)
    user_h_history = interaction_metadata['user_hypothesis_history']
    user_h_conf_history = list()
    fd_recall_history = list()
    fd_precision_history = list()
    fd_recall_seen_history = list()
    fd_precision_seen_history = list()
    user_h_seen_conf_history = list()
    seen_tuples = set()

    with open('./study-utils/users.json', 'r') as f:
        users = json.load(f)
    user_num_dict = dict()
    counter = 1
    for email in users.keys():
        user_num_dict[email] = counter
        counter += 1
    user_num = str(user_num_dict[project_info['email']])

    for h in user_h_history:
        fd = h['value'][0]
        if fd == 'Not Sure':
            user_h_conf_history.append(0)
            fd_recall_history.append(0)
            fd_precision_history.append(0)
            if h['iter_num'] > 0:
                user_h_seen_conf_history.append(0)
                fd_recall_seen_history.append(0)
                fd_precision_seen_history.append(0)
            continue

        lhs = fd.split(' => ')[0][1:-1].split(', ')
        rhs = fd.split(' => ')[1].split(', ')
        try:
            fd_meta = next(f for f in scenario['clean_hypothesis_space'] \
                if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(lhs) \
                and set(f['cfd'].split(' => ')[1].split(', ')) == set(rhs))
            dirty_fd_meta = next(f for f in scenario['hypothesis_space'] \
                if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(lhs) \
                and set(f['cfd'].split(' => ')[1].split(', ')) == set(rhs))
            support, vios = dirty_fd_meta['support'], dirty_fd_meta['vios']
            conf = fd_meta['conf']
            # fd = fd_meta['cfd']
        except StopIteration:
            support, vios = helpers.getSupportAndVios(data, clean_data, fd)
            conf = (len(support) - len(vios)) / len(support)
        
        target_fd_dirty_meta = next(f for f in scenario['hypothesis_space'] if f['cfd'] == scenario['target_fd'])
        target_vios = target_fd_dirty_meta['vios']

        user_h_conf_history.append(conf)
        fd_recall = len([v for v in vios if v in target_vios]) / len(target_vios)
        fd_precision = 0 if len(vios) == 0 else len([v for v in vios if v in target_vios]) / len(vios)
        fd_recall_history.append(fd_recall)
        fd_precision_history.append(fd_precision)

        if h['iter_num'] == 0:
            continue
        current_sample = next(i['value'] for i in interaction_metadata['sample_history'] if i['iter_num'] == h['iter_num'])
        seen_tuples |= set(current_sample)
        seen_data = data.iloc[list(seen_tuples)]
        seen_clean_data = clean_data.iloc[list(seen_tuples)]
        support, vios = helpers.getSupportAndVios(seen_data, seen_clean_data, fd)
        _, target_vios_seen = helpers.getSupportAndVios(seen_data, seen_clean_data, target_fd)
        conf = (len(support) - len(vios)) / len(support)
        user_h_seen_conf_history.append(conf)

        fd_recall_seen = len([v for v in vios if v in target_vios_seen]) / len(target_vios_seen)
        fd_precision_seen = 0 if len(vios) == 0 else len([v for v in vios if v in target_vios_seen]) / len(vios)

        fd_recall_seen_history.append(fd_recall_seen)
        fd_precision_seen_history.append(fd_precision_seen)
    
    study_metrics, fd_metadata = helpers.deriveStats(
        interaction_metadata,
        fd_metadata,
        h_space,
        study_metrics,
        data,
        clean_data,
        target_fd
    )
    with open(pathstart + project_id + '/study_metrics.json', 'w') as f:
        json.dump(study_metrics, f)
    with open(pathstart + project_id + '/fd_metadata.json', 'w') as f:
        json.dump(fd_metadata, f)
    
    cumulative_precision, cumulative_recall = study_metrics['cumulative_precision'], study_metrics['cumulative_recall']
    cumulative_precision_noover, cumulative_recall_noover = study_metrics['cumulative_precision_noover'], study_metrics['cumulative_recall_noover']
    
    # fig1, ax1 = plt.subplots()
    # fig2, ax2 = plt.subplots()
    # fig3, ax3 = plt.subplots()
    # fig4, ax4 = plt.subplots()
    # fig5, ax5 = plt.subplots()
    # fig6, ax6 = plt.subplots()
    # fig7, ax7 = plt.subplots()
    # fig8, ax8 = plt.subplots()
    # fig9, ax9 = plt.subplots()
    # fig10, ax10 = plt.subplots()

    # ax1.set_xticks(np.arange(0, 15, 3))
    # ax2.set_xticks(np.arange(0, 15, 3))
    # ax3.set_xticks(np.arange(0, 15, 3))
    # ax4.set_xticks(np.arange(0, 15, 3))
    # ax5.set_xticks(np.arange(0, 15, 3))
    # ax6.set_xticks(np.arange(0, 15, 3))
    # ax7.set_xticks(np.arange(0, 15, 3))
    # ax8.set_xticks(np.arange(0, 15, 3))
    # ax9.set_xticks(np.arange(0, 15, 3))
    # ax10.set_xticks(np.arange(0, 15, 3))

    # ax1.set_ylim([0, 1])
    # ax2.set_ylim([0, 1])
    # ax3.set_ylim([0, 1])
    # ax4.set_ylim([0, 1])
    # ax5.set_ylim([0, 1])
    # ax6.set_ylim([0, 1])
    # ax7.set_ylim([0, 1])
    # ax8.set_ylim([0, 1])
    # ax9.set_ylim([0, 1])
    # ax10.set_ylim([0, 1])

    # ax1.plot([i['iter_num'] for i in user_h_history], user_h_conf_history)
    # statstests.mannkendall(user_h_conf_history)

    # ax2.plot([i['iter_num'] for i in user_h_history], fd_recall_history)
    # statstests.mannkendall(fd_recall_history)

    # ax3.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], user_h_seen_conf_history)
    # statstests.mannkendall(user_h_seen_conf_history)

    # ax4.plot([i['iter_num'] for i in cumulative_precision], [i['value'] for i in cumulative_precision])
    # statstests.mannkendall([i['value'] for i in cumulative_precision])

    # ax5.plot([i['iter_num'] for i in cumulative_recall], [i['value'] for i in cumulative_recall])
    # statstests.mannkendall([i['value'] for i in cumulative_recall])

    # ax6.plot([i['iter_num'] for i in cumulative_precision_noover], [i['value'] for i in cumulative_precision_noover])
    # statstests.mannkendall([i['value'] for i in cumulative_precision_noover])

    # ax7.plot([i['iter_num'] for i in cumulative_recall_noover], [i['value'] for i in cumulative_recall_noover])
    # statstests.mannkendall([i['value'] for i in cumulative_recall_noover])

    # ax8.plot([i['iter_num'] for i in user_h_history], fd_precision_history)
    # statstests.mannkendall(fd_precision_history)

    # ax9.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_recall_seen_history)
    # statstests.mannkendall(fd_recall_seen_history)

    # ax10.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_precision_seen_history)
    # statstests.mannkendall(fd_precision_seen_history)

    # ax1.set_xlabel('Iteration #')
    # ax1.set_ylabel('Confidence')
    # ax1.set_title('Suggested FD Confidence Over the Interaction')
   
    # ax2.set_xlabel('Iteration #')
    # ax2.set_ylabel('Recall')
    # ax2.set_title('Suggested FD Recall')
    
    # ax3.set_xlabel('Iteration #')
    # ax3.set_ylabel('Confidence')
    # ax3.set_title('Suggested FD Confidence Over What the User Has Seen')
    
    # ax4.set_xlabel('Iteration #')
    # ax4.set_ylabel('Precision')
    # ax4.set_title('Cumulative User Precision')
    
    # ax5.set_xlabel('Iteration #')
    # ax5.set_ylabel('Recall')
    # ax5.set_title('Cumulative User Recall')
    
    # ax6.set_xlabel('Iteration #')
    # ax6.set_ylabel('Precision')
    # ax6.set_title('Cumulative User Precision (w/o Duplicate Vios)')
    
    # ax7.set_xlabel('Iteration #')
    # ax7.set_ylabel('Recall')
    # ax7.set_title('Cumulative User Recall (w/o Duplicate Vios)')

    # ax8.set_xlabel('Iteration #')
    # ax8.set_ylabel('Precision')
    # ax8.set_title('Suggested FD Precision')

    # ax9.set_xlabel('Iteration #')
    # ax9.set_ylabel('Recall')
    # ax9.set_title('Suggested FD Recall Over What the User Has Seen')

    # ax10.set_xlabel('Iteration #')
    # ax10.set_ylabel('Precision')
    # ax10.set_title('Suggested FD Precision Over What the User Has Seen')

    # fig1.tight_layout()
    # fig2.tight_layout()
    # fig3.tight_layout()
    # fig4.tight_layout()
    # fig5.tight_layout()
    # fig6.tight_layout()
    # fig7.tight_layout()
    # fig8.tight_layout()
    # fig9.tight_layout()
    # fig10.tight_layout()

    # fig1.savefig('./plots/fd-confidence/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig2.savefig('./plots/fd-recall/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig3.savefig('./plots/fd-confidence-seen/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig4.savefig('./plots/cumulative-user-precision/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig5.savefig('./plots/cumulative-user-recall/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig6.savefig('./plots/cumulative-user-precision-nodup/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig7.savefig('./plots/cumulative-user-recall-nodup/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig8.savefig('./plots/fd-precision/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig9.savefig('./plots/fd-recall-seen/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    # fig10.savefig('./plots/fd-precision-seen/' + project_id + '-s' + scenario_id + '-u' + user_num + '.jpg')
    
    # plt.clf()

def eval_h_grouped(group_type, run_type, id, background=None, max_iters=None):
    pathstart = './docker-out/' if run_type == 'real' else './store/'

    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()
    fig4, ax4 = plt.subplots()
    fig5, ax5 = plt.subplots()
    fig6, ax6 = plt.subplots()
    fig7, ax7 = plt.subplots()
    fig8, ax8 = plt.subplots()
    fig9, ax9 = plt.subplots()
    fig10, ax10 = plt.subplots()
    fig11, ax11 = plt.subplots()
    fig12, ax12 = plt.subplots()
    fig13, ax13 = plt.subplots()
    fig14, ax14 = plt.subplots()
    fig15, ax15 = plt.subplots()
    fig16, ax16 = plt.subplots()
    fig17, ax17 = plt.subplots()
    fig18, ax18 = plt.subplots()

    ax1.set_xticks(np.arange(0, 15, 3))
    ax2.set_xticks(np.arange(0, 15, 3))
    ax3.set_xticks(np.arange(0, 15, 3))
    ax4.set_xticks(np.arange(0, 15, 3))
    ax5.set_xticks(np.arange(0, 15, 3))
    ax6.set_xticks(np.arange(0, 15, 3))
    ax7.set_xticks(np.arange(0, 15, 3))
    ax8.set_xticks(np.arange(0, 15, 3))
    ax9.set_xticks(np.arange(0, 15, 3))
    ax10.set_xticks(np.arange(0, 15, 3))
    ax11.set_xticks(np.arange(0, 15, 3))
    ax12.set_xticks(np.arange(0, 15, 3))
    ax13.set_xticks(np.arange(0, 15, 3))
    ax14.set_xticks(np.arange(0, 1.1, 0.1))
    ax15.set_xticks(np.arange(0, 1.1, 0.1))
    ax16.set_xticks(np.arange(0, 15, 3))
    ax17.set_xticks(np.arange(0, 15, 3))
    ax18.set_xticks(np.arange(0, 15, 3))

    ax1.set_ylim([0, 1])
    ax2.set_ylim([0, 1])
    ax3.set_ylim([0, 1])
    ax4.set_ylim([0, 1])
    ax5.set_ylim([0, 1])
    ax6.set_ylim([0, 1])
    ax7.set_ylim([0, 1])
    ax8.set_ylim([0, 1])
    ax9.set_ylim([0, 1])
    ax10.set_ylim([0, 1])
    ax11.set_ylim([0, 1])
    ax12.set_ylim([0, 1])
    ax13.set_ylim([0, 1])
    ax14.set_ylim([-0.1, 0.1])
    ax15.set_ylim([-0.1, 0.1])
    ax16.set_ylim([0, 1])
    ax17.set_ylim([0, 1])
    ax18.set_ylim([0, 1])

    # bayesian_match_rate_1 = list()
    bayesian_match_rate_mrr_1 = list()
    # hp_match_rate_1 = list()
    hp_match_rate_mrr_1 = list()
    # bayesian_match_rate_penalty_1 = list()
    bayesian_match_rate_mrr_penalty_1 = list()
    # hp_match_rate_penalty_1 = list()
    hp_match_rate_mrr_penalty_1 = list()
    # bayesian_match_rate_3 = list()
    bayesian_match_rate_mrr_3 = list()
    # hp_match_rate_3 = list()
    hp_match_rate_mrr_3 = list()
    # bayesian_match_rate_penalty_3 = list()
    bayesian_match_rate_mrr_penalty_3 = list()
    # hp_match_rate_penalty_3 = list()
    hp_match_rate_mrr_penalty_3 = list()
    # bayesian_match_rate_5 = list()
    bayesian_match_rate_mrr_5 = list()
    # hp_match_rate_5 = list()
    hp_match_rate_mrr_5 = list()
    # bayesian_match_rate_penalty_5 = list()
    bayesian_match_rate_mrr_penalty_5 = list()
    # hp_match_rate_penalty_5 = list()
    hp_match_rate_mrr_penalty_5 = list()

    f1_mk_results = list()
    f1_seen_mk_results = list()
    user_f1_mk_results = list()
    user_f1_seen_mk_results = list()
    user_fd_f1_delta = list()

    user_f1_06 = list() # 0.6 alternative
    user_f1_045 = list()    # 0.45 alternative
    user_f1_06 = list()  # 0.6 alternative
    user_f1_045 = list() # 0.45 alternative

    user_f1_p_dict = {
        'significant-positive': 0,
        'significant-negative': 0,
        'insignificant': 0
    } # dict for how many runs were significant/insignificant

    user_seen_f1_p_dict = {
        'significant-positive': 0,
        'significant-negative': 0,
        'insignificant': 0
    } # dict for how many runs were significant/insignificant over seen data

    with open('./study-utils/users.json', 'r') as f:
        users = json.load(f)
    user_num_dict = dict()
    counter = 1
    for email in users.keys():
        user_num_dict[email] = counter
        counter += 1

    all_project_ids = os.listdir(pathstart)
    project_ids = list()
    training = list()
    for project_id in all_project_ids:
        with open(pathstart + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        scenario = project_info['scenario']
        scenario_id = project_info['scenario_id']
        user_num = str(user_num_dict[project_info['email']])

        # Test runs; not part of real data
        if 'test' in users[project_info['email']]['background']:
            continue

        # Training data; ignore unless we're specifically looking at training data
        if background != 'train' and 'train' in users[project_info['email']]['background']:
            training.append(project_id)

        if group_type == 'scenario':
            if scenario_id != id:
                continue
        elif group_type == 'user':
            if user_num != id:
                continue
        if background is not None:
            if background not in users[project_info['email']]['background']:
                continue
        
        project_ids.append(project_id)
    
    all_fd_f1_deltas = list()
    all_user_f1_deltas = list()

    all_cumulative_f1_06 = list()
    all_cumulative_f1_noover_06 = list()
    all_cumulative_f1_045 = list()
    all_cumulative_f1_noover_045 = list()
    
    for project_id in project_ids:
        console.log(project_id, '\n')
        with open(pathstart + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
        with open(pathstart + project_id + '/fd_metadata.json', 'r') as f:
            fd_metadata = json.load(f)
        scenario_id = project_info['scenario_id']
        scenario = scenarios[scenario_id]
        saved_scenario = project_info['scenario']
        user_num = str(user_num_dict[project_info['email']])
        
        data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
        target_fd = scenario['target_fd']
        target_fd_lhs = set(target_fd.split(' => ')[0][1:-1].split(', '))
        target_fd_rhs = set(target_fd.split(' => ')[1].split(', '))
        h_space = scenario['hypothesis_space']
        target_fd = next(h for h in fd_metadata.keys() if set(h.split(' => ')[0][1:-1].split(', ')) == target_fd_lhs and set(h.split(' => ')[1].split(', ')) == target_fd_rhs)

        data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)

        fds = [h['cfd'] for h in h_space]
        for fd in fds:
            lhs = set(fd.split(' => ')[0][1:-1].split(', '))
            rhs = set(fd.split(' => ')[1].split(', '))
            try:
                existing_fds = map(extract_fd, saved_scenario['hypothesis_space'])
                existing_fd = next(h for h in existing_fds if set(h.split(' => ')[0][1:-1].split(', ')) == lhs and set(h.split(' => ')[1].split(', ')) == rhs)
                fd = existing_fd
            except StopIteration:
                h = dict()
                h['cfd'] = fd
                h['score'] = 1
                support, vios = helpers.getSupportAndVios(data, clean_data, h['cfd'])
                vio_pairs = helpers.getPairs(data, support, h['cfd'])
                h['conf'] = (len(support) - len(vios)) / len(support)
                h['support'] = support
                h['vios'] = vios
                h['vio_pairs'] = set(tuple(vp) for vp in vio_pairs)
                mu = h['conf']
                if mu == 1:
                    mu = 0.99999
                variance = 0.0025
                
                # Calculate alpha and beta
                alpha, beta = helpers.initialPrior(mu, variance)
                
                # Initialize the FD metadata object
                fd_m = helpers.FDMeta(
                    fd=h['cfd'],
                    a=alpha,
                    b=beta,
                    support=h['support'],
                    vios=h['vios'],
                    vio_pairs=h['vio_pairs'],
                )
                fd_metadata[h['cfd']] = fd_m.asdict()
                if h['cfd'] not in [hs['cfd'] for hs in h_space]:
                    h_space.append(h)

        with open(pathstart + project_id + '/interaction_metadata.json', 'r') as f:
            interaction_metadata = json.load(f)
        with open(pathstart + project_id + '/study_metrics.json', 'r') as f:
            study_metrics = json.load(f)
        user_h_history = interaction_metadata['user_hypothesis_history']
        user_h_conf_history = list()
        fd_recall_history = list()
        fd_precision_history = list()
        fd_f1_history = list()
        fd_recall_seen_history = list()
        fd_precision_seen_history = list()
        fd_f1_seen_history = list()
        fd_f1_delta_history = list()
        user_h_seen_conf_history = list()
        seen_tuples = set()

        fd_f1_deltas = list()
        user_f1_deltas = list()

        alt_h_ratio = project_info['scenario']['alt_h_sample_ratio']

        target_fd_dirty_meta = next(f for f in scenario['hypothesis_space'] if f['cfd'] == scenario['target_fd'])
        target_vios = target_fd_dirty_meta['vios']
        for fd_m in fd_metadata.values():
            fd_m['precision'] = 0 if len(fd_m['vios']) else len([v for v in fd_m['vios'] if v in target_vios]) / len(fd_m['vios'])
            fd_m['recall'] = len([v for v in fd_m['vios'] if v in target_vios]) / len(target_vios)
            fd_m['f1'] = 0 if fd_m['precision'] == 0 and fd_m['recall'] == 0 else (2 * fd_m['precision'] * fd_m['recall']) / (fd_m['precision'] + fd_m['recall'])

        study_metrics, fd_metadata = helpers.deriveStats(
            interaction_metadata,
            fd_metadata,
            h_space,
            study_metrics,
            data,
            clean_data,
            target_fd,
            max_iters
        )

        for i in study_metrics['st_vio_f1']:
            if alt_h_ratio == 0.6:
                user_f1_06.append(i['value'])
            elif alt_h_ratio == 0.45:
                user_f1_045.append(i['value'])
        
        for n, h in enumerate(user_h_history):
            if max_iters is not None and n == max_iters + 1:
                break
            fd = h['value'][0]
            if fd == 'Not Sure':
                user_h_conf_history.append(0)
                fd_recall_history.append(0)
                fd_precision_history.append(0)
                fd_f1_history.append(0)
                # if project_info['scenario']['alt_h_sample_ratio'] == 0.6:
                #     user_fd_f1_06.append(0)
                # elif project_info['scenario']['alt_h_sample_ratio'] == 0.45:
                #     user_fd_f1_045.append(0)
                if h['iter_num'] > 0:
                    fd_f1_delta_history.append(abs(0 - fd_f1_history[-1]))
                    user_h_seen_conf_history.append(0)
                    fd_recall_seen_history.append(0)
                    fd_precision_seen_history.append(0)
                    fd_f1_seen_history.append(0)
                continue

            lhs = fd.split(' => ')[0][1:-1].split(', ')
            rhs = fd.split(' => ')[1].split(', ')
            try:
                fd_meta = next(f for f in scenario['clean_hypothesis_space'] \
                    if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(lhs) \
                    and set(f['cfd'].split(' => ')[1].split(', ')) == set(rhs))
                dirty_fd_meta = next(f for f in scenario['hypothesis_space'] \
                    if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(lhs) \
                    and set(f['cfd'].split(' => ')[1].split(', ')) == set(rhs))
                support, vios = dirty_fd_meta['support'], dirty_fd_meta['vios']
                conf = fd_meta['conf']
                # fd = fd_meta['cfd']
            except StopIteration:
                support, vios = helpers.getSupportAndVios(data, clean_data, fd)
                conf = (len(support) - len(vios)) / len(support)

            user_h_conf_history.append(conf)
            fd_recall = len([v for v in vios if v in target_vios]) / len(target_vios)
            fd_precision = 0 if len(vios) == 0 else len([v for v in vios if v in target_vios]) / len(vios)
            fd_f1 = 0 if fd_precision == 0 and fd_recall == 0 else ((2 * fd_precision * fd_recall) / (fd_precision + fd_recall))
            fd_recall_history.append(fd_recall)
            fd_precision_history.append(fd_precision)
            fd_f1_history.append(fd_f1)

            if h['iter_num'] == 0:
                continue
            current_sample = next(i['value'] for i in interaction_metadata['sample_history'] if i['iter_num'] == h['iter_num'])
            seen_tuples |= set(current_sample)
            seen_data = data.iloc[list(seen_tuples)]
            seen_clean_data = clean_data.iloc[list(seen_tuples)]
            support, vios = helpers.getSupportAndVios(seen_data, seen_clean_data, fd)
            _, target_vios_seen = helpers.getSupportAndVios(seen_data, seen_clean_data, target_fd)
            conf = (len(support) - len(vios)) / len(support)
            user_h_seen_conf_history.append(conf)

            fd_recall_seen = len([v for v in vios if v in target_vios_seen]) / len(target_vios_seen)
            fd_precision_seen = 0 if len(vios) == 0 else len([v for v in vios if v in target_vios_seen]) / len(vios)
            fd_f1_seen = 0 if fd_precision_seen == 0 and fd_recall_seen == 0 else ((2 * fd_precision_seen * fd_recall_seen) / (fd_precision_seen + fd_recall_seen))

            fd_recall_seen_history.append(fd_recall_seen)
            fd_precision_seen_history.append(fd_precision_seen)
            fd_f1_seen_history.append(fd_f1_seen)

            fd_f1_delta_history.append(abs(fd_f1_history[-1] - fd_f1_history[-2]))
        
        with open(pathstart + project_id + '/study_metrics.json', 'w') as f:
            json.dump(study_metrics, f)
        with open(pathstart + project_id + '/fd_metadata.json', 'w') as f:
            json.dump(fd_metadata, f)

        for i, h1 in enumerate(user_h_history):
            if max_iters is not None and i == max_iters + 1:
                break
            fd1 = h1['value'][0]
            if fd1 == 'Not Sure':
                fd1_f1 = 0
            else:
                lhs1 = set(fd1.split(' => ')[0][1:-1].split(', '))
                rhs1 = set(fd1.split(' => ')[1].split(', '))
                try:
                    fd1_meta = next(f for f in h_space \
                        if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == lhs1 \
                        and set(f['cfd'].split(' => ')[1].split(', ')) == rhs1)
                except StopIteration as e:
                    console.log(e)
                    return
                fd1_precision = 0 if len(fd1_meta['vios']) == 0 else len([v for v in fd1_meta['vios'] if v in target_vios]) / len(fd1_meta['vios'])
                fd1_recall = len([v for v in fd1_meta['vios'] if v in target_vios]) / len(target_vios)
                fd1_f1 = 0 if fd1_precision == 0 and fd1_recall == 0 else (2 * fd1_precision * fd1_recall) / (fd1_precision + fd1_recall)
                
            for j, h2 in enumerate(user_h_history):
                if i == j:
                    continue
                if max_iters is not None and j == max_iters + 1:
                    break
                fd2 = h2['value'][0]
                if fd2 == 'Not Sure':
                    fd2_f1 = 0
                else:
                    lhs2 = set(fd2.split(' => ')[0][1:-1].split(', '))
                    rhs2 = set(fd2.split(' => ')[1].split(', '))
                    try:
                        fd2_meta = next(f for f in h_space \
                            if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == lhs2 \
                            and set(f['cfd'].split(' => ')[1].split(', ')) == rhs2)
                    except StopIteration as e:
                        console.log(e)
                        return
                    fd2_precision = 0 if len(fd2_meta['vios']) == 0 else len([v for v in fd2_meta['vios'] if v in target_vios]) / len(fd2_meta['vios'])
                    fd2_recall = len([v for v in fd2_meta['vios'] if v in target_vios]) / len(target_vios)
                    fd2_f1 = 0 if fd2_precision == 0 and fd2_recall == 0 else (2 * fd2_precision * fd2_recall) / (fd2_precision + fd2_recall)
                
                fd_f1_delta = abs(fd1_f1 - fd2_f1)
                # fd_f1_deltas.append(fd_f1_delta / (len(user_h_history) * (len(user_h_history) - 1)))    # normalize
                fd_f1_deltas.append(fd_f1_delta)
        
        for i in study_metrics['st_vio_f1']:
            for j in study_metrics['st_vio_f1']:
                if i['iter_num'] == j['iter_num']:
                    continue
                user_f1_delta = abs(i['value'] - j['value'])
                user_f1_deltas.append(user_f1_delta)
            
        all_user_f1_deltas.extend(user_f1_deltas)
        all_fd_f1_deltas.extend(fd_f1_deltas)

        if project_id not in training:
            # bayesian_match_rate_1.append(study_metrics['bayesian_match_rate_1'])
            bayesian_match_rate_mrr_1.extend(study_metrics['bayesian_match_mrr_1'])
            # hp_match_rate_1.append(study_metrics['hp_match_rate_1'])
            hp_match_rate_mrr_1.extend(study_metrics['hp_match_mrr_1'][1:])
            # bayesian_match_rate_penalty_1.append(study_metrics['bayesian_match_rate_penalty_1'])
            bayesian_match_rate_mrr_penalty_1.extend(study_metrics['bayesian_match_mrr_penalty_1'])
            # hp_match_rate_penalty_1.append(study_metrics['hp_match_rate_penalty_1'])
            hp_match_rate_mrr_penalty_1.extend(study_metrics['hp_match_mrr_penalty_1'][1:])
            
            # bayesian_match_rate_3.append(study_metrics['bayesian_match_rate_3'])
            bayesian_match_rate_mrr_3.extend(study_metrics['bayesian_match_mrr_3'])
            # hp_match_rate_3.append(study_metrics['hp_match_rate_3'])
            hp_match_rate_mrr_3.extend(study_metrics['hp_match_mrr_3'][1:])
            # bayesian_match_rate_penalty_3.append(study_metrics['bayesian_match_rate_penalty_3'])
            bayesian_match_rate_mrr_penalty_3.extend(study_metrics['bayesian_match_mrr_penalty_3'])
            # hp_match_rate_penalty_3.append(study_metrics['hp_match_rate_penalty_3'])
            hp_match_rate_mrr_penalty_3.extend(study_metrics['hp_match_mrr_penalty_3'][1:])

            # bayesian_match_rate_5.append(study_metrics['bayesian_match_rate_5'])
            bayesian_match_rate_mrr_5.extend(study_metrics['bayesian_match_mrr_5'])
            # hp_match_rate_5.append(study_metrics['hp_match_rate_5'])
            hp_match_rate_mrr_5.extend(study_metrics['hp_match_mrr_5'][1:])
            # bayesian_match_rate_penalty_5.append(study_metrics['bayesian_match_rate_penalty_5'])
            bayesian_match_rate_mrr_penalty_5.extend(study_metrics['bayesian_match_mrr_penalty_5'])
            # hp_match_rate_penalty_5.append(study_metrics['hp_match_rate_penalty_5'])
            hp_match_rate_mrr_penalty_5.extend(study_metrics['hp_match_mrr_penalty_5'][1:])
        
        cumulative_precision, cumulative_recall = study_metrics['cumulative_precision'], study_metrics['cumulative_recall']
        cumulative_precision_noover, cumulative_recall_noover = study_metrics['cumulative_precision_noover'], study_metrics['cumulative_recall_noover']
        cumulative_f1, cumulative_f1_noover = study_metrics['cumulative_f1'], study_metrics['cumulative_f1_noover']

        if alt_h_ratio == 0.6:
            all_cumulative_f1_06.append([i['value'] for i in cumulative_f1])
            all_cumulative_f1_noover_06.append([i['value'] for i in cumulative_f1_noover])
        else:
            all_cumulative_f1_045.append([i['value'] for i in cumulative_f1])
            all_cumulative_f1_noover_045.append([i['value'] for i in cumulative_f1_noover])

        if len(user_h_history) > 2:

            res = statstests.mannkendall([i['value'] for i in cumulative_f1])
            user_f1_mk_results.append((res.trend, res.p, res.slope))

            if max_iters is None:
                ax1.plot([i['iter_num'] for i in user_h_history], user_h_conf_history)
                # statstests.mannkendall(user_h_conf_history)

                ax2.plot([i['iter_num'] for i in user_h_history], fd_recall_history)
                # statstests.mannkendall(fd_recall_history)

                ax3.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], user_h_seen_conf_history)
                # statstests.mannkendall(user_h_seen_conf_history)

                ax4.plot([i['iter_num'] for i in cumulative_precision], [i['value'] for i in cumulative_precision])
                # statstests.mannkendall([i['value'] for i in cumulative_precision])

                ax5.plot([i['iter_num'] for i in cumulative_recall], [i['value'] for i in cumulative_recall])
                # statstests.mannkendall([i['value'] for i in cumulative_recall])

                ax6.plot([i['iter_num'] for i in cumulative_precision_noover], [i['value'] for i in cumulative_precision_noover])
                # statstests.mannkendall([i['value'] for i in cumulative_precision_noover])

                ax7.plot([i['iter_num'] for i in cumulative_recall_noover], [i['value'] for i in cumulative_recall_noover])
                # statstests.mannkendall([i['value'] for i in cumulative_recall_noover])

                ax8.plot([i['iter_num'] for i in user_h_history], fd_precision_history)
                # statstests.mannkendall(fd_precision_history)

                ax9.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_recall_seen_history)
                # statstests.mannkendall(fd_recall_seen_history)

                ax10.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_precision_seen_history)
                # statstests.mannkendall(fd_precision_seen_history)

                ax11.plot([i['iter_num'] for i in user_h_history], fd_f1_history)
                res = statstests.mannkendall(fd_f1_history)
                f1_mk_results.append((res.trend, res.p, res.slope))
                # console.log(f1_mk_results[-1])

                res_seen = statstests.mannkendall(fd_f1_seen_history)
                f1_seen_mk_results.append((res_seen.trend, res_seen.p, res_seen.slope))

                ax12.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_f1_seen_history)
                # statstests.mannkendall(fd_f1_seen_history)

                # console.log(fd_f1_delta_history)
                ax13.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], fd_f1_delta_history)

                ax16.plot([i['iter_num'] for i in cumulative_f1], [i['value'] for i in cumulative_f1], color='#0000ff55' if alt_h_ratio == 0.6 else '#00ff0055', linewidth=1)
                # statstests.mannkendall([i['value'] for i in cumulative_precision_noover])

                ax17.plot([i['iter_num'] for i in cumulative_f1_noover], [i['value'] for i in cumulative_f1_noover], color='#0000ff55' if alt_h_ratio == 0.6 else '#00ff0055', linewidth=1)
                # statstests.mannkendall([i['value'] for i in cumulative_recall_noover])

            else:
                ax1.plot([i['iter_num'] for i in user_h_history if i['iter_num'] <= max_iters], user_h_conf_history)
                # statstests.mannkendall(user_h_conf_history)

                ax2.plot([i['iter_num'] for i in user_h_history if i['iter_num'] <= max_iters], fd_recall_history)
                # statstests.mannkendall(fd_recall_history)

                ax3.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0 and i['iter_num'] <= max_iters], user_h_seen_conf_history)
                # statstests.mannkendall(user_h_seen_conf_history)

                ax4.plot([i['iter_num'] for i in cumulative_precision if i['iter_num'] <= max_iters], [i['value'] for i in cumulative_precision])
                # statstests.mannkendall([i['value'] for i in cumulative_precision])

                ax5.plot([i['iter_num'] for i in cumulative_recall if i['iter_num'] <= max_iters], [i['value'] for i in cumulative_recall])
                # statstests.mannkendall([i['value'] for i in cumulative_recall])

                ax6.plot([i['iter_num'] for i in cumulative_precision_noover if i['iter_num'] <= max_iters], [i['value'] for i in cumulative_precision_noover])
                # statstests.mannkendall([i['value'] for i in cumulative_precision_noover])

                ax7.plot([i['iter_num'] for i in cumulative_recall_noover if i['iter_num'] <= max_iters], [i['value'] for i in cumulative_recall_noover])
                # statstests.mannkendall([i['value'] for i in cumulative_recall_noover])

                ax8.plot([i['iter_num'] for i in user_h_history if i['iter_num'] <= max_iters], fd_precision_history)
                # statstests.mannkendall(fd_precision_history)

                ax9.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0 and i['iter_num'] <= max_iters], fd_recall_seen_history)
                # statstests.mannkendall(fd_recall_seen_history)

                ax10.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0 and i['iter_num'] <= max_iters], fd_precision_seen_history)
                # statstests.mannkendall(fd_precision_seen_history)

                ax11.plot([i['iter_num'] for i in user_h_history if i['iter_num'] <= max_iters], fd_f1_history)
                res = statstests.mannkendall(fd_f1_history)
                f1_mk_results.append((res.trend, res.p, res.slope))
                # console.log(f1_mk_results[-1])

                ax12.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0 and i['iter_num'] <= max_iters], fd_f1_seen_history)
                # statstests.mannkendall(fd_f1_seen_history)

                # console.log(fd_f1_delta_history)
                ax13.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0 and i['iter_num'] <= max_iters], fd_f1_delta_history)

                ax16.plot([i['iter_num'] for i in cumulative_f1], [i['value'] for i in cumulative_f1], color='#0000ff55' if alt_h_ratio == 0.6 else '#00ff0055', linewidth=1)
                # statstests.mannkendall([i['value'] for i in cumulative_precision_noover])

                ax17.plot([i['iter_num'] for i in cumulative_f1_noover], [i['value'] for i in cumulative_f1_noover], color='#0000ff55' if alt_h_ratio == 0.6 else '#00ff0055', linewidth=1)
                # statstests.mannkendall([i['value'] for i in cumulative_recall_noover])

            r = f1_mk_results[-1]
            if r[1] <= 0.05:
                if r[0] == 'increasing':
                    user_f1_p_dict['significant-positive'] += 1
                else:
                    user_f1_p_dict['significant-negative'] += 1
            else:
                user_f1_p_dict['insignificant'] += 1
            # # ax14.plot([r[1]], np.zeros(1), color='g' if r[2] > 0 else 'grey' if r[2] == 0 else 'r', marker='x')
            
            r = f1_seen_mk_results[-1]
            if r[1] <= 0.05:
                if r[0] == 'increasing':
                    user_seen_f1_p_dict['significant-positive'] += 1
                else:
                    user_seen_f1_p_dict['significant-negative'] += 1
            else:
                user_seen_f1_p_dict['insignificant'] += 1
            # ax15.plot([r[1]], np.zeros(1), color='g' if r[2] > 0 else 'grey' if r[2] == 0 else 'r', marker='x')

            r = user_f1_mk_results[-1]
            if r[1] <= 0.05:
                if r[0] == 'increasing':
                    user_f1_p_dict['significant-positive'] += 1
                else:
                    user_f1_p_dict['significant-negative'] += 1
            else:
                user_f1_p_dict['insignificant'] += 1
    
    if group_type == 'scenario':
        all_cumulative_f1_06 = np.nanmean(np.array(list(zip_longest(*all_cumulative_f1_06)), dtype=float), axis=1)
        all_cumulative_f1_noover_06 = np.nanmean(np.array(list(zip_longest(*all_cumulative_f1_noover_06)), dtype=float), axis=1)
        all_cumulative_f1_045 = np.nanmean(np.array(list(zip_longest(*all_cumulative_f1_045)), dtype=float), axis=1)
        all_cumulative_f1_noover_045 = np.nanmean(np.array(list(zip_longest(*all_cumulative_f1_noover_045)), dtype=float), axis=1)
        ax16.plot(range(1, len(all_cumulative_f1_06)+1), all_cumulative_f1_06, color='blue', linewidth=3)
        ax16.plot(range(1, len(all_cumulative_f1_045)+1), all_cumulative_f1_045, color='green', linewidth=3)

    ax1.set_xlabel('Iteration #')
    ax1.set_ylabel('Confidence')
    ax1.set_title('Suggested FD Confidence Over the Interaction')
   
    ax2.set_xlabel('Iteration #')
    ax2.set_ylabel('Recall')
    ax2.set_title('Suggested FD Recall')
    
    ax3.set_xlabel('Iteration #')
    ax3.set_ylabel('Confidence')
    ax3.set_title('Suggested FD Confidence Over What the User Has Seen')
    
    ax4.set_xlabel('Iteration #')
    ax4.set_ylabel('Precision')
    ax4.set_title('Cumulative User Precision')
    
    ax5.set_xlabel('Iteration #')
    ax5.set_ylabel('Recall')
    ax5.set_title('Cumulative User Recall')
    
    ax6.set_xlabel('Iteration #')
    ax6.set_ylabel('Precision')
    ax6.set_title('Cumulative User Precision (w/o Duplicate Vios)')
    
    ax7.set_xlabel('Iteration #')
    ax7.set_ylabel('Recall')
    ax7.set_title('Cumulative User Recall (w/o Duplicate Vios)')

    ax8.set_xlabel('Iteration #')
    ax8.set_ylabel('Precision')
    ax8.set_title('Suggested FD Precision')

    ax9.set_xlabel('Iteration #')
    ax9.set_ylabel('Recall')
    ax9.set_title('Suggested FD Recall Over What the User Has Seen')

    ax10.set_xlabel('Iteration #')
    ax10.set_ylabel('Precision')
    ax10.set_title('Suggested FD Precision Over What the User Has Seen')

    ax11.set_xlabel('Iteration #')
    ax11.set_ylabel('F1 Score')
    ax11.set_title('Suggested FD F1 Score')

    ax12.set_xlabel('Iteration #')
    ax12.set_ylabel('F1 Score')
    ax12.set_title('Suggested F1 Score Over What the User Has Seen')
    
    ax13.set_xlabel('Iteration #')
    ax13.set_ylabel('Difference in F1 Score')
    ax13.set_title('Change in F1 Score of User\'s Hypotheses')

    ax14.set_xlabel('p-value')
    ax14.set_title('Change in F1-Score of User\'s Hypothesis Over All Data')

    ax15.set_xlabel('p-value')
    ax15.set_title('Change in F1-Score of User\'s Hypothesis Over Seen Data')

    ax16.set_xlabel('Iteration #')
    ax16.set_ylabel('F1-Score')
    ax16.set_title('Cumulative User F1-Score')
    
    ax17.set_xlabel('Iteration #')
    ax17.set_ylabel('F1-Score')
    ax17.set_title('Cumulative User F1-Score (w/o Duplicate Vios)')

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
    fig11.tight_layout()
    fig12.tight_layout()
    fig13.tight_layout()
    fig14.tight_layout()
    fig15.tight_layout()
    fig16.tight_layout()
    fig17.tight_layout()

    match_rates = {
        # 'bayesian_match_rate_1': np.mean(bayesian_match_rate_1),
        # 'hp_match_rate_1': np.mean(hp_match_rate_1),
        'bayesian_match_rate_mrr_1': np.mean(bayesian_match_rate_mrr_1),
        'hp_match_rate_mrr_1': np.mean(hp_match_rate_mrr_1),
        # 'bayesian_match_rate_penalty_1': np.mean(bayesian_match_rate_penalty_1),
        # 'hp_match_rate_penalty_1': np.mean(hp_match_rate_penalty_1),
        'bayesian_match_rate_mrr_penalty_1': np.mean(bayesian_match_rate_mrr_penalty_1),
        'hp_match_rate_mrr_penalty_1': np.mean(hp_match_rate_mrr_penalty_1),
        # 'bayesian_match_rate_3': np.mean(bayesian_match_rate_3),
        # 'hp_match_rate_3': np.mean(hp_match_rate_3),
        'bayesian_match_rate_mrr_3': np.mean(bayesian_match_rate_mrr_3),
        'hp_match_rate_mrr_3': np.mean(hp_match_rate_mrr_3),
        # 'bayesian_match_rate_penalty_3': np.mean(bayesian_match_rate_penalty_3),
        # 'hp_match_rate_penalty_3': np.mean(hp_match_rate_penalty_3),
        'bayesian_match_rate_mrr_penalty_3': np.mean(bayesian_match_rate_mrr_penalty_3),
        'hp_match_rate_mrr_penalty_3': np.mean(hp_match_rate_mrr_penalty_3),
        # 'bayesian_match_rate_5': np.mean(bayesian_match_rate_5),
        # 'hp_match_rate_5': np.mean(hp_match_rate_5),
        'bayesian_match_rate_mrr_5': np.mean(bayesian_match_rate_mrr_5),
        'hp_match_rate_mrr_5': np.mean(hp_match_rate_mrr_5),
        # 'bayesian_match_rate_penalty_5': np.mean(bayesian_match_rate_penalty_5),
        # 'hp_match_rate_penalty_5': np.mean(hp_match_rate_penalty_5),
        'bayesian_match_rate_mrr_penalty_5': np.mean(bayesian_match_rate_mrr_penalty_5),
        'hp_match_rate_mrr_penalty_5': np.mean(hp_match_rate_mrr_penalty_5)
    }

    if group_type == 'scenario' and background is None:
        # Comparing f1 of user hypotheses with different alt h configurations
        _, user_f1_alt_h_p = sp.stats.ttest_ind(user_f1_06, user_f1_045)

        with open('./plots/alt-h-stat-test/' + 's' + scenario_id + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(user_f1_alt_h_p, f)

    if background is None:
        # Bayes vs. HP
        # if np.array_equal(bayesian_match_rate_mrr_3, hp_match_rate_mrr_3):
        #     bayes_hp_3_wilcoxon_p = 1
        # else:
        #     _, bayes_hp_3_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_3, hp_match_rate_mrr_3)
        _, bayes_hp_1_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_1, hp_match_rate_mrr_1)
        _, bayes_hp_3_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_3, hp_match_rate_mrr_3)
        
        # if np.array_equal(bayesian_match_rate_mrr_5, hp_match_rate_mrr_5):
        #     bayes_hp_5_wilcoxon_p = 1
        # else:
        #     _, bayes_hp_5_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_5, hp_match_rate_mrr_5)
        _, bayes_hp_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_5, hp_match_rate_mrr_5)
        
        # Bayes vs. HP (w/ Sub-Super)
        # if np.array_equal(bayesian_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_3):
        #     bayes_hp_penalty_3_wilcoxon_p = 1
        # else:
        #     _, bayes_hp_penalty_3_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_3)
        _, bayes_hp_penalty_1_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_1, hp_match_rate_mrr_penalty_1)
        _, bayes_hp_penalty_3_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_3)
        
        # if np.array_equal(bayesian_match_rate_mrr_penalty_5, hp_match_rate_mrr_penalty_5):
        #     bayes_hp_penalty_5_wilcoxon_p = 1
        # else:
        #     _, bayes_hp_penalty_5_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_penalty_5, hp_match_rate_mrr_penalty_5)
        _, bayes_hp_penalty_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_5, hp_match_rate_mrr_penalty_5)

        # Bayes-3 vs. Bayes-5
        # if np.array_equal(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_5):
        #     bayes_mrr_wilcoxon_p = 1
        # else:
        #     _, bayes_mrr_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_5)
        _, bayes_mrr_1_3_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_1, bayesian_match_rate_mrr_3)
        _, bayes_mrr_1_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_1, bayesian_match_rate_mrr_5)
        _, bayes_mrr_3_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_5)
        
        # if np.array_equal(bayesian_match_rate_mrr_penalty_3, bayesian_match_rate_mrr_penalty_5):
        #     bayes_mrr_penalty_wilcoxon_p = 1
        # else:
        #     _, bayes_mrr_penalty_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_penalty_3, bayesian_match_rate_mrr_penalty_5)
        _, bayes_mrr_penalty_1_3_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_1, bayesian_match_rate_mrr_penalty_3)
        _, bayes_mrr_penalty_1_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_1, bayesian_match_rate_mrr_penalty_5)
        _, bayes_mrr_penalty_3_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_penalty_3, bayesian_match_rate_mrr_penalty_5)
        
        # HP-3 vs. HP-5
        # if np.array_equal(hp_match_rate_mrr_3, hp_match_rate_mrr_5):
        #     hp_mrr_wilcoxon_p = 1
        # else:
        #     _, hp_mrr_wilcoxon_p = sp.stats.wilcoxon(hp_match_rate_mrr_3, hp_match_rate_mrr_5)
        _, hp_mrr_1_3_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_1, hp_match_rate_mrr_3)
        _, hp_mrr_1_5_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_1, hp_match_rate_mrr_5)
        _, hp_mrr_3_5_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_3, hp_match_rate_mrr_5)
        
        # if np.array_equal(hp_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_5):
        #     hp_mrr_penalty_wilcoxon_p = 1
        # else:
        #     _, hp_mrr_penalty_wilcoxon_p = sp.stats.wilcoxon(hp_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_5)
        _, hp_mrr_penalty_1_3_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_penalty_1, hp_match_rate_mrr_penalty_3)
        _, hp_mrr_penalty_1_5_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_penalty_1, hp_match_rate_mrr_penalty_5)
        _, hp_mrr_penalty_3_5_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_penalty_3, hp_match_rate_mrr_penalty_5)

        # Bayes vs. Bayes w/ Sub-Super
        # if np.array_equal(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_penalty_3):
        #     bayes_compare_3_wilcoxon_p = 1
        # else:
        #     _, bayes_compare_3_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_penalty_3)
        _, bayes_compare_1_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_1, bayesian_match_rate_mrr_penalty_1)
        _, bayes_compare_3_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_3, bayesian_match_rate_mrr_penalty_3)
        
        # if np.array_equal(bayesian_match_rate_mrr_5, bayesian_match_rate_mrr_penalty_5):
        #     bayes_compare_5_wilcoxon_p = 1
        # else:
        #     _, bayes_compare_5_wilcoxon_p = sp.stats.wilcoxon(bayesian_match_rate_mrr_5, bayesian_match_rate_mrr_penalty_5)
        _, bayes_compare_5_ttest_ind_p = sp.stats.ttest_ind(bayesian_match_rate_mrr_5, bayesian_match_rate_mrr_penalty_5)
        
        # HP vs. HP w/ Sub-Super
        # if np.array_equal(hp_match_rate_mrr_3, hp_match_rate_mrr_penalty_3):
        #     hp_compare_3_wilcoxon_p = 1
        # else:
        #     _, hp_compare_3_wilcoxon_p = sp.stats.wilcoxon(hp_match_rate_mrr_3, hp_match_rate_mrr_penalty_3)
        _, hp_compare_1_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_1, hp_match_rate_mrr_penalty_1)
        _, hp_compare_3_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_3, hp_match_rate_mrr_penalty_3)
        
        # if np.array_equal(hp_match_rate_mrr_5, hp_match_rate_mrr_penalty_5):
        #     hp_compare_5_wilcoxon_p = 1
        # else:
        #     _, hp_compare_5_wilcoxon_p = sp.stats.wilcoxon(hp_match_rate_mrr_5, hp_match_rate_mrr_penalty_5)
        _, hp_compare_5_ttest_ind_p = sp.stats.ttest_ind(hp_match_rate_mrr_5, hp_match_rate_mrr_penalty_5)

        # Gather Wilcoxon results
        # wilcoxon_results = {
        #     'bayes_hp_3': bayes_hp_3_wilcoxon_p,
        #     'bayes_hp_5': bayes_hp_5_wilcoxon_p,
        #     'bayes_hp_penalty_3': bayes_hp_penalty_3_wilcoxon_p,
        #     'bayes_hp_penalty_5': bayes_hp_penalty_5_wilcoxon_p,
        #     'bayes_mrr': bayes_mrr_wilcoxon_p,
        #     'bayes_mrr_penalty': bayes_mrr_penalty_wilcoxon_p,
        #     'hp_mrr': hp_mrr_wilcoxon_p,
        #     'hp_mrr_penalty': hp_mrr_penalty_wilcoxon_p,
        #     'bayes_compare_3': bayes_compare_3_wilcoxon_p,
        #     'bayes_compare_5': bayes_compare_5_wilcoxon_p,
        #     'hp_compare_3': hp_compare_3_wilcoxon_p,
        #     'hp_compare_5': hp_compare_5_wilcoxon_p
        # }

        # Gather t Test results
        ttest_ind_results = {
            'bayes_hp_1': bayes_hp_1_ttest_ind_p,
            'bayes_hp_3': bayes_hp_3_ttest_ind_p,
            'bayes_hp_5': bayes_hp_5_ttest_ind_p,
            'bayes_hp_penalty_1': bayes_hp_penalty_1_ttest_ind_p,
            'bayes_hp_penalty_3': bayes_hp_penalty_3_ttest_ind_p,
            'bayes_hp_penalty_5': bayes_hp_penalty_5_ttest_ind_p,
            'bayes_mrr_1_3': bayes_mrr_1_3_ttest_ind_p,
            'bayes_mrr_1_5': bayes_mrr_1_5_ttest_ind_p,
            'bayes_mrr_3_5': bayes_mrr_3_5_ttest_ind_p,
            'bayes_mrr_penalty_1_3': bayes_mrr_penalty_1_3_ttest_ind_p,
            'bayes_mrr_penalty_1_5': bayes_mrr_penalty_1_5_ttest_ind_p,
            'bayes_mrr_penalty_3_5': bayes_mrr_penalty_3_5_ttest_ind_p,
            'hp_mrr_1_3': hp_mrr_1_3_ttest_ind_p,
            'hp_mrr_1_5': hp_mrr_1_5_ttest_ind_p,
            'hp_mrr_3_5': hp_mrr_3_5_ttest_ind_p,
            'hp_mrr_penalty_1_3': hp_mrr_penalty_1_3_ttest_ind_p,
            'hp_mrr_penalty_1_5': hp_mrr_penalty_1_5_ttest_ind_p,
            'hp_mrr_penalty_3_5': hp_mrr_penalty_3_5_ttest_ind_p,
            'bayes_compare_1': bayes_compare_1_ttest_ind_p,
            'bayes_compare_3': bayes_compare_3_ttest_ind_p,
            'bayes_compare_5': bayes_compare_5_ttest_ind_p,
            'hp_compare_1': hp_compare_1_ttest_ind_p,
            'hp_compare_3': hp_compare_3_ttest_ind_p,
            'hp_compare_5': hp_compare_5_ttest_ind_p
        }

        with open('./plots/fd-f1-pairwise-deltas/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(np.mean(all_fd_f1_deltas), f, indent=4)
        
        with open('./plots/user-f1-pairwise-deltas/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(np.mean(all_user_f1_deltas), f, indent=4)
        
        # with open('./plots/wilcoxon-results/' + 's' + scenario_id + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
        #     json.dump(wilcoxon_results, f, indent=4)
        
        with open('./plots/ttest-results/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(ttest_ind_results, f, indent=4)

    if background is None:
        fig1.savefig('./plots/fd-confidence/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig2.savefig('./plots/fd-recall/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig3.savefig('./plots/fd-confidence-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig4.savefig('./plots/cumulative-user-precision/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig5.savefig('./plots/cumulative-user-recall/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig6.savefig('./plots/cumulative-user-precision-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig7.savefig('./plots/cumulative-user-recall-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig8.savefig('./plots/fd-precision/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig9.savefig('./plots/fd-recall-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig10.savefig('./plots/fd-precision-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig11.savefig('./plots/fd-f1/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig12.savefig('./plots/fd-f1-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig13.savefig('./plots/fd-f1-delta/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        # fig14.savefig('./plots/f1-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig15.savefig('./plots/f1-seen-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig16.savefig('./plots/cumulative-user-f1/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig17.savefig('./plots/cumulative-user-f1-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')

        with open('./plots/match-rates/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(match_rates, f, indent=4)
        
        with open('./plots/f1-mk-results/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(f1_mk_results, f, indent=4)
        
        with open('./plots/f1-seen-mk-results/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(f1_seen_mk_results, f, indent=4)
        
        # with open('./plots/alt-h-stat-test/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
        #     json.dump(user_f1_alt_h_p, f)
        
        with open('./plots/f1-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(user_f1_p_dict, f)
        
        with open('./plots/f1-seen-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(user_seen_f1_p_dict, f)

    else:
        fig1.savefig('./plots/fd-confidence/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig2.savefig('./plots/fd-recall/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig3.savefig('./plots/fd-confidence-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig4.savefig('./plots/cumulative-user-precision/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig5.savefig('./plots/cumulative-user-recall/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig6.savefig('./plots/cumulative-user-precision-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig7.savefig('./plots/cumulative-user-recall-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig8.savefig('./plots/fd-precision/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig9.savefig('./plots/fd-recall-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig10.savefig('./plots/fd-precision-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig11.savefig('./plots/fd-f1/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig12.savefig('./plots/fd-f1-seen/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig13.savefig('./plots/fd-f1-delta/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        # fig14.savefig('./plots/f1-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig15.savefig('./plots/f1-seen-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig16.savefig('./plots/cumulative-user-f1/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')
        fig17.savefig('./plots/cumulative-user-f1-nodup/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.jpg')

        with open('./plots/match-rates/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(match_rates, f, indent=4)
        
        with open('./plots/f1-mk-results/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(f1_mk_results, f, indent=4)
        
        with open('./plots/f1-seen-mk-results/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(f1_seen_mk_results, f, indent=4)
        
        # with open('./plots/alt_h_stat_test/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
        #     json.dump(user_f1_alt_h_p, f)
        
        with open('./plots/f1-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(user_f1_p_dict, f)
        
        with open('./plots/f1-seen-mk-plots/' + (('s' + scenario_id) if group_type == 'scenario' else ('u' + user_num)) + '-' + background + (('-i' + str(max_iters)) if max_iters is not None else '') + '.json', 'w') as f:
            json.dump(user_seen_f1_p_dict, f)
    
    plt.clf()

if __name__ == '__main__':
    run_type = sys.argv[1]
    diff = sys.argv[2]
    id = sys.argv[3]
    group = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].isnumeric() else None
    max_iters = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isnumeric() and float(sys.argv[4]).is_integer() else None
    # alt_h_ratio = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isnumeric() and not float(sys.argv[4]).is_integer() else None
    
    if '0' in diff:
        eval_user_h(diff, run_type, id)
    else:
        eval_h_grouped(diff, run_type, id, group, max_iters)
