from random import randint, choice
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
        self.agent = agent      # user or system
        self.cfd_applied = cfd_applied
        self.iter = iter
        self.changed = changed

class Diff(object):
    def __init__(self, value, agent, iter):
        self.value = value
        self.agent = agent      # user or system
        self.iter = iter

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

    if current_iter == '00000001':    # First iteration, so no CFDs have been applied yet
        for idx in s_df.index:
            for col in s_df.columns:
                if d_rep.at[idx, col] != s_df.at[idx, col]:     # If the user modified the value of this cell
                    d_rep.at[idx, col] = s_df.at[idx, col]      # Save the user's new value
                    value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))   # Save value to cell's value history
                    if idx not in changed_ids:      # If this is the first cell in this row the user modified
                        changed_ids.append(idx)     # Add the row's index to the list of changed tuple IDs

    else:
        try:
            receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )   # load learning store
        except FileNotFoundError:
            receiver = None     # no learning store yet, since no CFDs applied yet
        cfd_applied_map = pickle.load( open('./store/' + project_id + '/cfd_applied_map.p', 'rb') )
        prev_iter = "{:08x}".format(int('0x' + current_iter, 0) - 1)

        # Count the number of rows in the sample each CFD from the previous iteration was applied to
        num_times_applied_each_cfd = dict()
        for idx in s_df.index:
            for col in s_df.columns:
                if cfd_applied_map[prev_iter][idx][col] in num_times_applied_each_cfd.keys():
                    num_times_applied_each_cfd[cfd_applied_map[prev_iter][idx][col]] += 1
                else:
                    num_times_applied_each_cfd[cfd_applied_map[prev_iter][idx][col]] = 1

        # Map the user's repairs on the sample to the full dataset, keeping track of which tuples have been modified
        for idx in s_df.index:
            for col in s_df.columns:
                if d_rep.at[idx, col] != s_df.at[idx, col]:
                    if idx not in changed_ids:
                        changed_ids.append(idx)
                    try:
                        # Get the most recent instance in the cell's history where the value is equal to the current value
                        latest_match_idx = next(i for i in reversed(range(len(value_metadata[idx][col]['history']))) if value_metadata[idx][col]['history'][i].value == s_df.at[idx, col])

                        # if a CFD resulted in this value, reinforce the CFD based on how recently it was applied
                        if receiver is not None and value_metadata[idx][col]['history'][latest_match_idx].cfd_applied is not None:
                            charm.reinforce(receiver, value_metadata[idx][col]['history'][latest_match_idx].cfd_applied, latest_match_idx/(len(value_metadata[idx][col]['history']) - 1))
                        value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))   # Save value to cell's value history
                    except StopIteration:      # This is the first time this cell has had this value
                        pass
                    d_rep.at[idx, col] = s_df.at[idx, col]      # Map the user's cell repair to the appropriate cell in the full dataset

                # Reinforce the last CFD that was applied to this cell
                else:
                    last_cfd_id = value_metadata[idx][col]['history'][-1].cfd_applied
                    if receiver is not None and last_cfd_id is not None:
                        charm.reinforce(receiver, last_cfd_id, 1/num_times_applied_each_cfd[last_cfd_id])

        if receiver is not None:
            pickle.dump(receiver, open('./store/' + project_id + '/receiver.p', 'wb'))

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
    dirty_fp = './store/' + project_id + '/before.csv'      # "dirty" dataset
    clean_fp = './store/' + project_id + '/after.csv'       # "repaired" dataset

    # run XPlode
    process = sp.Popen(['./xplode-master/CTane', dirty_fp, clean_fp, '0.25', '2'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})
    res = process.communicate()
    print(res[1].decode("utf-8"))
    output = res[0].decode("utf-8")

    if process.returncode == 0:     # XPlode exited successfully
        if output == '[NO CFDS FOUND]':  # if no CFDs were found
            print(output)
            return None
        else:   # if there were CFDs found
            output = np.array(output.split('\n'))[:-1]          # split the output into a list by newlines
            scores = output[:int(len(output)/2)]                # extract scores
            top_cfds = output[int(len(output)/2):]              # extract CFDs
            return np.array([{'cfd_id': i, 'cfd': top_cfds[i], 'score': scores[i]} for i in range(0, len(top_cfds))])       # return a dictionary holding the CFDs and their scores

    else:   # XPlode did not exit successfully
        print('[ERROR] CFD DISCOVERY FAILURE')
        return None


