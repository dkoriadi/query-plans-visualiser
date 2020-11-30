"""
qep_processor.py

This script retrieves all possible QEPs from the database.

"""
import re

from jsondiff import diff

import get_predicates_conditions

# Return status for public APIs
RET_DEFAULT_ERR = 0
RET_ALL_QEPS = 1
RET_ONLY_ACTUAL_QEP = 2
RET_CONVERT_QUERY_ERR = 3
RET_CONVERT_QUERY_OK = 4
RET_QEP_FOUND = 5
RET_QEP_NOT_FOUND = 6

# Constants
RESOLUTION = 10
PREDICATE_TOKEN = " :varies"


def processQuery(query, Communicator):
	"""
	The main function to retrieve multiple QEPs based on the actual query. The normal query is 
	first converted to a Picasso query template before calculating the selectivity values and 
	firing multiple queries for all the values. After which, the actual QEP is retrieved and 
	compared against other possible predicted QEPs.

	Parameters
	----------
	query : String
			A normal SQL query from user input

	objCommunicator : Postgres_Connect object
			For interfacing with database
		
	Returns
	-------
	lstAllQEPs : list
			All possibe QEPs for that Picasso query template

	lstPredicateAttributes : list
			List of all predicate attributes, maximum of 2 because only 2 dimensions are supported

	selectivityMap : list
			A list (either 1D or 2D array) that depicts all possible selectivites and all the plans
			taken for each selectivity

	"""
	lstPredicateAttributes = None
	templateQuery = None
	# Parse the normal query to retrieve predicate attributes
	result = _convertToQueryTemplate(query)
	if (result[0] == RET_CONVERT_QUERY_OK):
		lstPredicateAttributes = result[1]
		templateQuery = result[2]
	elif (result[0] == RET_CONVERT_QUERY_ERR):
		return RET_CONVERT_QUERY_ERR, None

	# Generate the selectivity values from histogram based on predicate attributes
	# NOTE: Maximum of 2 dimensions, 1 dimension is denoted by return value of lstSelValsDimension02 to be None
	lstSelValsDimension01, lstSelValsDimension02 = _generatePredicateValues(
		Communicator, lstPredicateAttributes)

	if lstSelValsDimension02 is None:
		selectivityMap, lstAllQEPs = _retrieveQEPs_OneDimension(
			templateQuery, lstSelValsDimension01, Communicator)
	else:
		selectivityMap, lstAllQEPs = _retrieveQEPs_TwoDimensions(
			templateQuery, lstSelValsDimension01, lstSelValsDimension02, Communicator)

	return RET_ALL_QEPS, lstAllQEPs, lstPredicateAttributes, selectivityMap


def getActualQEP(query, objCommunicator):
	"""
	Retrieve the actual QEP from the actual query. 

	Parameters
	----------
	query : String
			A normal SQL query from user input

	objCommunicator : Postgres_Connect object
			For interfacing with database

	Returns
	-------
	actualQEP : list
		The actual QEP from the actual query. 

	"""

	# Show the actual QEP from the actual query
	actualQEP = objCommunicator.getQEP(query)[0][0]
	# szQEPTree = visualiser.visualize_query_plan(actualQEP)
	return RET_ONLY_ACTUAL_QEP, actualQEP


def compareActualQEP(actualQEP, lstAllQEPs):
	"""
	Comparing all possible QEPs from Picasso query template vs the actual QEP taken by the original SQL query.

	Parameters
	----------
	lstAllQEPs : list
			All possibe QEPs for that Picasso query template

	actualQEP: list
			Actual QEP taken by the original SQL query
	
	Returns
	-------
	actualPlanIndex : int
		The plan number from predicted QEPs that the actual QEP is similar to 

	"""
	actualPlanIndex = int()
	for i, existingQEP in enumerate(lstAllQEPs):
		dict_qep_difference = _compareQEPs(existingQEP, actualQEP)
		bIsDifferentPlan = _findValueInNestedDict(
			dict_qep_difference, "Node Type")
		# None means a similar plan has been found
		if bIsDifferentPlan is None:
			actualPlanIndex = i + 1
			return RET_QEP_FOUND, actualPlanIndex
	return RET_QEP_NOT_FOUND, None


