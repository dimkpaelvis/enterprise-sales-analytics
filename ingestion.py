import os
import pandas as pd
import mysql.connector
import numpy as np
from dotenv import load_dotenv

load_dotenv(override=True)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "port": int(os.getenv("MYSQL_PORT")),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "ssl_disabled": False
}

def ingest_csv_to_mysql(csv_path):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return pd.DataFrame()
    # encoding='latin-1' fixes the UnicodeDecodeError on the Customers.csv
    return pd.read_csv(csv_path, encoding='latin-1')

def insert_data_to_mysql(insert_records, insert_sql, table_name):
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                # 1. Empty the table first
                cursor.execute(f"DELETE FROM {table_name};")
                # 2. Insert the new records
                cursor.executemany(insert_sql, insert_records)
                connection.commit()
                print(f"{cursor.rowcount} rows inserted into {table_name}.")
                return cursor.rowcount
    except mysql.connector.Error as e:
        print(f"Database error inserting into {table_name}: {e}")
        return 0

# --- SALES ---
df_sales = ingest_csv_to_mysql('data/Sales.csv')
if not df_sales.empty:
    df_sales['Order Date'] = pd.to_datetime(df_sales['Order Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df_sales['Delivery Date'] = pd.to_datetime(df_sales['Delivery Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Convert NaN to None properly
    insert_records = [tuple(x) for x in df_sales.replace({np.nan: None}).values]
    
    insert_sql = """
        INSERT INTO sales (`Order Number`, `Line Item`, `Order Date`, `Delivery Date`, `CustomerKey`, `StoreKey`, `ProductKey`, `Quantity`, `Currency Code`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    insert_data_to_mysql(insert_records, insert_sql, 'sales')

# --- PRODUCTS ---
df_product = ingest_csv_to_mysql('data/Products.csv')
if not df_product.empty:
     # Clean $ and , from prices
    df_product['Unit Cost USD'] = df_product['Unit Cost USD'].astype(str).str.replace(r'[\$,]', '', regex=True).astype(float)
    df_product['Unit Price USD'] = df_product['Unit Price USD'].astype(str).str.replace(r'[\$,]', '', regex=True).astype(float)
    insert_records = [tuple(x) for x in df_product.replace({np.nan: None}).values]
    
    insert_sql = """
        INSERT INTO products (`ProductKey`, `Product Name`, `Brand`, `Color`, `Unit Cost USD`, `Unit Price USD`, `SubcategoryKey`, `Subcategory`, `CategoryKey`, `Category`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    insert_data_to_mysql(insert_records, insert_sql, 'products')

# --- CUSTOMERS ---
df_customer = ingest_csv_to_mysql('data/Customers.csv')
if not df_customer.empty:
    df_customer['Birthday'] = pd.to_datetime(df_customer['Birthday'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    insert_records = [tuple(x) for x in df_customer.replace({np.nan: None}).values]
    
    insert_sql = """
        INSERT INTO customers (`CustomerKey`, `Gender`, `Name`, `City`, `State Code`, `State`, `Zip Code`, `Country`, `Continent`, `Birthday`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    insert_data_to_mysql(insert_records, insert_sql, 'customers')

# --- EXCHANGE RATES ---
df_exchange_rate = ingest_csv_to_mysql('data/Exchange_Rates.csv')
if not df_exchange_rate.empty:
    df_exchange_rate['Date'] = pd.to_datetime(df_exchange_rate['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    insert_records = [tuple(x) for x in df_exchange_rate.replace({np.nan: None}).values]
    
    insert_sql = """
        INSERT INTO exchange_rates (`Date`, `Currency`, `Exchange`)
        VALUES (%s, %s, %s)
    """
    insert_data_to_mysql(insert_records, insert_sql, 'exchange_rates')

# --- STORES ---
df_stores = ingest_csv_to_mysql('data/Stores.csv')
if not df_stores.empty:
    df_stores['Open Date'] = pd.to_datetime(df_stores['Open Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    insert_records = [tuple(x) for x in df_stores.replace({np.nan: None}).values]
    
    insert_sql = """
        INSERT INTO stores (`StoreKey`, `Country`, `State`, `Square Meters`, `Open Date`)
        VALUES (%s, %s, %s, %s, %s)
    """
    insert_data_to_mysql(insert_records, insert_sql, 'stores')