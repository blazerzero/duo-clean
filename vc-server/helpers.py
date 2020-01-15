from random import randint
from tqdm import tqdm
import pprint
import os
import json
import subprocess as sp
import pandas as pd
import numpy as np
import sys
import pickle
from collections import Counter
from pprint import pprint

sys.path.insert(0, './charm/keywordSearch/charm')
import charm


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
        dscv_df = pd.read_csv('./store/' + project_id + '/discovered_cfds.csv', usecols=['lhs', 'rhs'], keep_default_na=False)
        dscv_df['cfd'] = '(' + dscv_df['lhs'] + ') => ' + dscv_df['rhs']
        print('read from CFD file')
        score_df = pd.read_csv('./store/' + project_id + '/scores.csv', squeeze=True, keep_default_na=False)
        print('read from score file')

        for c in top_cfds:
            pieces = c['cfd'][1:].split(') => ')
            lhs = pieces[0]
            rhs = pieces[1]
            if c['cfd'] not in dscv_df['cfd']:
                dscv_df = dscv_df.append({'lhs': lhs, 'rhs': rhs, 'cfd': c['cfd']}, ignore_index=True)
                score_df = score_df.append({'score': c['score']}, ignore_index=True)
            else :
                idx = dscv_df[dscv_df['cfd'] == c.cfd]
                score_df[idx]['score'] = c.score

        dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
        score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')

        # TODO: uncomment when Charm is integrated
        #receiver = pickle.load( open('./store/' + project_id + '/charm_receiver.p', 'rb') )
        # receiver = charm.updateReceiver(receiver, project_id)   #TODO; implement updateReceiver; THIS IS WHERE THE RECEIVER AND STRATEGY GET UPDATED WITH THE NEW DATA
        #pickle.dump(receiver, open('./store/' + project_id + '/charm_receiver.p', 'wb'))
        #return receiver

    else:
        dscv_cfds = np.array([{'lhs': c['cfd'][1:].split(') => ')[0], 'rhs': c['cfd'][1:].split(') => ')[1], 'cfd': c['cfd']} for c in top_cfds])
        scores = np.array([c['score'] for c in top_cfds])
        dscv_df = pd.DataFrame({'lhs': [c['lhs'] for c in dscv_cfds], 'rhs': [c['rhs'] for c in dscv_cfds], 'cfd': [c['cfd'] for c in dscv_cfds]})
        score_df = pd.DataFrame({'score': scores})

        dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
        score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')

        # TODO: uncomment when Charm is integrated
        #receiver = charm.prepareReceiver(project_id)
        #pickle.dump( receiver, open('./store/' + project_id + '/charm_receiver.p', 'wb') )
        #return receiver


def buildCover(d_rep, top_cfds):
    cover = np.empty(len(d_rep.index), dtype=str)
    print(top_cfds[0]['cfd'])
    #print(top_cfds[0].cfd)
    print([c['cfd'] for c in top_cfds])
    just_cfds = np.array([c['cfd'] for c in top_cfds])
    for idx, row in d_rep.iterrows():
        relevant_cfds = []
        for cfd in just_cfds:
            lhs = cfd.split(' => ')[0][1:-1]
            rhs = cfd.split(' => ')[1]
            applies = True
            for lh in lhs.split(', '):
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


# TODO; TEMPORARY IMPLEMENTATION; charmPickCfds will be used eventually
def pickCfds(top_cfds, num_cfds):
    just_cfds = np.array([c['cfd'] for c in top_cfds if float(c['score']) > 0])
    just_scores = np.array([float(c['score']) for c in top_cfds if float(c['score']) > 0])
    norm_scores = np.array([s/sum(just_scores) for s in just_scores])
    if len(just_cfds) > 0:
        picked_cfds = np.random.choice(just_cfds, num_cfds, p=norm_scores.astype('float64'))
        return picked_cfds
    else:
        return None

def charmPickCfds(receiver, query, sample_size):
    return charm.getRules(receiver, query, sample_size)

# TODO: This will be the final version of applyCfdList
#def applyCfdList(project_id, d_rep, cfd_list, cfd_id_list):
#    for i in range(0, len(cfd_list)):
#        d_rep = applyCfd(project_id, d_rep, cfd_list[i], cfd_id_list[i])
#    return d_rep

# TODO: This version of applyCfdList will be removed
def applyCfdList(project_id, d_rep, cfd_list):
    for cfd in cfd_list:
        d_rep = applyCfd(project_id, d_rep, cfd)
    return d_rep

