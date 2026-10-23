import streamlit as st
import mysql.connector
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)

# 1. Cloud Database Connection Config
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": 4000,
    "ssl_disabled": False
}

st.title("🛡️ SQL Revenue Trust Auditor")
st.write("Detect Cartesian explosions and silent row multipliers in your joins.")

# 2. User Input Area
base_table = st.text_input("Enter the base table name (e.g., sales):", value="sales")
join_query = st.text_area("Paste your full JOIN query here:", height=200)

if st.button("Run Audit"):
    if base_table and join_query:
        st.write("Executing audit...")
        
        # 3. WE NEED TO RUN THE QUERIES HERE
        with mysql.connector.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                try:
                    # A. Execute the base table count query
                    cursor.execute(f"SELECT COUNT(*) FROM {base_table};")
                    base_count = cursor.fetchone()[0]
                    
                    # B. Execute the join query count
                    cursor.execute(f"SELECT COUNT(*) FROM ({join_query}) AS subquery;")
                    join_count = cursor.fetchone()[0]
                    
                    # Display results
                    st.write(f"Base Table Count ({base_table}): {base_count}")
                    st.write(f"Join Query Count: {join_count}")
                    
                    if join_count > base_count:
                        st.warning("⚠️ The join query returned more rows than the base table. " \
                        "This may indicate a Cartesian explosion or silent row multiplier.")
                    elif join_count < base_count:
                        st.warning("⚠️ The join query returned fewer rows than the base table. "
                        "This may indicate that some rows were filtered out unexpectedly.")
                    else:
                        st.success("✅ The join query returned a valid number of rows.")
                except mysql.connector.Error as e:
                    st.error(f"Database error: {e}")