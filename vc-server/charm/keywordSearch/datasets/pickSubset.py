import csv
import random

class Oracle(object):
	"""docstring for Oracle"""
	def __init__(self):
		super(Oracle, self).__init__()
		self.data1 = dict()
		self.data2 = dict()

	def initData(self, filename):
		with open(filename, encoding="latin-1") as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			self.header = next(spamreader)
			for row in spamreader:
				self.data1[row[0]] = row[1]
				self.data2[row[1]] = row[0]

	def getTruth(self, concept1, concept2):
		if concept1 in self.data1:
			if self.data1[concept1] == concept2:
				return True

		if concept1 in self.data2:
			if self.data2[concept1] == concept2:
				return True

		return False

	def getMatchingGoogle(self, key):
		if key not in self.data1:
			return None
		else:
			return self.data1[key]

	def getMatchingAmazon(self, key):
		return self.data2[key]

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
		return self.table[rowID]

	def getConcepts(self):
		stringList = list()
		signalList = list(self.table.values())
		for sig in signalList:
			stringList.append(str(sig))
		return stringList

	def getValues(self):
		return list(self.table.values())

	def getRandomTuple(self):
		return random.choice(list(self.table))
		

def main():
	amazonData = Data('AG/Amazon.csv', 'csv')
	googleData = Data('AG/GoogleProducts.csv', 'csv')
	oracle = Oracle()
	oracle.initData('AG/Amzon_GoogleProducts_perfectMapping.csv')
	linesWritten = 0
	desiredLines = 150

	with open('AG150/Amazon.csv', 'a+') as amazonFile:
		writer = csv.writer(amazonFile, delimiter=',')
		writer.writerow(amazonData.header)
	
	with open('AG150/GoogleProducts.csv', 'a+') as googleFile:
		writer = csv.writer(googleFile, delimiter=',')
		writer.writerow(googleData.header)

	with open('AG150/Amzon_GoogleProducts_perfectMapping.csv', 'a+') as oracleFile:
		writer = csv.writer(oracleFile, delimiter=',')
		writer.writerow(oracle.header)



	for value in amazonData.getValues():
		if linesWritten >= desiredLines:
			break
		
		amazonKey = value[0]
		#print(amazonData.getRow(amazonKey))
		googleKey = oracle.getMatchingGoogle(amazonKey)
		if googleKey is not None:
			linesWritten+=1
			with open('AG150/Amazon.csv', 'a+') as amazonFile:
				writer = csv.writer(amazonFile, delimiter=',')
				writer.writerow(amazonData.getRow(amazonKey))
			
			with open('AG150/GoogleProducts.csv', 'a+') as googleFile:
				writer = csv.writer(googleFile, delimiter=',')
				writer.writerow(googleData.getRow(googleKey))

			with open('AG150/Amzon_GoogleProducts_perfectMapping.csv', 'a+') as oracleFile:
				newList = list()
				newList.append(amazonKey)
				newList.append(googleKey)

				writer = csv.writer(oracleFile, delimiter=',')
				writer.writerow(newList)

		print(oracle.getMatchingGoogle(amazonKey))



	


if __name__ == '__main__':
	main()