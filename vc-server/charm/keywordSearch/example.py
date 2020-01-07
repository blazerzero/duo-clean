from players.receiver import ReceiverKeyword
from sys import *

def exampleFunction(receiverData, dataSource, fileToSave, reinforcementValue):
	receiver = ReceiverKeyword(receiverData, dataSource, fileToSave, 0.5)
	receiver.setData(receiverData, 'csv')
	receiver.initializeRE()
	for x in range(1,10):
		print()
		tuplesReturnedPartTime = receiver.getTuples(["('Republican', 'price')"], 10)
		for result in tuplesReturnedPartTime:
			if 'Robert W. Waterman' in result:
				receiver.reinforce(result, reinforcementValue)
		print('Results: ')
		for row in tuplesReturnedPartTime:
			print(receiver.data.getRow(row))


def advancedExample(receiverData, dataSource, fileToSave, reinforcementValue):
	receiver = ReceiverKeyword(receiverData, dataSource, fileToSave, 0.5)
	receiver.setData(receiverData, 'csv')
	receiver.initializeRE()
	header = receiver.data.getHeader()
	print("\n********************************************")
	while True:
		query = input("Enter query (to quit, enter 'Done'): ")
		if query == 'Done':
			print("********************************************\n")
			return None
		try:
			searchResults = receiver.getTuples(["('"+query+"', 'price')"], 10)

			resultRows = []
			for row in searchResults:
				resultRows.append(receiver.data.getRow(row))
			print("\nSearch Results: ")
			i = 0
			for i in range(0, len(resultRows)):
				print("\n" + repr(i+1) + ": " + resultRows[i] + "\n")
			idx = input("\nEnter the number of the search result to learn more, enter 0 to refine your search, or enter 'Done' to quit: ")
			while True:
				if idx == 'Done':
					print("********************************************\n")
					return None
				if idx == '0':
					print()
					break
				try:
					i = int(idx) - 1
					chosenResult = receiver.data.getListRow(searchResults[i])
					chosenResultStr = receiver.data.getRow(searchResults[i])
					#print("\n" + receiver.data.getRow(searchResults[int(idx)-1]))
					print("\n")
					for j in range(0, len(header)):
						print(header[j] + ": " + chosenResult[j])
					print("\nThis result will be reinforced:")
					receiver.reinforce(searchResults[i], reinforcementValue)
				except ValueError:
					print("\nERROR: Incorrectly formatted input. Try again.")
				idx = input("Enter the number of the search result to learn more, enter 0 to refine your search, or enter 'Done' to exit the program: ")
		except KeyError:
			print("No search results. Please try again.")

def main():
	dataset = 'testFile'
	datafile = 'target.csv'
	#dataset = 'movieFiles'
	#datafile = 'movies-with-plot-rating-runtime.csv'
	receiverData = 'datasets/WebTableBenchmark-packaged/' + dataset + '/' + datafile
	fileToSave = 'Testing'
	exampleFunction(receiverData, dataset, fileToSave, 1)
	#advancedExample(receiverData, dataset, fileToSave, 1)

if __name__ == '__main__':
	main()
