import copy
import pandas as pd
import numpy as np
import scipy as sp
import sys
import helpers
import json
import matplotlib.pyplot as plt
from rich.console import Console

console = Console()

def eval_user_h(project_id, run_type):
    pathstart = './docker-out/' if run_type == 'real' else './store/'
    with open(pathstart + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    scenario = project_info['scenario']
    data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
    clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
    with open(pathstart + project_id + '/interaction_metadata.json', 'r') as f:
        interaction_metadata = json.load(f)
    user_h_history = interaction_metadata['user_hypothesis_history']
    user_h_conf_history = list()
    user_h_vio_match_history = list()
    user_h_seen_conf_history = list()
    seen_tuples = set()
    for h in user_h_history:
        fd = h['value'][0]
        if fd == 'Not Sure':
            user_h_conf_history.append(0)
            user_h_vio_match_history.append(0)
            if h['iter_num'] > 0:
                user_h_seen_conf_history.append(0)
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
        vio_match_rate = len([v for v in vios if v in target_vios]) / len(target_vios)
        user_h_vio_match_history.append(vio_match_rate)

        if h['iter_num'] == 0:
            continue
        current_sample = next(i['value'] for i in interaction_metadata['sample_history'] if i['iter_num'] == h['iter_num'])
        seen_tuples |= set(current_sample)
        seen_data = data[seen_tuples]
        seen_clean_data = clean_data[seen_tuples]
        support, vios = helpers.getSupportAndVios(seen_data, seen_clean_data, fd)
        conf = (len(support) - len(vios)) / len(support)
        user_h_seen_conf_history.append(conf)
    
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()
    ax1.set_xticks(np.arange(0, 15, 3))
    ax2.set_xticks(np.arange(0, 15, 3))
    ax3.set_xticks(np.arange(0, 15, 3))
    ax1.set_ylim([0, 1])
    ax2.set_ylim([0, 1])
    ax3.set_ylim([0, 1])

    ax1.plot([i['iter_num'] for i in user_h_history], user_h_conf_history)
    ax2.plot([i['iter_num'] for i in user_h_history], user_h_vio_match_history)
    ax3.plot([i['iter_num'] for i in user_h_history if i['iter_num'] > 0], user_h_seen_conf_history)

    ax1.set_xlabel('Iteration #')
    ax1.set_ylabel('FD Precision')
    ax1.set_title('FD Precision Over the Interaction')
    ax2.set_xlabel('Iteration #')
    ax2.set_ylabel('Match Rate')
    ax2.set_title("Applicability of User FD to Real Violations")
    ax3.set_xlabel('Iteration #')
    ax3.set_ylabel('FD Precision')
    ax3.set_title('FD Precision Over What the User Has Seen So Far')

    fig1.tight_layout()
    fig2.tight_layout()
    fig3.tight_layout()
    fig1.savefig('./plots/fd-precicion/' + project_id + '.jpg')
    fig2.savefig('./plots/fd-applicability-to-violations/' + project_id + '.jpg')
    fig3.savefig('./plots/fd-precision-seen/' + project_id + '.jpg')
    plt.clf()

if __name__ == '__main__':
    run_type = sys.argv[1]
    project_id = sys.argv[2]
    eval_user_h(project_id, run_type)