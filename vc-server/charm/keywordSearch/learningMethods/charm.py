import random
import math
from datatype.features import FeatureConstructor
from datatype.whooshengine import KeywordSearchWithLearning
import pprint
import time
import heapq
import pickle
from whoosh import scoring
import pickle
import os
import pdb

class ReceiverCharmKeyword_Feature_NoFeature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore):
		super(ReceiverCharmKeyword_Feature_NoFeature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore


	def setupStrategy(self, data):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
			for intentFeature in intentFeatures:
				if intentFeature not in self.features:
					self.features.append(intentFeature)
				if intentFeature not in self.invertedIndex:
					self.invertedIndex[intentFeature] = list()
				self.invertedIndex[intentFeature].append(tupleID)
				self.numOfFeatures[tupleID].append(intentFeature)

	def pickSingleReturn(self, tupleWeights):
		chance = random.uniform(0, 1)
		cumulative = 0
		total = 0
		total = sum(tupleWeights.values())
		for tupleID in tupleWeights:
			cumulative += float(tupleWeights[tupleID])/total
			if cumulative > chance:
				return tupleID

	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signalsReceived]
		keywordQuery = ' '.join(keywordQuery)

		#signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()

		for signal in signalsReceived:
			if signal not in self.featureWeights:
				self.featureWeights[signal] = dict()

		# i = 0
		# for rID in returnedIDs:
		# 	for feature in self.numOfFeatures[rID]:
		# 		for signal in signalsReceived:
		# 			if feature not in self.featureWeights[signal]:
		# 				self.featureWeights[signal][feature] = 1
		# 	i += 1

		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			for signal in signalsReceived:
				if rID not in self.featureWeights[signal]:
					self.featureWeights[signal][rID] = 1

				weight += (self.featureWeights[signal][rID]) + scores[i]
			tupleWeights[rID] = math.exp(weight)
			i += 1

		print('getWeights: ' + str(time.time() - time_start))
		time_start = time.time()
		while len(returnedTuples) < numberToReturn:
			returnedTuple = self.pickSingleReturn(tupleWeights)
			if returnedTuple not in returnedTuples:
				returnedTuples.append(returnedTuple)
			if len(returnedTuples) >= len(returnedIDs):
				break

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples

	def reinforce(self, signals, intent, score):
#		for signal in self.strategy:
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		#signal = keywordQuery
		for inte in intent:
			if inte is not None:
				for signal in signals:
					self.featureWeights[signal][inte] += score


class ReceiverCharmKeyword_NoFeature_Feature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, projectPath):
		super(ReceiverCharmKeyword_NoFeature_Feature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore


	def setupStrategy(self, data):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
			for intentFeature in intentFeatures:
				if intentFeature not in self.features:
					self.features.append(intentFeature)
				if intentFeature not in self.invertedIndex:
					self.invertedIndex[intentFeature] = list()
				self.invertedIndex[intentFeature].append(tupleID)
				self.numOfFeatures[tupleID].append(intentFeature)

	def pickSingleReturn(self, tupleWeights):
		chance = random.uniform(0, 1)
		cumulative = 0
		total = sum(tupleWeights.values())
		for tupleID in tupleWeights:
			cumulative += float(tupleWeights[tupleID])/total
			if cumulative > chance:
				return tupleID

	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signalsReceived]
		keywordQuery = ' '.join(keywordQuery)

		signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()


		if signal not in self.featureWeights:
			self.featureWeights[signal] = dict()

		# i = 0
		# for rID in returnedIDs:
		# 	for feature in self.numOfFeatures[rID]:
		# 		for signal in signalsReceived:
		# 			if feature not in self.featureWeights[signal]:
		# 				self.featureWeights[signal][feature] = 1
		# 	i += 1

		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			for feature in self.numOfFeatures[rID]:
				if feature not in self.featureWeights[signal]:
					self.featureWeights[signal][feature] = 1

				weight += (self.featureWeights[signal][feature]/len(self.numOfFeatures[rID])) + scores[i]
			tupleWeights[rID] = math.exp(weight)
			i += 1

		print('getWeights: ' + str(time.time() - time_start))
		time_start = time.time()
		while len(returnedTuples) < numberToReturn:
			returnedTuple = self.pickSingleReturn(tupleWeights)
			if returnedTuple not in returnedTuples:
				returnedTuples.append(returnedTuple)
			if len(returnedTuples) >= len(returnedIDs):
				break

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples

	def reinforce(self, signals, intent, score):
#		for signal in self.strategy:
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		signal = keywordQuery
		for inte in intent:
			if inte is not None:
				for featureOfIntent in self.numOfFeatures[inte]:
					self.featureWeights[signal][featureOfIntent] += score


class ReceiverCharmKeyword_NoFeature_NoFeature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore):
		super(ReceiverCharmKeyword_NoFeature_NoFeature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore


	def setupStrategy(self, data):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
			for intentFeature in intentFeatures:
				if intentFeature not in self.features:
					self.features.append(intentFeature)
				if intentFeature not in self.invertedIndex:
					self.invertedIndex[intentFeature] = list()
				self.invertedIndex[intentFeature].append(tupleID)
				self.numOfFeatures[tupleID].append(intentFeature)

	def pickSingleReturn(self, tupleWeights):
		chance = random.uniform(0, 1)
		cumulative = 0
		total = sum(tupleWeights.values())
		for tupleID in tupleWeights:
			cumulative += float(tupleWeights[tupleID])/total
			if cumulative > chance:
				return tupleID

	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signalsReceived]
		keywordQuery = ' '.join(keywordQuery)

		signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()


		if signal not in self.featureWeights:
			self.featureWeights[signal] = dict()

		# i = 0
		# for rID in returnedIDs:
		# 	for feature in self.numOfFeatures[rID]:
		# 		for signal in signalsReceived:
		# 			if feature not in self.featureWeights[signal]:
		# 				self.featureWeights[signal][feature] = 1
		# 	i += 1

		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			if rID not in self.featureWeights[signal]:
				self.featureWeights[signal][rID] = 1

			weight += (self.featureWeights[signal][rID]) + scores[i]
			tupleWeights[rID] = math.exp(weight)
			i += 1

		print('getWeights: ' + str(time.time() - time_start))
		time_start = time.time()
		while len(returnedTuples) < numberToReturn:
			returnedTuple = self.pickSingleReturn(tupleWeights)
			if returnedTuple not in returnedTuples:
				returnedTuples.append(returnedTuple)
			if len(returnedTuples) >= len(returnedIDs):
				break

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples

	def reinforce(self, signals, intent, score):
