class NoStrategy(object):
	"""docstring for NoStrategy"""
	def __init__(self, concepts):
		super(NoStrategy, self).__init__()
		self.concepts = concepts
		self.evaluator = None
		
	def getConcept(self, signal):
		maxScore = -1
		bestConcept = None
		for concept in self.concepts:
			score = self.evaluator.evaluate(signal, concept)
			if score > maxScore:
				maxScore = score
				bestConcept = concept

		return bestConcept
		
	def setEvaluator(self, evaluator):
		self.evaluator = evaluator