def generateFoundExplanation(lstPredicateAttributes, selectivityMap):
	"""
	Attempt to generate an explanation if actual query QEP is found within the selectivity map

	Parameters
	----------
	selectivityMap : list
			A list (either 1D or 2D array) that depicts all possible selectivites and all the plans
			taken for each selectivity

	lstPredicateAttributes : list
			List of all predicate attributes, maximum of 2 because only 2 dimensions are supported

	Returns
	-------
	
	lstSelectivityExplanations : list
			List of all possible strings of explanations for each plan

	"""
	# Get the min and max of the selectivity ranges for all plans
	dictSelectvityRanges = _retrieveSelectivityRanges(selectivityMap)

	lstSelectivityExplanations = []
	for key, value in dictSelectvityRanges.items():
		if len(lstPredicateAttributes) == 1:
			# One dimension explanation, use the second set of tuples since first tuples are empty
			string = ("For Plan {}, the selectivity range for {} ranges from {} % to {} %\n".
					  format(key, lstPredicateAttributes[0], int(value[1][0])*10, (int(value[1][1])+1)*10))
			lstSelectivityExplanations.append(string)
		elif len(lstPredicateAttributes) == 2:
			# Two dimension explanation, use both sets of tuples
			string = ("For Plan {}, the selectivity range for {} ranges from {} % to {} %, and {} ranges from {} % to {} %\n".
					  format(key, lstPredicateAttributes[0], int(value[0][0])*10, (int(value[0][1])+1)*10,
							 lstPredicateAttributes[1], int(value[1][0])*10, (int(value[1][1])+1)*10))
			lstSelectivityExplanations.append(string)
	return lstSelectivityExplanations


"""
Private (implementation) methods

"""


def _convertToQueryTemplate(query):
	"""
	Retrieve the predicate attributes and convert to a Picasso query template by replacing clauses
	with the predicate token.

	Parameters
	----------
	query : String
			A normal SQL query from user input

	Returns
	-------
	lstPredicateAttributes : list
			List of all predicate attributes, maximum of 2 because only 2 dimensions are supported

	templateQuery : string
			A Picasso query template after conversion


	"""

	# Parse the normal query to retrieve predicate attributes
	lstPredicateAttributes, clauses_list = get_predicates_conditions.get_var_column(
		query)
	print(lstPredicateAttributes)
	print(clauses_list)
	lstClausesToBeRemoved = []
	for clause in clauses_list:
		lstCondAndPred = re.split("<|<=|>|>=|!=", clause)
		testPredicate = re.sub('[^A-Za-z0-9.-]+', '', lstCondAndPred[1])
		try:
			fVal = float(testPredicate)
		except ValueError:
			# If condition is not a valid integer or float, remove the clause and predicate from lists
			lstClausesToBeRemoved.append(clause)
			lstPredicateAttributes = [
				value for value in lstPredicateAttributes if value != lstCondAndPred[0].strip()]
	clauses_list = [x for x in clauses_list if x not in lstClausesToBeRemoved]
	for index, attribute in enumerate(lstPredicateAttributes):
		# If the attribute contains table name e.g. l1.l_extendedprice, split the string by the dot
		# char and obtain attribute right side of dot
		if attribute.find(".") != -1:
			attribute = attribute.split(".")[-1]
		lstPredicateAttributes[index] = attribute
	if (len(lstPredicateAttributes) == 0):
		print("ERROR! No predicates found! Check the query again")
		return RET_CONVERT_QUERY_ERR, None
	# Replace clauses with predicate token
	for index, clause in enumerate(clauses_list):
		query = query.replace(
			clause, lstPredicateAttributes[index] + PREDICATE_TOKEN)
	templateQuery = query
	print("Predicate attributes: ")
	print(lstPredicateAttributes)
	return RET_CONVERT_QUERY_OK, lstPredicateAttributes, templateQuery


