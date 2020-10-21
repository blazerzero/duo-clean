import pandas as pd
import numpy as np
import json
from collections import Counter
import random
import subprocess as sp

# GET FD SUPPORT AND VIOLATIONS
def getSupportAndVios(data, cfd):
    lhs = cfd.split(' => ')[0][1:-1]
    rhs = cfd.split(' => ')[1]
    patterns = fd2cfd(data, lhs, rhs)
        
    # CODE TO BUILD COVER AND VIOLATION LIST
    support = list()
    violations = list()
    for idx in data.index:
        applies = True
        for lh in lhs.split(', '):

            # If this element of the CFD is constant
            if '=' in lh:
                lh = np.array(lh.split('='))
                if data.at[idx, lh[0]] != lh[1]:     # CFD does not apply to this row
                    applies = False
                    break

        # If this CFD applies to this row
        if applies:
            support.append(idx)
            if lhs.count('=') == len(lhs.split(', ')) and '=' in rhs:
                rh = np.array(rhs.split('='))
                if data.at[idx, rh[0]] != rh[1]:
                    violations.append(idx)
            elif lhs.count('=') == len(lhs.split(', ')) and '=' not in rhs:
                rh_attribute = rhs.split('=')[0]
                applicable_rhv = patterns[lhs].split('=')[1]
                if data.at[idx, rh_attribute] != applicable_rhv:
                     violations.append(idx)
            elif lhs.count('=') < len(lhs.split(', ')):
                applicable_lhs = ''
                for lh in lhs.split(', '):
                    if '=' in lh:
                        applicable_lhs += lh + ', '
                    else:
                        applicable_lhs += lh + '=' + str(data.at[idx, lh]) + ', '
                applicable_lhs = applicable_lhs[:-2]
                applicable_rhs = patterns[applicable_lhs]
                rh = applicable_rhs.split('=')
                if data.at[idx, rh[0]] != rh[1]:
                    violations.append(idx)
        
    print('*** Support and violations built for (' + lhs + ') => ' + rhs + ' ***')
    return support, violations


# CONVERT FD OR PARTIAL CFD TO FULL CFD
def fd2cfd(data, lhs, rhs):
    patterns = dict()
    mappings = dict()

    # Gather all the possible patterns present in the dataset for each pure FD or partial CFD
    for idx in data.index:
        lhspattern = ''
        rhspattern = ''
        for clause in lhs.split(', '):
            if '=' in clause:
                lhspattern += clause + ', '
            else:
                lhspattern += clause + '=' + str(data.at[idx, clause]) + ', '
        lhspattern = lhspattern[:-2]
        if '=' in rhs:
            rhspattern = rhs
        else:
            rhspattern = rhs + '=' + str(data.at[idx, rhs])
        if lhspattern in patterns.keys():
            patterns[lhspattern].append(rhspattern)
            if (lhspattern, rhspattern) in mappings.keys():
                mappings[(lhspattern, rhspattern)].append(idx)
            else:
                mappings[(lhspattern, rhspattern)] = [idx]
        else:
            patterns[lhspattern] = [rhspattern]
            mappings[(lhspattern, rhspattern)] = [idx]
    print('*** Patterns and mappings built for (' + lhs + ') => ' + rhs + ' ***')

    # Pick RHS patterns for each LHS from these candidates
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [k for k, v in get_mode.items() if v == max(list(counts.values()))]
        # pprint('All RHS patterns for' + key + ':' + repr(patterns[key]))

        # If there is only one top RHS pattern for this LHS, pick it
        if len(patterns[key]) == 1:
            patterns[key] = patterns[key].pop()
        else:
            random_idx = random.randint(0, len(patterns[key])-1)
            patterns[key] = patterns[key][random_idx]
        # print('*** RHS pattern picked ***')

    return patterns

def makeVioPairs(data, support, vios, cfd):
    vio_pairs = list()
    lhs = cfd.split(' => ')[0][1:-1].split(', ')
    rhs = cfd.split(' => ')[1]
    for v in vios:
        for idx in [i for i in support if i not in vios]:
            match = True
            for lh in lhs:
                if data.at[idx, lh] != data.at[v, lh]:
                    match = False   # idx and v do not have the same LHS
                    break
            if match is True:   # if idx and v have the same LHS
                if idx not in vios and data.at[idx, rhs] != data.at[v, rhs]:    # if idx is clean and v is dirty
                    if v > idx:
                        vio_pair = (idx, v)
                    else:
                        vio_pair = (v, idx)
                    if vio_pair not in vio_pairs:
                        vio_pairs.append(vio_pair)

    return vio_pairs

if __name__ == '__main__':
    with open('scenarios-master.json', 'r') as f:
        scenarios_list = json.load(f)
    
    for s_id, scenario in scenarios_list.items():
        data = pd.read_csv(scenario['dirty_dataset'], keep_default_na=False)
        process = sp.Popen(['./data/cfddiscovery/CFDD', scenario['dirty_dataset'], str(len(data.index)), '0.8', '3'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # CFDD
        res = process.communicate()
        if process.returncode == 0:
            output = res[0].decode('latin_1').replace(',]', ']').replace('\r', '').replace('\t', '').replace('\n', '')
            cfds = json.loads(output, strict=False)['cfds']
            scenario['hypothesis_space'] = cfds
        else:
            scenario['hypothesis_space'] = list()

        for h in scenario['hypothesis_space']:
            cfd = h['cfd']
            support, vios = getSupportAndVios(data, cfd)
            vio_pairs = makeVioPairs(data, support, vios, cfd)
            h['support'] = support
            h['vios'] = vios
            h['vio_pairs'] = vio_pairs

    with open('scenarios.json', 'w') as f:
        json.dump(scenarios_list, f, indent=4)