'''
FUNCTION: fd2cfd
PURPOSE: Convert a pure FD (or a partial CFD, meaning not every attribute in the dependency has a condition present)
to a collection of CFDs representing the patterns relevant to this dependency that occur in the dataset
INPUT:
* data: The dataset
* lhs: The left-hand side of the dependency
* rhs: The right-hand side of the dependency
OUTPUT:
* patterns: The list of CFDs representing the patterns relevant to this depedency that occur in the dataset
'''
def fd2cfd(data, lhs, rhs, value_metadata, current_iter):
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
                #print(idx)
                #print(clause)
                last = value_metadata[idx][clause]['history'][-1]
                if last.iter == current_iter and last.agent == 'user':
                    lhspattern += clause + '=' + last.value + ', '
                else:
                    lhspattern += clause + '=' + data.at[idx, clause] + ', '
        lhspattern = lhspattern[:-2]
        if '=' in rhs:
            rhspattern = rhs
        else:
            last = value_metadata[idx][rhs]['history'][-1]
            if last.iter == current_iter and last.agent == 'user':
                rhspattern = rhs + '=' + last.value
            else:
                rhspattern = rhs + '=' + data.at[idx, rhs]
        if lhspattern in patterns.keys():
            patterns[lhspattern].append(rhspattern)
            if (lhspattern, rhspattern) in mappings.keys():
                mappings[(lhspattern, rhspattern)].append(idx)
            else:
                mappings[(lhspattern, rhspattern)] = [idx]
        else:
            patterns[lhspattern] = [rhspattern]
            mappings[(lhspattern, rhspattern)] = [idx]

    # Pick RHS patterns for each LHS from these candidates
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [key for key, v in get_mode.items() if v == max(list(counts.values()))]

        # If there is only one top RHS pattern for this LHS, pick it
        if len(patterns[key]) == 1:
            patterns[key] = patterns[key].pop()

        # If there is more than one top RHS pattern for this LHS, pick the pattern that has generally occurred more recently
        else:
            best_r = list()
            max_occur = 0
            print('all mappings:', mappings)
            print('\nall rhs:', [rhs for (lhs, rhs) in mappings.keys()])
            print('\nrelevant rhs:', [rhs for (lhs, rhs) in mappings.keys() if lhs == key])
            for r in [rhs for (lhs, rhs) in mappings.keys() if lhs == key]:
                count_r = 0
                for idx in mappings[(lhs, r)]:
                    count_r += sum([1/(int('0x' + current_iter, 0) - int('0x' + v.iter, 0)) for v in value_metadata[idx][r.split('=')[0]]['history'] if v.value == r.split('=')[1]])
                if count_r >= max_occur:
                    best_r.append(r)
                    max_occur = count_r

            # If there is now only one top RHS pattern for this LHS, pick it
            if len(best_r) == 1:
                patterns[key] = best_r

            # If there is still more than one top RHS pattern for this LHS, pick the pattern that has occurred more frequently
            else:
                best_r = list()
                max_occur = 0
                for r in [rhs for lhs, rhs in mappings.keys() if lhs == key]:
                    count_r = 0
                    for idx in mappings[(l, r)]:
                        count_r += len([v for v in value_metadata[idx][r.split('=')[0]]['history'] if v.value == r.split('=')[1]])
                    if count_r >= max_occur:
                        best_r.append(r)
                        max_occur = count_r

                # If there is now only one top RHS pattern for this LHS, pick it
                if len(best_r) == 1:
                    patterns[key] = best_r

                # If there is still more than one top RHS pattern for this LHS, pick randomly
                else:
                    patterns[key] = random.choice(patterns[key])

    return patterns

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
def updateReceiver(top_cfds, project_id, current_iter, query):

    eligible_cfds = [tc for tc in top_cfds if float(tc['score']) > 0]  # we do not consider CFDs with a negative XPlode score
    cfd_metadata = pickle.load(open('./store/' + project_id + '/cfd_metadata.p', 'rb'))
    receiver = pickle.load(open('./store/' + project_id + '/receiver.p', 'rb'))

    # If any CFDs have previously been discovered, add/update discovered CFDs based on latest XPlode results
    if len(cfd_metadata) > 0:
        for c in eligible_cfds:
            exists = False
            lhs = c['cfd'].split(' => ')[0][1:-1]
            rhs = c['cfd'].split(' => ')[1]
            for idx, cfd in enumerate(cfd_metadata):    # for each previously discovered CFD
                if cfd['lhs'] == lhs and cfd['rhs'] == rhs:     # if the CFD has already been discovered
                    exists = True
                    cfd['num_found'] += 1
                    cfd['num_changes'][current_iter] = 0

                    # reinforce this CFD's weight using its latest XPlode score and the number of times it's been discovered
                    charm.reinforce(receiver, idx, float(c['score'])/cfd['num_found'])
                    break
            if not exists:
                cfd_metadata.append(dict())                                 # create a new metadata dictionary for the new CFD
                cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]
                cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]
                cfd_metadata[-1]['num_found'] = 1
                cfd_metadata[-1]['num_changes'] = dict()
                cfd_metadata[-1]['num_changes'][current_iter] = 0

                c['cfd_id'] = len(cfd_metadata) - 1
                charm.updateReceiver(receiver, [c], query)                  # add this CFD to the receiver's CFD store
                charm.reinforce(receiver, c['cfd_id'], float(c['score']))   # initialize this CFD's weight to its XPlode score

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )

    # If no CFDs have previously been discovered
    else:
        for c in eligible_cfds:
            cfd_metadata.append(dict())                                 # create a new metadata dictionary for the CFD
            cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]
            cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]
            cfd_metadata[-1]['num_found'] = 1
            cfd_metadata[-1]['num_changes'] = dict()
            cfd_metadata[-1]['num_changes'][current_iter] = 0

        scores = [float(c['score']) for c in eligible_cfds]

        receiver = charm.prepareReceiver(project_id, top_cfds, query)   # initialize the learning store
        for idx, _ in enumerate(cfd_metadata):
            charm.reinforce(receiver, idx, scores[idx])     # initialize the CFD's weight to its XPlode score

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )


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
    print('Rules: ' + str(rules))
    print('Rule IDs: ' + str(rule_id_list))
    pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )
    return rules, rule_id_list


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
def buildCover(d_rep, lhs, rhs, patterns):
    for idx, row in d_rep.iterrows():
        applies = True
        for lh in lhs.split(', '):

            # If this element of the CFD is constant
            if '=' in lh:
                lh = np.array(lh.split('='))
                if row[lh[0]] != lh[1]:     # CFD does not apply to this row
                    applies = False
                    break

        # If this CFD applies to this row
        if applies:
            d_rep[idx]['cover'].append('; (' + lhs + ') => ' + rhs)

            # if not a constant CFD
            if lhs.count('=') < len(lhs.split(', ')) or '=' not in rhs:
                key = ''
                for lh in lhs.split(', '):
                    if '=' in lh:
                        key += ', ' + lh
                    else:
                        key += ', ' + d_rep[idx][lh]
                key = key[2:]
                d_rep[idx]['cover'].append(' | (' + key + ') => ' + patterns[key])      # Find the proper RHS pattern for this tuple
            if d_rep[idx]['cover'][0] == ';':
                d_rep[idx]['cover'] = d_rep[idx]['cover'][2:]   # Remove leading '; '

    return d_rep


