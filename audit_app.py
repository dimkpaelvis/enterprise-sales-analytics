import re
from datetime import datetime
import mysql.connector
import os
import pandas as pd
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(page_title="SQL Trust Auditor", page_icon="🛡️", layout="wide")

# Dark executive UI
BG, PANEL, TEXT, MUTED = "#080E1B", "#101A2B", "#F3F6FC", "#9AAAC0"
TEAL, AMBER, RED, BORDER = "#4CE0C1", "#FFC875", "#FF7D8A", "rgba(154,170,192,.16)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif}}
.stApp{{background:radial-gradient(ellipse at 15% 0%,#172B45 0%,{BG} 48%);color:{TEXT}}}
[data-testid="stHeader"]{{background:transparent}}
[data-testid="stSidebar"]{{background:#090F1C;border-right:1px solid {BORDER}}}
[data-testid="stSidebar"] *{{color:{TEXT}}}
.block-container{{max-width:1500px;padding-top:1.8rem;padding-bottom:3rem}}
h1,h2,h3{{font-family:'Manrope',sans-serif!important;color:{TEXT}!important;letter-spacing:-.035em}}
h1{{font-size:2.25rem!important;font-weight:800!important}}
p,label,[data-testid="stCaptionContainer"]{{color:{MUTED}}}
[data-testid="stMetric"]{{background:linear-gradient(145deg,{PANEL},#0D1625);border:1px solid {BORDER};border-radius:16px;padding:17px 19px;min-height:115px}}
[data-testid="stMetricLabel"]{{color:{MUTED};font-size:.8rem;font-weight:600}}
[data-testid="stMetricValue"]{{color:{TEXT};font-family:'Manrope',sans-serif;font-weight:800;font-size:1.65rem}}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{{background:#0A1322;border:1px solid {BORDER};border-radius:10px;color:{TEXT}}}
[data-testid="stTextArea"] textarea{{font-family:'DM Mono',monospace;font-size:.84rem;line-height:1.5}}
.stButton button,.stDownloadButton button{{border-radius:10px;font-weight:700;min-height:2.8rem}}
.stButton button[kind="primary"]{{background:linear-gradient(100deg,#35C9B0,{TEAL});color:#07151A;border:0}}
.stButton button[kind="secondary"],.stDownloadButton button{{background:{PANEL};color:{TEXT};border:1px solid {BORDER}}}
div[data-testid="stDataFrame"]{{border:1px solid {BORDER};border-radius:12px;overflow:hidden}}
.hero{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:1rem}}
.eyebrow,.section-label{{color:{TEAL};font-size:.72rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase}}
.hero-sub{{color:{MUTED};font-size:.96rem;line-height:1.55;max-width:760px}}
.pill{{display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(76,224,193,.08);border:1px solid rgba(76,224,193,.25);color:{TEAL};font-size:.74rem;font-weight:800;white-space:nowrap;margin-top:8px}}
.panel{{background:linear-gradient(145deg,{PANEL},#0D1625);border:1px solid {BORDER};border-radius:15px;padding:17px 19px}}
.panel-title{{color:{TEXT};font-family:'Manrope',sans-serif;font-weight:750;font-size:1rem;margin-bottom:6px}}
.panel-copy{{color:{MUTED};font-size:.86rem;line-height:1.55}}
.section-label{{color:{MUTED};margin:1.35rem 0 .4rem}}
.status{{display:inline-block;padding:6px 10px;border-radius:999px;font-size:.72rem;font-weight:800}}
.pass{{color:{TEAL};background:rgba(76,224,193,.1);border:1px solid rgba(76,224,193,.24)}}
.warn{{color:{AMBER};background:rgba(255,200,117,.1);border:1px solid rgba(255,200,117,.24)}}
.fail{{color:{RED};background:rgba(255,125,138,.1);border:1px solid rgba(255,125,138,.24)}}
.insight{{border-left:3px solid {TEAL};background:rgba(76,224,193,.055);border-radius:0 10px 10px 0;padding:12px 15px;margin:8px 0;color:{TEXT};line-height:1.5}}
.footer{{color:{MUTED};font-size:.76rem;border-top:1px solid {BORDER};margin-top:2rem;padding-top:1rem}}
</style>
""", unsafe_allow_html=True)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": int(os.getenv("MYSQL_PORT", "4000")),
    "ssl_disabled": False,
    "connection_timeout": 12,
}

SAMPLE_QUERY = """SELECT
    s.`Order Number`,
    s.`Order Date`,
    s.ProductKey,
    s.CustomerKey,
    s.StoreKey,
    s.Quantity
FROM sales AS s
LEFT JOIN products AS p
    ON s.ProductKey = p.ProductKey"""


def missing_settings():
    return [k for k in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE") if not os.getenv(k)]


def safe_identifier(value):
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", value):
        raise ValueError("Enter a table name like sales or schema_name.sales; SQL fragments are not allowed.")
    return ".".join(f"`{part}`" for part in value.split("."))


def safe_select(query):
    query = query.strip()
    if not query:
        raise ValueError("Paste a SQL query before running the audit.")
    if query.endswith(";"):
        query = query[:-1].rstrip()
    if ";" in query:
        raise ValueError("Only one SQL statement is allowed.")
    if not re.match(r"^(SELECT|WITH)\b", query, re.I):
        raise ValueError("For safety, only SELECT or WITH queries are accepted.")
    blocked = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE|CALL|EXECUTE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b"
    if re.search(blocked, query, re.I):
        raise ValueError("The query contains a blocked operation or keyword.")
    return query


def audit(base_table, query):
    table_sql = safe_identifier(base_table)
    query = safe_select(query)
    missing = missing_settings()
    if missing:
        raise RuntimeError("Missing .env settings: " + ", ".join(missing))
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor()
        try:
            start_time = time.time() # START THE TIMER
            
            cur.execute(f"SELECT COUNT(*) FROM {table_sql}")
            base_count = int(cur.fetchone()[0])
            
            cur.execute(f"SELECT COUNT(*) FROM ({query}) AS audit_subquery")
            join_count = int(cur.fetchone()[0])
            
            # FETCH THE DATA PREVIEW
            cur.execute(f"{query} LIMIT 5")
            preview_cols = [col[0] for col in cur.description]
            preview_data = cur.fetchall()
            
            execution_time = round(time.time() - start_time, 2) # END THE TIMER
            
        finally:
            cur.close()
    finally:
        conn.close()
        
    delta = join_count - base_count
    return {
        "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "base_table": base_table.strip(), "base_count": base_count,
        "join_count": join_count, "delta": delta,
        "ratio": join_count / base_count if base_count else None,
        "change_pct": delta / base_count * 100 if base_count else None,
        "query": query,
        "execution_time": execution_time, # Pass timer to UI
        "preview_cols": preview_cols,     # Pass columns to UI
        "preview_data": preview_data      # Pass data to UI
    }


if "audit_history" not in st.session_state:
    st.session_state.audit_history = []
if "latest_audit" not in st.session_state:
    st.session_state.latest_audit = None

with st.sidebar:
    st.markdown("## 🛡️ TRUST AUDITOR")
    st.caption("DATA QUALITY WORKSPACE")
    st.divider()
    st.markdown("### How to use")
    st.markdown("**1.** Choose a baseline table.\n\n**2.** Paste one SELECT/JOIN query.\n\n**3.** Compare row counts and investigate the difference.")
    st.divider()
    st.markdown("### Interpret the signal")
    st.markdown("- **Rows increased:** possible one-to-many multiplication.\n- **Rows decreased:** possible unmatched records or filters.\n- **Same count:** not proof the join is correct.")
    st.divider()
    st.caption("Use a dedicated MySQL account with SELECT-only privileges.")
    if st.button("Clear session history", use_container_width=True):
        st.session_state.audit_history = []
        st.session_state.latest_audit = None
        st.rerun()

st.markdown("""
<div class="hero">
  <div>
    <div class="eyebrow">DATA QUALITY · JOIN VALIDATION</div>
    <h1>SQL Revenue Trust Auditor</h1>
    <div class="hero-sub">Catch join fan-out, unexpected row loss, and suspicious result-set changes before they contaminate revenue reporting.</div>
  </div>
  <div class="pill">● READ-ONLY AUDIT MODE</div>
</div>
""", unsafe_allow_html=True)

missing = missing_settings()
if missing:
    st.warning("Database configuration is incomplete. Add these variables to your .env file: " + ", ".join(missing))
else:
    st.markdown('<div class="insight">Configuration loaded. Connection is tested when you run an audit.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">01 / CONFIGURE AUDIT</div>', unsafe_allow_html=True)
left, right = st.columns([.8, 1.7], gap="large")
with left:
    st.markdown('<div class="panel-title">Baseline table</div><div class="panel-copy">The table whose row count defines your baseline.</div>', unsafe_allow_html=True)
    base_table = st.text_input("Base table", value="sales", label_visibility="collapsed", placeholder="sales")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Audit settings</div>', unsafe_allow_html=True)
    show_diagnostics = st.toggle("Show diagnostic interpretation", True)
    remember_history = st.toggle("Keep history in this session", True)
    st.caption("Session history is temporary.")
with right:
    st.markdown('<div class="panel-title">JOIN query</div><div class="panel-copy">Paste a single read-only SELECT query. The auditor wraps it in COUNT(*).</div>', unsafe_allow_html=True)
    join_query = st.text_area("JOIN SQL", value=SAMPLE_QUERY, height=245, label_visibility="collapsed")
    run_col, sample_col, _ = st.columns([1.15, 1.05, 2.8])
    with run_col:
        run_clicked = st.button("▶ Run audit", type="primary", use_container_width=True)
    with sample_col:
        sample_clicked = st.button("↺ Reset sample", use_container_width=True)

if sample_clicked:
    st.session_state.sample_notice = True
    st.rerun()
if st.session_state.pop("sample_notice", False):
    st.toast("Sample query restored.", icon="🧪")

if run_clicked:
    try:
        with st.spinner("Connecting to MySQL and comparing row counts…"):
            result = audit(base_table, join_query)
        st.session_state.latest_audit = result
        if remember_history:
            st.session_state.audit_history.insert(0, result)
            st.session_state.audit_history = st.session_state.audit_history[:20]
        st.toast("Audit completed.", icon="✅")
    except ValueError as exc:
        st.error(f"Input validation: {exc}")
    except mysql.connector.Error as exc:
        st.error("MySQL could not execute the audit. Check credentials, permissions, table names, and SQL syntax.")
        with st.expander("Technical database details"):
            st.code(str(exc))
    except Exception as exc:
        st.error(str(exc))

st.markdown('<div class="section-label">02 / AUDIT RESULTS</div>', unsafe_allow_html=True)
result = st.session_state.latest_audit
if result is None:
    st.markdown('<div class="panel"><div class="panel-title">Your results will appear here</div><div class="panel-copy">Run an audit to compare the baseline table row count with the JOIN query result. Start with a clear definition of the table grain.</div></div>', unsafe_allow_html=True)
else:
    base_count, join_count, delta = result["base_count"], result["join_count"], result["delta"]
    if base_count == 0:
        status, css, summary = "EMPTY BASELINE", "warn", "The base table has zero rows; a multiplier ratio is not meaningful."
    elif delta > 0:
        status, css, summary = "ROW MULTIPLICATION SIGNAL", "fail", "The JOIN result has more rows than the baseline. Check duplicate join keys and one-to-many relationships."
    elif delta < 0:
        status, css, summary = "ROW LOSS SIGNAL", "warn", "The JOIN result has fewer rows. Check INNER JOIN exclusions, filters, and unmatched foreign keys."
    else:
        status, css, summary = "ROW COUNT MATCH", "pass", "The counts match. This is not proof of correctness: duplicated and missing rows can offset each other."
    st.markdown(f'<span class="status {css}">{status}</span><div class="panel-copy" style="margin-top:10px">{summary}</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Baseline rows", f"{base_count:,}")
    k2.metric("JOIN result rows", f"{join_count:,}")
    k3.metric("Row delta", f"{delta:+,}", delta_color="inverse")
    k4.metric("JOIN / baseline", f"{result['ratio']:.3f}×" if result["ratio"] is not None else "N/A")
    if base_count:
        st.progress(min(join_count / base_count, 1.0), text=f"Result size change: {result['change_pct']:+.2f}%")
        if join_count > base_count:
            st.caption("Progress display is capped at 100%; the ratio above shows the full multiplier.")
    st.caption(f"Completed {result['timestamp']} · Execution Time: **{result['execution_time']}s** · Baseline table: {result['base_table']}")
    with st.expander("🔍 Preview Joined Data (First 5 Rows)"):
        st.dataframe(pd.DataFrame(result['preview_data'], columns=result['preview_cols']), use_container_width=True)

    if show_diagnostics:
        st.markdown('<div class="section-label">03 / INVESTIGATION GUIDANCE</div>', unsafe_allow_html=True)
        d1, d2 = st.columns(2, gap="large")
        with d1:
            st.markdown(f'<div class="panel"><div class="panel-title">Audit snapshot</div><div class="panel-copy">Baseline: <b>{result["base_table"]}</b><br>Baseline rows: <b>{base_count:,}</b><br>JOIN rows: <b>{join_count:,}</b><br>Difference: <b>{delta:+,}</b></div></div>', unsafe_allow_html=True)
        with d2:
            if delta > 0:
                advice = "Test each join key for uniqueness using GROUP BY key HAVING COUNT(*) > 1. A single base row matching several dimension rows can multiply revenue."
            elif delta < 0:
                advice = "Compare LEFT JOIN and INNER JOIN behaviour, inspect WHERE filters on joined tables, and quantify unmatched keys before changing production SQL."
            else:
                advice = "Validate intended grain, uniqueness of joined keys, and unmatched-key counts. Equal row counts can hide offsetting duplicates and losses."
            st.markdown(f'<div class="panel"><div class="panel-title">Recommended next check</div><div class="panel-copy">{advice}</div></div>', unsafe_allow_html=True)
    with st.expander("Inspect audited SQL"):
        st.code(result["query"], language="sql")

st.markdown('<div class="section-label">04 / SESSION AUDIT HISTORY</div>', unsafe_allow_html=True)
history = st.session_state.audit_history
if history:
    history_df = pd.DataFrame([{
        "Timestamp": x["timestamp"], "Base table": x["base_table"],
        "Baseline rows": x["base_count"], "JOIN rows": x["join_count"],
        "Delta": x["delta"], "Ratio": round(x["ratio"], 3) if x["ratio"] is not None else None,
        "Change %": round(x["change_pct"], 2) if x["change_pct"] is not None else None,
    } for x in history])
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    st.download_button("⬇ Export audit history", history_df.to_csv(index=False).encode("utf-8"),
                       "sql_trust_audit_history.csv", "text/csv")
else:
    st.markdown('<div class="panel-copy">No audits saved yet. Run an audit with session history enabled to compare results during this session.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">SQL Revenue Trust Auditor · Join cardinality diagnostics · Row counts are diagnostic signals, not formal proof of correctness. Validate intended grain and key constraints. Use a least-privilege, SELECT-only database account.</div>', unsafe_allow_html=True)