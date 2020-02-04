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

sys.path.insert(0, './charm/keywordSearch/')
import charm

class ValueHistory(object):
    def __init__(self, value, agent, cfd_applied, iter, changed):
        self.value = value
        self.agent = agent
        self.cfd_applied = cfd_applied
        self.iter = iter
        self.changed = changed


'''
FUNCTION: applyUserRepairs
PURPOSE: Apply the user's repairs on the sample to the full dataset, reinforcing
previously applied CFDs along the way.
INPUT:
* d_dirty: the full dirty dataset
* s_df: the sample the user interacted with
* project_id: the ID of the current interaction
* current_iter: the current iteration number
OUTPUT:
* d_rep: the user-repaired version of the full dataset
* changed_ids: the IDs of the rows the user modified
'''
def applyUserRepairs(d_dirty, s_df, project_id, current_iter):
    d_rep = d_dirty
    print(s_df.index)
    changed_ids = list()
    value_metadata = pickle.load(open('./store/' + project_id + '/value_metadata.p', 'rb'))

    # First iteration; no CFDs have been applied in this interaction yet
    if current_iter == '00000001':
        # Map the user's repairs on the sample to the full dataset, keeping track of which tuples have been modified
        for idx in s_df.index:
            for col in s_df.columns:
                if d_rep.at[idx, col] != s_df.at[idx, col]:     # The user modified the value of this cell
                    d_rep.at[idx, col] = s_df.at[idx, col]      # Save the user's new value
                    value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))   # Add the new value to the history of this cell
                    if idx not in changed_ids:      # This is the first cell in this row the user modified
                        changed_ids.append(idx)     # Add the row's index to the list of changed tuple IDs

    # Not first iteration; CFDs may have been applied previously; reinforce CFDs based on user's feedback
    else:
        #cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
        #curr_iter_num = int('0x' + current_iter, 0)
        cfd_applied_map = pickle.load( open('./store/' + project_id + '/cfd_applied_map.p', 'rb') )

        # Count the number of rows in the sample each CFD from the previous iteration was applied to
        num_times_applied_each_cfd = dict()
        for idx in s_df.index:
            for col in s_df.columns:
                if cfd_applied_map[current_iter][idx][col] in num_times_applied_each_cfd.keys():
                    num_times_applied_each_cfd[cfd_applied_map[current_iter][idx][col]] += 1
                else:
                    num_times_applied_each_cfd[cfd_applied_map[current_iter][idx][col]] = 1

        # Map the user's repairs on the sample to the full dataset, keeping track of which tuples have been modified
        for idx in s_df.index:
            for col in s_df.columns:
                if d_rep.at[idx, col] != s_df.at[idx, col]:     # The user modified the value of this cell
                    if idx not in changed_ids:      # This is the first cell in this row the user modified
                        changed_ids.append(idx)     # Add the row's index to the list of changed tuple IDs
                    try:
                        latest_match_idx = next(i for i in reversed(range(len(value_metadata[idx][col]['history']))) if value_metadata[idx][col]['history'][i].value == s_df.at[idx, col])      # Get the most recent CFD that resulted in the value declared by the user
                        charm.reinforce(receiver, value_metadata[idx][col]['history'][latest_match_index].cfd_applied, latest_match_idx/(len(value_metadata[idx][col]['history']) - 1))         # Reinforce this CFD based on how recently it was applied
                        value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))       # Add the new value to the history of this cell
                        #charm.reinforce(receiver, value_metadata[idx][col]['history'][-1][1], -1/num_times_applied_each_cfd[value_metadata[idx][col]['history'][-1][1]])
                    except ValueError:      # This is the first time this cell has had this value
                        pass
                        #last_cfd_id = value_metadata[idx][col]['history'][-1].cfd_applied
                        #charm.reinforce(receiver, last_cfd_id, -1/num_times_applied_each_cfd[last_cfd_id])
                    d_rep.at[idx, col] = s_df.at[idx, col]
                else:       # The user did not modify the value of this cell
                    last_cfd_id = value_metadata[idx][col]['history'][-1].cfd_applied       # Get the cfd_id of the CFD that was just applied to this cell
                    charm.reinforce(receiver, last_cfd_id, 1/num_times_applied_each_cfd[last_cfd_id])       # Reinforce this CFD



        #TODO: Find the CFD applied by the system for changes made by the user, and check if it was reverted to match a previous CFD


        pickle.dump(receiver, open('./store/' + project_id + '/receiver.p', 'wb'))
        #pickle.dump(cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb'))

    print(changed_ids)
    return d_rep, changed_ids