'''
FUNCTION: applyCfdList
PURPOSE: Apply the selected CFDs to the dataset.
INPUT:
* project_id: The ID of the current interaction
* d_rep: The user-cleaned dataset
* cfd_list: The list of CFDs to be applied
* cfd_id_list: The list of the CFD IDs of the CFDs to be applied
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration
* current_iter: The current iteration number
OUTPUT:
* d_rep: The fully cleaned version of the dataset.
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration, updated for this iteration
* contradictions: A dictionary holding the contradictions that have occurred in the dataset through this cleaning iteration
* changes: A dictionary holding the locations of system repairs
'''
def applyCfdList(project_id, d_rep, cfd_list, cfd_id_list, cfd_applied_map, current_iter):
    contradictions = dict()
    changes = dict()
    for i in d_rep.index:
        for j in d_rep.columns:
            changes[(i, j)] = False
    for i in range(0, len(cfd_list)):
        d_rep, cfd_applied_map, changes = applyCfd(project_id, d_rep, cfd_list[i], cfd_id_list[i], cfd_applied_map, current_iter, contradictions, changes)
    return d_rep, cfd_applied_map, contradictions, changes


'''
FUNCTION: applyCfd
PURPOSE: Apply a CFD to the dataset.
INPUT:
* project_id: The ID of the current interaction
* d_rep: The user-cleaned dataset
* cfd: The CFD to be applied
* cfd_id: The CFD ID of the CFD to be applied
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration
* current_iter: The current iteration number
* contradictions: A dictionary holding the contradictions that have occurred in the dataset through this cleaning iteration
OUTPUT:
* d_rep: The fully cleaned version of the dataset.
* cfd_applied_map: A map of which CFDs have been applied to each cell in each iteration, updated for this iteration
'''
def applyCfd(project_id, d_rep, cfd, cfd_id, cfd_applied_map, current_iter, contradictions, changes):
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')
    cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )

    for idx, row in d_rep.iterrows():
        cover = row['cover'].split('; ')

        # If this CFD applies to this tuple and is violated, apply it
        if row['cover'] is not None and cfd in [c.split(' | ')[0] for c in cover]:
            lhs = cfd.split(' => ')[0][1:-1]
            rhs = cfd.split(' => ')[1]

            # If the RHS of the CFD is a constant
            if '=' in rhs:
                rh = np.array(rhs.split('='))

                # if the CFD is violated, enforce it
                if row[rh[0]] != rh[1]:
                    row[rh[0]] = rh[1]
                    changes[(idx, rh[0])] = True
                    cfd_applied_map[current_iter][idx][rh[0]].append(cfd_id)      # Add a mapping for this cell in this iteration to this CFD's ID
                    cfd_metadata[cfd_id]['num_changes'][current_iter] += 1
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, True))     # Save the specifics of this modification to the cell's value history
                    tuple_metadata.at[idx, 'weight'] += 1

                    # If the system has already repaired this cell in this iteration, check for a contradiction
                    if value_metadata[idx][rh[0]]['history'][-2].iter == current_iter and value_metadata[idx][rh[0]]['history'][-2].value != rh[1] and value_metadata[idx][rh[0]]['history'][-2].agent == 'system':
                        if (idx, col) in contradictions.keys():
                            if rh[1] not in contradictions[(idx, col)]:
                                contradictions[(idx, col)].append(rh[1])
                        else:
                            contradictions[(idx, col)] = [value_metadata[idx][rh[0]]['history'][-2].value, rh[1]]
                else:
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, False))    # Save the specifics of this modification to the cell's value history

            # If this CFD is not a constant CFD
            else:
                cfd_index = [i for i, c in enumerate(cover) if cfd in c].pop()
                pattern = cover[cfd_index].split(' | ')[1][1:-1]        # Get the pattern that corresponds to this tuple for the CFD
                rh = np.array(pattern.split(' => ')[1].split('='))
                if row[rh[0]] != rh[1]:
                    row[rh[0]] = rh[1]
                    changes[(idx, rh[0])] = True
                    cfd_applied_map[current_iter][idx][rh[0]].append(cfd_id)      # Add a mapping for this cell in this iteration to this CFD's ID
                    cfd_metadata[cfd_id]['num_changes'][current_iter] += 1
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, True))     # Save the specifics of this modification to the cell's value history
                    tuple_metadata.at[idx, 'weight'] += 1

                    # If the system has already repaired this cell in this iteration, check for a contradiction
                    if value_metadata[idx][rh[0]]['history'][-2].iter == current_iter and value_metadata[idx][rh[0]]['history'][-2].value != rh[1] and value_metadata[idx][rh[0]]['history'][-2].agent == 'system':
                        if (idx, col) in contradictions.keys():
                            if rh[1] not in contradictions[(idx, col)]:
                                contradictions[(idx, col)].append(rh[1])
                        else:
                            contradictions[(idx, col)] = [value_metadata[idx][rh[0]]['history'][-2].value, rh[1]]

                else:
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, False))    # Save the specifics of this modification to the cell's value history

    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )
    tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
    pickle.dump(cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb'))

    return d_rep, cfd_applied_map, changes


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
            prev_spread = len(set([v.value for v in value_metadata[idx][col]['history'] if int('0x' + v.iter, 0) < int('0x' + current_iter, 0)]))           # Calculate the value spread through the previous iteration
            curr_spread = len(set([v.value for v in value_metadata[idx][col]['history']]))      # Calculate the value spread through the current iteration
            vspr_d = curr_spread - prev_spread      # Calculate the difference in value spread between iterations

            # Find the mode in the cell's value history and the percentage of time it's there --> value agreement
            cell_values = Counter([vh.value for vh in value_metadata[idx][col]['history']])
            num_occurrences_mode = cell_values.most_common(1)[0][1]
            new_vdis = 1 - (num_occurrences_mode/len(value_metadata[idx][col]['history']))
            vdis_d = new_vdis - value_metadata[idx][col]['disagreement']
            value_metadata[idx][col]['disagreement'] = new_vdis

            # Check to disallow the possibility of negative tuple weights
            if vdis_d < 0:
                vdis_d = 0

            reinforcementValue += (vspr_d + new_vdis + vdis_d)

        tuple_metadata.at[idx, 'weight'] += reinforcementValue

    tuple_metadata['weight'] = tuple_metadata['weight'] / tuple_weight['weight'].sum()      # Normalize tuple weights

    print('Tuple weights:')
    pprint(tuple_metadata['weight'])
    print()
    tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')
    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )


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

    tuple_weights = tuple_metadata['weight']
    chosen_tuples = list()

    while len(chosen_tuples) < sample_size:
        returned_tuple = pickSingleReturn(tuple_weights)		# pick one tuple
        if returned_tuple not in chosen_tuples:
            chosen_tuples.append(returned_tuple)		# if not already picked, add to list of tuples to return
        if len(chosen_tuples) >= len(tuple_weights.index):
            # if every possible tuples has been selected, break out of the while loop
            break

    print('Chosen example indexes:')
    pprint(chosen_tuples)

    sample = d_rep.iloc[chosen_tuples]      # get the tuples that correspond to the tuple IDs from above
    return sample

