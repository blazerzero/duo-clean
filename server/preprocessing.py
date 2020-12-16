import pandas as pd
import numpy as np
import json
from collections import Counter
import random
import subprocess as sp
import re
import string
from tqdm import tqdm
import analyze
import helpers

def makeVioSets(data, support, vios, fd):
    vio_pairs = list()
    vio_trios = list()
    lhs = fd.split(' => ')[0][1:-1].split(', ')
    rhs = fd.split(' => ')[1].split(', ')
    for v in vios:
        for idx1 in [i for i in support if i not in vios]:
            match1 = True
            for lh in lhs:
                if data.at[idx1, lh] != data.at[v, lh]:
                    match1 = False   # idx and v do not have the same LHS
                    break
            if match1 is True:   # if idx and v have the same LHS
                vio_pair = None
                for rh in rhs:
                    if data.at[idx1, rh] != data.at[v, rh]:
                        vio_pair = (idx1, v) if v > idx1 else (v, idx1)
                        break
                if vio_pair is not None and vio_pair not in vio_pairs:
                    vio_pairs.append(vio_pair)

                for idx2 in [j for j in support if j not in vios and j != idx1]:
                    match2 = True
                    for lh in lhs:
                        if data.at[idx2, lh] != data.at[v, lh]:
                            match2 = False   # idx and v do not have the same LHS
                            break
                    if match2 is True:
                        pos_match = True
                        for rh in rhs:
                            if data.at[idx1, rh] != data.at[idx2, rh]:
                                pos_match = False
                                break
                        if pos_match is True:
                            vio_trio_list = sorted([v, idx1, idx2])
                            vio_trio = tuple(vio_trio_list)
                            if vio_trio not in vio_trios:
                                vio_trios.append(vio_trio)
                        
                '''if data.at[idx1, rhs] != data.at[v, rhs]:    # if idx is clean and v is dirty
                    if v > idx1:
                        vio_pair = (idx1, v)
                    else:
                        vio_pair = (v, idx1)
                    if vio_pair not in vio_pairs:
                        vio_pairs.append(vio_pair)
                for idx2 in [j for j in support if j not in vios and j != idx1]:
                    match2 = True
                    for lh in lhs:
                        if data.at[idx2, lh] != data.at[v, lh]:
                            match2 = False   # idx and v do not have the same LHS
                            break
                    if match1 is True and match2 is True:
                        if data.at[idx1, rhs] == data.at[idx2, rhs]:
                            vio_trio_list = sorted([v, idx1, idx2])
                            vio_trio = tuple(vio_trio_list)
                            if vio_trio not in vio_trios:
                                vio_trios.append(vio_trio)'''


    return vio_pairs, vio_trios

def calculateG1Prime(data, fds):
    numerator = 0
    for fd in fds:
        lhs = fd.split(' => ')[0][1:-1].split(', ')
        rhs = fd.split(' => ')[1]
        for i in data.index:
            for j in data.index:
                if i == j:
                    continue
                match = True
                for lh in lhs:
                    if data.at[i, lh] != data.at[j, lh]:
                        match = False
                        break
                if match is True and data.at[i, rhs] != data.at[j, rhs]:
                    numerator += 1
    g1Prime = numerator / (np.square(len(data.index)) - len(data.index))
    return g1Prime

def dataDiff(dirty_df, clean_df):
    diff = pd.DataFrame(columns=clean_df.columns)
    for row in clean_df.index:
        for col in clean_df.columns:
            diff.at[row, col] = dirty_df.at[row, col] == clean_df.at[row, col]
    # print(diff)
    return diff

