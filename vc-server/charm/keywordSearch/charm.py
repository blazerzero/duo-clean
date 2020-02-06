# This module connects to the Charm framework

from players.receiver import ReceiverKeyword
from sys import *
import pickle

class CFD:
    def __init__(self, rule):
        self.cfd_id = rule[0]
        self.lhs = rule[1]
        self.rhs = rule[2]


'''
FUNCTION: prepareReceiver
PURPOSE: Initialize the system learning receiver
INPUT:
* project_id: The ID of the interaction.
* data: The initial set of discovered CFDs
* query: A formatted version of the rows the user modified; used for mapping repaired tuples to CFDs in the receiver
OUTPUT:
* receiver: The system learning object
'''
def prepareReceiver(project_id, data, query):
    projectPath = './store/' + project_id + '/'

    receiver = ReceiverKeyword(projectPath, None, None, None, None, data, query)        # initialize the bare receiver
    receiver.initializeRE_CFD()     # set the receiver to be a Charm CFD receiver
    return receiver


'''
FUNCTION: updateReceiver
PURPOSE: Add new data to the system learning receiver
INPUT:
* receiver: The system learning object
* data: The set of newly discovered CFDs
* query: A formatted version of the rows the user modified; used for mapping repaired tuples to CFDs in the receiver
OUTPUT: None
'''
def updateReceiver(receiver, data, query):
    receiver.strategy.updateStrategy(data, query)       # add new data to the receiver and update feature mappings
    #return receiver


'''
FUNCTION: getRules
PURPOSE: Select CFDs to apply via the learning receiver
INPUT:
* receiver: The system learning object
* query: A stringified representation of the rows repaired by the user.
* sample_size: How many CFDs are to be selected
OUTPUT:
* rules: The selected CFDs, or None if there was a KeyError while searching
* rule_id_list: A list of the IDs of the selected CFDs, or None if there was a KeyError while searching
'''
def getRules(receiver, query, sample_size):
    try:
        rule_id_list = receiver.getTuples(query, sample_size)       # get rule IDs from receiver
        rules = []

        for rule_id in rule_id_list:
            #print(receiver.data[rule_id])
            rule = receiver.data[rule_id]       # get the rule that corresponds with this rule ID
            rules.append(rule)                  # add the rule to the list of selected rules
        return rules, rule_id_list
    except KeyError:        # There was an error selecting CFDs from the receiver
        print('There was an error selecting CFDs. Please try again.')
        return None, None


'''
FUNCTION: reinforce
PURPOSE: Reinforce the weight of a particular CFD
INPUT:
* receiver: The system learning object
* cfd_id: The CFD ID of a particular CFD
* reinforcement_value: The value to reinforce the CFD's weight by
OUTPUT: None
'''
def reinforce(receiver, cfd_id, reinforcement_value):
    receiver.reinforce(cfd_id, reinforcement_value)         # reinforce the weight of this CFD
    print("The CFD with cfd_id " + str(cfd_id) + " has been reinforced.")
