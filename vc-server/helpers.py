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
    top_cfds = np.array(['[ERROR] CFD DISCOVERY FAIL'])
    if process.returncode == 0:
        top_cfds = np.array(process.communicate()[0].split('\n'))
    return top_cfds

def addNewCfdsToList(top_cfds, project_id):
    discovered_cfds = np.loadtxt('./store/' + project_id + '/discovered_cfds.txt')
    f = open('./store/' + project_id + '/discovered_cfds.txt', a)
    for cfd in np.nditer(top_cfds):
        if cfd not in discovered_cfds:
            f.write(cfd + '\n')
            discovered_cfds = np.append(discovered_cfds, cfd)
    f.close()
    return discovered_cfds

def buildCover(d_rep, discovered_cfds):
    return

def pickCfd(top_cfds):
    return

def applyCfd(d_rep, cfd):
    return

def buildSample(d_rep):
    return

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
