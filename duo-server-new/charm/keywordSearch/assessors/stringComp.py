from difflib import SequenceMatcher

class StringComparison(object):
	"""docstring for StringComparison"""
	def __init__(self):
		super(StringComparison, self).__init__()
		
	def evaluate(self, concept1, concept2):
		return SequenceMatcher(None, concept1, concept2).ratio()