# Importing the required libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime 

# Function to log the progress of the ETL process
def log_progress(msg):
    ''' This function logs the progress of the ETL process at each stage.
    It writes the timestamp and the message to a log file.'''
    
    # Format for the timestamp
    timeformat = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timeformat)

    # Append the timestamp and message to the log file
    with open(logfile, 'a') as f:
        f.write(timestamp + ' : ' + msg + '\n')

# Function to extract data from the webpage
def extract(url, table_attribs):
    ''' This function extracts data from the webpage using BeautifulSoup.
    It creates a DataFrame with the specified attributes and populates it with the extracted data.'''
    
    # Initialize an empty DataFrame with the specified attributes
    df = pd.DataFrame(columns = table_attribs)

    # Send a GET request to the URL and parse the HTML content
    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')

    # Find the first table body in the HTML and get all its rows
    tables = data.find_all('tbody')[0]
    rows = tables.find_all('tr')

    # For each row, find all the data cells
    for row in rows:
        col = row.find_all('td')
        # If the row has data cells
        if len(col) != 0:
            # Get the second anchor tag in the second data cell
            ancher_data = col[1].find_all('a')[1]
            # If the anchor tag exists
            if ancher_data is not None:
                # Create a dictionary with the bank name and market capitalization in USD
                data_dict = {
                    'Name': ancher_data.contents[0],
                    'MC_USD_Billion': col[2].contents[0]
                }
                # Create a DataFrame from the dictionary and append it to the main DataFrame
                df1 = pd.DataFrame(data_dict, index = [0])
                df = pd.concat([df, df1], ignore_index = True)

    # Convert the market capitalization values to floats
    USD_list = list(df['MC_USD_Billion'])
    USD_list = [float(''.join(x.split('\n'))) for x in USD_list]
    df['MC_USD_Billion'] = USD_list

    return df

# Function to transform the extracted data
def transform(df, exchange_rate_path):
    ''' This function transforms the extracted data by converting the market capitalization values 
    from USD to other currencies. It reads the exchange rates from a CSV file and applies them 
    to the USD values.'''
    
    # Read the exchange rates from the CSV file
    csvfile = pd.read_csv(exchange_rate_path)

    # Create a dictionary of the exchange rates
    dict = csvfile.set_index('Currency').to_dict()['Rate']

    # Convert the market capitalization values from USD to GBP, INR, and EUR
    df['MC_GBP_Billion'] = [np.round(x * dict['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x * dict['INR'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x * dict['EUR'],2) for x in df['MC_USD_Billion']]

    return df

# Function to load the transformed data to a CSV file
def load_to_csv(df, output_path):
    ''' This function loads the transformed data to a CSV file.'''
    
    df.to_csv(output_path)

# Function to load the transformed data to a database
def load_to_db(df, sql_connection, table_name):
    ''' This function loads the transformed data to a database.
    It creates a new table with the specified name and replaces it if it already exists.'''
    
    df.to_sql(table_name, sql_connection, if_exists = 'replace', index = False)

# Function to run SQL queries on the loaded data
def run_query(query_statements, sql_connection):
    ''' This function runs SQL queries on the loaded data and prints the results.'''
    
    for query in query_statements:
        print(query)
        print(pd.read_sql(query, sql_connection), '\n')

# URL of the webpage to extract data from
url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
# Path to the CSV file with the exchange rates
exchange_rate_path = 'exchange_rate.csv'

# Attributes of the DataFrame to create
table_attribs = ['Name', 'MC_USD_Billion']
# Name of the database to load data to
db_name = 'Banks.db'
# Name of the table to create in the database
table_name = 'Largest_banks'
# Create a connection to the database
conn = sqlite3.connect(db_name)
# SQL queries to run on the loaded data
query_statements = [
        'SELECT * FROM Largest_banks',
        'SELECT AVG(MC_GBP_Billion) FROM Largest_banks',
        'SELECT Name from Largest_banks LIMIT 5'
    ]

# Path to the log file
logfile = 'code_log.txt'
# Path to the output CSV file
output_csv_path = 'Largest_banks_data.csv'

# Log the start of the ETL process
log_progress('Preliminaries complete. Initiating ETL process.')

# Extract data from the webpage
df = extract(url, table_attribs)
# Log the completion of the data extraction
log_progress('Data extraction complete. Initiating Transformation process.')

# Transform the extracted data
df = transform(df, exchange_rate_path)
# Log the completion of the data transformation
log_progress('Data transformation complete. Initiating loading process.')

# Load the transformed data to a CSV file
load_to_csv(df, output_csv_path)
# Log the completion of the data loading to the CSV file
log_progress('Data saved to CSV file.')

# Log the initiation of the SQL connection
log_progress('SQL Connection initiated.')

# Load the transformed data to the database
load_to_db(df, conn, table_name)
# Log the completion of the data loading to the database
log_progress('Data loaded to Database as table. Running the query.')

# Run the SQL queries on the loaded data
run_query(query_statements, conn)
# Close the connection to the database
conn.close()
# Log the completion of the ETL process
log_progress('Process Complete.')