#TODO: Figure out how to apply CFDs with no "=" sign on the RHS, and remove None from cfd_id and receiver when integrating
def applyCfd(project_id, d_rep, cfd, cfd_id=None, receiver=None):
    #mod_count = 0
    #lhs = np.array(cfd.split(' => ')[0][1:-1].split(', '))
    #rhs = cfd.split(' => ')[1]
    tuple_weights = pd.read_pickle('./store/' + project_id + '/tuple_weights.p')
    for idx, row in d_rep.iterrows():
        mod_count = 0
        if cfd in row['cover'].split(', '):
            lhs = cfd.split(' => ')[0][1:-1]
            rhs = cfd.split(' => ')[1]
            if '=' in rhs:
                rh = np.array(rhs.split('='))
                if row[rh[0]] != rh[1]:
                    row[rh[0]] = rh[1]
                    mod_count += 1
        tuple_weights.at[idx, 'weight'] += mod_count

    #charm.reinforce(receiver, cfd_id, mod_count)        # reinforcement value is equal to the number of modifications made to the dataset by this CFD (i.e. number of rows modified)
    return d_rep


def reinforceTuplesBasedOnContradiction(project_id, current_iter, d_latest):
    tuple_weights = pd.read_pickle('./store/' + project_id + '/tuple_weights.p')
    value_mapper = pickle.load( open('./store/' + project_id + '/value_mapper.p', 'rb') )
    prev_iter = "{:08x}".format(int('0x' + current_iter, 0) - 1)
    # TODO: Implement checking previous value spread and value disagreement
    value_spread = pickle.load( open('./store/' + project_id + '/' + prev_iter + '/value_spread.p', 'rb') )
    value_disagreement = pickle.load( open('./store/' + project_id + '/' + prev_iter + '/value_disagreement.p', 'rb') )
    for idx in d_latest.index:
        reinforcementValue = 0
        for col in d_latest.columns:
            value_mapper[idx][col].append(d_latest.at[idx, col])
            num_unique = len(set(value_mapper[idx][col]))
            vspr_d = 0       # value spread delta (change in value spread from last iteration)
            if num_unique > value_spread[idx][col]:
                vspr_d = 1
            value_spread[idx][col] = num_unique

            cell_values = Counter(value_mapper[idx][col])
            num_occurrences_mode = cell_values.most_common(1)[0][1]
            new_vdis = 1 - (num_occurrences_mode/len(value_mapper[idx][col]))   # new value disagreement (value disagreement for the current iteration)
            vdis_d = new_vdis - value_disagreement[idx][col]            # value disagreement delta (change in value disagreement from last iteration; set to 0 if less than 0 so as to disallow negative tuple weights)
            if vdis_d < 0:
                vdis_d = 0
            value_disagreement[idx][col] = new_vdis

            reinforcementValue += (vspr_d + new_vdis + vdis_d)     # add change in value spread, new value disagreement, and change in value disagreement from last iteration

            #mode = cell_values.most_common(1)[0][0]
            #num_occurrences_mode = value_mapper[idx][col].count(most_common)
            #current_value_spread = num_unique/len(value_mapper[idx][col])
            #current_value_disagreement = 1 - (num_occurrences_mode/len(value_mapper[idx][col]))
            #reinforcementValue += current_value_spread
            #reinforcementValue += current_value_disagreement

        tuple_weights.at[idx, 'weight'] += reinforcementValue

    tuple_weights['weight'] = tuple_weights['weight']/tuple_weights['weight'].sum()
    print('Tuple weights:')
    pprint(tuple_weights)
    print()
    #pprint(value_mapper)
    #pprint(value_spread)
    #pprint(value_disagreement)
    tuple_weights.to_pickle('./store/' + project_id + '/tuple_weights.p')
    pickle.dump( value_mapper, open('./store/' + project_id + '/value_mapper.p', 'wb') )
    pickle.dump( value_spread, open('./store/' + project_id + '/' + current_iter + '/value_spread.p', 'wb') )
    pickle.dump( value_disagreement, open('./store/' + project_id + '/' + current_iter + '/value_disagreement.p', 'wb') )




# TODO
def buildSample(d_rep, sample_size, project_id):
    # TEMPORARY IMPLEMENTATION
    tuple_weights = pd.read_pickle('./store/' + project_id + '/tuple_weights.p')
    chosen_tups = tuple_weights.sample(n=sample_size, weights='weight')     # tuples with a larger weight (a.k.a. larger value in the 'weight' column of tuple_weights) are more likely to be chosen
    print('Chosen example indexes:')
    pprint(chosen_tups.index)
    sample = d_rep.iloc[chosen_tups.index]
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
