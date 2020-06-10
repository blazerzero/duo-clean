from .stringComp import StringComparison
from .hamming import HamDistance
from .levenshtein import Levenshtein

class Evaluator(object):
	"""docstring for Evaluator"""
	def __init__(self):
		super(Evaluator, self).__init__()
		self.assessors = list()
		
	def evaluate(self, concept1, concept2):
		score = 0
		for assessor in self.assessors:
			score += assessor.evaluate(concept1, concept2)
		return score

	def stringComparisonActivate(self):
		self.assessors.append(StringComparison())

	def hammingDistanceActivate(self):
		self.assessors.append(HamDistance())

	def levenshtein(self):
		self.assessors.append(Levenshtein())