'''
FUNCTION: pickSingleReturn
PURPOSE: Pick one tuple to return
INPUT:
* tuple_weights: The weights of each tuple in the dataset
OUTPUT:
* tuple_id: The ID of the selected tuple
'''
def pickSingleReturn(self, tuple_weights):
    chance = random.uniform(0, 1)
    cumulative = 0
    total = sum(tuple_weights.values())
    for tuple_id in tuple_weights:
        cumulative += tuple_weights[tuple_id]/total
        if cumulative > chance:
            del tuple_weights[tuple_id]
            return tuple_id

def calcDiffs(d_rep, clean_src, project_id, agent, iter):
    diffs = pickle.load( open('./store/' + project_id + '/diffs.p', 'rb') )
    d_clean = pd.read_csv(clean_src)
    cell_diff_count = 0
    tup_diff_count = 0
    for idx in d_rep.index:
        is_tup_diff = False
        for col in d_rep.columns:
            if d_rep.at[idx, col] != d_clean.at[idx, col]:
                cell_diff_count += 1
                is_tup_diff = True
        if is_tup_diff is True:
            tup_diff_count += 1
    cell_diff_value = cell_diff_count / (len(d_rep.index) * len(d_rep.columns))
    tup_diff_value = tup_diff_count / len(d_rep.index)
    cell_diff = Diff(cell_diff_value, agent, iter)
    tup_diff = Diff(tup_diff_value, agent, iter)
    diffs['cells'].append(cell_diff)
    diffs['tups'].append(tup_diff)
    pickle.dump( diffs, open('./store/' + project_id + '/diffs.p', 'wb') )
