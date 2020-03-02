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

    if current_iter == '00000001':    # If this is the first iteration, no CFDs have been applied in this interaction yet, so map the user's repairs on the sample to the full dataset, keeping track of which tuples have been modified
        for idx in s_df.index:
            for col in s_df.columns:
                if d_rep.at[idx, col] != s_df.at[idx, col]:     # If the user modified the value of this cell
                    d_rep.at[idx, col] = s_df.at[idx, col]          # Save the user's new value
                    value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))   # Add the new value to the history of this cell
                    if idx not in changed_ids:      # If this is the first cell in this row the user modified
                        changed_ids.append(idx)         # Add the row's index to the list of changed tuple IDs

    else:      # If this is not the first iteration, CFDs may have been applied previously, so reinforce CFDs based on the user's feedback
        try:
            receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )   # load the system learning receiver
        except FileNotFoundError:
            receiver = None     # no CFDs have been applied in previous iterations, so there is no receiver yet
        cfd_applied_map = pickle.load( open('./store/' + project_id + '/cfd_applied_map.p', 'rb') )     # load the CFD application map
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
                if d_rep.at[idx, col] != s_df.at[idx, col]:     # If the user modified the value of this cell
                    if idx not in changed_ids:                      # If this is the first cell in this row the user modified
                        changed_ids.append(idx)                         # Add the row's index to the list of changed tuple IDs
                    try:
                        latest_match_idx = next(i for i in reversed(range(len(value_metadata[idx][col]['history']))) if value_metadata[idx][col]['history'][i].value == s_df.at[idx, col])      # Get the most recent CFD that resulted in the same value declared by the user
                        if receiver is not None and value_metadata[idx][col]['history'][latest_match_idx].cfd_applied is not None:                                                              # is a CFD actually resulted in this value
                            charm.reinforce(receiver, value_metadata[idx][col]['history'][latest_match_idx].cfd_applied, latest_match_idx/(len(value_metadata[idx][col]['history']) - 1))         # Reinforce this CFD based on how recently it was applied
                        value_metadata[idx][col]['history'].append(ValueHistory(s_df.at[idx, col], 'user', None, current_iter, True))                                                           # Add the new value to the history of this cell
                    except StopIteration:      # This is the first time this cell has had this value
                        pass
                    d_rep.at[idx, col] = s_df.at[idx, col]      # Map the user's cell repair to the appropriate cell in the full dataset
                else:       # If the user did not modify the value of this cell
                    last_cfd_id = value_metadata[idx][col]['history'][-1].cfd_applied       # Get the cfd_id of the CFD that was just applied to this cell
                    if receiver is not None and last_cfd_id is not None:
                        charm.reinforce(receiver, last_cfd_id, 1/num_times_applied_each_cfd[last_cfd_id])       # Reinforce this CFD

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
    print('about to run xplode')
    process = sp.Popen(['./xplode-master/CTane', dirty_fp, clean_fp, '0.25', '2'], stdout=sp.PIPE, stderr=sp.PIPE, env={'LANG': 'C++'})     # run XPlode
    output = process.communicate()[0].decode("utf-8")       # get output of XPlode
    if process.returncode == 0:                             # if XPlode exited successfully
        if output == '[NO CFDS FOUND]':                         # if no CFDs were found
            print(output)
            return None
        else:                                                   # if there were CFDs found
            output = np.array(output.split('\n'))[:-1]          # split the output into a list by newlines
            scores = output[:int(len(output)/2)]                # extract the scores (they are listed in the same order as the CFDs)
            top_cfds = output[int(len(output)/2):]              # extract the CFDs
            return np.array([{'cfd_id': i, 'cfd': top_cfds[i], 'score': scores[i]} for i in range(0, len(top_cfds))])       # return a dictionary holding the CFDs and their scores
    else:                                                   # if there was some error during XPlode execution
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
    for key in patterns.keys():
        counts = Counter(patterns[key])
        get_mode = dict(counts)
        patterns[key] = [key for key, v in get_mode.items() if v == max(list(counts.values()))]
        if len(patterns[key]) == 1:
            patterns[key] = patterns[key].pop()
        else:
            #curr_rhs_values = [r for l, r in mappings.keys() if l == key]
            best_r = list()
            max_occur = 0
            print('all mappings:', mappings)
            print('\nall rhs:', [rhs for (lhs, rhs) in mappings.keys()])
            print('\nrelevant rhs:', [rhs for (lhs, rhs) in mappings.keys() if lhs == key])
            for r in [rhs for (lhs, rhs) in mappings.keys() if lhs == key]:
                count_r = 0
                for idx in mappings[(lhs, r)]:
                    count_r += sum([1/(int('0x' + current_iter, 0) - int('0x' + v.iter, 0)) for v in value_history[idx][r.split('=')[0]]['history'] if v.value == r.split('=')[1]])
                if count_r >= max_occur:
                    best_r.append(r)
                    max_occur = count_r

            if len(best_r) == 1:
                patterns[key] = best_r
            else:
                best_r = list()
                max_occur = 0
                for r in [rhs for lhs, rhs in mappings.keys() if lhs == key]:
                    count_r = 0
                    for idx in mappings[(l, r)]:
                        count_r += len([v for v in value_history[idx][r.split('=')[0]]['history'] if v.value == r.split('=')[1]])
                    if count_r >= max_occur:
                        best_r.append(r)
                        max_occur = count_r
                if len(best_r) == 1:
                    patterns[key] = best_r
                else:
                    #selection = randint(0, len(patterns[key]))
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
def addNewCfdsToList(top_cfds, project_id, current_iter, query):
    if os.path.isfile('./store/' + project_id + '/cfd_metadata.p'):                             # if CFD metadata object already exists (i.e. CFDs have been discovered in previous iterations)
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )       # load the CFD metadata object
        receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )               # load the system learning receiver
        eligible_cfds = [tc for tc in top_cfds if float(tc['score']) > 0]
        for c in eligible_cfds:                                 # for each CFD with a positive XPlode score
            exists = False
            lhs = c['cfd'].split(' => ')[0][1:-1]
            rhs = c['cfd'].split(' => ')[1]
            if lhs.count('=') < len(lhs) or '=' not in rhs:
                #patterns = fd2cfd(d_rep, lhs, rhs)
                patterns = []
                eligible_cfds.extend(patterns)
                break
            for idx, cfd in enumerate(cfd_metadata):                                                    # for each previously discovered CFD
                if cfd['lhs'] == lhs and cfd['rhs'] == rhs:                                             # if the CFD has already been discovered
                    exists = True
                    cfd['num_found'] += 1                                                                   # increment the number of times this CFD has been found
                    cfd['num_changes'][current_iter] = 0                                                    # initialize the number of changes this CFD has made in this iteration
                    charm.reinforce(receiver, idx, float(c['score'])/cfd['num_found'])                      # reinforce this CFD's weight using its latest XPlode score and the number of times it's been discovered
                    break
            if not exists:
                cfd_metadata.append(dict())                                                             # create a new metadata dictionary for the new CFD
                cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]                               # save the CFD's LHS
                cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]                                     # save the CFD's RHS
                cfd_metadata[-1]['num_found'] = 1                                                       # initialize the number of times this CFD has been found
                cfd_metadata[-1]['num_changes'] = dict()                                                # create a dictionary for changes made by this CFD over various iterations
                cfd_metadata[-1]['num_changes'][current_iter] = 0                                       # initialize the number of changes this CFD has made in this iteration

                c['cfd_id'] = len(cfd_metadata) - 1                                                     # create this CFD's ID
                charm.updateReceiver(receiver, [c], query)                                              # add this CFD to the receiver's CFD store
                charm.reinforce(receiver, c['cfd_id'], float(c['score']))                               # initialize this CFD's weight to its XPlode score

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )                    # save the updated receiver
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )            # save the updated CFD metadata object

    else:                                                                                       # if the CFD metadata dictionary does NOT already exist (i.e. no CFDs have been discovered in previous iterations, or this is the first iteration)
        cfd_metadata = list()                                                                       # create the CFD metadata object
        for c in [tc for tc in top_cfds if float(tc['score']) > 0]:                                 # for each CFD with a positive XPlode
            cfd_metadata.append(dict())                                                                 # create a new metadata dictionary for the CFD
            cfd_metadata[-1]['lhs'] = c['cfd'].split(' => ')[0][1:-1]                                   # save the CFD's LHS
            cfd_metadata[-1]['rhs'] = c['cfd'].split(' => ')[1]                                         # save the CFD's RHS
            cfd_metadata[-1]['num_found'] = 1                                                           # initialize the number of times this CFD has been found
            cfd_metadata[-1]['num_changes'] = dict()                                                    # create a dictionary for changes made by this CFD over various iterations
            cfd_metadata[-1]['num_changes'][current_iter] = 0                                           # initialize the number of changes this CFD has made in this iteration

        scores = [float(c['score']) for c in top_cfds if float(c['score']) > 0]                     # extract the CFDs' scores

        receiver = charm.prepareReceiver(project_id, top_cfds, query)                               # initialize the system learning receiver object
        for idx, _ in enumerate(cfd_metadata):                                                      # for each CFD
            charm.reinforce(receiver, idx, scores[idx])                                                 # initialize the CFD's weight to its XPlode score

        pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )                # save the receiver
        pickle.dump( cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )        # save the CFD metadata object


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
    receiver = pickle.load( open('./store/' + project_id + '/receiver.p', 'rb') )       # load the system learning receiver
    rules, rule_id_list = charm.getRules(receiver, query, num_cfds)                     # get CFDs and their IDs from the receiver
    print('Rules: ' + str(rules))
    print('Rule IDs: ' + str(rule_id_list))
    pickle.dump( receiver, open('./store/' + project_id + '/receiver.p', 'wb') )        # save the receiver
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
    for idx, row in d_rep.iterrows():                           # for each row in the dataset
        applies = True
        for lh in lhs.split(', '):                          # for each element of the CFD's LHS
            if '=' in lh:                                       # if the element requires a specific value
                lh = np.array(lh.split('='))                        # split up this LHS attribute from its value
                if row[lh[0]] != lh[1]:                             # if this LHS attribute value does NOT hold in this row
                    applies = False                                     # this CFD does NOT apply to this row
                    break
        if applies:                                         # if this CFD applies to this row
            d_rep[idx]['cover'].append('; (' + lhs + ') => ' + rhs)
            #TODO: Check if CFD is not a pure CFD and, if not, find and append the corresponding pattern for this row
            if lhs.count('=') < len(lhs.split(', ')) or '=' not in rhs:
                key = ''
                for lh in lhs.split(', '):
                    if '=' in lh:
                        key += ', ' + lh
                    else:
                        key += ', ' + d_rep[idx][lh]
                key = key[2:]
                d_rep[idx]['cover'].append(' | (' + key + ') => ' + patterns[key])
            if d_rep[idx]['cover'][0] == ';':
                d_rep[idx]['cover'] = d_rep[idx]['cover'][2:]
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

