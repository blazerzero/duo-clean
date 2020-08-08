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

def plot_cfd_weights():
    with open('scenarios.json') as f:
        scenarios = json.load(f)
    random_pure_scenarios = [s for s in scenarios.keys() if s['sampling_method'] == 'RANDOM_PURE']
    random_ub_scenarios = [s for s in scenarios.keys() if s['sampling_method'] == 'RANDOM-UB']
    duo_scenarios = [s for s in scenarios.keys() if s['sampling_method'] == 'DUO']

    iterations = [i for i in range(1, 26)]

    project_ids = [d for d in os.listdir('./store') if os.path.isdir(os.path.join('./store/', d))]
    random_pure_weights_lists = list()
    random_ub_weights_lists = list()
    duo_weights_lists = list()
    
    for proj in project_ids:
        with open('./store/' + proj + '/project_info.json') as f:
            project_info = json.load(f)
        cfd_metadata = pickle.load( open('./store/' + proj + '/cfd_metadata.p', 'rb') )
        for c in project_info['cfds']:
            try:
                cfd_m = cfd_metadata[c]
                weights = list()
                current_iter = 1
                for idx, cwh in enumerate(cfd_m['weight_history']):
                    while cwh.iter_num > current_iter:
                        if idx == 0:
                            weights.append(0)
                        else:
                            weights.append(weights[-1])
                        current_iter += 1
                    weights.append(cwh.weight)
                
            except KeyError:
                weights = [0 for i in range(1, 26)]
            if project_info['scenario']['sampling_method'] == 'RANDOM-PURE':
                random_pure_weights_lists.append(weights)
            elif project_info['scenario']['sampling_method'] == 'RANDOM-UB':
                random_ub_weights_lists.append(weights)
            elif project_info['scenario']['sampling_method'] == 'DUO':
                duo_weights_lists.append(weights)
    
    # plot for random pure
    # plot for random ub
    # plot for duo
        


