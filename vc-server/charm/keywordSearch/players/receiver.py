import sys
import random
sys.path.append("..")

#from learningMethods.charm import ReceiverCharm
#from learningMethods.charm import ReceiverCharmAll
from learningMethods.charm import ReceiverCharmKeyword
from learningMethods.charm import ReceiverCharmKeyword_CFDLite
from learningMethods.charm import ReceiverCharmKeyword_NoFeature_Feature
from learningMethods.charm import ReceiverCharmKeyword_Feature_NoFeature
from learningMethods.charm import ReceiverCharmKeyword_NoFeature_NoFeature
from learningMethods.ucb import ReceiverUCBKeyword
from learningMethods.ucb import ReceiverUCBKeyword_NoFeature_NoFeature
from learningMethods.ucb import ReceiverUCBKeyword_Feature_NoFeature
from learningMethods.ucb import ReceiverUCBKeyword_NoFeature_Feature
from datatype.datastore import Data
from learningMethods.NoStrategy import NoStrategy


class ReceiverKeyword(object):
	"""docstring for ReceiverAll"""
	def __init__(self, projectPath, fileToStore, dataSource, receiverData=None, idfLevel=None):
		super(ReceiverKeyword, self).__init__()
		self.data = None
		self.projectPath = projectPath
		self.receiverData = receiverData
		self.dataSource = dataSource
		self.fileToStore = fileToStore
		self.idfLevel = idfLevel

	def initializeRE(self):
		self.strategy = ReceiverCharmKeyword(self.data, self.receiverData, self.dataSource, self.fileToStore, self.idfLevel, self.projectPath)

	def initializeRE_CFDLite(self, data):
		self.strategy = ReceiverCharmKeyword_CFDLite(data, self.dataSource, self.fileToStore, self.projectPath)

	def initializeRE_NoFeature_NoFeature(self):
		self.strategy = ReceiverCharmKeyword_NoFeature_NoFeature(self.data, self.receiverData, self.dataSource, self.fileToStore)

	def initializeRE_Feature_NoFeature(self):
		self.strategy = ReceiverCharmKeyword_Feature_NoFeature(self.data, self.receiverData, self.dataSource, self.fileToStore)

	def initializeRE_NoFeature_Feature(self):
		self.strategy = ReceiverCharmKeyword_NoFeature_Feature(self.data, self.receiverData, self.dataSource, self.fileToStore)

	def initializeUCB(self, alpha=0.5):
		self.strategy = ReceiverUCBKeyword(self.data, self.receiverData, self.dataSource, self.fileToStore, alpha, self.idfLevel, projectPath)

	def initializeUCB_NoFeature_NoFeature(self, alpha=0.5):
		self.strategy = ReceiverUCBKeyword_NoFeature_NoFeature(self.data, self.receiverData, self.dataSource, self.fileToStore, alpha)

	def initializeUCB_Feature_NoFeature(self, alpha=0.5):
		self.strategy = ReceiverUCBKeyword_Feature_NoFeature(self.data, self.receiverData, self.dataSource, self.fileToStore, alpha)

	def initializeUCB_NoFeature_Feature(self, alpha=0.5):
		self.strategy = ReceiverUCBKeyword_NoFeature_Feature(self.data, self.receiverData, self.dataSource, self.fileToStore, alpha)

	def initializeNone(self, evaluator):
		self.strategy = NoStrategy(self.data.getConcepts())
		self.strategy.setEvaluator(evaluator)

	def setData(self, filename, filetype):
		self.data = Data(filename, filetype)

	def getTuples(self, signal, numberToReturn=1):
		self.receivedSignal = signal
		self.returnedTuples = self.strategy.returnTuples(signal, numberToReturn)
		return self.returnedTuples

	def reinforce(self, picked, score=1, signalReceived=None):
		listOfPicked = list()
		listOfPicked.append(picked)
		if signalReceived is None:
			self.strategy.reinforce(self.receivedSignal, listOfPicked, score)
		else:
			self.strategy.reinforce(signalReceived, listOfPicked, score)


class ReceiverAll(object):
	"""docstring for ReceiverAll"""
	def __init__(self):
		super(ReceiverAll, self).__init__()
		self.data = None

	def initializeRE(self):
		self.strategy = ReceiverCharmAll(self.data)

	def initializeNone(self, evaluator):
		self.strategy = NoStrategy(self.data.getConcepts())
		self.strategy.setEvaluator(evaluator)

	def setData(self, filename, filetype):
		self.data = Data(filename, filetype)

	def getTuples(self, signal, numberToReturn=1):
		self.receivedSignal = signal
		self.returnedTuples = self.strategy.returnTuples(signal, numberToReturn)
		return self.returnedTuples

	def reinforce(self, score=1):
		self.strategy.reinforce(self.receivedSignal, self.returnedTuples, score)


class Receiver(object):
	"""docstring for Receiver"""
	def __init__(self):
		super(Receiver, self).__init__()
		self.data = None

	def initializeRE(self):
		self.strategy = ReceiverCharm(self.data)

	def initializeNone(self, evaluator):
		self.strategy = NoStrategy(self.data.getConcepts())
		self.strategy.setEvaluator(evaluator)

	def setData(self, filename, filetype):
		self.data = Data(filename, filetype)

	def getTuples(self, signal, numberToReturn=1):
		self.receivedSignal = signal
		self.returnedTuples = self.strategy.returnTuples(signal, numberToReturn)
		return self.returnedTuples

	def reinforce(self, score=1):
		self.strategy.reinforce(self.receivedSignal, self.returnedTuples, score)
