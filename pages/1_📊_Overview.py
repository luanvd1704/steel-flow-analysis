"""
Overview Page
Data summary and quality checks
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data, get_data_summary
from config.config import TICKERS, CACHE_TTL
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("📊 Data Overview")

# Load data with caching
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

@st.cache_data(ttl=CACHE_TTL)
def get_summary(data):
    return get_data_summary(data)

# Load data
with st.spinner("Loading data..."):
    data = load_all_data()
    summary = get_summary(data)

# Display summary
st.header("Data Summary")

st.dataframe(summary, use_container_width=True)

# Timeline visualization
st.header("Data Coverage Timeline")

fig = go.Figure()

for _, row in summary.iterrows():
    ticker = row['Ticker']
    fig.add_trace(go.Scatter(
        x=[row['Start Date'], row['End Date']],
        y=[ticker, ticker],
        mode='lines+markers',
        name=ticker,
        line=dict(width=10)
    ))

fig.update_layout(
    title="Data Coverage by Ticker",
    xaxis_title="Date",
    yaxis_title="Ticker",
    height=300,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# Data quality metrics
st.header("Data Quality Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Tickers Loaded",
        len(data),
        delta=None
    )

with col2:
    avg_days = int(summary['Total Days'].mean())
    st.metric(
        "Avg Data Points",
        f"{avg_days:,}",
        delta=None
    )

with col3:
    avg_foreign = int(summary['Foreign Data Points'].mean())
    st.metric(
        "Avg Foreign Trading Points",
        f"{avg_foreign:,}",
        delta=None
    )

# Missing data analysis
st.header("Missing Data Analysis")

missing_data = []
for ticker, df in data.items():
    missing_row = {
        'Ticker': ticker,
        'Foreign Net Buy': f"{(df[FOREIGN_NET_BUY_VAL].isna().sum() / len(df) * 100):.1f}%",
        'Self Net Buy': f"{(df[SELF_NET_BUY_VAL].isna().sum() / len(df) * 100):.1f}%" if SELF_NET_BUY_VAL in df.columns else "N/A",
        'PE': f"{(df[PE].isna().sum() / len(df) * 100):.1f}%" if PE in df.columns else "N/A",
        'PB': f"{(df[PB].isna().sum() / len(df) * 100):.1f}%" if PB in df.columns else "N/A",
        'Close': f"{(df[CLOSE].isna().sum() / len(df) * 100):.1f}%"
    }
    missing_data.append(missing_row)

missing_df = pd.DataFrame(missing_data)
st.dataframe(missing_df, use_container_width=True)

# Sample data
st.header("Sample Data")

selected_ticker = st.selectbox("Select Ticker", TICKERS)

if selected_ticker in data:
    ticker_df = data[selected_ticker]

    st.subheader(f"{selected_ticker} - Latest 10 Days")

    # Select columns to display
    display_cols = [DATE, CLOSE, FOREIGN_NET_BUY_VAL, MARKET_RETURN]
    if SELF_NET_BUY_VAL in ticker_df.columns:
        display_cols.insert(3, SELF_NET_BUY_VAL)
    if PE in ticker_df.columns:
        display_cols.append(PE)
    if PB in ticker_df.columns:
        display_cols.append(PB)

    available_cols = [col for col in display_cols if col in ticker_df.columns]

    st.dataframe(
        ticker_df[available_cols].tail(10).sort_values(DATE, ascending=False),
        use_container_width=True
    )

# Warnings
st.warning("""
⚠️ **Data Limitations**:
- Dữ liệu tự doanh chỉ có từ 2022-11 (3 năm)
- Một số ngày có thể thiếu dữ liệu giao dịch (NaN)
- Giá được forward-fill nhưng trading data giữ nguyên NaN
""")

st.info("""
💡 **Tip**: Sử dụng sidebar để điều hướng đến các trang phân tích cụ thể
""")
