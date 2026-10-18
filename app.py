import streamlit as st
import pandas as pd
import mysql.connector
import os
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "port": 4000,
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

# 1. PAGE CONFIG & CUSTOM CSS
st.set_page_config(page_title="Global Retail Dashboard", page_icon="🌌", layout="wide")

# Custom Colors & Helper Functions
PURPLE = "#c084fc"  # Brighter purple
BLUE = "#60a5fa"    # Brighter blue

def money(val):
    return f"${val:,.2f}"

def chart_layout(fig, height=400):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f8fafc", # Bright white text for charts
        margin=dict(l=20, r=20, t=40, b=20),
        height=height
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color="#cbd5e1"))
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color="#cbd5e1"))
    return fig

def empty_state():
    st.info("No data available for the current selection.")

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    }

     /* FIX FOR PHONE NOTCHES */
    .block-container { 
        padding-top: 4rem !important; 
        padding-bottom: 3rem !important; 
    }
    
    /* FORCE ALL TEXT TO BE BRIGHT AND READABLE */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #f8fafc !important;
    }
    
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid #334155;
    }
    
    /* Glassmorphism Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        color: #60a5fa !important; /* Bright blue values */
        font-weight: 700;
    }
    
    /* Data Table Styling (Fix for grayed out rows) */
    div[data-testid="stDataFrame"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* Input boxes (Search, Slider, Selectbox) */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-color: #475569 !important;
        color: #f8fafc !important;
    }
    
    /* Section Kicker Style */
    .section-kicker {
        color: #c084fc !important;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Insight Box Style */
    .insight {
        background: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #c084fc;
        padding: 15px 20px;
        border-radius: 0 8px 8px 0;
    }
    .insight-body { color: #e2e8f0 !important; font-size: 0.95rem; }
    .small-note { color: #94a3b8 !important; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# 2. DATA FETCHING
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_master_analytics():
    query = """
        SELECT 
            s.`Order Number`,
            s.`Order Date`,
            s.Quantity,
            p.`Product Name`,
            p.Category,
            p.Subcategory,
            p.`Unit Price USD`,
            p.`Unit Cost USD`,
            st.Country AS StoreCountry,
            c.Name AS CustomerName,
            c.Country AS CustomerCountry
        FROM sales s
        INNER JOIN products p ON s.ProductKey = p.ProductKey
        INNER JOIN stores st ON s.StoreKey = st.StoreKey
        INNER JOIN customers c ON s.CustomerKey = c.CustomerKey;
    """
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                records = cursor.fetchall()
                columns = cursor.column_names
                
        df = pd.DataFrame(records, columns=columns)
        
        df['Revenue USD'] = df['Quantity'] * df['Unit Price USD']
        df['Cost USD'] = df['Quantity'] * df['Unit Cost USD']
        df['Profit USD'] = df['Revenue USD'] - df['Cost USD']
        df['Order Date'] = pd.to_datetime(df['Order Date'])
        return df
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

with st.spinner("Connecting to database and calculating metrics..."):
    df = fetch_master_analytics()

if df.empty:
    st.warning("No data found. Please check your database connection.")
    st.stop()

# 3. SIDEBAR FILTERS
with st.sidebar:
    st.title("Global Filters")
    countries = ["All"] + df['StoreCountry'].unique().tolist()
    selected_country = st.selectbox("🌍 Store Country", countries)
    
    date_min = df['Order Date'].min().date()
    date_max = df['Order Date'].max().date()
    date_range = st.date_input("📅 Date Range", [date_min, date_max])

filtered = df.copy()
if selected_country != "All":
    filtered = filtered[filtered['StoreCountry'] == selected_country]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered['Order Date'].dt.date >= start_date) & 
        (filtered['Order Date'].dt.date <= end_date)
    ]

if filtered.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# 4. CALCULATE KPIS
total_revenue = filtered['Revenue USD'].sum()
total_profit = filtered['Profit USD'].sum()
total_orders = filtered['Order Number'].nunique()
margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

st.title("🌐 Global Retail Analytics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Revenue", money(total_revenue))
kpi2.metric("Gross Profit", money(total_profit))
kpi3.metric("Total Orders", f"{total_orders:,}")
kpi4.metric("Gross Margin", f"{margin:.1f}%")

# 5. VISUAL ANALYTICS
st.markdown('<div class="section-kicker">01 / CATEGORY & TIME TRENDS</div>', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    cat = filtered.groupby("Category")["Revenue USD"].sum().reset_index()
    fig_pie = px.pie(cat, values="Revenue USD", names="Category", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
    chart_layout(fig_pie, 350)
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

with col_right:
    time_df = filtered.groupby(filtered['Order Date'].dt.to_period('M'))["Revenue USD"].sum().reset_index()
    time_df['Order Date'] = time_df['Order Date'].astype(str)
    fig_line = px.line(time_df, x="Order Date", y="Revenue USD", markers=True)
    fig_line.update_traces(line_color=BLUE, line_width=3)
    chart_layout(fig_line, 350)
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

# 6. COUNTRY PERFORMANCE
st.markdown('<div class="section-kicker">02 / GEOGRAPHIC PERFORMANCE</div>', unsafe_allow_html=True)
st.subheader("Revenue by Store Country")
country = filtered.groupby("StoreCountry", as_index=False).agg(
    **{"Revenue USD": ("Revenue USD", "sum"), "Profit USD": ("Profit USD", "sum")}
).sort_values("Revenue USD", ascending=False)

if country.empty:
    empty_state()
else:
    fig_country = px.bar(
        country, x="Revenue USD", y="StoreCountry", orientation="h",
        color_discrete_sequence=[BLUE],
        custom_data=["Profit USD"]
    )
    fig_country.update_traces(
        marker_line_width=0,
        hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<br>Profit: $%{customdata[0]:,.0f}<extra></extra>",
    )
    chart_layout(fig_country, max(330, 34 * len(country)))
    st.plotly_chart(fig_country, use_container_width=True, config={"displayModeBar": False})

# 7. PRODUCT LEADERS
st.markdown('<div class="section-kicker">03 / PRODUCT PERFORMANCE</div>', unsafe_allow_html=True)
st.subheader("Top products by revenue")
top_n = st.slider("Products to display", min_value=5, max_value=15, value=8, step=1)

products = (
    filtered.groupby(["Product Name", "Category"], as_index=False)
    .agg(
        **{
            "Revenue USD": ("Revenue USD", "sum"),
            "Profit USD": ("Profit USD", "sum"),
            "Units sold": ("Quantity", "sum"),
        }
    )
)
products["Profit Margin %"] = products["Profit USD"].div(
    products["Revenue USD"].replace(0, pd.NA)
) * 100
products = products.sort_values("Revenue USD", ascending=False).head(top_n)

if products.empty:
    empty_state()
else:
    fig_products = px.bar(
        products.sort_values("Revenue USD", ascending=True),
        x="Revenue USD", y="Product Name", orientation="h",
        color_discrete_sequence=[PURPLE],
        custom_data=["Category", "Profit USD", "Units sold", "Profit Margin %"],
    )
    fig_products.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "%{y}<br>Category: %{customdata[0]}<br>Revenue: $%{x:,.0f}"
            "<br>Profit: $%{customdata[1]:,.0f}<br>Units: %{customdata[2]:,.0f}"
            "<br>Margin: %{customdata[3]:.1f}%<extra></extra>"
        ),
    )
    chart_layout(fig_products, max(320, 38 * len(products)))
    st.plotly_chart(fig_products, use_container_width=True, config={"displayModeBar": False})

# 8. EXECUTIVE INSIGHTS
best_category = cat.sort_values("Revenue USD", ascending=False).iloc[0] if not cat.empty else None
best_country = country.iloc[0] if not country.empty else None
best_product = products.iloc[0] if not products.empty else None

insights = []
if best_category is not None:
    share = (best_category["Revenue USD"] / total_revenue * 100) if total_revenue else 0
    insights.append(
        f"<b>{best_category['Category']}</b> is the leading category, contributing "
        f"<b>{share:.1f}%</b> of filtered revenue ({money(best_category['Revenue USD'])})."
    )
if best_country is not None:
    insights.append(
        f"<b>{best_country['StoreCountry']}</b> is the top store market by revenue "
        f"({money(best_country['Revenue USD'])})."
    )
if best_product is not None:
    insights.append(
        f"<b>{best_product['Product Name']}</b> is the highest-revenue product in the displayed top-product set "
        f"({money(best_product['Revenue USD'])})."
    )
insights.append(
    f"Gross margin is <b>{margin:.1f}%</b>. This is product-level gross margin, not net profit margin, "
    "because operating expenses, taxes and overhead are not included."
)

st.markdown('<div class="section-kicker">04 / EXECUTIVE TAKEAWAYS</div>', unsafe_allow_html=True)
st.subheader("What stands out")
for insight in insights:
    st.markdown(
        f'<div class="insight" style="margin-bottom:9px;"><div class="insight-body">{insight}</div></div>',
        unsafe_allow_html=True,
    )

# 9. DETAIL TABLE
st.markdown('<div class="section-kicker">05 / DATA EXPLORER</div>', unsafe_allow_html=True)
st.subheader("Sales line-item detail")
st.caption("Use this table to inspect the joined sales, product, store and customer records behind the KPIs.")

search = st.text_input("Search product, customer, category or country", placeholder="e.g. laptop, UK, accessories")
table_df = filtered.copy()

if search:
    mask = table_df.astype(str).apply(
        lambda col: col.str.contains(search, case=False, na=False)
    ).any(axis=1)
    table_df = table_df[mask]

table_df["Profit Margin %"] = table_df["Profit USD"].div(table_df["Revenue USD"].replace(0, pd.NA)) * 100

display_cols = [
    "Order Number", "Order Date", "Product Name", "Category", "Subcategory",
    "Quantity", "Unit Price USD", "Unit Cost USD", "Revenue USD", "Cost USD",
    "Profit USD", "Profit Margin %", "StoreCountry", "CustomerName", "CustomerCountry",
]
display_cols = [c for c in display_cols if c in table_df.columns]

st.dataframe(
    table_df[display_cols].sort_values("Order Date", ascending=False, na_position="last"),
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        "Order Date": st.column_config.DateColumn("Order date", format="DD MMM YYYY"),
        "Unit Price USD": st.column_config.NumberColumn("Unit price", format="$%.2f"),
        "Unit Cost USD": st.column_config.NumberColumn("Unit cost", format="$%.2f"),
        "Revenue USD": st.column_config.NumberColumn("Revenue", format="$%.2f"),
        "Cost USD": st.column_config.NumberColumn("Cost", format="$%.2f"),
        "Profit USD": st.column_config.NumberColumn("Gross profit", format="$%.2f"),
        "Profit Margin %": st.column_config.NumberColumn("Margin", format="%.1f%%"),
    },
)

csv = table_df[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Export filtered rows as CSV",
    data=csv,
    file_name="global_retail_filtered.csv",
    mime="text/csv",
)

st.markdown("---")
st.markdown(
    '<div class="small-note">Definitions: Revenue = quantity × unit price. Cost = quantity × unit cost. '
    'Gross profit = revenue − cost. AOV = filtered revenue ÷ distinct orders. '
    'Results reflect the current filters and the joined records returned by MySQL.</div>',
    unsafe_allow_html=True,
)