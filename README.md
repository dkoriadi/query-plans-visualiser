# query-plans-visualiser
A tool for visualising multiple query plans.

### Overview 
In a DBMS, there are multiple possible query plans to successfully execute a query. The DBMS selects the most optimised plan based on internal cost calculations.
This tool aims to visualise these query plans to better understand the inner workings of the query optimiser. 

### Requirements
- Python 3.7 or later
- PostgreSQL 9.6 or later (tested on TPC-H database benchmark)

### Setup
- Install required libraries from `requirements.txt` text file
```sh
$ pip install -r requirements.txt
```
- Install PostgreSQL and setup required database  

### Usage 
- Run `app.py` to launch the user interface as below
```sh
$ python app.py
```
- Enter `host`, `database`, `port`, `username` and `password` for database info
- Enter desired query
- Click on `Explain Query` button to view comparisons of query plans
- Click on `View Plans` button to visualise all query plans 
