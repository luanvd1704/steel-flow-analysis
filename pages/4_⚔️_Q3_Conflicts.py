"""
Q3: Foreign vs Self Conflicts Page
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data
from analysis.conflicts import (
    analyze_conflict_returns, identify_leader,
    conflict_analysis_by_regime
)
from analysis.self_trading import check_data_availability
from config.config import TICKERS, CACHE_TTL, SELF_TRADING_WARNING
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q3: Conflicts", page_icon="⚔️", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("⚔️ Q3: Foreign vs Self Conflicts")

st.markdown("""
**Research Question**: Who leads when foreign and self-trading flows disagree?

This analysis examines:
1. **Conflict States**: Returns when foreign and self traders disagree
2. **Leadership**: Who predicts whom using Granger causality
3. **Market Regime**: Do patterns differ in bull vs bear markets?
""")

st.warning(SELF_TRADING_WARNING)

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

# Sidebar
st.sidebar.header("Filters")
selected_ticker = st.sidebar.selectbox("Select Ticker", TICKERS)
selected_horizon = st.sidebar.selectbox("Forward Horizon", [5, 10], format_func=lambda x: f"T+{x}")

# Load data
with st.spinner("Loading data..."):
    data = load_all_data()
    df = data[selected_ticker]

    # Check self-trading data availability
    availability = check_data_availability(df)

if not availability['available']:
    st.error(f"❌ {availability['reason']}")
    st.stop()

# Data info
st.info(f"📊 Self-trading data: {availability['data_points']:,} points | Coverage: {availability['coverage']:.1%}")

# Conflict state analysis
st.header(f"Conflict State Analysis - T+{selected_horizon}")

@st.cache_data(ttl=CACHE_TTL)
def run_conflict_analysis(ticker):
    return analyze_conflict_returns(data[ticker])

results = run_conflict_analysis(selected_ticker)

horizon_key = f'T+{selected_horizon}'
if horizon_key in results and 'error' not in results[horizon_key]:
    result = results[horizon_key]
    state_returns = result['state_returns']

    # Conflict matrix heatmap
    st.subheader("Returns by Conflict State")

    # Create 2x2 matrix
    matrix_data = {
        BOTH_BUY: state_returns[state_returns[CONFLICT_STATE] == BOTH_BUY]['mean'].values[0] if BOTH_BUY in state_returns[CONFLICT_STATE].values else 0,
        FOREIGN_BUY_SELF_SELL: state_returns[state_returns[CONFLICT_STATE] == FOREIGN_BUY_SELF_SELL]['mean'].values[0] if FOREIGN_BUY_SELF_SELL in state_returns[CONFLICT_STATE].values else 0,
        FOREIGN_SELL_SELF_BUY: state_returns[state_returns[CONFLICT_STATE] == FOREIGN_SELL_SELF_BUY]['mean'].values[0] if FOREIGN_SELL_SELF_BUY in state_returns[CONFLICT_STATE].values else 0,
        BOTH_SELL: state_returns[state_returns[CONFLICT_STATE] == BOTH_SELL]['mean'].values[0] if BOTH_SELL in state_returns[CONFLICT_STATE].values else 0
    }

    # Bar chart
    fig = go.Figure()

    colors = []
    for state in matrix_data.keys():
        val = matrix_data[state]
        if 'Buy' in state and 'Sell' not in state:
            colors.append('green')
        elif 'Sell' in state and 'Buy' not in state:
            colors.append('red')
        else:
            colors.append('orange')

    fig.add_trace(go.Bar(
        x=list(matrix_data.keys()),
        y=list(matrix_data.values()),
        marker_color=colors,
        text=[f"{v:.2%}" for v in matrix_data.values()],
        textposition='outside'
    ))

    fig.update_layout(
        title=f"{selected_ticker} - Forward Returns by Conflict State (T+{selected_horizon})",
        xaxis_title="Conflict State",
        yaxis_title="Mean Forward Return",
        yaxis_tickformat='.2%',
        height=500,
        template='plotly_white'
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.subheader("Detailed Statistics")
    st.dataframe(
        state_returns.style.format({
            'mean': '{:.4f}',
            'std': '{:.4f}',
            'count': '{:.0f}'
        }),
        use_container_width=True
    )

    # Key insights
    st.subheader("Key Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Conflict States (Disagreement)**:")
        fb_ss = matrix_data.get(FOREIGN_BUY_SELF_SELL, 0)
        fs_sb = matrix_data.get(FOREIGN_SELL_SELF_BUY, 0)

        st.write(f"- Foreign Buy, Self Sell: {fb_ss:.2%}")
        st.write(f"- Foreign Sell, Self Buy: {fs_sb:.2%}")

        if fb_ss > fs_sb:
            st.success("✅ Foreign buying signal stronger when they disagree")
        else:
            st.info("📊 Self buying signal stronger when they disagree")

    with col2:
        st.write("**Agreement States**:")
        both_buy = matrix_data.get(BOTH_BUY, 0)
        both_sell = matrix_data.get(BOTH_SELL, 0)

        st.write(f"- Both Buy: {both_buy:.2%}")
        st.write(f"- Both Sell: {both_sell:.2%}")

        if both_buy > 0:
            st.success("✅ Positive returns when both buy")
        if both_sell < 0:
            st.info("📉 Negative returns when both sell")

else:
    st.error("Unable to perform conflict analysis")

# Leadership analysis
st.header("Leadership Analysis (Granger Causality)")

st.markdown("""
This test examines whether one group's trading helps predict the other's trading.
""")

@st.cache_data(ttl=CACHE_TTL)
def run_leadership_analysis(ticker):
    return identify_leader(data[ticker])

leadership = run_leadership_analysis(selected_ticker)

if 'error' not in leadership:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Foreign → Self")
        st.caption("Does foreign trading predict self trading?")

        foreign_self = leadership['foreign_leads_self']

        if not foreign_self.empty:
            # Find most significant lag
            sig_lags = foreign_self[foreign_self['significant'] == True]

            if len(sig_lags) > 0:
                best_lag = sig_lags.iloc[0]
                st.success(f"✅ Significant at lag {int(best_lag['lag'])}")
                st.write(f"- Correlation: {best_lag['correlation']:.4f}")
                st.write(f"- P-value: {best_lag[P_VALUE]:.4f}")
            else:
                st.info("No significant lags found")

            st.dataframe(
                foreign_self.head(5).style.format({
                    'correlation': '{:.4f}',
                    P_VALUE: '{:.4f}'
                }),
                use_container_width=True
            )

    with col2:
        st.subheader("Self → Foreign")
        st.caption("Does self trading predict foreign trading?")

        self_foreign = leadership['self_leads_foreign']

        if not self_foreign.empty:
            sig_lags = self_foreign[self_foreign['significant'] == True]

            if len(sig_lags) > 0:
                best_lag = sig_lags.iloc[0]
                st.success(f"✅ Significant at lag {int(best_lag['lag'])}")
                st.write(f"- Correlation: {best_lag['correlation']:.4f}")
                st.write(f"- P-value: {best_lag[P_VALUE]:.4f}")
            else:
                st.info("No significant lags found")

            st.dataframe(
                self_foreign.head(5).style.format({
                    'correlation': '{:.4f}',
                    P_VALUE: '{:.4f}'
                }),
                use_container_width=True
            )

else:
    st.error(leadership['error'])

# Regime analysis
st.header("Analysis by Market Regime")

@st.cache_data(ttl=CACHE_TTL)
def run_regime_analysis(ticker, horizon):
    return conflict_analysis_by_regime(data[ticker], horizon)

regime_results = run_regime_analysis(selected_ticker, selected_horizon)

if regime_results:
    col1, col2 = st.columns(2)

    for col, (regime_name, regime_result) in zip([col1, col2], regime_results.items()):
        with col:
            st.subheader(f"{regime_name} Market")

            if 'error' not in regime_result and 'state_returns' in regime_result:
                state_returns = regime_result['state_returns']
                st.dataframe(
                    state_returns.style.format({
                        'mean': '{:.4f}',
                        'std': '{:.4f}',
                        'count': '{:.0f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info(regime_result.get('error', 'No data'))

# Interpretation
st.header("Interpretation")

st.info("""
**How to interpret these results:**

**Conflict States**:
- **Both Buy / Both Sell**: Agreement between foreign and self
- **Disagreement states**: Who wins when they conflict?

**Leadership (Granger Causality)**:
- **Significant p-value**: One group helps predict the other
- **Foreign → Self significant**: Foreign traders lead
- **Self → Foreign significant**: Self traders lead

**Market Regime**:
- Patterns may differ in bull vs bear markets
""")

st.warning("""
⚠️ **Limitations**:
- Self-trading data limited to ~3 years
- Granger causality tests correlation, not true causation
- Results may vary across different market conditions
""")
