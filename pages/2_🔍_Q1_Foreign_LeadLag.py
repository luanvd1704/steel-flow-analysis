"""
Q1: Foreign Lead/Lag Analysis Page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data
from analysis.lead_lag import lead_lag_analysis_full, find_optimal_normalization_window
from config.config import TICKERS, FORWARD_RETURN_HORIZONS, CACHE_TTL, QUINTILE_COLORS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q1: Foreign Lead/Lag", page_icon="🔍", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("🔍 Q1: Foreign Lead/Lag Analysis")

st.markdown("""
**Research Question**: Do foreign investors predict future returns?

This analysis examines whether foreign net buying today predicts stock returns at T+1, T+3, T+5, and T+10.
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

with st.spinner("Loading data..."):
    data = load_all_data()

# Sidebar filters
st.sidebar.header("Filters")
selected_ticker = st.sidebar.selectbox("Select Ticker", TICKERS)
selected_horizon = st.sidebar.selectbox(
    "Forward Return Horizon",
    FORWARD_RETURN_HORIZONS,
    format_func=lambda x: f"T+{x} days"
)

# Run analysis
@st.cache_data(ttl=CACHE_TTL)
def run_lead_lag_analysis(ticker):
    return lead_lag_analysis_full(data[ticker])

with st.spinner(f"Analyzing {selected_ticker}..."):
    results = run_lead_lag_analysis(selected_ticker)

# Display results
horizon_key = f'T+{selected_horizon}'

if horizon_key in results:
    result = results[horizon_key]

    # Summary metrics
    st.header(f"Results for {selected_ticker} at T+{selected_horizon}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Q5 Mean Return",
            f"{result['q5_mean']:.4f}",
            delta=f"{result['q5_mean']:.2%}"
        )

    with col2:
        st.metric(
            "Q1 Mean Return",
            f"{result['q1_mean']:.4f}",
            delta=f"{result['q1_mean']:.2%}"
        )

    with col3:
        st.metric(
            "Q5 - Q1 Spread",
            f"{result['spread']:.4f}",
            delta=f"{result['spread']:.2%}"
        )

    with col4:
        significance = "✅ Significant" if result['significant'] else "❌ Not Significant"
        st.metric(
            "Statistical Test",
            significance,
            delta=f"p={result['p_value']:.4f}"
        )

    # Quintile bar chart
    st.header("Mean Excess Return by Quintile")

    quintile_stats = result['quintile_stats']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=quintile_stats[QUINTILE],
        y=quintile_stats['mean'],
        marker_color=QUINTILE_COLORS,
        text=quintile_stats['mean'].apply(lambda x: f"{x:.2%}"),
        textposition='outside'
    ))

    fig.update_layout(
        title=f"Mean Excess Return by Foreign Net Buying Quintile (T+{selected_horizon})",
        xaxis_title="Quintile (Q1 = Lowest Foreign Net Buy, Q5 = Highest)",
        yaxis_title="Mean Excess Return",
        yaxis_tickformat='.2%',
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Detailed statistics table
    st.header("Detailed Statistics")

    st.dataframe(
        quintile_stats.style.format({
            'mean': '{:.4f}',
            'std': '{:.4f}',
            'median': '{:.4f}',
            'count': '{:.0f}'
        }),
        use_container_width=True
    )

# Information Coefficient Analysis
if 'ic_analysis' in results:
    st.header("Information Coefficient (IC) Analysis")

    st.markdown("""
    IC measures the correlation between foreign net buying and forward returns.
    Higher absolute IC indicates stronger predictive power.
    """)

    ic_data = []
    for horizon_key, ic_result in results['ic_analysis'].items():
        ic_data.append({
            'Horizon': horizon_key,
            'IC': ic_result['ic'],
            'P-Value': ic_result[P_VALUE],
            'Significant': '✅' if ic_result['significant'] else '❌',
            'Sample Size': ic_result['n']
        })

    ic_df = pd.DataFrame(ic_data)

    col1, col2 = st.columns([2, 1])

    with col1:
        # IC chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=ic_df['Horizon'],
            y=ic_df['IC'],
            marker_color=['green' if x > 0 else 'red' for x in ic_df['IC']],
            text=ic_df['IC'].apply(lambda x: f"{x:.4f}"),
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Information Coefficient by Horizon - {selected_ticker}",
            xaxis_title="Horizon",
            yaxis_title="IC",
            height=400,
            template='plotly_white'
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            ic_df.style.format({
                'IC': '{:.4f}',
                'P-Value': '{:.4f}',
                'Sample Size': '{:.0f}'
            }),
            use_container_width=True
        )

# All horizons comparison
st.header("All Horizons Comparison")

comparison_data = []
for horizon in FORWARD_RETURN_HORIZONS:
    hkey = f'T+{horizon}'
    if hkey in results:
        r = results[hkey]
        comparison_data.append({
            'Horizon': hkey,
            'Q5 Mean': r['q5_mean'],
            'Q1 Mean': r['q1_mean'],
            'Spread': r['spread'],
            'T-Stat': r['t_stat'],
            'P-Value': r['p_value'],
            'Significant': '✅' if r['significant'] else '❌'
        })

comp_df = pd.DataFrame(comparison_data)

st.dataframe(
    comp_df.style.format({
        'Q5 Mean': '{:.4f}',
        'Q1 Mean': '{:.4f}',
        'Spread': '{:.4f}',
        'T-Stat': '{:.2f}',
        'P-Value': '{:.4f}'
    }),
    use_container_width=True
)

# Interpretation
st.header("Interpretation")

st.info("""
**How to interpret these results:**

- **Positive Spread (Q5 > Q1)**: Foreign buying predicts higher future returns
- **Negative Spread (Q5 < Q1)**: Foreign buying predicts lower future returns (contrarian)
- **Statistical Significance**: p-value < 0.05 indicates reliable pattern
- **IC close to 0**: Weak predictive power
- **|IC| > 0.05**: Moderate predictive power
- **|IC| > 0.10**: Strong predictive power
""")

st.warning("""
⚠️ **Disclaimer**: Past performance does not guarantee future results.
This analysis is for research purposes only and should not be considered investment advice.
""")
