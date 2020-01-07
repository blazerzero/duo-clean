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

def getSearchResults(receiver, query, sampleSize):
    try:
        tokenizedQuery = query.split(' ')
        formattedQuery = []
        for q in tokenizedQuery:
            word = "('" + q + "')"
            formattedQuery.append(word)
        print(formattedQuery)

        searchResults = receiver.getTuples(formattedQuery, sampleSize)
        res = []

        for row in searchResults:
            rule = receiver.data.getListRow(row)
            res.append(CFD(rule))
        return res
    except KeyError:
        print('No search results. Please try again.')
        return None