"""
Q2: Self-Trading Analysis Page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data
from analysis.self_trading import (
    check_data_availability, compare_normalization_methods,
    get_best_normalization_method
)
from config.config import TICKERS, CACHE_TTL, SELF_TRADING_WARNING, TERCILE_LABELS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q2: Self-Trading", page_icon="💼", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("💼 Q2: Self-Trading Signal Analysis")

st.markdown("""
**Research Question**: Are proprietary (self-trading) flows profitable? Which normalization method works better?

This analysis compares two normalization methods:
- **ADV20**: Net Buy / 20-day average volume
- **GTGD**: Net Buy / (Buy Value + Sell Value)
""")

# Warning banner
st.warning(SELF_TRADING_WARNING)

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

# Sidebar
st.sidebar.header("Filters")
selected_ticker = st.sidebar.selectbox("Select Ticker", TICKERS)
selected_horizon = st.sidebar.selectbox(
    "Forward Return Horizon",
    [1, 3, 5, 10],
    index=2,
    format_func=lambda x: f"T+{x} days"
)

# Load and check data
with st.spinner("Loading data..."):
    data = load_all_data()
    df = data[selected_ticker]

    availability = check_data_availability(df)

# Check if data is available
if not availability['available']:
    st.error(f"❌ {availability['reason']}")
    st.stop()

# Show data availability
st.header(f"Data Availability - {selected_ticker}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Data Points", f"{availability['data_points']:,}")

with col2:
    st.metric("Coverage", f"{availability['coverage']:.1%}")

with col3:
    st.metric("Start Date", str(availability['start_date'])[:10] if availability['start_date'] else "N/A")

with col4:
    st.metric("End Date", str(availability['end_date'])[:10] if availability['end_date'] else "N/A")

# Run analysis
@st.cache_data(ttl=CACHE_TTL)
def run_comparison(ticker):
    return compare_normalization_methods(data[ticker])

with st.spinner(f"Analyzing {selected_ticker}..."):
    comparison = run_comparison(selected_ticker)
    best_method = get_best_normalization_method(comparison)

# Method comparison summary
st.header("Normalization Method Comparison")

st.info(f"**Recommended Method**: {best_method} (based on average IC across horizons)")

# Create comparison table
comp_data = []
for method in ['ADV20', 'GTGD']:
    if method in comparison:
        for horizon in [1, 3, 5, 10]:
            horizon_key = f'T+{horizon}'
            if horizon_key in comparison[method]:
                result = comparison[method][horizon_key]
                if 'error' not in result:
                    comp_data.append({
                        'Method': method,
                        'Horizon': horizon_key,
                        'IC': result['ic']['ic'],
                        'IC P-value': result['ic'][P_VALUE],
                        'Sample Size': result['sample_size'],
                        'Monotonic': '✅' if result['monotonicity'] else '❌'
                    })

if comp_data:
    comp_df = pd.DataFrame(comp_data)

    st.dataframe(
        comp_df.style.format({
            'IC': '{:.4f}',
            'IC P-value': '{:.4f}',
            'Sample Size': '{:.0f}'
        }),
        use_container_width=True
    )

# Detailed analysis for selected horizon
st.header(f"Detailed Analysis - T+{selected_horizon}")

tabs = st.tabs(['ADV20 Method', 'GTGD Method'])

for idx, method in enumerate(['ADV20', 'GTGD']):
    with tabs[idx]:
        horizon_key = f'T+{selected_horizon}'

        if horizon_key in comparison[method]:
            result = comparison[method][horizon_key]

            if 'error' in result:
                st.error(result['error'])
                continue

            # Tercile statistics
            st.subheader(f"Returns by {method} Signal Tercile")

            tercile_stats = result['tercile_stats']

            # Bar chart
            colors = ['red', 'gray', 'green']
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=tercile_stats[TERCILE],
                y=tercile_stats['mean'],
                marker_color=colors,
                text=tercile_stats['mean'].apply(lambda x: f"{x:.2%}"),
                textposition='outside'
            ))

            fig.update_layout(
                title=f"{selected_ticker} - Forward Returns by {method} Signal (T+{selected_horizon})",
                xaxis_title="Tercile",
                yaxis_title="Mean Forward Return",
                yaxis_tickformat='.2%',
                height=400,
                template='plotly_white'
            )

            fig.add_hline(y=0, line_dash="dash", line_color="gray")

            st.plotly_chart(fig, use_container_width=True)

            # Metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                ic_val = result['ic']['ic']
                st.metric(
                    "Information Coefficient",
                    f"{ic_val:.4f}",
                    delta="Significant" if result['ic']['significant'] else "Not significant"
                )

            with col2:
                monotonic = result['monotonicity']
                st.metric(
                    "Monotonic Trend",
                    "✅ Yes" if monotonic else "❌ No"
                )

            with col3:
                st.metric(
                    "Sample Size",
                    f"{result['sample_size']:,}"
                )

            # Detailed table
            st.subheader("Tercile Statistics")

            st.dataframe(
                tercile_stats.style.format({
                    'mean': '{:.4f}',
                    'std': '{:.4f}',
                    'median': '{:.4f}',
                    'count': '{:.0f}'
                }),
                use_container_width=True
            )

            # Statistical tests
            st.subheader("Statistical Tests")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Information Coefficient Test**")
                st.write(f"- IC: {result['ic']['ic']:.4f}")
                st.write(f"- P-value: {result['ic'][P_VALUE]:.4f}")
                st.write(f"- Significant: {'✅' if result['ic']['significant'] else '❌'}")
                st.write(f"- Sample: {result['ic']['n']}")

            with col2:
                st.write("**ANOVA Test**")
                anova = result['anova']
                st.write(f"- F-statistic: {anova.get('f_stat', 'N/A'):.2f}")
                st.write(f"- P-value: {anova.get(P_VALUE, 'N/A'):.4f}")
                st.write(f"- Significant: {'✅' if anova.get('significant') else '❌'}")

# Interpretation
st.header("Interpretation")

st.info(f"""
**Key Findings for {selected_ticker}**:

- **Recommended Method**: {best_method}
- **Data Period**: {availability.get('start_date', 'N/A')} to {availability.get('end_date', 'N/A')} (~{availability['data_points']} points)

**How to interpret**:
- **Positive IC**: Self-trading signal predicts forward returns
- **Monotonic Terciles**: T1 (Sell) < T2 (Neutral) < T3 (Buy) → Signal works!
- **Significant tests (p < 0.05)**: Reliable pattern

**ADV20 vs GTGD**:
- **ADV20**: Normalizes by trading volume
- **GTGD**: Normalizes by total trading value (may be more stable)
""")

st.warning("""
⚠️ **Important Limitations**:

1. **Limited History**: Self-trading data only available from 2022-11 (~3 years)
2. **Statistical Power**: Shorter history = less reliable patterns
3. **Market Regime**: Results may vary in different market conditions
4. **Not Investment Advice**: Research purposes only

The limited data means results should be interpreted with extra caution!
""")
