import pandas as pd
import numpy as np
import json
import subprocess as sp
from tqdm import tqdm
import helpers
from rich.console import Console

console = Console()

def dataDiff(dirty_df, clean_df):
    diff = pd.DataFrame(columns=clean_df.columns)
    for row in clean_df.index:
        for col in clean_df.columns:
            diff.at[row, col] = dirty_df.at[row, col] == clean_df.at[row, col]
    return diff

if __name__ == '__main__':
    with open('scenarios-master.json', 'r') as f:
        scenarios = json.load(f)

    all_scenarios = dict()
    for s_id, scenario in tqdm(scenarios.items()):
        data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)
        min_conf = 0.001
        max_ant = 3

        process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
        clean_process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['clean_dataset'], str(len(data.index)), str(min_conf), str(max_ant)], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})   # CFDD for clean h space

        res = process.communicate()
        clean_res = clean_process.communicate()
        if process.returncode == 0:
            output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            fds = [c['cfd'] for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            
            fds = helpers.buildCompositionSpace(fds, None, data, clean_data, min_conf, max_ant)
        else:
            fds = list()

        if clean_process.returncode == 0:
            clean_output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            # NOTE: THIS SHOULD BE CLEAN_OUTPUT IN THE LINE BELOW, NOT OUTPUT
            clean_fds = [c['cfd'] for c in json.loads(output, strict=False)['cfds'] if '=' not in c['cfd'].split(' => ')[0] and '=' not in c['cfd'].split(' => ')[1] and c['cfd'].split(' => ')[0] != '()']
            clean_fds = helpers.buildCompositionSpace(clean_fds, None, clean_data, None, min_conf, max_ant)
        else:
            clean_fds = list()
        
        intersecting_fds = list(set([f['cfd'] for f in fds]).intersection(set([c['cfd'] for c in clean_fds])))

        h_space = list()
        for fd in fds:
            if fd['cfd'] not in intersecting_fds:
                continue
            h = dict()
            h['cfd'] = fd['cfd']
            h['score'] = 1
            support, vios = helpers.getSupportAndVios(data, clean_data, h['cfd'])
            vio_pairs = helpers.getPairs(data, support, h['cfd'])
            h['conf'] = (len(support) - len(vios)) / len(support)
            h['support'] = support
            h['vios'] = vios
            h['vio_pairs'] = vio_pairs
            h_space.append(h)

        clean_h_space = list()
        for fd in clean_fds:
            if fd['cfd'] not in intersecting_fds:
                continue
            h = dict()
            h['cfd'] = fd['cfd']
            h['score'] = 1
            support, vios = helpers.getSupportAndVios(clean_data, None, h['cfd'])
            h['conf'] = (len(support) - len(vios)) / len(support)
            # console.log(fd['cfd'])
            # console.log(vios)
            clean_h_space.append(h)
        
        scenario['min_conf'] = min_conf
        scenario['max_ant'] = max_ant
        scenario['hypothesis_space'] = h_space
        scenario['clean_hypothesis_space'] = clean_h_space
        console.log([(h['cfd'], h['conf']) for h in scenario['hypothesis_space']])
        console.log([(h['cfd'], h['conf']) for h in scenario['clean_hypothesis_space']])
        scenario['target_fd'] = next(f['cfd'] for f in scenario['hypothesis_space'] if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(scenario['target_fd'].split(' => ')[0][1:-1].split(', ')) and set(f['cfd'].split(' => ')[1].split(', ')) == set(scenario['target_fd'].split(' => ')[1].split(', ')))
        formatted_alt_h = list()
        for alt_fd in scenario['alt_h']:
            fd = next(f['cfd'] for f in scenario['hypothesis_space'] if set(f['cfd'].split(' => ')[0][1:-1].split(', ')) == set(alt_fd.split(' => ')[0][1:-1].split(', ')) and set(f['cfd'].split(' => ')[1].split(', ')) == set(alt_fd.split(' => ')[1].split(', ')))
            formatted_alt_h.append(fd)
        scenario['alt_h'] = formatted_alt_h

        clean_data = pd.read_csv(scenario['clean_dataset'], keep_default_na=False)

        diff_df = dataDiff(data, clean_data)
        diff = json.loads(diff_df.to_json(orient='index'))
        scenario['diff'] = diff

        all_scenarios[s_id] = scenario
        all_scenarios[s_id]['sampling_method'] = 'DUO'
        all_scenarios[s_id]['update_method'] = 'BAYESIAN'

    with open('scenarios.json', 'w') as f:
        json.dump(all_scenarios, f)
