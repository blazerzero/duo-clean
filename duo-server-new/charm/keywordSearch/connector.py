# This module connects to the interface

from players.receiver import ReceiverKeyword
from sys import *

class Movie:
    def __init__(self, info):
        self.imdbID = info[0]
        self.title = info[1]
        self.year = info[2]
        self.rating = info[3]
        self.runtime = info[4]
        self.genre = info[5]
        self.released = info[6]
        self.director = info[7]
        self.writer = info[8]
        self.cast = info[9]
        self.metacritic = info[10]
        self.imdbRating = info[11]
        self.imdbVotes = info[12]
        self.poster = info[13]
        self.plot = info[14]
        self.language = info[15]
        self.country = info[16]
        self.awards = info[17]
        self.lastUpdated = info[18]

def prepareReceiver():
    reinforcementValue = 1
    dataSource = 'movieFiles'
    datafile = 'movies-with-plot-rating-runtime.csv'
    receiverData = './omdbsearch/UserStudy/keywordSearch/datasets/WebTableBenchmark-packaged/' + dataSource + '/' + datafile
    fileToSave = 'Testing'

    receiver = ReceiverKeyword(receiverData, dataSource, fileToSave, 0.5)
    receiver.setData(receiverData, 'csv')
    receiver.initializeRE()
    header = receiver.data.getHeader()
    print('Ready')
    return receiver, header

def getSearchResults(receiver, header, query):
    try:
        tokenizedQuery = query.split(' ')
        formattedQuery = []
        for q in tokenizedQuery:
            word = "('"
            word += q
            word += "')"
            formattedQuery.append(word)
        print(formattedQuery)

        searchResults = receiver.getTuples(formattedQuery, 10)

        res = []
        print("Search Result imdbIDs:")
        for i in range(0, 10):
            row = searchResults[i]
            info = receiver.data.getListRow(row)
            res.append(Movie(info))
            print(info[0])
        return res, searchResults
    except KeyError:
        res = 'No search results. Please try again.'
        return res, None

def getResultDetails(receiver, header, searchResults, idx, reinforcementValue):
    movieInfo = receiver.data.getListRow(searchResults[idx])
    '''res = '<details>'
    for i in range(0, len(header)):
        res += '<'+header[i]+'>'
        res += chosenResult[i]
        res += '</'+header[i]+'>'
    res += '</details>'''
    receiver.reinforce(searchResults[idx], reinforcementValue)
    print("The tuple with imdbID " + searchResults[idx] + " has been reinforced.")
    return Movie(movieInfo)
