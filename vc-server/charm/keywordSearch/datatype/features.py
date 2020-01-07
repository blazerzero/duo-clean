import nltk
from nltk import word_tokenize
from nltk.util import ngrams
from nltk.stem import *
from nltk.stem.porter import *
from nltk.corpus import stopwords
from collections import Counter
import string
import random


class FeatureConstructor(object):
	"""docstring for FeatureConstructor"""
	def __init__(self):
		super(FeatureConstructor, self).__init__()
		
	def getFeaturesOfSingleTuple(self, record, header, n=1):
		features = list()
		stop_words = set(stopwords.words('english'))
		ngramsResult = set()

		translator = str.maketrans('', '', string.punctuation)
		stemmer = PorterStemmer()
		index = 1
		
		for s in record[1:]:
			if header is None:
				headerValue = ''
			else:
				headerValue = header[index]
			result = s.translate(translator)

			newTokenResult = list()
			tokenResult = nltk.word_tokenize(result)
			for token in tokenResult:
				if token not in stop_words:
					newTokenResult.append(stemmer.stem(token))

			for x in range(1,n+1):
				for grammed in list(ngrams(newTokenResult,x)):
					grammed = grammed + (headerValue,)
					ngramsResult.add(grammed)

			index += 1
		
		for gramResult in ngramsResult:
			features.append(str(gramResult))

		return features