'''
def applyCfdList(project_id, d_rep, cfd_list, cfd_id_list, cfd_applied_map, current_iter):
    contradictions = dict()
    for i in range(0, len(cfd_list)):                                                                                                       # for each selected CFD
        d_rep, cfd_applied_map = applyCfd(project_id, d_rep, cfd_list[i], cfd_id_list[i], cfd_applied_map, current_iter, contradictions)        # apply the CFD to the dataset
    return d_rep, cfd_applied_map, contradictions                                                                                           # return the cleaned dataset and the updated cell/CFD map


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
def applyCfd(project_id, d_rep, cfd, cfd_id, cfd_applied_map, current_iter, contradictions):
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )                                   # load the cell value metadata object
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')                                              # load the tuple metadata DataFrame


    for idx, row in d_rep.iterrows():                                                                                           # for each row in the dataset
        cover = row['cover'].split('; ')
        if row['cover'] is not None and cfd in [c.split(' | ')[0] for c in cover]:                                                            # if this CFD is in the row's cover
            lhs = cfd.split(' => ')[0][1:-1]                                                                                        # extract the CFD's LHS
            rhs = cfd.split(' => ')[1]                                                                                              # extract the CFD's RHS
            if '=' in rhs:                                                                                                          # if the RHS value pertains to a specific value
                rh = np.array(rhs.split('='))                                                                                           # split up the RHS attribute from its value
                if row[rh[0]] != rh[1]:                                                                                                 # if the RHS attribute value does NOT hold in this row
                    row[rh[0]] = rh[1]                                                                                                      # set this cell's value to the RHS attribute value of the CFD
                    cfd_applied_map[current_iter][idx][rh[0]] = cfd_id                                                                      # add a mapping for this cell in this iteration to this CFD's ID
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, True))                 # add this new value to this cell's value history, along with the CFD the resulted in it, the agent who made the change, the iteration number, and the fact that this value is the result of a change
                    tuple_metadata.at[idx, 'weight'] += 1
                    if value_metadata[idx][rh[0]]['history'][-2].iter == current_iter and value_metadata[idx][rh[0]]['history'][-2].value != rh[1] and value_metadata[idx][rh[0]]['history'][-2].agent == 'system':      # if a contradiction has occurred for this cell
                        if (idx, col) in contradictions.keys():                             # if this is the first time this cell has a contradiction in this cleaning iteration
                            if rh[1] not in contradictions[(idx, col)]:                         # if this value hasn't already been seen in the cleaning
                                contradictions[(idx, col)].append(rh[1])
                        else:
                            contradictions[(idx, col)] = [value_metadata[idx][rh[0]]['history'][-2].value, rh[1]]
                else:                                                                                                                   # if the RHS attribute value already holds in this row
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, False))                # add this value to this cell's value history, along with the CFD that was tested on it, the agent who did the test, the iteration number, and the fact that this value is NOT the result of a change (i.e. it holds from its previous state)
            #else:
            #    pass        # TODO: FD functionality
            else:
                cfd_index = [i for i, c in enumerate(cover) if cfd in c].pop()
                pattern = cover[cfd_index].split(' | ')[1][1:-1]
                rh = np.array(pattern.split(' => ')[1].split('='))
                if row[rh[0]] != rh[1]:                                                                                                 # if the RHS attribute value does NOT hold in this row
                    row[rh[0]] = rh[1]                                                                                                      # set this cell's value to the RHS attribute value of the CFD
                    cfd_applied_map[current_iter][idx][rh[0]] = cfd_id                                                                      # add a mapping for this cell in this iteration to this CFD's ID
                    value_metadata[idx][rh[0]]['history'].append(ValueHistory(rh[1], 'system', cfd_id, current_iter, True))                 # add this new value to this cell's value history, along with the CFD the resulted in it, the agent who made the change, the iteration number, and the fact that this value is the result of a change
                    tuple_metadata.at[idx, 'weight'] += 1
                    if value_metadata[idx][rh[0]]['history'][-2].iter == current_iter and value_metadata[idx][rh[0]]['history'][-2].value != rh[1] and value_metadata[idx][rh[0]]['history'][-2].agent == 'system':      # if a contradiction has occurred for this cell
                        if (idx, col) in contradictions.keys():                             # if this is the first time this cell has a contradiction in this cleaning iteration
                            if rh[1] not in contradictions[(idx, col)]:                         # if this value hasn't already been seen in the cleaning
                                contradictions[(idx, col)].append(rh[1])
                        else:
                            contradictions[(idx, col)] = [value_metadata[idx][rh[0]]['history'][-2].value, rh[1]]
    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )                                    # save the updated value metadata object
    tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')                                                     # save the updated tuple metadata DataFrame

    return d_rep, cfd_applied_map                                                                                               # return the cleaned dataset and the cell/CFD map


'''
FUNCTION: reinforceTuplesBasedOnContradiction
PURPOSE: Reinforce tuples in the dataset based on the variance of values each cell has held, both in the current iteration and in all iterations.
INPUT:
* project_id: The ID of the interaction.
* d_latest: The latest cleaned version of the dataset.
OUTPUT: None
'''
def reinforceTuplesBasedOnContradiction(project_id, current_iter, d_latest):
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')                                                                  # load the tuple metadata DataFrame
    value_metadata = pickle.load( open('./store/' + project_id + '/value_metadata.p', 'rb') )                                                       # load the cell value metadata object
    for idx in d_latest.index:                                                                                                                      # for each row in the cleaned dataset
        reinforcementValue = 0                                                                                                                          # initialize the reinforcement value for this row to 0
        for col in d_latest.columns:                                                                                                                    # for each column in the dataset
            prev_spread = len(set([v.value for v in value_metadata[idx][col]['history'] if int('0x' + v.iter, 0) < int('0x' + current_iter, 0)]))           # calculate the set of values in this cell's value history, NOT including the current iteration
            curr_spread = len(set([v.value for v in value_metadata[idx][col]['history']]))                                                                  # calculate the set of values in this cell's value history, including the current iteration
            vspr_d = 0                                                                                                                                      # initialize the value spread delta (change in value spread from last iteration) to 0
            if curr_spread > prev_spread:                                                                                                                   # if the cell has a larger value spread now than it did in the previous iteration
                vspr_d = 1                                                                                                                                      # set the value spread delta to 1
            cell_values = Counter([vh.value for vh in value_metadata[idx][col]['history']])                                                                 # calculate the frequency of each value in the cell's value history
            num_occurrences_mode = cell_values.most_common(1)[0][1]                                                                                         # find the mode of these values
            new_vdis = 1 - (num_occurrences_mode/len(value_metadata[idx][col]['history']))                                                                  # calculate the cell's new value disagreement (value disagreement through the current iteration)
            vdis_d = new_vdis - value_metadata[idx][col]['disagreement']                                                                                    # calculate the cell's value disagreement delta (change in value disagreement from last iteration)
            value_metadata[idx][col]['disagreement'] = new_vdis                                                                                             # update this cell's value disagreement to the new value
            if vdis_d < 0:                                                                                                                                  # if the cell's value disagreement delta is negative
                vdis_d = 0                                                                                                                                      # set the cell's value disagreement to 0 so as to disallow negative tuple weights

            reinforcementValue += (vspr_d + new_vdis + vdis_d)                                      # update the reinforcement value for this row by adding the value spread delta, new value disagreement, and value disagreement delta

        tuple_metadata.at[idx, 'weight'] += reinforcementValue                                  # update the weight for this row

    print('Tuple weights:')
    pprint(tuple_metadata['weight'])
    print()
    tuple_metadata.to_pickle('./store/' + project_id + '/tuple_metadata.p')                     # save the updated tuple metadata DataFrame
    pickle.dump( value_metadata, open('./store/' + project_id + '/value_metadata.p', 'wb') )    # save the updated value metadata object


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
    tuple_metadata = pd.read_pickle('./store/' + project_id + '/tuple_metadata.p')                                              # load the tuple metadata DataFrame
    try:
        cfd_metadata = pickle.load( open('./store/' + project_id + '/cfd_metadata.p', 'rb') )                                       # load the CFD metadata object if it exists
    except FileNotFoundError:                                                                                                   # if the CFD metadata object does not exist
        cfd_metadata = None                                                                                                         # set cfd_metadata to None
    chosen_tups = tuple_metadata.sample(n=sample_size, weights='weight')                                                        # generate the list of tuple IDs in the sample; tuples with a larger weight (a.k.a. larger value in the 'weight' column of tuple_metadata) are more likely to be chosen
    print('Chosen example indexes:')
    pprint(chosen_tups.index)

    if cfd_metadata is not None:                                                                                                # if the CFD metadata object exists
        for idx in chosen_tups.index:                                                                                               # for each row in the sample
            seen = list()                                                                                                               # create an empty list to hold the list of CFDs that were applied in the latest iteration and resulted in the values in this sample
            for col in d_rep.columns:                                                                                                   # for each column in the dataset
            # Calculate how many rows the CFD was applied to in the sample
                if cfd_applied_map[current_iter][idx][col] is not None and cfd_applied_map[current_iter][idx][col] not in seen:             # if a CFD was applied to this cell in the last iteration and this is the first row in the sample this CFD was applied to
                    seen.append(cfd_applied_map[current_iter][idx][col])                                                                        # add this CFD to the list of seen CFDs
                    cfd_metadata[cfd_applied_map[current_iter][idx][col]]['num_changes'][current_iter] += 1                                     # increment the change count for this CFD for this iteration

        pickle.dump(cfd_metadata, open('./store/' + project_id + '/cfd_metadata.p', 'wb') )                                         # save the updated CFD metadata object

    sample = d_rep.iloc[chosen_tups.index]                                                                                      # get the data rows that have the sampled tuple IDs
    return sample
