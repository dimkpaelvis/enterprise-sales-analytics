import streamlit as st
import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

# Read them
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}


# 1. Page Configuration
st.set_page_config(page_title="Retail App", page_icon="🛒", layout="wide")

# 2. UI Headers
st.title("🛒 Retail App")
st.caption("A simple retail application to manage products and inventory.")

# 3. Load Data
@st.cache_data
def fetch_inventory():
    connection = None
    cursor = None
    records = []
    columns = []
    with mysql.connector.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sales")  # Fetch all records from the sales table
            records = cursor.fetchall()
            columns = cursor.column_names
    return pd.DataFrame(records, columns=columns)

# 4. Department Selection
df = fetch_inventory()

if df.empty:
    st.info("No inventory records are available.")
    st.stop()

check_box = st.selectbox('Select Date of sales you would like to view?', df['Order Date'].dropna().unique())
df_filtered = df[df['Order Date'] == check_box]

dept_options = df['Order Date'].dropna().unique().tolist() if not df.empty else []
if not dept_options:
    st.warning("No sales dates available. Add a product first.")
    st.stop()

# 5. Display the filtered DataFrame
st.dataframe(df_filtered)


# Section 2: Visualization
st.subheader("Inventory Visualization")
# setting x and y axis

st.write(f"Total Sales in {check_box}: {len(df_filtered)}")
st.bar_chart(df_filtered, x='ProductKey', y='Quantity', color='red', horizontal=False, stack=False,
             use_container_width=True, height=400)

'''
with st.form("Add New Sale Record"):
    st.subheader("Add a New Sale Record")
    new_product_name = st.text_input("")
    new_product_department = st.selectbox("Department", df['departments'].dropna().unique())
    new_product_price = st.number_input("Price (£)", min_value=0.0, step=0.01)
    new_product_stock = st.number_input("Stock Quantity", min_value=0, step=1)
    submit_button = st.form_submit_button("Add Product")
    # Invalid input handling
    if submit_button:
        if not new_product_name.strip():
            st.warning("Product name cannot be empty.")
        elif new_product_price <= 0:
            st.warning("Price must be greater than zero.")
        elif new_product_stock < 0:
            st.warning("Stock quantity cannot be negative.")
        else:
            try:
                with mysql.connector.connect(**DB_CONFIG) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """INSERT INTO products (name, departments, price, in_stock)
                            VALUES (%s, %s, %s, %s)""",
                            (new_product_name, new_product_department, new_product_price, new_product_stock),
                        )
                        connection.commit()
                st.success(f"Product '{new_product_name}' added successfully!")
                st.cache_data.clear()
                st.rerun()   # refresh page so new product shows up
            except mysql.connector.Error as e:
                st.error(f"Error adding product: {e}")
'''
