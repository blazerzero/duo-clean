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
    output = process.communicate()[0].decode("utf-8")
    if process.returncode == 0:
        if output == '[NO CFDS FOUND]':
            return None
        else:
            output = np.array(output.split('\n'))[:-1]
            scores = output[:int(len(output)/2)]
            top_cfds = output[int(len(output)/2):]
            return np.array([{'cfd': top_cfds[i], 'score': scores[i]} for i in range(0, len(top_cfds))])
    else:
        return '[ERROR] CFD DISCOVERY FAILURE'


def addNewCfdsToList(top_cfds, project_id, receiver=None):
    dscv_df = None
    score_df = None
    #if os.path.isfile('./store/' + project_id + '/discovered_cfds.csv'):
    #    dscv_df = pd.read_csv('./store/' + project_id + '/discovered_cfds.csv', usecols=['lhs', 'rhs'], keep_default_na=False)
    #    dscv_df['cfd'] = '(' + dscv_df['lhs'] + ') => ' + dscv_df['rhs']
    #    score_df = pd.read_csv('./store/' + project_id + '/scores.csv', squeeze=True, keep_default_na=False)

    #    for c in top_cfds:
    #        pieces = c['cfd'][1:].split(') => ')
    #        lhs = pieces[0]
    #        rhs = pieces[1]
    #        if c['cfd'] not in dscv_df['cfd']:
    #            dscv_df = dscv_df.append({'lhs': lhs, 'rhs': rhs, 'cfd': c['cfd']}, ignore_index=True)
    #            score_df = score_df.append({'score': c['score']}, ignore_index=True)
    #        else :
    #            idx = dscv_df[dscv_df['cfd'] == c['cfd']]
    #            score_df.at[idx, 'score'] = c['score']

    #    dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
    #    score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')

    #    receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
        # TODO: Update receiver stuff to account for new CFDs
    #    receiver = charm.updateReceiver(receiver, top_cfds)
    #    pickle.dump(receiver, open('./store/' + project_id + '/receiver.p', 'wb'))

    if os.path.isfile('./store/' + project_id + '/cfd_metadata.p'):
        cfd_metadata = pd.read_pickle('./store/' + project_id + '/cfd_metadata.p')
        receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
        for c in [tc for tc in top_cfds if tc['score'] > 0]:
            exists = False
            for idx, row in cfd_metadata:
                lhs = c['cfd'].split(' => ')[0][1:-1]
                rhs = c['cfd'].split(' => ')[1]
                if cfd_metadata['lhs'] == lhs and cfd_metadata['rhs'] == rhs:
                    exists = True
                    row['num_found'] += 1
                    charm.reinforce(receiver, idx, c['score']/row['num_found'])
                    break
            if not exists:
                df = pd.DataFrame({'lhs': [lhs], 'rhs': [rhs], 'num_found': [1]})
                cfd_metadata.append(df, ignore_index=True)
                charm.updateReceiver(receiver, [c])
                charm.reinforce(receiver, len(cfd_metadata)-1, c['score'])

        pickle.dump(receiver, open('./store/' + project_id + '/receiver.p', 'wb'))
        cfd_metadata.to_pickle('./store/' + project_id + '/cfd_metadata.p')

    else:
        cfd_metadata = pd.DataFrame(index=range(0, len(top_cfds)), columns=['lhs', 'rhs', 'num_found'])
        cfd_metadata['lhs'] = [c['cfd'].split(' => ')[0][1:-1] for c in top_cfds if c['score'] > 0]
        cfd_metadata['rhs'] = [c['cfd'].split(' => ')[1] for c in top_cfds if c['score'] > 0]
        cfd_metadata['num_found'] = 1

        scores = [c['score'] for c in top_cfds]

        receiver = charm.prepareReceiver(project_id, top_cfds)
        for idx in cfd_metadata.index:
            charm.reinforce(receiver, idx, scores[idx])

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
        cfd_metadata.to_pickle('./store/' + project_id + '/cfd_metadata.p')


    #else:
    #    dscv_cfds = np.array([{'lhs': c['cfd'][1:].split(') => ')[0], 'rhs': c['cfd'][1:].split(') => ')[1], 'cfd': c['cfd']} for c in top_cfds])
    #    scores = np.array([c['score'] for c in top_cfds])
    #    dscv_df = pd.DataFrame({'lhs': [c['lhs'] for c in dscv_cfds], 'rhs': [c['rhs'] for c in dscv_cfds], 'cfd': [c['cfd'] for c in dscv_cfds]})
    #    score_df = pd.DataFrame({'score': scores})

    #    dscv_df.to_csv('./store/' + project_id + '/discovered_cfds.csv', index_label='cfd_id', columns=['lhs', 'rhs'])
    #    score_df.to_csv('./store/' + project_id + '/scores.csv', index_label='cfd_id')

    #    receiver = charm.prepareReceiver(project_id, top_cfds)
    #    pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )


