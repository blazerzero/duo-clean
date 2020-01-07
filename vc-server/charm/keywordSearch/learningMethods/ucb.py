import random
import math
from datatype.features import FeatureConstructor
from datatype.whooshengine import KeywordSearchWithLearning
import pprint
import operator
import time
import pickle
import os
import pdb

class ReceiverUCBKeyword_Feature_NoFeature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, alpha):
		super(ReceiverUCBKeyword_Feature_NoFeature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.featureWeightsDenom = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore
		self.alpha = 0.2
		
	def setupStrategy(self, data):
		self.time = dict()
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
				self.time[tupleID] = 1
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
		
		#signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()
		for signal in signalsReceived:
			if signal not in self.featureWeights:
				self.featureWeights[signal] = dict()
				self.featureWeightsDenom[signal] = dict()

		for rID in returnedIDs:
			for signal in signalsReceived:
				if rID not in self.featureWeights[signal]:
					self.featureWeights[signal][rID] = 1
					self.featureWeightsDenom[signal][rID] = 1
			
		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			for signal in signalsReceived:
				weight += self.ucbCalculation(signal, rID, rID, scores[i])/len(self.numOfFeatures[rID])
			if rID not in tupleWeights:
				tupleWeights[rID] = weight
			else:
				tupleWeights[rID] += weight
			i += 1

		time_start = time.time()
		sortedReturnedTuples = sorted(tupleWeights.items(), key=operator.itemgetter(1), reverse=True)
		returnedTuples = [x[0] for x in sortedReturnedTuples][:numberToReturn]

		for rID in returnedTuples:
			self.time[rID] += 1
			for signal in signalsReceived:
				self.featureWeightsDenom[signal][rID] += 1

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples
	
	def ucbCalculation(self, signal, feature, rID, bm25):
		exploit = (self.featureWeights[signal][feature]+bm25) / (self.featureWeightsDenom[signal][feature] + 1)
		explore = self.alpha * math.sqrt((2*math.log(self.time[rID])) / self.featureWeightsDenom[signal][feature])
		return exploit + explore

	def reinforce(self, signals, intent, score):
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		#signal = keywordQuery
		
		for signal in signals:
			for inte in intent:
				if inte is not None:
					self.featureWeights[signal][inte] += score


class ReceiverUCBKeyword_NoFeature_Feature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, alpha):
		super(ReceiverUCBKeyword_NoFeature_Feature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.featureWeightsDenom = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore
		self.alpha = 0.2

	def setupStrategy(self, data):
		self.time = dict()
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
				self.time[tupleID] = 1
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
			self.featureWeightsDenom[signal] = dict()

		for rID in returnedIDs:
			for feature in self.numOfFeatures[rID]:
				if feature not in self.featureWeights[signal]:
					self.featureWeights[signal][feature] = 1
					self.featureWeightsDenom[signal][feature] = 1
		
		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			for feature in self.numOfFeatures[rID]:
				weight += self.ucbCalculation(signal, feature, rID, scores[i])/len(self.numOfFeatures[rID])
			if rID not in tupleWeights:
				tupleWeights[rID] = weight
			else:
				tupleWeights[rID] += weight
			i += 1

		time_start = time.time()
		sortedReturnedTuples = sorted(tupleWeights.items(), key=operator.itemgetter(1), reverse=True)
		returnedTuples = [x[0] for x in sortedReturnedTuples][:numberToReturn]

		for rID in returnedTuples:
			self.time[rID] += 1
			for feature in self.numOfFeatures[rID]:
				self.featureWeightsDenom[signal][feature] += 1

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples
	
	def ucbCalculation(self, signal, feature, rID, bm25):
		exploit = (self.featureWeights[signal][feature]+bm25) / (self.featureWeightsDenom[signal][feature] + 1)
		explore = self.alpha * math.sqrt((2*math.log(self.time[rID])) / self.featureWeightsDenom[signal][feature])
		return exploit + explore

	def reinforce(self, signals, intent, score):
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		signal = keywordQuery
		
#		for signal in self.strategy:
		for inte in intent:
			if inte is not None:
				for featureOfIntent in self.numOfFeatures[inte]:
					self.featureWeights[signal][featureOfIntent] += score


class ReceiverUCBKeyword_NoFeature_NoFeature(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, alpha):
		super(ReceiverUCBKeyword_NoFeature_NoFeature, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.featureWeightsDenom = dict()
		self.returnedTuples = list()
		self.receivedSignals = list()
		self.setupStrategy(data)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore
		self.alpha = 0.2
		


	def setupStrategy(self, data):
		self.time = dict()
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		for record in listOfTuples:
			intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			tupleID = record[0]
			if tupleID not in self.numOfFeatures:
				self.numOfFeatures[tupleID] = list()
				self.time[tupleID] = 1
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
			self.featureWeightsDenom[signal] = dict()

		for rID in returnedIDs:
			if rID not in self.featureWeights[signal]:
				self.featureWeights[signal][rID] = 1
				self.featureWeightsDenom[signal][rID] = 1
		
		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			weight += self.ucbCalculation(signal, rID, rID, scores[i])/len(self.numOfFeatures[rID])
			if rID not in tupleWeights:
				tupleWeights[rID] = weight
			else:
				tupleWeights[rID] += weight
			i += 1

		time_start = time.time()
		sortedReturnedTuples = sorted(tupleWeights.items(), key=operator.itemgetter(1), reverse=True)
		returnedTuples = [x[0] for x in sortedReturnedTuples][:numberToReturn]

		for rID in returnedTuples:
			self.time[rID] += 1
			self.featureWeightsDenom[signal][rID] += 1

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples
	
	def ucbCalculation(self, signal, feature, rID, bm25):
		exploit = (self.featureWeights[signal][feature]+bm25) / (self.featureWeightsDenom[signal][feature] + 1)
		explore = self.alpha * math.sqrt((2*math.log(self.time[rID])) / self.featureWeightsDenom[signal][feature])
		return exploit + explore

	def reinforce(self, signals, intent, score):
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		signal = keywordQuery
		
#		for signal in self.strategy:
		for inte in intent:
			if inte is not None:
				self.featureWeights[signal][inte] += score


class ReceiverUCBKeyword(object):
	"""docstring for ReceiverCharm"""
	def __init__(self, data, receiverData, dataSource, fileToStore, alpha, idfLevel):
		super(ReceiverUCBKeyword, self).__init__()
		self.features = list()
		self.invertedIndex = dict()
		self.numOfFeatures = dict()
		self.featureWeights = dict()
		self.featureWeightsDenom = dict()
		self.returnedTuples = list()
		self.dataPath = dataSource
		self.receivedSignals = list()
		self.fileToStore = fileToStore
		self.setupStrategy(data, idfLevel)
		self.receiver = KeywordSearchWithLearning(receiverData, dataSource, fileToStore)
		self.fileToStore = fileToStore
		self.alpha = 0.2
		
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

	def setupStrategy(self, data, idfLevel):
		self.time = dict()
		#b000jz4hqo
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countTermInDoc = dict()
		self.idf = dict()

		if not os.path.exists("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/"):
			os.makedirs("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/")

			for record in listOfTuples:
				intentFeatures = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				tupleID = record[0]
				if tupleID not in self.numOfFeatures:
					self.numOfFeatures[tupleID] = list()
					self.time[tupleID] = 1
				for intentFeature in intentFeatures:
					if intentFeature not in self.features:
						self.features.append(intentFeature)
					if intentFeature not in self.invertedIndex:
						self.invertedIndex[intentFeature] = list()
					self.invertedIndex[intentFeature].append(tupleID)
					self.numOfFeatures[tupleID].append(intentFeature)

					if intentFeature not in countTermInDoc:
						countTermInDoc[intentFeature] = 1
					else:
						countTermInDoc[intentFeature] += 1

			numDocuments = len(listOfTuples)
			for term in countTermInDoc:
				self.idf[term] = math.log(numDocuments / float(countTermInDoc[term]))
			maxIDF = max(list(self.idf.values()))
			for term in self.idf:
				self.idf[term] = self.idf[term]/maxIDF
				#print(self.idf[term])
			for term in countTermInDoc:
				if self.idf[term] < idfLevel:
					del self.invertedIndex[term]
					for intent in self.numOfFeatures:
						if term in self.numOfFeatures[intent]:
							self.numOfFeatures[intent].remove(term)
			print('saving stats')
			self.save_obj(self.idf, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/idf")
			self.save_obj(self.invertedIndex, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/invertedIndex")
			self.save_obj(self.numOfFeatures, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/numOfFeatures")
			self.save_obj(self.features, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/features")
			self.save_obj(self.time, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/time")

		else:
			print("loading data...")
			self.idf = self.load_obj("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/idf")
			self.invertedIndex = self.load_obj("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/invertedIndex")
			self.numOfFeatures = self.load_obj("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/numOfFeatures")
			self.features = self.load_obj("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/features")
			self.time = self.load_obj("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"/time")



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
		
		#signal = keywordQuery
		returnedIDs, contentPartTime, scores = self.receiver.search(keywordQuery, None)
		returnedTuples = list()
		for signal in signalsReceived:
			if signal not in self.featureWeights:
				self.featureWeights[signal] = dict()
				self.featureWeightsDenom[signal] = dict()

		for rID in returnedIDs:
			for feature in self.numOfFeatures[rID]:
				for signal in signalsReceived:
					if feature not in self.featureWeights[signal]:
						self.featureWeights[signal][feature] = 1
						self.featureWeightsDenom[signal][feature] = 1
			
		time_start = time.time()
		tupleWeights = dict()

		i = 0
		for rID in returnedIDs:
			weight = 0
			for feature in self.numOfFeatures[rID]:
				for signal in signalsReceived:
					weight += self.ucbCalculation(signal, feature, rID, scores[i])/len(self.numOfFeatures[rID])
			if rID not in tupleWeights:
				tupleWeights[rID] = weight
			else:
				tupleWeights[rID] += weight
			i += 1

		time_start = time.time()
		sortedReturnedTuples = sorted(tupleWeights.items(), key=operator.itemgetter(1), reverse=True)
		returnedTuples = [x[0] for x in sortedReturnedTuples][:numberToReturn]

		for rID in returnedTuples:
			self.time[rID] += 1
			for signal in signalsReceived:
				for feature in self.numOfFeatures[rID]:
					self.featureWeightsDenom[signal][feature] += 1

		print('Get ' + str(numberToReturn) + ': ' + str(time.time() - time_start))
		self.returnedTuples = returnedTuples
		return returnedTuples
	
	def ucbCalculation(self, signal, feature, rID, bm25):
		exploit = (self.featureWeights[signal][feature]+bm25) / (self.featureWeightsDenom[signal][feature] + 1)
		explore = self.alpha * math.sqrt((2*math.log(self.time[rID])) / self.featureWeightsDenom[signal][feature])
		return exploit + explore

	def reinforce(self, signals, intent, score):
		keywordQuery = [x.split(',')[0].strip()[1:].replace('\'', '') for x in signals]
		keywordQuery = ' '.join(keywordQuery)
		#signal = keywordQuery
		
		for signal in signals:
			for inte in intent:
				if inte is not None:
					for featureOfIntent in self.numOfFeatures[inte]:
						self.featureWeights[signal][featureOfIntent] += score

class SenderUCB_zipf(object):
	"""docstring for SenderCharm"""
	def __init__(self, data, alpha, idfLevel, datatype, fileToStore):
		super(SenderUCB_zipf, self).__init__()
		self.strategy = dict()
		self.datatype = datatype
		self.fileToStore = fileToStore
		self.dataPath = datatype
		self.strategyDenom = dict()
		self.strategyTime = 0
		self.setupStrategy(data, alpha, idfLevel)
		self.specificityDict = dict()
		self.createDistribution()

	def save_obj_idf(self, obj, name ):
		with open(name + '.pkl', 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj_idf(self, name ):
		with open(name + '.pkl', 'rb') as f:
			return pickle.load(f)

	
	def save_obj(self, obj, name ):
		with open('zipf/'+ name + '.pkl', 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj(self, name ):
		with open('zipf/' + name + '.pkl', 'rb') as f:
			return pickle.load(f)

	def setupStrategy(self, data, alpha, idfLevel):
		#b000jz4hqo
		self.time = dict()
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countSignals = dict()
		countTermInDoc = dict()
		self.uniqueSignals = list()
		self.idf = dict()
		self.alpha = 0.2
		self.intentFeatures = dict()
		self.maxValue = dict()

		if not os.path.exists("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/"):
			os.makedirs("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/")

			for record in listOfTuples:
				signals = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				intentSet = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
				self.intentFeatures
				signalSet = set(signals)
				intentSet = set(intentSet)
				self.intentFeatures[record[0]] = list(intentSet)
				#intent = record[0]
				for intent in intentSet:
					self.time[intent] = 1
					if intent not in self.strategy:
						self.strategy[intent] = dict()
						self.strategyDenom[intent] = dict()
					for signal in signalSet:

						self.strategy[intent][signal] = 1
						self.strategyDenom[intent][signal] = 1

						if signal not in countSignals:
							countSignals[signal] = 1
						else:
							countSignals[signal] += 1

				for signalSetSingle in signalSet:
					if signalSetSingle not in countTermInDoc:
						countTermInDoc[signalSetSingle] = 1
					else:
						countTermInDoc[signalSetSingle] += 1
			
			# for intent in self.strategy:
			# 	for signal in allSignals:
			# 		if signal not in self.strategy[intent]:
			# 			self.strategy[intent][signal] = 0.1

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
					del self.strategyDenom[term]
					for intent in self.intentFeatures:
						if term in self.intentFeatures[intent]:
							self.intentFeatures[intent].remove(term)
					for goodTerm in self.strategy:
						if term in self.strategy[goodTerm]:
							del self.strategy[goodTerm][term]
							del self.strategyDenom[goodTerm][term]

			self.save_obj_idf(self.idf, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/idf")
			self.save_obj_idf(self.strategy, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/strategy")
			self.save_obj_idf(self.strategyDenom, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/strategyDenom")
			self.save_obj_idf(self.intentFeatures, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/intentFeatures")
			self.save_obj_idf(self.time, "/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/time")

		else:
			print("loading data...")
			self.idf = self.load_obj_idf("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/idf")
			self.strategy = self.load_obj_idf("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/strategy")
			self.strategyDenom = self.load_obj_idf("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/strategyDenom")
			self.intentFeatures = self.load_obj_idf("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/intentFeatures")
			self.time = self.load_obj_idf("/data/mccamish/datatype/idfStats/"+self.dataPath+self.fileToStore+"_sender/time")
		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 1/len(allSignals)
	
	def createDistribution(self):
		try:
			self.distribution = self.load_obj(self.datatype)
		except (OSError, IOError) as e:
			i = 2
			for tup in self.invertedIndex.keys():
				self.distribution[tup] = 1/i
				i += 1
			self.save_obj(self.distribution, self.datatype)
			
	def pickTuplesToJoin(self, howMany=1):
		tuples = list()
		while len(tuples) < howMany:
			chance = random.uniform(0, 1)
			cumulative = 0
			for tup in self.intentFeatures.keys():
				cumulative += self.distribution[tup]
				if cumulative > chance:
					if tup not in tuples:
						tuples.append(tup)
						if len(tuples) >= howMany:
							break

		return tuples

	# def pickTuplesToJoin(self, howMany=1):
	# 	tuples = list()
	# 	while len(tuples) < howMany:
	# 		tuples.append(random.choice(list(self.intentFeatures.keys())))

	# 	return tuples

	def ucbCalculation(self, intent, signal):
		exploit = self.strategy[intent][signal] / self.strategyDenom[intent][signal]
		explore = self.alpha * math.sqrt((2* math.log(self.time[intent])) / self.strategyDenom[intent][signal])
		return exploit + explore

	#def pickSignals(self, intents, howMany):
	#	signals = list()
	#	potentialSignals = list()
	#	for intent in intents:
	#		for i in self.intentFeatures[intent]:
	#			for signal in self.strategy[i]:
	#				potentialSignals.append((signal, self.ucbCalculation(i, signal)))
	#	sortedSignals = sorted(potentialSignals, key=lambda x: x[1], reverse=True)
	#	
	#	signals = [x[0] for x in sortedSignals][:howMany]
	#	for intent in intents:
	#		for i in self.intentFeatures[intent]:
	#			for signal in signals:
	#				if signal in self.strategyDenom[i]:
	#					self.strategyDenom[i][signal] += 1
	#			self.time[i] += 1
	#	return signals

	def pickSignals(self, intents, howMany):
		signals = list()
		potentialSignals = list()
		for intent in intents:
			for i in self.intentFeatures[intent]:
				if i not in self.maxValue:
						self.maxValue[i] = 1
						
				for signal in self.strategy[i]:
					potentialSignals.append((signal, self.ucbCalculation(i, signal)))
		sortedSignals = sorted(potentialSignals, key=lambda x: x[1], reverse=True)
		
		signals = [x[0] for x in sortedSignals][:howMany]
		for intent in intents:
			for i in self.intentFeatures[intent]:
				for signal in signals:
					if signal in self.strategyDenom[i]:
						self.strategyDenom[i][signal] += 1
				self.time[i] += 1
		return signals
	
	#def reinforce(self, intents, signals, score):
	#	#for intent in self.strategy:
	#	for intent in intents:
	#		for i in self.intentFeatures[intent]:
	#			for signal in signals:
	#				if signal in self.strategy[i]:
	#					self.strategy[i][signal] += score
	
	def reinforce(self, intents, signals, score):
		#for intent in self.strategy:
		for intent in intents:
			for i in self.intentFeatures[intent]:
				for signal in signals:
					if signal in self.strategy[i]:
						self.strategy[i][signal] += score
						if self.strategy[i][signal] > self.maxValue[i]:
							self.maxValue[i] = self.strategy[i][signal]

	def addSignal(self, intent, features, weight):
		for intentFeature in self.intentFeatures[intent]:
			for feature in features:
				if feature not in self.strategy[intentFeature]:
					self.strategy[intentFeature][feature] = weight
					self.strategyDenom[intentFeature][feature] = weight

	def addSignalWithIDFPrune(self, intent, features, receiverIDF, idfLevel):
		for intentFeature in self.intentFeatures[intent]:
			for feature in features:
			
				maxWeight = self.maxValue[intentFeature]
				weightForNewFeature = maxWeight/2
			
				if feature not in self.strategy[intentFeature] and idfLevel <= receiverIDF[feature]:
					self.strategy[intentFeature][feature] = weightForNewFeature
					self.strategyDenom[intentFeature][feature] = weightForNewFeature
		
class SenderUCB(object):
	"""docstring for SenderCharm"""
	def __init__(self, data, alpha, idfLevel):
		super(SenderUCB, self).__init__()
		self.strategy = dict()
		self.strategyDenom = dict()
		self.strategyTime = 0
		self.setupStrategy(data, alpha, idfLevel)
		self.specificityDict = dict()

	def setupStrategy(self, data, alpha, idfLevel):
		#b000jz4hqo
		self.time = dict()
		featureConst = FeatureConstructor()
		listOfTuples = data.getValues()
		allSignals = set()
		countSignals = dict()
		countTermInDoc = dict()
		self.uniqueSignals = list()
		self.idf = dict()
		self.alpha = 0.2
		self.intentFeatures = dict()

		for record in listOfTuples:
			signals = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			intents = featureConst.getFeaturesOfSingleTuple(record, data.getHeader(), 1)
			self.intentFeatures
			signalSet = set(signals)
			intentSet = set(intents)
			self.intentFeatures[record[0]] = list(intentSet)
			#intent = record[0]
			for intent in intentSet:
				self.time[intent] = 1
				if intent not in self.strategy:
					self.strategy[intent] = dict()
					self.strategyDenom[intent] = dict()
				for signal in signalSet:
					self.strategy[intent][signal] = 1
					self.strategyDenom[intent][signal] = 1

					if signal not in countSignals:
						countSignals[signal] = 1
					else:
						countSignals[signal] += 1

			for signalSetSingle in signalSet:
				if signalSetSingle not in countTermInDoc:
					countTermInDoc[signalSetSingle] = 1
				else:
					countTermInDoc[signalSetSingle] += 1
		
		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 0.1

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
				del self.strategyDenom[term]
				for intent in self.intentFeatures:
					if term in self.intentFeatures[intent]:
						self.intentFeatures[intent].remove(term)
				for goodTerm in self.strategy:
					if term in self.strategy[goodTerm]:
						del self.strategy[goodTerm][term]
						del self.strategyDenom[goodTerm][term]


		# for intent in self.strategy:
		# 	for signal in allSignals:
		# 		if signal not in self.strategy[intent]:
		# 			self.strategy[intent][signal] = 1/len(allSignals)
		
	def pickTuplesToJoin(self, howMany=1):
		tuples = list()
		while len(tuples) < howMany:
			tuples.append(random.choice(list(self.intentFeatures.keys())))

		return tuples

	def ucbCalculation(self, intent, signal):
		exploit = self.strategy[intent][signal] / self.strategyDenom[intent][signal]
		explore = self.alpha * math.sqrt((2* math.log(self.time[intent])) / self.strategyDenom[intent][signal])
		return exploit + explore

	def pickSignals(self, intents, howMany):
		signals = list()
		potentialSignals = list()
		for intent in intents:
			for i in self.intentFeatures[intent]:
				for signal in self.strategy[i]:
					potentialSignals.append((signal, self.ucbCalculation(i, signal)))
		sortedSignals = sorted(potentialSignals, key=lambda x: x[1], reverse=True)
		
		signals = [x[0] for x in sortedSignals][:howMany]
		for intent in intents:
			for i in self.intentFeatures[intent]:
				for signal in signals:
					if signal in self.strategyDenom[i]:
						self.strategyDenom[i][signal] += 1
				self.time[i] += 1
		return signals

	def reinforce(self, intents, signals, score):
		#for intent in self.strategy:
		for intent in intents:
			for i in self.intentFeatures[intent]:
				for signal in signals:
					if signal in self.strategy[i]:
						self.strategy[i][signal] += score

	def addSignal(self, intent, features, weight):
		for intentFeature in self.intentFeatures[intent]:
			for feature in features:
				if feature not in self.strategy[intentFeature]:
					self.strategy[intentFeature][feature] = weight
					self.strategyDenom[intentFeature][feature] = weight
# class Charm(object):
# 	"""docstring for Charm"""
# 	def __init__(self, concepts):
# 		super(Charm, self).__init__()
# 		self.strategy = dict()
# 		self.concepts = concepts

# 	def getConcept(self, signal):
# 		if signal not in self.strategy:
# 			self.strategy[signal] = dict()

# 		for con in self.concepts:
# 			self.strategy[signal][con] = 1

# 		total = sum(self.strategy[signal].values())
# 		chance = random.uniform(0, 1)
# 		cumulative = 0
# 		for concept in self.strategy[signal]:
# 			cumulative += float(self.strategy[signal][concept])/total
# 			if cumulative > chance:
# 				return concept

# 	def reinforce(self, score, signal, concept):
# 		self.strategy[signal][concept] += score

