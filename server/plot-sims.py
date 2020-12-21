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

def plot_sims(project_id, x_axis):
    user_fd_metadata = pickle.load( open('./store/' + project_id + '/simulated_user_fd_metadata.p', 'rb') )
    system_fd_metadata = pickle.load( open('./store/' + project_id + '/fd_metadata.p', 'rb') )
    with open('./store/' + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    scenario_id = project_info['scenario_id']
    print(scenario_id)

    kL = list()
    target_fd = project_info['scenario']['target_fd']
    user_fd_m = user_fd_metadata[target_fd]
    system_fd_m = system_fd_metadata[target_fd]
    for i in range(0, len(user_fd_m.alpha_history)):
        user_distr = list()
        system_distr = list()
        for step in np.arange(0, 1.0, 0.05):
            print(step)
            print(user_fd_m.alpha_history[i])
            print(user_fd_m.beta_history[i])
            print(system_fd_m.alpha_history[i])
            print(system_fd_m.beta_history[i])
            user_distr.append(pTheta(step, user_fd_m.alpha_history[i], user_fd_m.beta_history[i]))
            system_distr.append(pTheta(step, system_fd_m.alpha_history[i], system_fd_m.beta_history[i]))
        kL.append(st.entropy(pk=user_distr, qk=system_distr))

    fig, ax1 = plt.subplots()
    ax1.set_ylabel('kL Divergence (nats)')
    ax1.set_xlabel('Iteration #' if x_axis == 'iter' else 'Time Elapsed (seconds)')
    ax1.set_title('Scenario #' + scenario_id)

    if x_axis == 'iter':
        ax1.set_xticks(np.arange(0, 36, 6.0))
    ax1.plot([i for i in range(0, len(kL))], kL)
    fig.tight_layout()
    fig.savefig('./plots/sim-plot-kL-' + scenario_id + '-' + x_axis + '.jpg')
    plt.clf()

if __name__ == '__main__':
    plot_sims(sys.argv[1], sys.argv[2])
