# Enterprise Retail Analytics & Data Trust Pipeline
**Architect & Developer:** Elvis  
**Live Application:** https://enterprise-sales-analytics-kab4yfktbntsb6qlff3x99.streamlit.app/

## 📌 Architecture Overview
This project is an end-to-end Data Engineering and Analytics pipeline built for a retail environment. It ingests messy raw data, normalizes it, securely loads it into a cloud database, and serves it to a web-facing dashboard. 

Crucially, this system implements **Data Governance & Grain Auditing** to prevent Cartesian explosions—ensuring that the revenue metrics displayed to executives are mathematically accurate and immune to silent row-multiplication bugs.

## 🛠️ Tech Stack
* **Extraction & Transformation:** Python, Pandas
* **Database & Cloud Storage:** MySQL, TiDB Server-less (Cloud)
* **Frontend & Visualization:** Streamlit, Plotly
* **Security:** Environment Variables (`.env`), Streamlit Secrets Manager, TLS Encryption

## 🚀 Pipeline Lifecycle

### 1. Data Ingestion & Transformation (`ingest.py`)
* Reads over 60,000 rows of raw retail data from local CSVs.
* Implements dynamic type casting (`.astype(str)`) to prevent runtime null-value crashes.
* Cleans messy string data using Python text methods (e.g., `str.strip()`) before it enters the database, ensuring clean data at the source.

### 2. Cloud Database Schema (`setup_db.py`)
* Defines a multi-table relational schema (`sales`, `products`, `customers`, `stores`, `exchange_rates`).
* Establishes Primary Keys to enforce uniqueness and prevent duplicate product/customer entries.
* Hosted on a TiDB Serverless cloud cluster, queried via a TLS-secured connection on port 4000.

### 3. Analytics & Dashboard (`app.py`)
* Connects securely to the TiDB cloud backend using environment secrets.
* Utilizes SQL Joins and subqueries (`EXISTS`) optimized for low-latency retrieval.
* Renders real-time interactive KPIs (Revenue, Sales Volume) and dynamic Plotly charts.

## 🛡️ Data Governance: The "Trust Audit" 
Dashboards are useless if the underlying joins inflate the data. This project treats SQL execution as an engineered system, not just a query. 

Before deploying revenue KPIs, the pipeline was audited for **grain shifts**. A 4-way `INNER JOIN` across `sales`, `products`, `stores`, and `customers` was verified against the base `sales` table (`COUNT(*)` = 62,884 for both). This proves the schema cleanly maps many-to-one relationships and guarantees the total revenue sum is 100% accurate, with zero Cartesian inflation.
