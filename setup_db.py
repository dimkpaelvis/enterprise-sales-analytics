import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(override=True)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": 4000,
    "ssl_disabled": False
}

TABLES = {}

TABLES['products'] = """
CREATE TABLE IF NOT EXISTS products (
    `ProductKey` INT,
    `Product Name` VARCHAR(255),
    `Brand` VARCHAR(255),
    `Color` VARCHAR(255),
    `Unit Cost USD` FLOAT,
    `Unit Price USD` FLOAT,
    `SubcategoryKey` INT,
    `Subcategory` VARCHAR(255),
    `CategoryKey` INT,
    `Category` VARCHAR(255)
)
"""

TABLES['customers'] = """
CREATE TABLE IF NOT EXISTS customers (
    `CustomerKey` INT,
    `Gender` VARCHAR(50),
    `Name` VARCHAR(255),
    `City` VARCHAR(255),
    `State Code` VARCHAR(50),
    `State` VARCHAR(255),
    `Zip Code` VARCHAR(50),
    `Country` VARCHAR(255),
    `Continent` VARCHAR(255),
    `Birthday` DATE
)
"""

TABLES['stores'] = """
CREATE TABLE IF NOT EXISTS stores (
    `StoreKey` INT,
    `Country` VARCHAR(255),
    `State` VARCHAR(255),
    `Square Meters` INT,
    `Open Date` DATE
)
"""

TABLES['exchange_rates'] = """
CREATE TABLE IF NOT EXISTS exchange_rates (
    `Date` DATE,
    `Currency` VARCHAR(50),
    `Exchange` FLOAT
)
"""

TABLES['sales'] = """
CREATE TABLE IF NOT EXISTS sales (
    `Order Number` VARCHAR(100),
    `Line Item` INT,
    `Order Date` DATE,
    `Delivery Date` DATE,
    `CustomerKey` INT,
    `StoreKey` INT,
    `ProductKey` INT,
    `Quantity` INT,
    `Currency Code` VARCHAR(50)
)
"""

print("Connecting to cloud database to build tables...")
try:
    with mysql.connector.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            for name, ddl in TABLES.items():
                print(f"Building {name}...")
                cursor.execute(ddl)
            conn.commit()
    print("✅ All tables created successfully!")
except Exception as e:
    print(f"Error: {e}")