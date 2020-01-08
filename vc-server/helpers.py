from random import randint
from tqdm import tqdm
import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np


def applyUserRepairs(d_dirty, s_in):
    d_rep = d_dirty
    s_df = pd.read_json(s_in, orient='index')

    for idx, row in s_df.iterrows():
        d_rep.iloc[idx] = row

    return d_rep


def discoverCFDs(project_id, current_iter):
    #prev_iter = "{:08x}".format(int('0x'+current_iter, 0) - 1)
    dirty_fp = './store/' + project_id + '/00000001/data.csv'
    clean_fp = './store/' + project_id + '/' + current_iter + '/data.csv'

    process = sp.Popen(['./xplode-master/CTane', dirty_fp, clean_fp, '0.25', '2'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    print(process)
    print(process.returncode)
    output = process.communicate()[0].decode("utf-8")
    print(len(output)/2)
    if process.returncode == 0:
        if output == '[NO CFDS FOUND]':
            return None
        else:
            output = np.array(output.split('\n'))[:-1]
            print(len(output))
            scores = output[:int(len(output)/2)]
            top_cfds = output[int(len(output)/2):]
            return np.array([{'cfd': top_cfds[i], 'score': scores[i]} for i in range(0, len(top_cfds))])
    else:
        return '[ERROR] CFD DISCOVERY FAILURE'


def addNewCfdsToList(top_cfds, project_id):
    print('about to read from file')
    if os.path.isfile('./store/' + project_id + '/discovered_cfds.csv'):
        dscv_df = pd.read_csv('./store/' + project_id + '/discovered_cfds.csv', usecols=['lhs', 'rhs'])
        dscv_df['cfd'] = '(' + dscv_df['lhs'] + ') => ' + dscv_df['rhs']
        print('read from CFD file')
        score_df = pd.read_csv('./store/' + project_id + '/scores.csv', squeeze=True)
        print('read from score file')

        for c in top_cfds:
            pieces = c.cfd[1:].split(') => ')
            lhs = pieces[0]
            rhs = pieces[1]
            if c.cfd not in dscv_df['cfd']:
                dscv_df = dscv_df.concat({'lhs': lhs, 'rhs': rhs, 'cfd': c.cfd}, ignore_index=True)
                score_df = score_df.concat({'score': c.score}, ignore_index=True)
            else :
                idx = dscv_df[dscv_df['cfd'] == c.cfd]
                score_df[idx]['score'] = c.score

        dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
        score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')
    else:
        dscv_cfds = np.array([{'lhs': c['cfd'][1:].split(') => ')[0], 'rhs': c['cfd'][1:].split(') => ')[1], 'cfd': c['cfd']} for c in top_cfds])
        scores = np.array([c['score'] for c in top_cfds])
        dscv_df = pd.DataFrame({'lhs': [c['lhs'] for c in dscv_cfds], 'rhs': [c['rhs'] for c in dscv_cfds], 'cfd': [c['cfd'] for c in dscv_cfds]})
        score_df = pd.DataFrame({'score': scores})

        dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
        score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')


def buildCover(d_rep, top_cfds):
    cover = np.empty(len(d_rep.index), dtype=str)
    print(top_cfds[0]['cfd'])
    #print(top_cfds[0].cfd)
    print([c['cfd'] for c in top_cfds])
    just_cfds = np.array([c['cfd'] for c in top_cfds])
    for idx, row in d_rep.iterrows():
        relevant_cfds = []
        for cfd in just_cfds:
            lhs = np.array(cfd.split(' => ')[0][1:-1].split(', '))
            rhs = cfd.split(' => ')[1]
            applies = True
            for lh in lhs:
                if '=' in lh:
                    lh = np.array(lh.split('='))
                    if row[lh[0]] != lh[1]:
                        applies = False
                        break
            if applies:
                relevant_cfds.append(cfd)
        #relevant_cfds = np.array(relevant_cfds)
        cover[idx] = '; '.join(relevant_cfds)

    d_rep['cover'] = cover
    return d_rep


# TODO; TEMPORARY IMPLEMENTATION
def pickCfds(top_cfds, num_cfds):
    #picked_cfds = np.empty(num_cfds)
    # pick CFDs
    # TEMPORARY IMPLEMENTATION; SHOULD INTEGRATE CHARM HERE
    just_cfds = np.array([c['cfd'] for c in top_cfds if float(c['score']) > 0])
    just_scores = np.array([float(c['score']) for c in top_cfds if float(c['score']) > 0])
    norm_scores = np.array([s/sum(just_scores) for s in just_scores])
    if len(just_cfds) > 0:
        picked_cfds = np.random.choice(just_cfds, num_cfds, p=norm_scores.astype('float64'))
        return picked_cfds
    else:
        return None


def applyCfdList(d_rep, cfdList):
    for cfd in cfdList:
        d_rep = applyCfd(d_rep, cfd)
    return d_rep


def applyCfd(d_rep, cfd):
    lhs = np.array(cfd.split(' => ')[0][1:-1].split(', '))
    rhs = cfd.split(' => ')[1]
    for idx, row in d_rep.iterrows():
        if cfd in row['cover'].split(', '):
            if '=' in rhs:
                rh = np.array(rhs.split('='))
                row[rh[0]] = rh[1]

    return d_rep


# TODO
def buildSample(d_rep, sample_size):
    # TEMPORARY IMPLEMENTATION
    sample = d_rep.sample(n=sample_size)
    return sample

'''def map_csv(csv_file):
    header = list()
    relationships = dict()
    csv_data = list()

    data = csv_file.read().decode('utf-8-sig')
    lines = data.split('\n')
    count = 0
    maxOccurence = 1
    for line in tqdm(lines):
        fields = line.split(',')
        if count == 0:
            for field in fields:
                header.append(field)
        else:
            data_line = list()
            for i in range(0, len(fields)):
                field = dict()
                field.update({'cellValue': fields[i]})
                field.update({'dirtiness': -1})
                data_line.append(field)
                for j in range(0, len(fields)):
                    if i != j:
                        if (header[i], fields[i]) not in relationships.keys():
                            relationships[(header[i], fields[i])] = dict()
                            relationships[(header[i], fields[i])][(header[j], fields[j])] = 1
                        elif (header[j], fields[j]) not in relationships[(header[i], fields[i])].keys():
                            relationships[(header[i], fields[i])][(header[j], fields[j])] = 1
                        else:
                            relationships[(header[i], fields[i])][(header[j], fields[j])] += 1
                            if relationships[(header[i], fields[i])][(header[j], fields[j])] > maxOccurence:
                                maxOccurence = relationships[(header[i], fields[i])][(header[j], fields[j])]
            csv_data.append(data_line)
        count += 1
    pprint.pprint(relationships)
    return header, csv_data, relationships, maxOccurence'''
