# This module connects to the Charm framework

from players.receiver import ReceiverKeyword
from sys import *
import pickle

class CFD:
    def __init__(self, rule):
        self.lhs = rule[0]
        self.title = rule[1]

def prepareReceiver(project_id):
    receiverData = '../../store/' + project_id + '/discovered_cfds.txt'
    dataSource = project_id
    fileToStore = '_rules'

    receiver = ReceiverKeyword(receiverData, dataSource, fileToStore, 0.5)
    receiver.setData(receiverData, 'csv')
    receiver.initializeRE('../../store/' + project_id + '/')
    return receiver

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
            rule = receiver.data.getListRow(rule_id)
            rules.append(CFD(rule))
        return rules, rule_id_list
    except KeyError:
        print('No search results. Please try again.')
        return None

def reinforce(receiver, cfd_id, reinforcement_value):
    receiver.reinforce(cfd_id, reinforcement_value)
    print("The CFD with cfd_id " + cfd_id + " has been reinforced.")
