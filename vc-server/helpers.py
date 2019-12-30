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
    prev_iter = current_iter - 1
    dirty_fp = './store/' + project_id + '/' + prev_iter + '/data.csv'
    clean_fp = './store/' + project_id + '/' + current_iter + '/data.csv'

    process = sp.Popen(['./xplode-master/CTane', dirty_fp, clean_fp, '0.25', '2'], stdout=sp.PIPE).wait()
    print(process.communicate()[0])
    print(process.returncode)
    if process.returncode == 0:
        scores = np.array(process.communicate()[0].split('\n')[0])
        top_cfds = np.array(process.communicate()[0].split('\n')[1:])
        return np.array([{cfd: c.cfd, score: c.score} for c in np.nditer(top_cfds)])
    else:
        return '[ERROR] CFD DISCOVERY FAIL'

def addNewCfdsToList(top_cfds, project_id):
    discovered_c_s = np.loadtxt('./store/' + project_id + '/discovered_cfds.txt')
    discovered_c_s = np.array([json.loads(s) for s in np.nditer(discovered_c_s)])
    discovered_cfds = [c.cfd for c in np.nditer(discovered_c_s)]

    for c in np.nditer(top_cfds):
        if c.cfd not in discovered_cfds:
            discovered_c_s = np.append(discovered_c_s, c)
        else:
            idx = np.where(discovered_c_s.cfd == c.cfd)
            # TEMPORARY IMPLEMENTATION
            discovered_c_s[idx].score = c.score     # INSERT ITERATIVE SCORE UPDATING FUNCTION HERE

    np.savetxt('./store/' + project_id + '/discovered_cfds.txt', discovered_c_s)
    #return discovered_c_s

def buildCover(d_rep, top_cfds):
    cover = np.empty(len(d_rep.index))
    just_cfds = np.array([c.cfd for c in np.nditer(top_cfds)])
    for idx, row in d_rep.iterrows():
        relevant_cfds = []
        for cfd in np.nditer(just_cfds):
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
        relevant_cfds = np.array(relevant_cfds)
        cover[idx] = relevant_cfds

    d_rep['cover'] = cover
    return d_rep

# TODO
def pickCfds(top_cfds, num_cfds):
    #picked_cfds = np.empty(num_cfds)
    # pick CFDs
    # TEMPORARY IMPLEMENTATION
    just_cfds = np.array([c.cfd for c in np.nditer(top_cfds)])
    just_scores = np.array([c.score for c in np.nditer(top_cfds)])
    picked_cfds = np.random.choice(just_cfds, num_cfds, p=just_scores)
    return picked_cfds

def applyCfdList(d_rep, cfdList):
    for cfd in np.nditer(cfdList):
        d_rep = applyCfd(d_rep, cfd)
    return d_rep

def applyCfd(d_rep, cfd):
    lhs = np.array(cfd.split(' => ')[0][1:-1].split(', '))
    rhs = cfd.split(' => ')[1]
    for idx, row in d_rep.iterrows():
        if cfd in row['cover']:
            if '=' in rhs:
                rh = np.array(rhs.split('='))
                row[rh[0]] = rh[1]

    return d_rep

# TODO
def buildSample(d_rep, sample_size):
    # TEMPORARY IMPLEMENTATION
    sample = d_rep.sample(n=sample_size, random_state=1)
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
