import sys
import random
sys.path.append("..")

from datatype.datastore import Data
from learningMethods.charm import SenderCharm
from learningMethods.charm import SenderCharm_zipf
from learningMethods.charm import SenderBaseline
from learningMethods.ucb import SenderUCB
from learningMethods.ucb import SenderUCB_zipf


class Sender(object):
	"""docstring for Sender"""
	def __init__(self, idfLevel, learningMethod=None):
		super(Sender, self).__init__()
		self.data = None
		self.idfLevel = idfLevel

		if learningMethod == 're':
			self.initializeRE()
		elif learningMethod == 'dnn':
			self.initializeDNN()
		elif learningMethod == 'ucb':
			self.initializeUCB()


	def initializeRE(self, alpha=0.5):
		self.strategy = SenderCharm(self.data, alpha, self.idfLevel)

	def initializeRE_zipf(self, dataType, fileToStore, alpha=0.5):
		self.strategy = SenderCharm_zipf(self.data, alpha, self.idfLevel, dataType, fileToStore)

	def initializeUCB(self, alpha=0.5):
		self.strategy = SenderUCB(self.data, alpha, self.idfLevel)

	def initializeUCB_zipf(self, dataType, fileToStore, alpha=0.5):
		self.strategy = SenderUCB_zipf(self.data, alpha, self.idfLevel, dataType, fileToStore)

	def initializeBaseline(self, alpha=0.5):
		self.strategy = SenderBaseline(self.data, alpha)

	def setData(self, filename, filetype):
		self.data = Data(filename, filetype)
		return len(self.data.getHeader())

	def pickTupleToJoin(self):
		self.currentTuples = self.strategy.pickTuplesToJoin()
		return self.currentTuples

	def pickSignalsBaseline(self, intent, howMany):
		self.signals = self.strategy.pickSignals(intent, howMany)
		return self.signals
		
	def pickSignals(self, intents=None, howMany=2, ratio=0.5):
		specificityGap = 0.1
		if intents:
			self.signals = self.strategy.pickSignals(intents, howMany)
		else:
			self.signals = self.strategy.pickSignals(self.currentTuples, howMany)

		#self.signals = self.strategy.pickSignals(self.currentTuples, howMany, ratio)
		return self.signals

	def reinforce(self, score=1, tuplesSent=None, signalsSent=None):
		if tuplesSent is None:
			toSend = list()
			toSend.append(self.currentTuples)
			self.strategy.reinforce(toSend, self.signals, score)
		else:
			toSend = list()
			toSend.append(tuplesSent)
			self.strategy.reinforce(toSend, signalsSent, score)
			
	def reinforceTEMP(self, score=1):
		self.strategy.reinforce(self.currentTuples, self.signals, score)

	def getWeight(self, intent, signal):
		return self.strategy.strategy[intent][signal]

	def addSignal(self, intent, features, weight):
		self.strategy.addSignal(intent, features, weight)
		
	def addSignalWithIDFPrune(self, intent, features, receiverIDF, idfLevel):
		self.strategy.addSignalWithIDFPrune(intent, features, receiverIDF, idfLevel)

def main():
	testSender = Sender()
	testSender.setData('../datasets/AG/Amazon.csv', 'csv')
	testSender.pickTupleToJoin()
	testSender.pickSignal()


if __name__ == '__main__':
	main()

