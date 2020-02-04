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
PURPOSE:
INPUT:
OUTPUT:
* receiver: The system learning object
'''
def prepareReceiver(project_id, data, query):
    projectPath = './store/' + project_id + '/'
    #dataSource = project_id
    #fileToStore = '_rules'

    receiver = ReceiverKeyword(projectPath, None, None, None, None, data, query)
    receiver.initializeRE_CFD()
    return receiver


'''
FUNCTION: updateReceiver
PURPOSE:
INPUT:
OUTPUT: None
'''
def updateReceiver(receiver, data, query):
    receiver.strategy.updateStrategy(data, query)
    #return receiver


'''
FUNCTION: getRules
PURPOSE:
INPUT:
OUTPUT:
* rules: The selected CFDs, or None if there was a KeyError while searching
* rule_id_list: A list of the IDs of the selected CFDs, or None if there was a KeyError while searching
'''
def getRules(receiver, query, sample_size):
    try:
        tokenized_query = query.split(' ')
        formatted_query = []
        for q in tokenized_query:
            word = "('" + q + "')"
            formatted_query.append(word)
        print(formatted_query)

        rule_id_list = receiver.getTuples(formatted_query, sample_size)
        rules = []

        for rule_id in rule_id_list:
            rule = receiver.data[rule_id]
            rules.append(CFD(rule))
        return rules, rule_id_list
    except KeyError:
        print('No search results. Please try again.')
        return None, None


'''
FUNCTION: reinforce
PURPOSE:
INPUT:
OUTPUT: None
'''
def reinforce(receiver, cfd_id, reinforcement_value):
    receiver.reinforce(cfd_id, reinforcement_value)
    print("The CFD with cfd_id " + str(cfd_id) + " has been reinforced.")
