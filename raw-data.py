import os
import pandas as pd
import mysql.connector
import numpy as np
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

def ingest_csv_to_mysql(csv_path, table_name, insert_sql):
    df = pd.read_csv(csv_path)
    # Clean NaN values
    df = df.where(pd.notna(df), None)
    
    insert_records = df.values.tolist()
    
    with mysql.connector.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(insert_sql, insert_records)
            connection.commit()
            print(f"{cursor.rowcount} rows inserted into {table_name}.")




df = pd.read_csv('data/Sales.csv')  # Load data from CSV file   
# 2. Fix the Date Formats (Convert M/D/YYYY to YYYY-MM-DD)
df['Order Date'] = pd.to_datetime(df['Order Date']).dt.strftime('%Y-%m-%d')
df['Delivery Date'] = pd.to_datetime(df['Delivery Date']).dt.strftime('%Y-%m-%d')

# 3. Handle the Missing Dates (Convert Pandas NaN to Python None so MySQL reads it as a proper NULL)
df.replace({np.nan: None}, inplace=True)
# replace NaN values with None to ensure MySQL interprets them as NULL
df = df.where(pd.notna(df), None)

insert_records = df.values.tolist()  # Convert the DataFrame into a list of records for insertion

with mysql.connector.connect(**DB_CONFIG) as connection:
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO sales
            (`Order Number`, `Line Item`, `Order Date`, `Delivery Date`,
            `CustomerKey`, `StoreKey`, `ProductKey`, `Quantity`, `Currency Code`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """  # SQL query to insert records
        cursor.executemany(sql, insert_records)  # Execute the SQL query to insert multiple records
        connection.commit()  # Commit the changes to the database

        print(f"{cursor.rowcount} rows were inserted.")

print("Data insertion completed successfully.")
print(df.head())  # Print the first few rows of the DataFrame to verify the data