def buildCover(d_rep, picked_cfds):
    cover = np.empty(len(d_rep.index), dtype=str)
    print(picked_cfds[0]['cfd'])
    print([c['cfd'] for c in picked_cfds])
    just_cfds = np.array([c['cfd'] for c in picked_cfds])
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
        cover[idx] = '; '.join(relevant_cfds)

    d_rep['cover'] = cover
    return d_rep

# TODO; CHARM-INTEGRATED IMPLEMENTATION
#def pickCfds(query, num_cfds):
#    receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
#    return charm.getRules(receiver, query, num_cfds)

# TODO; TEMPORARY IMPLEMENTATION
def pickCfds(top_cfds, num_cfds):
    just_cfds = np.array([c['cfd'] for c in top_cfds if float(c['score']) > 0])
    just_scores = np.array([float(c['score']) for c in top_cfds if float(c['score']) > 0])
    norm_scores = np.array([s/sum(just_scores) for s in just_scores])
    if len(just_cfds) > 0:
        picked_cfds = np.random.choice(just_cfds, num_cfds, p=norm_scores.astype('float64'))
        return picked_cfds
    else:
        return None

def applyCfdList(project_id, d_rep, cfd_list):
    for cfd in cfd_list:
        #stringified_cfd = '(' + cfd.lhs + ') => ' + cfd.rhs
        d_rep = applyCfd(project_id, d_rep, cfd)
        #d_rep = applyCfd(project_id, d_rep, stringified_cfd, cfd.cfd_id, receiver)
    return d_rep

def applyCfd(project_id, d_rep, cfd, cfd_id=None, receiver=None):
    #mod_count = 0
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    for idx, row in d_rep.iterrows():
        mod_count = 0
        if row['cover'] is not None and cfd in row['cover'].split('; '):
            lhs = cfd.split(' => ')[0][1:-1]
            rhs = cfd.split(' => ')[1]
            if '=' in rhs:
                rh = np.array(rhs.split('='))
                if row[rh[0]] != rh[1]:
                    row[rh[0]] = rh[1]
                    mod_count += 1
        #tuple_metadata.at[idx, 'weight'] += mod_count
        #charm.reinforce(receiver, cfd_id, 1)
    return d_rep


def reinforceTuplesBasedOnContradiction(project_id, current_iter, d_latest):
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
    #prev_iter = "{:08x}".format(int('0x' + current_iter, 0) - 1)
    for idx in d_latest.index:
        reinforcementValue = 0
        for col in d_latest.columns:
            prev_spread = len(set(value_metadata[idx][col]['history']))
            value_metadata[idx][col]['history'].append(d_latest.at[idx, col])
            curr_spread = len(set(value_metadata[idx][col]['history']))
            vspr_d = 0       # value spread delta (change in value spread from last iteration)
            if curr_spread > prev_spread:
                vspr_d = 1

            cell_values = Counter(value_metadata[idx][col]['history'])
            num_occurrences_mode = cell_values.most_common(1)[0][1]
            new_vdis = 1 - (num_occurrences_mode/len(value_metadata[idx][col]['history']))   # new value disagreement (value disagreement for the current iteration)
            vdis_d = new_vdis - value_metadata[idx][col]['disagreement']            # value disagreement delta (change in value disagreement from last iteration; set to 0 if less than 0 so as to disallow negative tuple weights)
            value_metadata[idx][col]['disagreement'] = new_vdis
            if vdis_d < 0:
                vdis_d = 0

            reinforcementValue += (vspr_d + new_vdis + vdis_d)     # add change in value spread, new value disagreement, and change in value disagreement from last iteration

        tuple_metadata.at[idx, 'weight'] += reinforcementValue

    #tuple_weights['weight'] = tuple_weights['weight']/tuple_weights['weight'].sum()
    print('Tuple weights:')
    pprint(tuple_metadata['weight'])
    print()
    tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )


# TODO
def buildSample(d_rep, sample_size, project_id):
    # TEMPORARY IMPLEMENTATION
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    chosen_tups = tuple_weights.sample(n=sample_size, weights='weight')     # tuples with a larger weight (a.k.a. larger value in the 'weight' column of tuple_weights) are more likely to be chosen
    print('Chosen example indexes:')
    pprint(chosen_tups.index)
    sample = d_rep.iloc[chosen_tups.index]
    return sample