def _generatePredicateValues(objCommunicator, lstPredicateAttributes):
	"""
	Generates predicate values for all attributes required by retrieving from the histogram in
	PostgreSQL. Default resolution of predicate values can be changed via the RESOLUTION
	constant.

	Parameters
	----------
	objCommunicator : Postgres_Connect object
			For interfacing with database

	lstPredicateAttributes : list
			List of all predicate attributes, maximum of 2 because only 2 dimensions are supported

	Returns
	-------
	lstSelValsDimension01 : list
			Selectivity values for first dimension

	lstSelValsDimension02 : list
			Selectivity values for second dimension. If only one attribute is available, None is returned

	"""

	lstSelValsDimension01 = []
	lstSelValsDimension02 = []
	for index, attribute in enumerate(lstPredicateAttributes):
		schema = objCommunicator.findRelation(attribute)
		histogram = objCommunicator.getHistogram(schema, attribute)
		cardinality = objCommunicator.getCardinality(schema)
		selVals, predValues = _readHistogram(histogram)
		if index == 0:
			lstSelValsDimension01.extend(selVals)
		elif index == 1:
			lstSelValsDimension02.extend(selVals)
		else:
			print("More than 2 predicates not allowed!")
			quit()
	if len(lstSelValsDimension02) == 0:
		lstSelValsDimension02 = None
	return lstSelValsDimension01, lstSelValsDimension02


def _readHistogram(histogram):
	"""
	Parses the histogram retrieved from the database to retrieve histogram values, MCVs and
	frequencies. Default resolution of predicate values can be changed via the RESOLUTION
	constant.

	Parameters
	----------
	histogram : list
			The full histogram information after querying the database

	Returns
	-------
	selValues : list
			Selectivity values ranging from 0 to 1. Each element is a float.

	predicateValues : list
			Predicate values for a dimension because histogram contains info for just one attribute.

	"""
	sumMCV = 0 	# Most common values
	# Convert histogram values in string into list
	szHistogramValues = histogram[0][0][1:-1]
	lstHistogramValues = szHistogramValues.split(",")
	# Convert MCVs in string into list
	szMostCommonValues = histogram[0][1][1:-1]
	lstMCV = szMostCommonValues.split(",")
	# Frquencies already in list form
	lstFreqValues = histogram[0][2][1:-1]

	step = int(100 / RESOLUTION)+1
	histogramValues = [float(item) for item in lstHistogramValues[::step]]
	histogramNextValues = [float(item) for item in lstHistogramValues[::step]]

	predicateValues = []
	startpoint = 0
	endpoint = 1
	sel = startpoint + ((endpoint - startpoint)/(2*RESOLUTION))

	for i in range(int(RESOLUTION)):
		predicateValues.append(sel)
		sel += ((endpoint - startpoint)/RESOLUTION)

	# Find lower bound and upper bound, and get a number between them
	selValues = []
	for index, element in enumerate(histogramValues):
		lowerBound = element
		upperBound = histogramNextValues[index]
		val = ((upperBound - lowerBound) * 0.5) + lowerBound
		selValues.append(val)

	return selValues, predicateValues