'''
FUNCTION: discoverCFDs
PURPOSE: Run XPlode on the before-repair and after-repair versions of the dataset.
INPUT:
* project_id: The ID of the current interaction, used to retrieve the datasets.
OUTPUT: 
* An array of JSON objects containing information on each discovered CFD
(including CFD ID, CFd, and score), or None if there was an XPlode runtime error or no CFDs were found.
'''
def discoverCFDs(project_id):
    dirty_fp = './store/' + project_id + '/before.csv'
    clean_fp = './store/' + project_id + '/after.csv'
    print('about to run xplode')
    process = sp.Popen(['./xplode-master/CTane', dirty_fp, clean_fp, '0.25', '2'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    output = process.communicate()[0].decode("utf-8")
    if process.returncode == 0:
        if output == '[NO CFDS FOUND]':
            print(output)
            return None
        else:
            output = np.array(output.split('\n'))[:-1]
            scores = output[:int(len(output)/2)]
            top_cfds = output[int(len(output)/2):]
            return np.array([{'cfd_id': i, 'cfd': top_cfds[i], 'score': scores[i]} for i in range(0, len(top_cfds))])
    else:
        print('[ERROR] CFD DISCOVERY FAILURE')
        return None


'''
FUNCTION: addNewCfdsToList
PURPOSE: Add the newly discovered CFDs to the list of discovered CFDs, and initialize/reinforce their weights based on
its score from the last run of XPlode and how many times XPlode has returned the CFD
INPUT:
* top_cfds: The list of discovered CFDs from the latest run of XPlode
* project_id: The ID of this interaction.
* current_iter: The current iteration number.
* query: A formatted version of the rows the user modified; used for mapping repaired tuples to CFDs in the receiver
OUTPUT: None
'''
def addNewCfdsToList(top_cfds, project_id, current_iter, query):
    if os.path.isfile('./store/' + project_id + '/cfd_metadata.p'):
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
        receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
        for c in [tc for tc in top_cfds if float(tc['score']) > 0]:
            exists = False
            for idx, cfd in enumerate(cfd_metadata):
                lhs = c['cfd'].split(' => ')[0][1:-1]
                rhs = c['cfd'].split(' => ')[1]
                if cfd['lhs'] == lhs and cfd['rhs'] == rhs:
                    exists = True
                    cfd['num_found'] += 1
                    cfd['num_changes'][current_iter] = [0]
                    charm.reinforce(receiver, idx, float(c['score'])/cfd['num_found'])
                    break
            if not exists:
                cfd_metadata.append(dict())
                cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]
                cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]
                cfd_metadata[-1]['num_found'] = 1
                cfd_metadata[-1]['num_changes'] = dict()
                cfd_metadata[-1]['num_changes'][current_iter] = 0

                c['cfd_id'] = len(cfd_metadata) - 1
                charm.updateReceiver(receiver, [c], query)
                charm.reinforce(receiver, c['cfd_id'], float(c['score']))

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )

    else:
        cfd_metadata = list()
        for c in [tc for tc in top_cfds if float(tc['score']) > 0]:
            cfd_metadata.append(dict())
            cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]
            cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]
            cfd_metadata[-1]['num_found'] = 1
            cfd_metadata[-1]['num_changes'] = dict()
            cfd_metadata[-1]['num_changes'][current_iter] = 0

        scores = [float(c['score']) for c in top_cfds if float(c['score']) > 0]

        receiver = charm.prepareReceiver(project_id, top_cfds, query)
        for idx, _ in enumerate(cfd_metadata):
            charm.reinforce(receiver, idx, scores[idx])

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )


'''
FUNCTION: buildCover
PURPOSE: Map every picked CFD to the rows it applies to, so that unnecessary checking can
be avoided when repairing the dataset.
INPUT:
* d_rep: The user-cleaned dataset
* picked_cfd: The CFDs picked by the learning framework.
OUTPUT:
* d_rep: The user-cleaned dataset, with a 'cover' column added to hold the cover map.
'''
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


'''
FUNCTION: pickCfds
PURPOSE: Pick CFDs from the learning receiver to apply to the dataset.
INPUT:
* project_id: The ID of the current interaction.
* query: A stringified representation of the rows repaired by the user.
* num_cfds: How many CFDs to select from the learning receiver.
OUTPUT:
* rules: The selected CFDs
* rule_id_list: The CFD IDs of the selected CFDs
'''
def pickCfds(project_id, query, num_cfds):
    receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )
    rules, rule_id_list = charm.getRules(receiver, query, num_cfds)
    pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
    return rules, rule_id_list


