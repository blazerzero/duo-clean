from datatype.features import FeatureConstructor

class FeatureMapper(object):
	"""docstring for FeatureMapper"""
	def __init__(self):
		super(FeatureMapper, self).__init__()
		self.mapping = dict()
		self.count = dict()
		self.similarity = dict()
		self.receiverFeatures = dict()


	def updateMapping(self, senderFeatures, receiverFeatures, similarityValue, receiverKey):
		if receiverKey not in receiverFeatures:
			self.receiverFeatures[receiverKey] = receiverFeatures

		for senderFeature in senderFeatures:
			if senderFeature not in self.mapping:
				self.mapping[senderFeature] = dict()
				self.count[senderFeature] = dict()
				self.similarity[senderFeature] = dict()

			for receiverFeature in receiverFeatures:
				if receiverFeature not in self.mapping[senderFeature]:
					self.similarity[senderFeature][receiverFeature] = similarityValue
					self.count[senderFeature][receiverFeature] = 1
					self.mapping[senderFeature][receiverFeature] = self.similarity[senderFeature][receiverFeature] / self.count[senderFeature][receiverFeature]
				else:
					self.similarity[senderFeature][receiverFeature] += similarityValue
					self.count[senderFeature][receiverFeature] += 1
					self.mapping[senderFeature][receiverFeature] = self.similarity[senderFeature][receiverFeature] / self.count[senderFeature][receiverFeature]

	def getWeightOfPair(self, senderFeatures, receiverKeys):
		actualTotal = 0
		totalPossible = 1
		for senderFeature in senderFeatures:
			if senderFeature in self.mapping:
				for receiverKey in receiverKeys:
					if receiverKey in self.receiverFeatures:
						for feature in self.receiverFeatures[receiverKey]:
							if feature in self.mapping[senderFeature]:
								totalPossible += 1
								actualTotal += self.mapping[senderFeature][feature]
		return (actualTotal / totalPossible) * 0.5