def _retrieveQEPs_OneDimension(query, lstSelValsDimension01, objCommunicator):
	"""
	Retrieves alternative QEPs for one predicate attribute (i.e one dimension only). This is done
	by replacing the predicate token with the corresponding selectivity values and then querying
	the database.

	Parameters
	----------
	query : String
					A valid Picasso template query. Conversion should be done prior to calling this method

	lstSelValsDimension01 : list
					Selectivity values for first dimension

	objCommunicator : Postgres_Connect object
					For interfacing with database

	Returns
	-------
	planIndexes : list
					A list that contains all the plans selected. First plan is denoted by 0 integer, and so on.

	lstAllQEPs : list
					All possibe QEPs for that Picasso query template

	"""
	planIndexes = []
	lstAllQEPs = []
	for index, selectivityValue in enumerate(lstSelValsDimension01):
		qepCount = index * len(lstSelValsDimension01)
		if (qepCount % 10 == 0):
			print("Retrieving QEP {} of {}...".format(
				qepCount, len(lstSelValsDimension01)))
		# Always save the original Picasso query template before replacing it within predicate value
		origQuery = query
		query = query.replace(PREDICATE_TOKEN, "<= " +
							  str(selectivityValue), 1)
		qep = objCommunicator.getQEP(query)[0][0]
		if (index == 0):
			# First plan, add it to the list. Compare subsequent plans with this plan
			lstAllQEPs.append(qep)
			planIndexes.append(1)
		else:
			bAddQEPFlag = True
			for i, existingQEP in enumerate(lstAllQEPs):
				dict_qep_difference = _compareQEPs(existingQEP, qep)
				bIsDifferentPlan = _findValueInNestedDict(
					dict_qep_difference, "Node Type")
				# None means a similar plan has been found
				if bIsDifferentPlan is None:
					bAddQEPFlag = False
					planIndexes.append(i+1)
					# print("Similar plan found in QEP index", i)
					break
			if bAddQEPFlag == True:
				print("New plan found")
				lstAllQEPs.append(qep)
				planIndexes.append(len(lstAllQEPs))
		query = origQuery
	return planIndexes, lstAllQEPs


def _retrieveQEPs_TwoDimensions(query, lstSelValsDimension01, lstSelValsDimension02, objCommunicator):
	"""
	Retrieves alternative QEPs for two predicate attribute (i.e two dimensions only). This is done
	by replacing the predicate token with the corresponding selectivity values and then querying
	the database.

	Parameters
	----------
	query : String
					A valid Picasso template query. Conversion should be done prior to calling this method

	lstSelValsDimension01 : list
					Selectivity values for first dimension

	lstSelValsDimension02 : list
					Selectivity values for second dimension

	objCommunicator : Postgres_Connect object
					For interfacing with database

	Returns
	-------
	planIndexes : list
					A list that contains all the plans selected. First plan is denoted by 0 integer, and so on.

	lstAllQEPs : list
					All possibe QEPs for that Picasso query template

	"""
	planIndexes = []
	lstAllQEPs = []
	for index, selectivityValue in enumerate(lstSelValsDimension01):
		for index2, selectivityValue2 in enumerate(lstSelValsDimension02):
			qepCount = index * len(lstSelValsDimension01) + (index2 + 1)
			if (qepCount % 10 == 0):
				print("Retrieving QEP {} of {}...".format(qepCount, len(
					lstSelValsDimension01)*len(lstSelValsDimension02)))
			# Always save the original Picasso query template before replacing it within predicate value
			origQuery = query
			query = query.replace(
				PREDICATE_TOKEN, "<= " + str(selectivityValue), 1)
			query = query.replace(
				PREDICATE_TOKEN, "<= " + str(selectivityValue2), 1)
			qep = objCommunicator.getQEP(query)[0][0]
			if (index == 0 and index2 == 0):
				# First plan, add it to the list. Compare subsequent plans with this plan
				lstAllQEPs.append(qep)
				planIndexes.append(1)
			else:
				bAddQEPFlag = True
				for i, existingQEP in enumerate(lstAllQEPs):
					dict_qep_difference = _compareQEPs(existingQEP, qep)
					bIsDifferentPlan = _findValueInNestedDict(
						dict_qep_difference, "Node Type")
					# None means a similar plan has been found
					if bIsDifferentPlan is None:
						bAddQEPFlag = False
						planIndexes.append(i+1)
						# print("Similar plan found in QEP index", i)
						break
				if bAddQEPFlag == True:
					print("New plan found")
					lstAllQEPs.append(qep)
					planIndexes.append(len(lstAllQEPs))
			query = origQuery
	return planIndexes, lstAllQEPs


