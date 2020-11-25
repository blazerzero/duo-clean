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
    rhs = fd.split(' => ')[1]
    for v in vios:
        for idx1 in [i for i in support if i not in vios]:
            match1 = True
            for lh in lhs:
                if data.at[idx1, lh] != data.at[v, lh]:
                    match1 = False   # idx and v do not have the same LHS
                    break
            if match1 is True:   # if idx and v have the same LHS
                if data.at[idx1, rhs] != data.at[v, rhs]:    # if idx is clean and v is dirty
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
                                vio_trios.append(vio_trio)


    return vio_pairs, vio_trios

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
        if int(s_id) <= 4:
            # Restrict hypothesis space to the minimum requirement for still including the FDs of concern in the hypothesis space
            # process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), '0.7', '2'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
            process = sp.Popen(['java -cp metanome-cli-1.1.0.jar:pyro-distro-1.0-SNAPSHOT-distro.jar de.metanome.cli.App --algorithm de.hpi.isg.pyro.algorithms.Pyro --algorithm-config maxArity:2,isFindFds:true,maxFdError:0.20,topKFds:5 --table-key inputFile --header $true --output print --separator , --tables ' + scenario['dirty_dataset']], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   # PYRO

        else:
            # Loosen parameters of hypothesis space for a bigger hypothesis space
            # process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), '0.5', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
            process = sp.Popen(['java -cp metanome-cli-1.1.0.jar:pyro-distro-1.0-SNAPSHOT-distro.jar de.metanome.cli.App --algorithm de.hpi.isg.pyro.algorithms.Pyro --algorithm-config maxArity:2,isFindFds:true,maxFdError:0.20,topKFds:10 --table-key inputFile --header $true --output print --separator , --tables ' + scenario['dirty_dataset']], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   # PYRO

        res = process.communicate()
        # print(res)
        # print(process.returncode)
        if process.returncode == 0:
            # output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            # fds = [c for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            output = res[0].decode('latin_1')
            fds = helpers.parseOutputPYRO(output)
            # scenario['hypothesis_space'] = fds
        else:
            fds = list()
            # scenario['hypothesis_space'] = list()

        h_space = list()
        for fd in fds:
            h = dict()
            h['cfd'] = fd
            h['score'] = 1
            support, vios = helpers.getSupportAndVios(data, fd)
            vio_pairs, vio_trios = makeVioSets(data, support, vios, fd)
            h['support'] = support
            h['vios'] = vios
            h['vio_pairs'] = vio_pairs
            h['vio_trios'] = vio_trios
            h_space.append(h)
        
        scenario['hypothesis_space'] = h_space

        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
        '''clean_process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['clean_dataset'], str(len(clean_data.index)), '0.7', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
        clean_res = clean_process.communicate()
        if clean_process.returncode == 0:
            clean_output = clean_res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            clean_fds = [c for c in json.loads(clean_output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            scenario['clean_hypothesis_space'] = clean_fds
        else:
            scenario['clean_hypothesis_space'] = list()

        for h in scenario['clean_hypothesis_space']:
            fd = "".join(filter(lambda char: char in string.printable, h['cfd']))
            h['conf'] = 1
            support, vios = getSupportAndVios(data, fd)
            vio_pairs, vio_trios = makeVioSets(data, support, vios, fd)
            h['support'] = support
            h['vios'] = vios
            h['vio_pairs'] = vio_pairs
            h['vio_trios'] = vio_trios'''

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
        if int(s_id) == 0:
            print('DUO')
            all_scenarios[s_id]['sampling_method'] = 'DUO'
        elif int(s_id) >= 1 and int(s_id) <= 8:
            print('DUO')
            all_scenarios[s_id]['sampling_method'] = 'DUO'
        else:
            print('RANDOM-PURE')
            all_scenarios[s_id]['sampling_method'] = 'RANDOM-PURE'

    with open('scenarios.json', 'w') as f:
        json.dump(all_scenarios, f)
