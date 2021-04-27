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
    for h in user_h_history:
        fd = h['value']
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
        vio_match_rate = len([v for v in vios in v in target_vios]) / len(target_vios)
        user_h_vio_match_history.append(vio_match_rate)
    
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    ax1.set_xticks(np.arange(0, 15, 3))
    ax2.set_xticks(np.arange(0, 15, 3))
    ax1.set_ylim([0, 1])
    ax2.set_ylim([0, 1])

    ax1.plot([i['iter_num'] for i in user_h_history], user_h_conf_history)
    ax2.plot([i['iter_num'] for i in user_h_history], user_h_vio_match_history)

    ax1.set_xlabel('Iteration #')
    ax1.set_ylabel('FD Confidence')
    ax1.set_title('Hypothesis Strength Over the Interaction')
    ax2.set_xlabel('Iteration #')
    ax2.set_ylabel('Match Rate')
    ax2.set_title("Applicability of the User's Hypothesis to the Ground Truth Violations in the Data")

    fig1.tight_layout()
    fig2.tight_layout()
    fig1.savefig('./plots/h_strength.jpg')
    fig2.savefig('./plots/h_applicability_vios.jpg')
    plt.clf()

if __name__ == '__main__':
    run_type = sys.argv[1]
    project_id = sys.argv[2]
    func = sys.argv[3]
    eval_user_h(project_id, run_type)