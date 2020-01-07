import csv
import random

class Data():
	"""docstring for Data"""

	def __init__(self, filename, fileType):
		super(Data, self).__init__()
		self.filename = None
		self.header = None
		self.table = dict()
		self.filename = filename
		if fileType is 'csv':
			self.readInCSVData()

	def readInCSVData(self):
		with open(self.filename, encoding="latin-1") as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			self.header = next(spamreader)
			for row in spamreader:
				self.table[row[0]] = row

	def getRow(self, rowID):
		return str(self.table[rowID])

	def getListRow(self, rowID):
		return self.table[rowID]

	def getConcepts(self):
		stringList = list()
		signalList = list(self.table.values())
		for sig in signalList:
			stringList.append(str(sig))
		return stringList

	def getValues(self):
		return list(self.table.values())

	def getHeader(self):
		return self.header

	def getRandomTuple(self):
		return random.choice(list(self.table))
		

def main():
	testData = Data('../datasets/AG150/Amazon.csv', 'csv')
	print(testData.getValues()[0][0])
	print(' '.join(testData.getListRow('b000hcv1ky')))



if __name__ == '__main__':
	main()