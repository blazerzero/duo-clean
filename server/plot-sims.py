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

class FDMeta(object):
    def __init__(self, fd, theta, p_theta, a, b, support, vios, vio_pairs):
        self.lhs = fd.split(' => ')[0][1:-1].split(', ')
        self.rhs = fd.split(' => ')[1].split(', ')
        self.theta = theta
        self.theta_history = [theta]
        self.p_theta = p_theta
        self.p_theta_history = [p_theta]
        self.p_X_given_theta = None
        self.p_X_given_theta_history = []
        self.alpha = a
        self.alpha_history = [a]
        self.beta = b
        self.beta_history = [b]
        self.support = support
        self.vios = vios
        self.vio_pairs = vio_pairs

def pTheta(theta, a, b):
    return (math.pow(theta, (a-1)) * math.pow((1-theta), (b-1))) / sc.beta(a, b)

def plot_sims(project_ids, x_axis):
    avg_across_runs_kL = pd.DataFrame(columns=range(0, 101), index=range(0, len(project_ids)))
    avg_across_runs_conf_diff_user = pd.DataFrame(columns=range(0, 101), index=range(0, len(project_ids)))
    avg_across_runs_conf_diff_sys = pd.DataFrame(columns=range(0, 101), index=range(0, len(project_ids)))
    for project_id in project_ids:
        user_fd_metadata = pickle.load( open('./store/' + project_id + '/simulated_user_fd_metadata.p', 'rb') )
        system_fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
        current_iter = pickle.load( open('./store/' + project_id + '/current_iter.p', 'rb') )
        with open('./store/' + project_id + '/project_info.json', 'r') as f:
            project_info = json.load(f)
        scenario_id = project_info['scenario_id']
        clean_hypothesis_space = project_info['scenario']['clean_hypothesis_space']
        print(scenario_id)

        kL = pd.DataFrame(columns=range(1, current_iter+1), index=list(user_fd_metadata.keys()))
        conf_diff_user = pd.DataFrame(columns=range(1, current_iter+1), index=list(user_fd_metadata.keys()))
        conf_diff_sys = pd.DataFrame(columns=range(1, current_iter+1), index=list(user_fd_metadata.keys()))
        target_fd = project_info['scenario']['target_fd']
        # target_fd = '(owner, ownertype) => type, manager'
        user_fd_metadata = {k: v for k, v in user_fd_metadata.items() if k == target_fd}
        print(user_fd_metadata)
        system_fd_metadata = {k: v for k, v in system_fd_metadata.items() if k == target_fd}
        print(system_fd_metadata)
        for fd in user_fd_metadata.keys():
            fd_kL = list()
            fd_conf_diff_user = list()
            fd_conf_diff_sys = list()
            for i in range(0, len(user_fd_metadata[fd].alpha_history)):
                user_distr = list()
                system_distr = list()
                print('iter:', i)
                print('a/b\'s:', user_fd_metadata[fd].alpha_history[i], user_fd_metadata[fd].beta_history[i], system_fd_metadata[fd].alpha_history[i], system_fd_metadata[fd].beta_history[i])
                for step in np.arange(0, 1.0, 0.05):
                    user_pTheta = pTheta(step, user_fd_metadata[fd].alpha_history[i], user_fd_metadata[fd].beta_history[i])
                    system_pTheta = pTheta(step, system_fd_metadata[fd].alpha_history[i], system_fd_metadata[fd].beta_history[i])
                    # print('pThetas:', user_pTheta, system_pTheta)
                    if user_pTheta > 0 and system_pTheta == 0:
                        continue
                    user_distr.append(user_pTheta)
                    system_distr.append(system_pTheta)
                iter_kL = st.entropy(pk=user_distr, qk=system_distr)

                iter_a_user = user_fd_metadata[fd].alpha_history[i]
                iter_b_user = user_fd_metadata[fd].beta_history[i]
                iter_theta_user = iter_a_user / (iter_a_user + iter_b_user)

                iter_a_sys = system_fd_metadata[fd].alpha_history[i]
                iter_b_sys = system_fd_metadata[fd].beta_history[i]
                iter_theta_sys = iter_a_sys / (iter_a_sys + iter_b_sys)

                clean_fd = next(i for i in clean_hypothesis_space if i['cfd'] == fd)

                iter_conf_diff_user = abs(iter_theta_user - clean_fd['conf'])
                iter_conf_diff_sys = abs(iter_theta_sys - clean_fd['conf'])
                print(iter_kL)
                fd_kL.append(iter_kL)
                fd_conf_diff_user.append(iter_conf_diff_user)
                fd_conf_diff_sys.append(iter_conf_diff_sys)
            # print(fd_kL)
            kL.loc[fd] = fd_kL
            conf_diff_user.loc[fd] = fd_conf_diff_user
            conf_diff_sys.loc[fd] = fd_conf_diff_sys

        # print(kL)

        # avg_kL = kL.mean(axis=0, skipna=True).tolist()
        avg_across_runs_kL.loc[project_id] = kL.mean(axis=0, skipna=True).tolist()
        avg_across_runs_conf_diff_user.loc[project_id] = conf_diff_user.mean(axis=0, skipna=True).tolist()
        avg_across_runs_conf_diff_sys.loc[project_id] = conf_diff_sys.mean(axis=0, skipna=True).tolist()

    avg_kL = avg_across_runs_kL.mean(axis=0, skipna=True).tolist()
    avg_conf_diff_user = avg_across_runs_conf_diff_user.mean(axis=0, skipna=True).tolist()
    avg_conf_diff_sys = avg_across_runs_conf_diff_sys.mean(axis=0, skipna=True).tolist()
    # print(avg_kL)

    fig1, ax1 = plt.subplots()
    ax1.set_ylabel('kL Divergence (nats)')
    ax1.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1.set_title('Scenario #' + scenario_id)

    if x_axis == 'iter':
        ax1.set_xticks(np.arange(0, 110, 10.0))
    ax1.plot([i for i in range(0, len(avg_kL))], avg_kL)
    fig1.tight_layout()
    fig1.savefig('./plots/kL-out.jpg')
    plt.clf()

    fig2, ax2 = plt.subplots()
    ax2.set_ylabel('Distance Between User and Ground Truth FD Confidence')
    ax2.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax2.set_title('Scenario #' + scenario_id)

    if x_axis == 'iter':
        ax2.set_xticks(np.arange(0, 110, 10.0))
    ax2.plot([i for i in range(0, len(avg_conf_diff_user))], avg_conf_diff_user)
    fig2.tight_layout()
    fig2.savefig('./plots/conf-diff-user-out.jpg')
    plt.clf()

    fig3, ax3 = plt.subplots()
    ax3.set_ylabel('Distance Between System and Ground Truth FD Confidence')
    ax3.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax3.set_title('Scenario #' + scenario_id)

    if x_axis == 'iter':
        ax3.set_xticks(np.arange(0, 110, 10.0))
    ax3.plot([i for i in range(0, len(avg_conf_diff_sys))], avg_conf_diff_sys)
    fig3.tight_layout()
    fig3.savefig('./plots/conf-diff-sys-out.jpg')
    plt.clf()

if __name__ == '__main__':
    plot_sims(sys.argv[1:-1], sys.argv[-1])
