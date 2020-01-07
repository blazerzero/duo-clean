import jellyfish


class Levenshtein(object):
	"""docstring for Levenshtein"""
	def __init__(self):
		super(Levenshtein, self).__init__()

	def evaluate(self, s1, s2):
		length = max(len(s1), len(s2))
		return (length - jellyfish.levenshtein_distance(s1, s2))/length
		# return (length - self.levenshtein(s1, s2))/length

	def levenshtein(self, s1, s2):
		if len(s1) < len(s2):
			return self.levenshtein(s2, s1)

		# len(s1) >= len(s2)
		if len(s2) == 0:
			return len(s1)

		previous_row = range(len(s2) + 1)
		for i, c1 in enumerate(s1):
			current_row = [i + 1]
			for j, c2 in enumerate(s2):
				insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
				deletions = current_row[j] + 1 # than s2
				substitutions = previous_row[j] + (c1 != c2)
				current_row.append(min(insertions, deletions, substitutions))
		previous_row = current_row

		return previous_row[-1]