#		for signal in self.strategy:
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		signal = keywordQuery
		for inte in intent:
			if inte is not None:
				self.featureWeights[signal][inte] += score


class ReceiverCharmCFD(object):
	"""docstring from ReceiverCharm CFD"""
	def __init__(self, data, projectPath, signalsReceived):
		self.featureMap = dict()
		self.featureWeights = dict()
		self.returnedCFDs = list()
		self.receivedSignals = list()
		self.projectPath = projectPath
		self.maxValue = dict()
		self.cfds = dict()
		self.cfdWeights = dict()
		self.updateStrategy(data, signalsReceived)

	def save_obj(self, obj, name):
		#with open(name, 'wb') as f:
		pickle.dump(obj, open(name, 'wb'))

	def load_obj(self, name):
		#with open(name, 'rb') as f:
		return pickle.load(open(name, 'rb'))

	def loadPickle(self, obj, name):
		try:
			obj = load_obj(name)
		except (OSError, IOError) as e:
			save_obj(obj, name)

		return obj

	########################################
	# FUNCTION: updateStrategy
	# PURPOSE:
	# INPUT:
	# OUTPUT:
	########################################
	def updateStrategy(self, cfds, signalsReceived):
		self.receivedSignals = signalsReceived
		print('Updating strategy...')

		for signal in self.receivedSignals:
			if signal not in self.maxValue:
				self.maxValue[signal] = 1

		if os.path.exists(self.projectPath + 'feature_map.p'):
			print('Loading feature map...')
			self.featureMap = self.load_obj(self.projectPath + 'feature_map.p')
		else:
			print('Creating feature map...')

		for cfd in cfds:
			lhs = cfd['cfd'].split(' => ')[0][1:-1]
			rhs = cfd['cfd'].split(' => ')[1]
			print(lhs)
			print(rhs)
			#print([cL for cL in lhs.split(', ')])
			#print([cR for cR in rhs.split(', ')])
			cfdFeatures = [cL for cL in lhs.split(', ')]
			cfdFeatures.extend([cR for cR in rhs.split(', ')])
			cfdID = cfd['cfd_id']
			if cfdID not in self.cfds.keys():
				self.cfds[cfdID] = dict()
				self.cfds[cfdID]['lhs'] = lhs
				self.cfds[cfdID]['rhs'] = rhs
			if cfdID not in self.featureMap:
				self.featureMap[cfdID] = list()
			for feature in cfdFeatures:
				if feature not in self.featureMap[cfdID]:
					self.featureMap[cfdID].append(feature)

		print('Saving stats...')
		self.save_obj(self.featureMap, self.projectPath + 'feature_map.p')
		print('Done updating strategy!')

	########################################
	# FUNCTION: pickSingleReturn
	# PURPOSE:
	# INPUT:
	# OUTPUT:
	########################################
	def pickSingleReturn(self, cfdWeights):
		chance = random.uniform(0, 1)
		cumulative = 0
		total = sum(cfdWeights.values())
		for cfdID in cfdWeights:
			cumulative += cfdWeights[cfdID]/total
			if cumulative > chance:
				del cfdWeights[cfdID]
				return cfdID

	########################################
	# FUNCTION: returnTuples
	# PURPOSE:
	# INPUT:
	# OUTPUT:
	########################################
	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived

		returnedCFDs = list()
		cfdIDs = self.cfds.keys()
		cfdWeights = dict()

		for cfdID in cfdIDs:
			topKFeaturesStore = dict()
			weight = 1
			for signal in self.receivedSignals:
				if signal not in self.featureWeights:
					self.featureWeights[signal] = dict()
				for feature in self.featureMap[cfdID]:
					if feature not in self.featureWeights[signal]:
						self.featureWeights[signal][feature] = 1
					topKFeaturesStore[(signal, feature)] = self.featureWeights[signal][feature]

			topKFeatures = heapq.nlargest(100, topKFeaturesStore, key=topKFeaturesStore.__getitem__)
			for signal, feature in topKFeatures:
				weight *= math.exp(self.featureWeights[signal][feature]/self.maxValue[signal])
			cfdWeights[cfdID] = weight

		while len(returnedCFDs) < numberToReturn:
			returnedCFD = self.pickSingleReturn(cfdWeights)
			if returnedCFD not in returnedCFDs:
				returnedCFDs.append(returnedCFD)
			if len(returnedCFDs) >= len(cfdIDs):
				break

		self.returnedCFDs = returnedCFDs
		return returnedCFDs

	########################################
	# FUNCTION: reinforce
	# PURPOSE:
	# INPUT:
	# OUTPUT:
	########################################
	def reinforce(self, signals, intent, score):
		for inte in intent:
			if inte is not None:
				for featureOfIntent in self.cfds[inte]:
					for sig in signals:
						if sig in self.featureWeights.keys():
							if featureOfIntent in self.featureWeights[sig].keys():
								self.featureWeights[sig][featureOfIntent] += score
							else:
								self.featureWeights[sig][featureOfIntent] = score
						else:
							self.featureWeights[sig] = dict()
							self.featureWeights[sig][featureOfIntent] = score
						if self.featureWeights[sig][featureOfIntent] > self.maxValue[sig]:
							self.maxValue[sig] = self.featureWeights[sig][featureOfIntent]


