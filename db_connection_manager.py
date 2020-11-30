"""
db_connection_manager.py

This script connects to the database and run queries.
Database settings can be configured from the GUI

"""

import psycopg2

class Postgres_Connect():
	"""
	This is the class that interfaces with the PostgreSQL database server

	Attributes
	----------
	conn : psycopg2.Connection object
		Handles the connection to a PostgreSQL database instance. It encapsulates a database session.

		cur : psycopg2.Cursor object
		Allows Python code to execute PostgreSQL command in a database session.

	Methods
	-------
	connect(host, database, port, username, password)
		Initialise connection to the PostgreSQL server

	disconnect()
		Disconnect from the server, if it was previously connected

`	getQEP(query)
			Get the QEP in JSON from the database, based on the query provided

	getHistogram(tableName, attrName)
			Get histogram for specific column in table to determine min and max values

	getCardinality(tableName)
			Get cardinality for specific relation

	findRelation(attrName)
			Determine which relation a column attribute is from

	processQuery(query)
			Handle generic queries to database`

	"""

	def __init__(self):
		self.conn = None
		self.cur = None

	def connect(self, host, database, port, username, password):
		"""
		Initialise connection to the PostgreSQL server

		Parameters
		----------
		host : string
		database : string
		port : string
		username : string
		password : string
				Required information by PostgreSQL to connect to database

		"""
		print("Connecting to DB...")
		try:
			self.conn = psycopg2.connect(
				host=host, database=database, user=username, password=password, port=port)
			self.cur = self.conn.cursor()
			print("Connection is successful.")

		except (Exception, psycopg2.DatabaseError) as error:
			print(error)

	def disconnect(self):
		"""
		Disconnect from the server, if it was previously connected

		"""
		if (self.conn is not None):
			self.conn.close()
			print("Connection is closed.")

	def getQEP(self, query):
		"""
		Get the QEP in JSON from the database, based on the query provided

		Parameters
		----------
		query : String
				A valid SQL query

		Returns
		-------
		result : list
				A QEP in JSON format, including costs

		"""
		if (self.conn is not None):
			try:
				"""
				https://www.postgresql.org/docs/9.3/sql-explain.html
				Optional parameters:
				- ANALYZE [BOOLEAN] ==> False (Default)
				- VERBOSE [BOOLEAN] ==> True
				- COSTS [BOOLEAN] ==> True
				- BUFFERS [BOOLEAN] ==> False (Default)
				- TIMING [BOOLEAN] ==> False
				- FORMAT {TEXT | XML | JSON | YAML}
				"""
				statement = "EXPLAIN (FORMAT JSON, COSTS TRUE, TIMING FALSE, VERBOSE TRUE)"
				self.cur.execute(statement + query)
				result = self.cur.fetchall()
				return result
			except (Exception, psycopg2.DatabaseError) as error:
				print(error)

	def getHistogram(self, tableName, attrName):
		"""
		Get histogram for specific column in table to determine selectivity values

		Parameters
		----------
		tableName : String
				A relation which contains the attribute

		attrName : String
				An attribute that is contained within the relation table

		Returns
		-------
		result : list
				The histogram given by database

		"""
		print("Retrieving histogram for {}.{}...".format(tableName, attrName))
		if (self.conn is not None):
			try:
				query = ("SELECT histogram_bounds, most_common_vals, most_common_freqs \
						FROM pg_stats WHERE tablename = '{}' AND attname = '{}'"
						 .format(tableName, attrName))
				self.cur.execute(query)
				result = self.cur.fetchall()
				print("Histogram retrieved.")
				return result
			except (Exception, psycopg2.DatabaseError) as error:
				print(error)

	def getCardinality(self, tableName):
		"""
		Get cardinality for specific table

		Parameters
		----------
		tableName : String
				A relation in the database

		Returns
		-------
		result : integer
				The cardinality for the relation

		"""
		cardinality = 0
		query = (
			"SELECT reltuples FROM pg_class WHERE relname = '{}';".format(tableName))
		self.cur.execute(query)
		result = self.cur.fetchall()
		cardinality = result[0][0]
		# print("Cardinality of {} retrieved = {}".format(tableName, cardinality))
		return cardinality

	def findRelation(self, attrName):
		"""
		Determine which relation a column attribute is from

		Parameters
		----------
		attrName : String
				An valid attribute that is contained within some relation table

		Returns
		-------
		tableName : String
				A relation in the database that contains the attribute in parameter

		"""
		query = ("SELECT c.relname FROM pg_class AS c INNER JOIN pg_attribute AS a ON a.attrelid = c.oid \
				WHERE a.attname = '{}' AND c.relkind = 'r'".format(attrName))
		self.cur.execute(query)
		result = self.cur.fetchall()
		tableName = result[0][0]
		# print("Attr name {} found in table {}".format(attrName, tableName))
		return tableName

	def processQuery(self, query):
		"""
		Handle generic queries to database

		Parameters
		----------
		query : String
				A valid SQL query

		Returns
		-------
		result : list
				Result of query

		"""
		if (self.conn is not None):
			try:
				self.cur.execute(query)
				result = self.cur.fetchall()
				return result
			except (Exception, psycopg2.DatabaseError) as error:
				print(error)


def main():
	# Initialise server details
	host = "localhost"
	database = "TPC-H"
	port = 5432
	username = "postgres"
	password = "root"

	# Test conection to database
	Communicator = Postgres_Connect()
	Communicator.connect(host, database, port, username, password)

if __name__ == '__main__':
	main()