'''
FUNCTION: applyCfdList
PURPOSE: Apply the selected CFDs to the dataset.
INPUT:
* project_id: The ID of the current interaction
* d_rep: The user-cleaned dataset
* cfd_list: The list of CFDs to be applied
* cfd_id_list: The list of the CFD IDs of the CFDs to be applied
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration
* current_iter: The current iteration number.
OUTPUT:
* d_rep: The fully cleaned version of the dataset.
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration, updated for this iteration
'''
def applyCfdList(project_id, d_rep, cfd_list, cfd_id_list, cfd_applied_map, current_iter):
    cfd_applied_map[current_iter] = dict()
    for idx in d_rep.index:
        cfd_applied_map[current_iter][idx] = dict()
        for col in d_rep.columns:
            cfd_applied_map[current_iter][idx][col] = None
    for i in range(0, len(cfd_list)):
        #stringified_cfd = '(' + cfd.lhs + ') => ' + cfd.rhs
        d_rep, cfd_applied_map = applyCfd(project_id, d_rep, cfd_list[i], cfd_id_list[i], cfd_applied_map, current_iter)
        #d_rep = applyCfd(project_id, d_rep, stringified_cfd, cfd.cfd_id, receiver)
    return d_rep, cfd_applied_map


'''
FUNCTION: applyCfd
PURPOSE: Apply a CFD to the dataset.
INPUT:
* project_id: The ID of the current interaction
* d_rep: The user-cleaned dataset
* cfd: The CFD to be applied
* cfd_id: The CFD ID of the CFD to be applied
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration
* current_iter: The current iteration number.
OUTPUT:
* d_rep: The fully cleaned version of the dataset.
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration, updated for this iteration
'''
def applyCfd(project_id, d_rep, cfd, cfd_id, cfd_applied_map, current_iter):
    #mod_count = 0
    #tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )

    for idx, row in d_rep.iterrows():
        #mod_count = 0
        if row['cover'] is not None and cfd in row['cover'].split('; '):
            lhs = cfd.split(' => ')[0][1:-1]
            rhs = cfd.split(' => ')[1]
            if '=' in rhs:
                rh = np.array(rhs.split('='))
                if row[rh[0]] != rh[1]:
                    row[rh[0]] = rh[1]
                    #mod_count += 1
                    cfd_applied_map[current_iter][idx][rh[0]] = cfd_id
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, True))
                else:
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, False))
        #tuple_metadata.at[idx, 'weight'] += mod_count
        #charm.reinforce(receiver, cfd_id, 1)
    return d_rep, cfd_applied_map


'''
FUNCTION: reinforceTuplesBasedOnContradiction
PURPOSE: Reinforce tuples in the dataset based on the variance of values each cell has held, both in the current iteration and in all iterations.
INPUT:
* project_id: The ID of the interaction.
* d_latest: The latest cleaned version of the dataset.
OUTPUT: None
'''
def reinforceTuplesBasedOnContradiction(project_id, current_iter, d_latest):
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
    for idx in d_latest.index:
        reinforcementValue = 0
        for col in d_latest.columns:
            prev_spread = len(set([v.value for v in value_metadata[idx][col]['history'] if int('0x' + v.iter, 0) < int('0x' + current_iter, 0)]))
            curr_spread = len(set([v.value for v in value_metadata[idx][col]['history']]))
            vspr_d = 0       # value spread delta (change in value spread from last iteration)
            if curr_spread > prev_spread:
                vspr_d = 1

            cell_values = Counter([vh.value for vh in value_metadata[idx][col]['history']])
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
'''
FUNCTION: buildSample
PURPOSE: Create a new sample of the dataset for the user to interact with and give feedback through.
INPUT:
* d_rep: The cleaned dataset.
* sample_size: The size of the sample to be created.
* cfd_applied_map: A map of which CFD was applied to each cell in every iteration of the interaction.
* current_iter: The current iteration number.
OUTPUT:
* sample: The created sample.
'''
def buildSample(d_rep, sample_size, project_id, cfd_applied_map, current_iter):
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )
    chosen_tups = tuple_metadata.sample(n=sample_size, weights='weight')     # tuples with a larger weight (a.k.a. larger value in the 'weight' column of tuple_metadata) are more likely to be chosen
    print('Chosen example indexes:')
    pprint(chosen_tups.index)

    for idx in chosen_tups.index:
        seen = list()
        for col in d_rep.columns:
        # TODO; Calculate how many rows the CFD was applied to in the sample
            if cfd_applied_map[current_iter][idx][col] is not None and cfd_applied_map[current_iter][idx][col] not in seen:
                seen.append(cfd_applied_map[current_iter][idx][col])
                cfd_metadata[cfd_applied_map[current_iter][idx][col]]['num_changes'][current_iter] += 1

    pickle.dump(cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )
    sample = d_rep.iloc[chosen_tups.index]
    return sample