class ReceiverCharmKeyword_CFDLite_OLD(object):
	"""docstring for ReceiverCharm Lite"""
	def __init__(self, data, dataSource, fileToStore, projectPath):
		super(ReceiverCharmKeyword_CFDLite_OLD, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.dataPath = dataSource
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.fileToStore = fileToStore
		self.receiver = dict()
		self.projectPath = projectPath
		self.updateStrategy(data)
		self.maxValue = dict()

	def save_obj(self, obj, name):
		with open(name + '.pkl', 'wb') as f:
			pickle.dump(obj, f)

	def load_obj(self, name):
		with open(name + '.pkl', 'rb') as f:
			return pickle.load(f)

	def loadPickle(self, obj, name):
		try:
			obj = load_obj(name)
		except (OSError, IOError) as e:
			save_obj(obj, name)

		return obj

	def updateStrategy(self, data):
		print('Updating strategy...')
		listOfTuples = data
		lengthOfFeatures = list()

		print('Updating records...')

		if os.path.exists(projectPath + 'idfStats/' + self.dataPath + self.fileStore + '/'):
			print('Loading data...')
			self.invertedIndex = self.load_obj(self.projectPath + 'idfStats/' + self.dataPath + self.fileToStore + '/invertedIndex')
			self.numOfFeatures = self.load_obj(self.projectPath + 'idfStats/' + self.dataPath + self.fileToStore + '/numOfFeatures')
		else:
			os.makedirs(projectPath + 'idfStats/' + self.dataPath + self.fileToStore + '/')
			print('Creating data...')

		for record in listOfTuples:
			intentFeatures = [cL for cL in record['lhs'].split(', ')].extend([cR for cR in record['rhs'].split(', ')])
			tupleID = record['cfd_id']
			if tupleID not in self.receiver.keys():
				self.receiver[tupleID] = dict()
				self.receiver[tupleID]['lhs'] = record['lhs']
				self.receiver[tupleID]['rhs'] = record['rhs']
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
			for intentFeature in intentFeatures:
				if intentFeature not in self.invertedIndex:
					self.invertedIndex[intentFeature] = list()
				if tupleID not in self.invertedIndex[intentFeature]:
					self.invertedIndex[intentFeature].append(tupleID)
				if intentFeature not in self.numOfFeatures[tupleID]:
					self.numOfFeatures[tupleID].append(intentFeature)

			lengthOfFeatures.append(len(self.numOfFeatures[tupleID]))

		print('Saving stats...')
		self.save_obj(self.invertedIndex, self.projectPath + 'idfStats/' + self.dataPath + self.fileToStore + '/invertedIndex')
		self.save_obj(self.numOfFeatures, self.projectPath + 'idfStats/' + self.dataPath + self.fileToStore + '/numOfFeatures')
		print('Done updating strategy!')

	def pickSingleReturn(self, tupleWeights):
		chance = random.uniform(0, 1)
		cumulative = 0
		total = sum(tupleWeights.values())
		for tupleID in tupleWeights:
			cumulative += tupleWeights[tupleID]/total
			if cumulative > chance:
				del tupleWeights[tupleID]
				return tupleID

	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived
		#keywordQuery = ' '.join(signalsReceived)		# signalsReceived should come in as a list of "words"

		returnedTuples = list()
		cfdIDs = self.receiver.keys()
		tupleWeights = dict()

		for cfdID in cfdIDs:
			topKFeaturesStore = dict()
			weight = 1
			for signal in signalsReceived:
				if signal not in self.featureWeights:
					self.featureWeights[signal] = dict()
				if signal not in self.maxValue:
					self.maxValue[signal] = 1
				for feature in self.numOfFeatures[cfdID]:
					if feature not in self.featureWeights[signal]:
						self.featureWeights[signal][feature] = 1
					topKFeaturesStore[(signal, feature)] = self.featureWeights[signal][feature]

			topKFeatures = heapq.nlargest(100, topKFeaturesStore, key=topKFeaturesStore.__getitem__)
			for signal, feature in topKFeatures:
				weight *= math.exp(self.featureWeights[signal][feature]/self.maxValue[signal])
			tupleWeights[cfdID] = weight

		#topKWewights = heapq.nlargest(10, tupleWeights, key=tupleWeights.__getitem__)
		while len(returnedTuples) < numberToReturn:
			returnedTuple = self.pickSingleReturn(tupleWeights)
			if returnedTuple not in returnedTuples:
				returnedTuples.append(returnedTuple)
			if len(returnedTuples) >= len(cfdIDs):
				break

		self.returnedTuples = returnedTuples
		return returnedTuples

	def reinforce(self, signals, intent, score):
		#keywordQuery = ' '.join(signals)

		for inte in intent:
			if inte is not None:
				for featureOfIntent in self.numOfFeatures[inte]:
					for sig in signals:
						self.featureWeights[sig][featureOfIntent] += score
						if self.featureWeights[sig][featureOfIntent] > self.maxValue[sig]:
							self.maxValue[sig] = self.featureWeights[sig][featureOfIntent]


class ReceiverCharmKeyword(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, idfLevel, projectPath):
		super(ReceiverCharmKeyword, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.dataPath = dataSource
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.fileToStore = fileToStore
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.setupStrategy(data, idfLevel, projectPath)
		self.fileToStore = fileToStore
		self.maxValue = dict()


	# def lengths(self, x):
	# 	if isinstance(x,list):
	# 		yield len(x)
	# 		for y in x:
	# 			yield from lengths(y)

	def save_obj(self, obj, name):
		with open(name + '.pkl', 'wb') as f:
			pickle.dump(obj, f)


	def load_obj(self, name):
		with open(name + '.pkl', 'rb') as f:
			return pickle.load(f)


	def loadPickle(self, obj, name):
		try:
			obj = load_obj(name)
		except (OSError, IOError) as e:
			save_obj(obj, name)

		return obj

	def setupStrategy(self, data, idfLevel, projectPath):
		print('Setting Up Strategy')
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		lengthOfFeatures = list()
		countTermInDoc = dict()
		self.idf = dict()
		print('Initializing records...')
		#"+self.dataPath+self.fileToStore+"
		#100ksigmodDemoRE_100k
		#/data/mccamish/datatype/idfStats/100ksigmodDemoRE_100k,,1547895437000
		if not os.path.exists(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/"):
			os.makedirs(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/")
			print('Creating data...')
			for record in listOfTuples:

				intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				tupleID = record[0]
				if tupleID not in self.numOfFeatures:
					self.numOfFeatures[tupleID] = list()
				for intentFeature in intentFeatures:
					if intentFeature not in self.features:
						self.features.append(intentFeature)
					if intentFeature not in self.invertedIndex:
						self.invertedIndex[intentFeature] = list()
					if tupleID not in self.invertedIndex[intentFeature]:
						self.invertedIndex[intentFeature].append(tupleID)
					if intentFeature not in self.numOfFeatures[tupleID]:
						self.numOfFeatures[tupleID].append(intentFeature)
					if intentFeature not in countTermInDoc:
						countTermInDoc[intentFeature] = 1
					else:
						countTermInDoc[intentFeature] += 1

				lengthOfFeatures.append(len(self.numOfFeatures[tupleID]))

			print('Getting IDF stats...')
			numDocuments = len(listOfTuples)
			for term in countTermInDoc:
				self.idf[term] = math.log(numDocuments / float(countTermInDoc[term]))
			maxIDF = max(list(self.idf.values()))

			for term in self.idf:
				self.idf[term] = self.idf[term]/maxIDF
				#print(self.idf[term])
			print('removing features...')
			for term in countTermInDoc:
				if self.idf[term] < idfLevel:
					del self.invertedIndex[term]
					for intent in self.numOfFeatures:
						if term in self.numOfFeatures[intent]:
							self.numOfFeatures[intent].remove(term)

			print('saving stats')
			self.save_obj(self.idf, projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/idf")
			self.save_obj(self.invertedIndex, projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/invertedIndex")
			self.save_obj(self.numOfFeatures, projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/numOfFeatures")
			self.save_obj(self.features, projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/features")

		else:
			print("loading data...")
			self.idf = self.load_obj(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/idf")
			self.invertedIndex = self.load_obj(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/invertedIndex")
			self.numOfFeatures = self.load_obj(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/numOfFeatures")
			self.features = self.load_obj(projectPath+"idfStats/"+self.dataPath+self.fileToStore+"/features")

	def pickSingleReturn(self, tupleWeights):
		#print(len(tupleWeights))
		chance = random.uniform(0, 1)
		cumulative = 0
		total = sum(tupleWeights.values())
		for tupleID in tupleWeights:
			cumulative += tupleWeights[tupleID]/total
			#print('weight',tupleWeights[tupleID])
			#print('total',total)
			#print('cum',cumulative)
			if cumulative > chance:
				del tupleWeights[tupleID]
				return tupleID

	def returnTuples(self, signalsReceived, numberToReturn):
		self.receivedSignals = signalsReceived
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signalsReceived]
		keywordQuery = ' '.join(keywordQuery)
		topKFeaturesStore = dict()
		#signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()

		# for signal in signalsReceived:
		# 	if signal not in self.featureWeights:
		# 		self.featureWeights[signal] = dict()

		# i = 0
		# for rID in returnedIDs:
		# 	for feature in self.numOfFeatures[rID]:
		# 		for signal in signalsReceived:
		# 			if feature not in self.featureWeights[signal]:
		# 				self.featureWeights[signal][feature] = 1
		# 	i += 1

		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			topKFeaturesStore = dict()
			weight = 1
			for signal in signalsReceived:
				#print('1')
				if signal not in self.featureWeights:
					self.featureWeights[signal] = dict()
				#print('2')
				# if len(self.featureWeights[signal].values()) > 0:
				# 	maxValue = max(self.featureWeights[signal].values())
				# else:
				#print(len(self.featureWeights[signal].values()))
				#maxValue = 1
				#print('3')
				if signal not in self.maxValue:
					self.maxValue[signal] = 1

				#if rID not in self.featuresStored[signal]:
				for feature in self.numOfFeatures[rID]:
					if feature not in self.featureWeights[signal]:
						self.featureWeights[signal][feature] = 1
					topKFeaturesStore[(signal, feature)] = self.featureWeights[signal][feature]

				#self.featuresStored[signal].add(rID)
			topKFeatures = heapq.nlargest(100, topKFeaturesStore, key=topKFeaturesStore.__getitem__)
			#print(topKFeatures)
			for signal, feature in topKFeatures:
				#print(signal)
				#topKFeatures = sorted(range(len(self.numOfFeatures[rID])), key=lambda i: self.numOfFeatures[rID][i])[-100:]
				#print(topKFeatures)

				weight *= math.exp(self.featureWeights[signal][feature]/self.maxValue[signal])# + scores[i]
					#print(self.featureWeights[signal][feature])
					#print(self.maxValue[signal])
					#print(weight)
				#print('4')
			#print(weight)
			tupleWeights[rID] = weight
			i += 1
		topKWeights = heapq.nlargest(10, tupleWeights, key=tupleWeights.__getitem__)
		# #print(signalsReceived)
		for w in topKWeights:
			if tupleWeights[w] == 1:
		 		print(tupleWeights)
		 		print()
		 		print(topKFeatures)
			print(w, tupleWeights[w]/sum(tupleWeights.values()))
		print('getWeights: ' + str(time.time() - time_start))
		time_start = time.time()
		while len(returnedTuples) < numberToReturn:
			returnedTuple = self.pickSingleReturn(tupleWeights)
			if returnedTuple not in returnedTuples:
				returnedTuples.append(returnedTuple)
			if len(returnedTuples) >= len(returnedIDs):
				break

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		#for row in returnedTuples:
		#	print("this " + row[0:9])
		#	if row[0:9] in tupleWeights:
		#		print(row[0:9] + ' weight: ' + tupleWeights[i])
		#print(tupleWeights)
		return returnedTuples

	def reinforce(self, signals, intent, score):
#		for signal in self.strategy:
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		#signal = keywordQuery
		for inte in intent:
			if inte is not None:
				for featureOfIntent in self.numOfFeatures[inte]:
					for sig in signals:
						# print(sig, inte)
						# print(self.featureWeights[sig][featureOfIntent])
						self.featureWeights[sig][featureOfIntent] += score
						# print(self.featureWeights[sig][featureOfIntent])
						# print()
						if self.featureWeights[sig][featureOfIntent] > self.maxValue[sig]:
							self.maxValue[sig] = self.featureWeights[sig][featureOfIntent]
		#time.sleep(3)


# class ReceiverCharmAll(object):
# 	"""docstring for ReceiverCharm"""
# 	def __init__(self, data):
# 		super(ReceiverCharmAll, self).__init__()
# 		self.strategy = dict()
# 		self.tupleIDs = list()
# 		self.setupStrategy(data)

# 	def setupStrategy(self, data):
# 		#b000jz4hqo
# 		listOfTuples = data.getValues()
# 		for record in listOfTuples:
# 			self.tupleIDs.append(record[0])

# 	def pickSingleReturn(self, tupleWeights):
# 		chance = random.uniform(0, 1)
# 		cumulative = 0
# 		total = sum(tupleWeights.values())
# 		for tupleID in tupleWeights:
# 			cumulative += float(tupleWeights[tupleID])/total
# 			if cumulative > chance:
# 				return tupleID

# 	def returnTuples(self, signalsReceived, numberToReturn):
# 		self.receivedSignals = signalsReceived
# 		returnedTuples = list()
# 		for signal in signalsReceived:
# 			if signal not in self.strategy:
# 				self.strategy[signal] = dict()
# 				for tupleID in self.tupleIDs:
# 					if tupleID not in self.strategy[signal]:
# 						self.strategy[signal][tupleID] = 1

# 		time_start = time.time()
# 		tupleWeights = dict()
# 		# for feature in self.features:
# 		# 	tupleIDs = self.invertedIndex[feature]
# 		# 	for tupleID in tupleIDs:
# 		# 		for signal in signalsReceived:
# 		# 			weight = self.featureWeights[signal][feature]
# 		# 			if tupleID not in tupleWeights:
# 		# 				tupleWeights[tupleID] = weight/len(self.numOfFeatures[tupleID])
# 		# 			else:
# 		# 				tupleWeights[tupleID] += weight/len(self.numOfFeatures[tupleID])


# 		for signal in signalsReceived:
# 			for tupleID in self.strategy[signal]:
# 				weight = self.strategy[signal][tupleID]
# 				if tupleID not in tupleWeights:
# 					tupleWeights[tupleID] = weight
# 				else:
# 					tupleWeights[tupleID] += weight

# 		print('getWeights: ' + str(time.time() - time_start))
# 		time_start = time.time()
# 		while len(returnedTuples) < numberToReturn:
# 			returnedTuple = self.pickSingleReturn(tupleWeights)
# 			if returnedTuple not in returnedTuples:
# 				returnedTuples.append(returnedTuple)
# 		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
# 		self.returnedTuples = returnedTuples
# 		return returnedTuples

# 	def reinforce(self, signals, intent, score):
# #		for signal in self.strategy:
# 		for signal in signals:
# 			for inten in intent:
# 				self.strategy[signal][inten] += score




# class ReceiverCharm(object):
# 	"""docstring for ReceiverCharm"""
# 	def __init__(self, data):
# 		super(ReceiverCharm, self).__init__()
# 		self.features = list()
# 		self.invertedIndex = dict()
# 		self.numOfFeatures = dict()
# 		self.featureWeights = dict()
# 		self.returnedTuples = list()
# 		self.receivedSignals = list()
# 		self.setupStrategy(data)

# 	def setupStrategy(self, data):
# 		#b000jz4hqo
# 		featureConst = FeatureConstructor()
# 		listOfTuples = data.getValues()
# 		allSignals = set()
# 		for record in listOfTuples:
# 			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
# 			tupleID = record[0]
# 			if tupleID not in self.numOfFeatures:
# 				self.numOfFeatures[tupleID] = list()
# 			for intentFeature in intentFeatures:
# 				if intentFeature not in self.features:
# 					self.features.append(intentFeature)
# 				if intentFeature not in self.invertedIndex:
# 					self.invertedIndex[intentFeature] = list()
# 				self.invertedIndex[intentFeature].append(tupleID)
# 				self.numOfFeatures[tupleID].append(intentFeature)

# 	def pickSingleReturn(self, tupleWeights):
# 		chance = random.uniform(0, 1)
# 		cumulative = 0
# 		total = sum(tupleWeights.values())
# 		for tupleID in tupleWeights:
# 			cumulative += float(tupleWeights[tupleID])/total
# 			if cumulative > chance:
# 				return tupleID

# 	def returnTuples(self, signalsReceived, numberToReturn):
# 		self.receivedSignals = signalsReceived
# 		returnedTuples = list()
# 		for signal in signalsReceived:
# 			if signal not in self.featureWeights:
# 				self.featureWeights[signal] = dict()
# 				for feature in self.features:
# 					if feature not in self.featureWeights[signal]:
# 						self.featureWeights[signal][feature] = 1
# 		time_start = time.time()
# 		tupleWeights = dict()
# 		# for feature in self.features:
# 		# 	tupleIDs = self.invertedIndex[feature]
# 		# 	for tupleID in tupleIDs:
# 		# 		for signal in signalsReceived:
# 		# 			weight = self.featureWeights[signal][feature]
# 		# 			if tupleID not in tupleWeights:
# 		# 				tupleWeights[tupleID] = weight/len(self.numOfFeatures[tupleID])
# 		# 			else:
# 		# 				tupleWeights[tupleID] += weight/len(self.numOfFeatures[tupleID])


# 		for signal in signalsReceived:
# 			for feature in self.featureWeights[signal]:
# 				tupleIDs = self.invertedIndex[feature]
# 				weight = self.featureWeights[signal][feature]
# 				for tupleID in tupleIDs:
# 					if tupleID not in tupleWeights:
# 						tupleWeights[tupleID] = weight/len(self.numOfFeatures[tupleID])
# 					else:
# 						tupleWeights[tupleID] += weight/len(self.numOfFeatures[tupleID])

# 		print('getWeights: ' + str(time.time() - time_start))
# 		time_start = time.time()
# 		while len(returnedTuples) < numberToReturn:
# 			returnedTuple = self.pickSingleReturn(tupleWeights)
# 			if returnedTuple not in returnedTuples:
# 				returnedTuples.append(returnedTuple)
# 		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
# 		self.returnedTuples = returnedTuples
# 		return returnedTuples

# 	def reinforce(self, signals, intent, score):
# #		for signal in self.strategy:
# 		for signal in signals:
# 			for featureOfIntent in self.numOfFeatures[intent]:
# 				self.featureWeights[signal][featureOfIntent] += score

class SenderBaseline(object):
	"""docstring for SenderCharm"""
	def __init__(self, data, alpha):
		super(SenderBaseline, self).__init__()
		self.strategy = dict()
		self.setupStrategy(data, alpha)
		self.specificityDict = dict()

	def setupStrategy(self, data, alpha):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countSignals = dict()
		countTermInDoc = dict()
		self.uniqueSignals = list()
		self.idf = dict()

		for record in listOfTuples:
			signals = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			signalSet = set(signals)
			intent = record[0]
			if intent not in self.strategy:
				self.strategy[intent] = dict()
				for signal in signals:
					if signal not in self.strategy[intent]:
						self.strategy[intent][signal] = 1+alpha
						allSignals.add(signal)

					if signal not in countSignals:
						countSignals[signal] = 1
					else:
						countSignals[signal] += 1


			for signalSetSingle in signalSet:
				if signalSetSingle not in countTermInDoc:
					countTermInDoc[signalSetSingle] = 1
				else:
					countTermInDoc[signalSetSingle] += 1

		for intent in self.strategy:
			for signal in allSignals:
				if signal not in self.strategy[intent]:
					self.strategy[intent][signal] = 0.1

		for signal in countSignals:
			if countSignals[signal] <= 2:
				self.uniqueSignals.append(signal)

		numDocuments = len(listOfTuples)
		for term in countTermInDoc:
			self.idf[term] = math.log(numDocuments / float(countTermInDoc[term]))
		maxIDF = max(list(self.idf.values()))
		for term in self.idf:
			self.idf[term] = self.idf[term]/maxIDF
			#print(self.idf[term])

		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 1/len(allSignals)

	def pickTuplesToJoin(self, howMany=1):
		tuples = list()
		return list(self.strategy.keys())


	def pickSingleSignal(self, intent):
		total = sum(self.strategy[intent].values())
		chance = random.uniform(0, 1)
		cumulative = 0
		for signal in self.strategy[intent]:
			cumulative += float(self.strategy[intent][signal])/total
			if cumulative > chance:
				return signal

	def pickSingleUniqueSignal(self, intent, numberOfSignals):
		total = sum(self.strategy[intent].values())

		signalsAvailable = list(self.strategy[intent].keys())
		intersection = [val for val in self.uniqueSignals if val in signalsAvailable]
		if len(intersection) > 0 and len(intersection) > len(numberOfSignals):
			total = 0
			for signal in intersection:
				total += self.strategy[intent][signal]
			chance = random.uniform(0, 1)
			cumulative = 0

			for signal in intersection:
				cumulative += float(self.strategy[intent][signal])/total
				if cumulative > chance:
					return signal

	def randomlyPickSignals(self, keys, howMany):
		newList = list()
		while len(newList) < howMany:
			item = random.choice(keys)
			if item not in newList:
				newList.append(item)
			if len(newList) >= len(keys):
				break
		return newList

	def pickSignals(self, intent, howMany):
		signals = list()
		if howMany is not None:
			return self.randomlyPickSignals(list(self.strategy[intent].keys()), howMany)
		else:
			return list(self.strategy[intent].keys())

	def reinforce(self, intents, signals, score):
		#for intent in self.strategy:
		for intent in intents:
			for signal in signals:
				if signal in self.strategy[intent]:
					self.strategy[intent][signal] += score

class SenderCharm_zipf(object):
	"""docstring for SenderCharm"""
	def __init__(self, data, alpha, idfLevel, dataType, fileToStore, projectPath):
		super(SenderCharm_zipf, self).__init__()
		self.fileToStore = fileToStore
		self.dataType = dataType
		self.strategy = dict()
		self.setupStrategy(data, alpha, idfLevel, projectPath)
		self.specificityDict = dict()
		self.createDistribution()

	def save_obj_strat(self, obj, name ):
		with open(name + '.pkl', 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj_strat(self, name ):
		with open(name + '.pkl', 'rb') as f:
			return pickle.load(f)

	def save_obj(self, obj, name ):
		with open('zipf/'+ name + '.pkl', 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj(self, name ):
		with open('zipf/' + name + '.pkl', 'rb') as f:
			return pickle.load(f)

	def setupStrategy(self, data, alpha, idfLevel, projectPath):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countSignals = dict()
		countTermInDoc = dict()
		self.uniqueSignals = list()
		self.idf = dict()
		self.invertedIndex = dict()
		self.countSignals = dict()
		self.maxValue = dict()
		signalSet = set()
		intnetSet = set()
		self.distribution = dict()
		i = 0
		print(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/")
		if not os.path.exists(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/"):
			os.makedirs(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/")
			print('Creating data...')
			for record in listOfTuples:
				signals = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				signalSet = set(signals)
				intentSet = set(intentFeatures)
				intent = record[0]
				for intentFeature in intentSet:
					if intent not in self.invertedIndex:
						self.invertedIndex[intent] = list()
					self.invertedIndex[intent].append(intentFeature)
				self.countSignals[intent] = len(signalSet)
				for signalSetSingle in signalSet:
					if signalSetSingle not in countTermInDoc:
						countTermInDoc[signalSetSingle] = 1
					else:
						countTermInDoc[signalSetSingle] += 1

				i+=1

				for intent in intentSet:
					if intent not in self.strategy:
						self.strategy[intent] = dict()
					for signal in signalSet:
						self.strategy[intent][signal] = 1+alpha
						allSignals.add(signal)
			print(max(self.countSignals.values()))

			# for intent in self.strategy:
			# 	for signal in allSignals:
			# 		if signal not in self.strategy[intent]:
			# 			self.strategy[intent][signal] = alpha

			numDocuments = len(listOfTuples)
			for term in countTermInDoc:
				self.idf[term] = math.log(numDocuments / float(countTermInDoc[term]))
			maxIDF = max(list(self.idf.values()))
			for term in self.idf:
				self.idf[term] = self.idf[term]/maxIDF
				#print(self.idf[term])
			for term in countTermInDoc:
				if self.idf[term] < idfLevel:
					del self.strategy[term]
					for intent in self.invertedIndex:
						if term in self.invertedIndex[intent]:
							self.invertedIndex[intent].remove(term)
					for goodTerm in self.strategy:
						if term in self.strategy[goodTerm]:
							del self.strategy[goodTerm][term]


			print(len(self.strategy.keys()))

			print('saving stats')
			self.save_obj_strat(self.idf, projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/idf")
			self.save_obj_strat(self.invertedIndex, projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/invertedIndex")
			self.save_obj_strat(self.countSignals, projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/countSignals")
			self.save_obj_strat(self.strategy, projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/strategy")

		else:
			print("loading data...")
			self.idf = self.load_obj_strat(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/idf")
			self.invertedIndex = self.load_obj_strat(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/invertedIndex")
			self.countSignals = self.load_obj_strat(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/countSignals")
			self.strategy = self.load_obj_strat(projectPath+"idfStats/"+self.dataType+self.fileToStore+"_sender/strategy")
		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 1/len(allSignals)

	def createDistribution(self):
		try:
			self.distribution = self.load_obj(self.dataType)
		except (OSError, IOError) as e:
			i = 2
			for tup in self.invertedIndex.keys():
				self.distribution[tup] = 1/i
				i += 1
			self.save_obj(self.distribution, self.dataType)

	# 	i = 2
	# 	for tup in self.invertedIndex.keys():
	# 		self.distribution[tup] = 1/i
	# 		i += 1

	# 	self.save_obj(self.distribution, 'ag')

	def pickTuplesToJoin(self, howMany=1):
		tuples = list()
		while len(tuples) < howMany:
			chance = random.uniform(0, 1)
			cumulative = 0
			for tup in self.invertedIndex.keys():
				cumulative += self.distribution[tup]
				if cumulative > chance:
					if tup not in tuples:
						tuples.append(tup)
						if len(tuples) >= howMany:
							break

		return tuples

	def pickSingleSignal(self, featureWeights):
		total = sum(featureWeights.values())
		chance = random.uniform(0, 1)
		cumulative = 0
		for signal in featureWeights:
			cumulative += float(featureWeights[signal])/total
			if cumulative > chance:
				del featureWeights[signal]
				return signal

	def pickSignals(self, intents, howMany):
		signals = list()
		for intent in intents:
			currentSignalCount = 0
			featureWeights = dict()
			for intentFeature in self.invertedIndex[intent]:
				if intentFeature not in self.maxValue:
					self.maxValue[intentFeature] = 1
				#maxValue = max(self.strategy[intentFeature].values())
				for signalFeature in self.strategy[intentFeature]:
					if signalFeature not in featureWeights:
						featureWeights[signalFeature] = 1
					featureWeights[signalFeature] *= math.exp(self.strategy[intentFeature][signalFeature]/self.maxValue[intentFeature])

			while len(signals) < howMany:
				returnedSignal = self.pickSingleSignal(featureWeights)
				if returnedSignal not in signals:
					currentSignalCount += 1
					signals.append(returnedSignal)

				if self.countSignals[intent] <= currentSignalCount or len(featureWeights) == 0:
					break

		return signals

	def reinforce(self, intents, signals, score):
		#for intent in self.strategy:
		for intent in intents:
			for intentFeature in self.invertedIndex[intent]:
				for signal in signals:
					if signal in self.strategy[intentFeature]:
						self.strategy[intentFeature][signal] += score
						if self.strategy[intentFeature][signal] > self.maxValue[intentFeature]:
							self.maxValue[intentFeature] = self.strategy[intentFeature][signal]

	def addSignal(self, intent, features, weight):
		for intentFeature in self.invertedIndex[intent]:
			for feature in features:
				if feature not in self.strategy[intentFeature]:
					self.strategy[intentFeature][feature] = weight

	def addSignalWithIDFPrune(self, intent, features, receiverIDF, idfLevel):

		for intentFeature in self.invertedIndex[intent]:

			# weight is 50% of the highest weighted feature in self.strategy[intentFeature]
			# don't need to update max value since weightForNewFeature < maxweight
			maxWeight = self.maxValue[intentFeature]
			weightForNewFeature = maxWeight/4

			for feature in features:
				if feature not in self.strategy[intentFeature] and idfLevel <= receiverIDF[feature]:
					self.strategy[intentFeature][feature] = weightForNewFeature

class SenderCharm(object):
	"""docstring for SenderCharm"""
	def __init__(self, data, alpha, idfLevel):
		super(SenderCharm, self).__init__()
		self.strategy = dict()
		self.setupStrategy(data, alpha, idfLevel)
		self.specificityDict = dict()

	def setupStrategy(self, data, alpha, idfLevel):
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countSignals = dict()
		countTermInDoc = dict()
		self.uniqueSignals = list()
		self.idf = dict()
		self.invertedIndex = dict()
		self.countSignals = dict()
		self.maxValue = dict()
		signalSet = set()
		intnetSet = set()

		for record in listOfTuples:
			signals = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			signalSet = set(signals)
			intentSet = set(intentFeatures)
			intent = record[0]
			for intentFeature in intentSet:
				if intent not in self.invertedIndex:
					self.invertedIndex[intent] = list()
				self.invertedIndex[intent].append(intentFeature)
			self.countSignals[intent] = len(signalSet)
			for signalSetSingle in signalSet:
				if signalSetSingle not in countTermInDoc:
					countTermInDoc[signalSetSingle] = 1
				else:
					countTermInDoc[signalSetSingle] += 1


			for intent in intentSet:
				if intent not in self.strategy:
					self.strategy[intent] = dict()
				for signal in signalSet:
					self.strategy[intent][signal] = 1+alpha
					allSignals.add(signal)
		print(max(self.countSignals.values()))

		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = alpha

		numDocuments = len(listOfTuples)
		for term in countTermInDoc:
			self.idf[term] = math.log(numDocuments / float(countTermInDoc[term]))
		maxIDF = max(list(self.idf.values()))
		for term in self.idf:
			self.idf[term] = self.idf[term]/maxIDF
			#print(self.idf[term])
		for term in countTermInDoc:
			if self.idf[term] < idfLevel:
				del self.strategy[term]
				for intent in self.invertedIndex:
					if term in self.invertedIndex[intent]:
						self.invertedIndex[intent].remove(term)
				for goodTerm in self.strategy:
					if term in self.strategy[goodTerm]:
						del self.strategy[goodTerm][term]

		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 1/len(allSignals)

	def pickTuplesToJoin(self, howMany=1):
		tuples = list()
		while len(tuples) < howMany:
			tuples.append(random.choice(list(self.invertedIndex.keys())))

		return tuples

	def pickSingleSignal(self, featureWeights):
		total = sum(featureWeights.values())
		chance = random.uniform(0, 1)
		cumulative = 0
		for signal in featureWeights:
			cumulative += float(featureWeights[signal])/total
			if cumulative > chance:
				del featureWeights[signal]
				return signal

	def pickSignals(self, intents, howMany):
		signals = list()
		for intent in intents:
			currentSignalCount = 0
			featureWeights = dict()
			for intentFeature in self.invertedIndex[intent]:
				if intentFeature not in self.maxValue:
					self.maxValue[intentFeature] = 1
				#maxValue = max(self.strategy[intentFeature].values())
				for signalFeature in self.strategy[intentFeature]:
					if signalFeature not in featureWeights:
						featureWeights[signalFeature] = 1
					featureWeights[signalFeature] *= math.exp(self.strategy[intentFeature][signalFeature]/self.maxValue[intentFeature])

			while len(signals) < howMany:
				returnedSignal = self.pickSingleSignal(featureWeights)
				if returnedSignal not in signals:
					currentSignalCount += 1
					signals.append(returnedSignal)

				if self.countSignals[intent] <= currentSignalCount or len(featureWeights) == 0:
					break

		return signals

	def reinforce(self, intents, signals, score):
		#for intent in self.strategy:
		for intent in intents:
			for intentFeature in self.invertedIndex[intent]:
				for signal in signals:
					if signal in self.strategy[intentFeature]:
						self.strategy[intentFeature][signal] += score
						if self.strategy[intentFeature][signal] > self.maxValue[intentFeature]:
							self.maxValue[intentFeature] = self.strategy[intentFeature][signal]

	def addSignal(self, intent, features, weight):
		for intentFeature in self.invertedIndex[intent]:
			for feature in features:
				if feature not in self.strategy[intentFeature]:
					self.strategy[intentFeature][feature] = weight

	def addSignalWithIDFPrune(self, intent, features, receiverIDF, idfLevel):

		for intentFeature in self.invertedIndex[intent]:

			# weight is 50% of the highest weighted feature in self.strategy[intentFeature]
			# don't need to update max value since weightForNewFeature < maxweight
			maxWeight = self.maxValue[intentFeature]
			weightForNewFeature = maxWeight/4

			for feature in features:
				if feature not in self.strategy[intentFeature] and idfLevel <= receiverIDF[feature]:
					self.strategy[intentFeature][feature] = weightForNewFeature

class Charm(object):
	"""docstring for Charm"""
	def __init__(self, concepts):
		super(Charm, self).__init__()
		self.strategy = dict()
		self.concepts = concepts

	def getConcept(self, signal):
		if signal not in self.strategy:
			self.strategy[signal] = dict()

		for con in self.concepts:
			self.strategy[signal][con] = 1

		total = sum(self.strategy[signal].values())
		chance = random.uniform(0, 1)
		cumulative = 0
		for concept in self.strategy[signal]:
			cumulative += float(self.strategy[signal][concept])/total
			if cumulative > chance:
				return concept

	def reinforce(self, score, signal, concept):
		self.strategy[signal][concept] += score