def _compareQEPs(qep1, qep2):
	"""
	Compare two QEPs for any difference using JSONdiff library

	Parameters
	----------
	qep1 : list
	qep2 : list
					Two possible QEPs in JSON format retrieved from PostgreSQL

	Returns
	-------
	result : dict
					A dictionary containing all differences between two QEPs

	"""
	result = diff(qep1, qep2, syntax="explicit")
	return result


def _retrieveSelectivityRanges(planIndexes):
	"""
	Retrieves selectivity range for all dimensions based on the plans taken.

	Parameters
	----------
	planIndexes : list
			A list that contains all the plans selected. First plan is denoted by 0 integer, and so on.

	Returns
	-------
	dictSelectvityRanges : dict
			Key: The plan index number, starting from 0
			Value: A tuple containing the min and max of selectivity values for each dimension

	"""
	lstSelectivityTuples = []
	planIndexes = _convert2DArray(planIndexes, RESOLUTION)
	# print("\nSelectivity Map: ")
	# print('\n'.join([''.join(['{:4}'.format(item) for item in row]) for row in planIndexes]))
	for rowIndex, row in enumerate(planIndexes):
		for colIndex, col in enumerate(row):
			lstSelectivityTuples.append(
				(planIndexes[rowIndex][colIndex], rowIndex, colIndex))
	lstSelectivityTuples.sort(key=lambda x: x[0])
	temp = _splitListOfTuplesByKey(lstSelectivityTuples)
	temp = list(temp.values())
	dictSelectvityRanges = {}
	# For one dimensions, the tuples are found in tupleMinMaxDim2 instead
	for index, lst in enumerate(temp):
		tupleMinMaxDim1 = (min(lst)[1], max(lst)[1])
		tupleMinMaxDim2 = (min(lst)[2], max(lst)[2])
		dictSelectvityRanges[index+1] = (tupleMinMaxDim1, tupleMinMaxDim2)
	return dictSelectvityRanges


"""
Utility functions

"""


def _splitListOfTuplesByKey(items, idx=0):
	"""
	Split a list of tuples into sublists based on first values of tuple. This is used for 
	determining the selectivity ranges for all predicate attributes.

	Parameters
	---------- 
	items : list
			A list of tuples to be sorted and split by key

	"""
	result = {}
	for item in items:
		key = item[idx]
		if key not in result:
			result[key] = []
		result[key].append(item)
	return result


def _convert2DArray(lstOrigList, nElementsInList):
	"""
	Split the list of column names into several lists like a 2D array. his is used for 
	determining the selectivity ranges for all predicate attributes.

	Parameters
	---------- 
	lstOrigList: list
			Original 1D list to be split

	nElementsInList: int
			Set the number of elements per list

	"""
	return [lstOrigList[i: i + nElementsInList] for i in range(0, len(lstOrigList), nElementsInList)]


def _findValueInNestedDict(obj, key):
	"""
	Find a value within a nested dictionary recursively. This is used to check the results after finding the 
	difference in QEPs.

	Parameters
	---------- 
	obj: dict
			The nested dictionary

	key: string
			The key to be found

	"""
	if key in obj:
		return obj[key]
	for k, v in obj.items():
		if isinstance(v, dict):
			item = _findValueInNestedDict(v, key)
			if item is not None:
				return item


if __name__ == '__main__':
	# Initialise Server Details
	host = "localhost"
	database = "TPC-H"
	port = 5432
	username = "postgres"
	password = "root"

	import db_connection_manager as db_connect
	import query_plan_visualizer as visualiser

	# Attempt to fetch QEP for sample query and display it
	Communicator = db_connect.Postgres_Connect()
	Communicator.connect(host, database, port, username, password)

	with open('sample_query_3_2D.txt') as f:
		query = f.read()
	result = getActualQEP(query, Communicator)
	if (result[0] == RET_ONLY_ACTUAL_QEP):
		szQEPTree = visualiser.visualize_query_plan(result[1])
		print(szQEPTree)
