# Enterprise Retail Analytics & Data Trust Pipeline
**Architect & Developer:** Elvis  
**Enterprise-Dashboard:** https://enterprise-sales-analytics-kab4yfktbntsb6qlff3x99.streamlit.app/  
**SQL-Trust-Audit:** https://sql-trust-auditor-auuujtpudncssxeikj3rrx.streamlit.app/

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

  ## 🧰 Applications in this Repository

This repository contains two distinct Streamlit applications, separating business intelligence from data governance.

### 1. The Executive Dashboard (`app.py`)
* **Target Audience:** Business Owners, C-Suite, Sales Managers.
* **Function:** A real-time reporting interface that visualizes revenue, product performance, and geographic sales distribution. 
* **Run locally:** `streamlit run app.py`

### 2. The SQL Revenue Trust Auditor (`audit_app.py`)
* **Target Audience:** Data Engineers, Analytics Engineers, Database Administrators.
* **Function:** A data governance testing environment. It intercepts SQL `JOIN` queries and dynamically executes `COUNT(*)` checks against the base table to detect Cartesian explosions (row inflation) or dropped rows (silent data loss) before queries are pushed to production.
* **Key Features:** 
  * Parses raw SQL and injects it into derived tables for safe execution.
  * Tracks query execution latency (milliseconds) for performance tuning.
  * Utilizes Streamlit Session State to cache audit history and prevent redundant database pings.
* **Run locally:** `streamlit run audit_app.py`