if __name__ == '__main__':
    with open('scenarios-master.json', 'r') as f:
        scenarios = json.load(f)
    
    all_scenarios_duo = dict()
    all_scenarios_random = dict()
    for s_id, scenario in tqdm(scenarios.items()):
        data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
        g1Prime = calculateG1Prime(data, scenario['cfds'])
        # print(g1Prime)
        if int(s_id) <= 4:
            min_conf = 0.75
            max_ant = 2
            # Restrict hypothesis space to the minimum requirement for still including the FDs of concern in the hypothesis space
            # process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
            # process = sp.Popen(['java -cp metanome-cli-1.1.0.jar:pyro-distro-1.0-SNAPSHOT-distro.jar de.metanome.cli.App --algorithm de.hpi.isg.pyro.algorithms.Pyro --algorithm-config maxArity:2,isFindFds:true,maxFdError:0.20,topKFds:10 --table-key inputFile --header $true --output print --separator , --tables ' + scenario['dirty_dataset']], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   # PYRO
            # clean_process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['clean_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})

        else:
            min_conf = 0.7
            max_ant = 3
            # Loosen parameters of hypothesis space for a bigger hypothesis space
            # process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), '0.7', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
            # process = sp.Popen(['java -cp metanome-cli-1.1.0.jar:pyro-distro-1.0-SNAPSHOT-distro.jar de.metanome.cli.App --algorithm de.hpi.isg.pyro.algorithms.Pyro --algorithm-config maxArity:3,isFindFds:true,maxFdError:0.20,topKFds:10 --table-key inputFile --header $true --output print --separator , --tables ' + scenario['dirty_dataset']], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   # PYRO
            # clean_process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['clean_dataset'], str(len(data.index)), '0.7', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
            #min_conf = 0.7

        process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
        clean_process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['clean_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})   # CFDD for clean h space

        res = process.communicate()
        clean_res = clean_process.communicate()
        # print(res)
        # print(process.returncode)
        if process.returncode == 0:
            output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            fds = [c['cfd'] for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            fds = helpers.buildCompositionSpace(fds, None, data, clean_data, min_conf, max_ant)
            # output = res[0].decode('latin_1')
            # fds = helpers.parseOutputPYRO(output)
            # scenario['hypothesis_space'] = fds
        else:
            fds = list()
            # scenario['hypothesis_space'] = list()

        if clean_process.returncode == 0:
            clean_output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            clean_fds = [c['cfd'] for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            clean_fds = helpers.buildCompositionSpace(clean_fds, None, clean_data, None, min_conf, max_ant)
            # output = res[0].decode('latin_1')
            # fds = helpers.parseOutputPYRO(output)
            # scenario['hypothesis_space'] = fds
        else:
            clean_fds = list()
            # scenario['hypothesis_space'] = list()

        h_space = list()
        for fd in fds:
            h = dict()
            h['cfd'] = fd['cfd']
            h['score'] = 1
            support, vios = helpers.getSupportAndVios(data, clean_data, h['cfd'])
            h['conf'] = (len(support) - len(vios)) / len(support)
            if h['conf'] <= 0.95:
                vio_pairs, vio_trios = makeVioSets(data, support, vios, h['cfd'])
                h['support'] = support
                h['vios'] = vios
                h['vio_pairs'] = vio_pairs
                h['vio_trios'] = vio_trios
                h_space.append(h)

        clean_h_space = list()
        for fd in clean_fds:
            h = dict()
            h['cfd'] = fd['cfd']
            h['score'] = 1
            support, vios = helpers.getSupportAndVios(clean_data, clean_data, h['cfd'])
            h['conf'] = (len(support) - len(vios)) / len(support)
            clean_h_space.append(h)
        
        scenario['min_conf'] = min_conf
        scenario['max_ant'] = max_ant
        scenario['hypothesis_space'] = h_space
        scenario['clean_hypothesis_space'] = clean_h_space

        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)

        diff_df = dataDiff(data, clean_data)
        diff = json.loads(diff_df.to_json(orient='index'))
        scenario['diff'] = diff

        all_scenarios_duo[s_id] = scenario
        s_id_plus_8 = str(int(s_id) + 8)
        if s_id == '0':
            continue
        all_scenarios_random[s_id_plus_8] = scenario.copy()

    all_scenarios = {**all_scenarios_duo, **all_scenarios_random}

    for s_id in all_scenarios.keys():
        print(s_id)
        if int(s_id) == 0 or (int(s_id) >= 1 and int(s_id) <= 8):
            # all_scenarios[s_id]['sampling_method'] = 'DUO'
            all_scenarios[s_id]['update_method'] = 'BAYESIAN'
        else:
            # all_scenarios[s_id]['sampling_method'] = 'RANDOM-PURE'
            all_scenarios[s_id]['update_method'] = 'REINFORCEMENT'

    with open('scenarios.json', 'w') as f:
        json.dump(all_scenarios, f)

    typescripted_scenarios = list()
    for s in all_scenarios.values():
        typescripted_scenarios.append(s)
    with open('./simulators/scenarios.json', 'w') as f:
        json.dump(typescripted_scenarios, f)
