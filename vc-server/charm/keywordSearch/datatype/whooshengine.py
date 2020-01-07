import whoosh
import csv
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from whoosh.index import exists_in
from whoosh.index import open_dir
from whoosh import qparser
from whoosh import scoring
from nltk import word_tokenize
from nltk.stem import *
from nltk.stem.porter import *
import nltk
from nltk import word_tokenize
from nltk.util import ngrams
from nltk.stem import *
from nltk.stem.porter import *
from nltk.corpus import stopwords
import shutil
import os

sys.path.append("..")

from datatype.datastore import Data

class KeywordSearchWithLearning(object):
	"""docstring for KeywordSearch"""
	def __init__(self, pathName, datasource, fileToSave):
		super(KeywordSearchWithLearning, self).__init__()
		self.dataPath = pathName
		self.table = dict()
		self.datasource = datasource
		self.storeData(self.dataPath)
		self.fileToSave = fileToSave
		self.indexer = self.createIndex()

	def storeData(self, dataPath):
		stop_words = set(stopwords.words('english'))
		stemmer = PorterStemmer()
		with open(dataPath, encoding="latin-1") as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			self.header = next(spamreader)
			for row in spamreader:
				newTokenResult = list()
				tokenResult = nltk.word_tokenize(' '.join(row[1:]))
				for token in tokenResult:
					if token not in stop_words:
						newTokenResult.append(stemmer.stem(token))
				self.table[row[0]] = ' '.join(newTokenResult)

	def search(self, searchTerm, numberToReturn):
		indexer = self.indexer
		titles = list()
		content = list()
		scores = list()
		with indexer.searcher() as searcher:
			query = MultifieldParser(["content"], schema=indexer.schema, group=qparser.OrGroup).parse(searchTerm)
			results = searcher.search(query, limit=numberToReturn)
			for line in results:
				titles.append(line['title'])
				content.append(line['content'])
				scores.append(line.score)


		return titles[:numberToReturn], content[:numberToReturn], scores[:numberToReturn]

	def createIndex(self):
		print('creating index: ' + str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"))
		if not os.path.exists("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"):
			os.makedirs("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")

		if exists_in(str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")):
				print('Found index, loading...')
				indexer = open_dir(str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"))
				return indexer
				
		shutil.rmtree("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")
		os.makedirs("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")
		schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
		indexer = create_in("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"", schema)
		
		writer = indexer.writer()
		
		for key in self.table:
			row = self.table[key]
			title = key
			writer.add_document(title=title, content=row)

		writer.commit()
		return indexer

class KeywordSearch(object):
	"""docstring for KeywordSearch"""
	def __init__(self, pathName, datasource, fileToSave):
		super(KeywordSearch, self).__init__()
		self.dataPath = pathName
		self.table = dict()
		self.fileToSave = fileToSave
		self.datasource = datasource
		self.storeData(self.dataPath)
		self.indexer = self.createIndex()


	def storeData(self, dataPath):
		with open(dataPath, encoding="latin-1") as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			self.header = next(spamreader)
			for row in spamreader:
				self.table[row[0]] = ' '.join(row)

	def search(self, searchTerm, numberToReturn):
		indexer = self.indexer
		titles = list()
		content = list()
		with indexer.searcher() as searcher:
			query = MultifieldParser(["content"], schema=indexer.schema, group=qparser.OrGroup).parse(searchTerm)
			results = searcher.search(query, limit=numberToReturn)
			#print('hey1')
			for line in results:
				titles.append(line['title'])
				content.append(line['content'])
			#print('hey2')

		return titles[:numberToReturn], content[:numberToReturn]

	def createIndex(self):
		print('creating index: ' + str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"))
		if not os.path.exists("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"):
			os.makedirs("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")

		if exists_in(str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")):
				print('Found index, loading...')
				indexer = open_dir(str("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/"))
				return indexer

		shutil.rmtree("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")
		os.makedirs("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"/")
		schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
		indexer = create_in("/data/mccamish/datatype/"+self.datasource+self.fileToSave+"", schema)
		
		writer = indexer.writer()
		
		for key in self.table:
			row = self.table[key]
			title = key
			writer.add_document(title=title, content=row)

		writer.commit()
		return indexer


def main():
	reciever = KeywordSearch('../datasets/WebTableBenchmark-packaged/california govs 1/target.csv')
	print(reciever.table['Peter H. Burnett'])
	reciever.search('democrat')

if __name__ == '__main__':
	main()