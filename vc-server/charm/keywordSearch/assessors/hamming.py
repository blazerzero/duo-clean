import jellyfish

class HamDistance(object):
	"""docstring for HamDistance"""
	def __init__(self):
		super(HamDistance, self).__init__()
	

	def evaluate(self, s1, s2):
		"""Return the Hamming distance between equal-length sequences"""
		length = max(len(s1), len(s2))
		return (length - jellyfish.hamming_distance(s1, s2))/length
		
		# jellyfish.hamming_distance(s1, s2)
		# if len(s1) != len(s2):
		# 	return 0
		# return (len(s1) - sum(el1 != el2 for el1, el2 in zip(s1, s2)))/len(s1)