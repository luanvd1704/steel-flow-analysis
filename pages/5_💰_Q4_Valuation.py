"""
Q4: Valuation Analysis Page
"""
import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data
from analysis.valuation import (
    calculate_valuation_percentiles, analyze_percentile_returns,
    valuation_summary, compare_valuation_metrics, predict_forward_return,
    identify_valuation_zones
)
from visualization.charts_q4 import (
    create_percentile_timeseries, create_decile_returns_chart,
    create_valuation_gauge, create_zone_comparison_chart
)
from config.config import TICKERS, CACHE_TTL
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q4: Valuation", page_icon="💰", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("💰 Q4: Valuation Percentile Analysis")

st.markdown("""
**Research Question**: Do cheap valuations (low PE/PB percentiles) predict higher forward returns?

This analysis examines whether buying stocks when they're historically cheap leads to better returns.
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

@st.cache_data(ttl=CACHE_TTL)
def prepare_valuation_data(ticker):
    data = load_all_data()
    df = data[ticker].copy()
    df = calculate_valuation_percentiles(df)
    df = identify_valuation_zones(df)
    return df

# Sidebar
st.sidebar.header("Filters")
selected_ticker = st.sidebar.selectbox("Select Ticker", TICKERS)
selected_metric = st.sidebar.selectbox("Valuation Metric", [PE, PB, PCFS])
forward_horizon = st.sidebar.slider("Forward Return Horizon (days)", 1, 60, 30)

# Load data
with st.spinner(f"Loading {selected_ticker} data..."):
    df = prepare_valuation_data(selected_ticker)

# Current valuation summary
st.header(f"Current Valuation - {selected_ticker}")

summary = valuation_summary(df, metrics=[PE, PB, PCFS])

if 'date' in summary:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Date", str(summary['date'])[:10] if summary['date'] else "N/A")

    metrics_display = [PE, PB, PCFS]
    cols = [col2, col3, col4]

    for metric, col in zip(metrics_display, cols):
        with col:
            val = summary['valuations'].get(metric)
            pct = summary['percentiles'].get(metric)
            zone = summary['zones'].get(metric, 'N/A')

            if val and pct:
                st.metric(
                    f"{metric.upper()}",
                    f"{val:.2f}",
                    delta=f"{pct:.0f}% ile | {zone}"
                )

# Gauge chart
st.header(f"{selected_metric.upper()} Percentile Position")

percentile_col = f'{selected_metric}_percentile'
if percentile_col in df.columns:
    current_pct = df[percentile_col].iloc[-1]

    if not pd.isna(current_pct):
        fig_gauge = create_valuation_gauge(current_pct, selected_metric)
        st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.warning("No current percentile data available")

# Historical percentile
st.header(f"{selected_metric.upper()} Historical Percentile")

fig_timeseries = create_percentile_timeseries(df, selected_metric, selected_ticker)
st.plotly_chart(fig_timeseries, use_container_width=True)

# Decile analysis
st.header(f"Forward Returns by {selected_metric.upper()} Percentile")

with st.spinner("Analyzing decile returns..."):
    analysis = analyze_percentile_returns(df, percentile_col, forward_horizon)

if 'error' not in analysis:
    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Cheap Zone Return (0-20%)",
            f"{analysis['cheap_zone_return']:.2%}",
            delta=None
        )

    with col2:
        st.metric(
            "Expensive Zone Return (80-100%)",
            f"{analysis['expensive_zone_return']:.2%}",
            delta=None
        )

    with col3:
        spread = analysis['cheap_expensive_spread']
        st.metric(
            "Cheap - Expensive Spread",
            f"{spread:.2%}",
            delta="Positive is good" if spread > 0 else "Negative is bad"
        )

    # Decile bar chart
    fig_decile = create_decile_returns_chart(
        analysis['decile_stats'],
        selected_metric,
        selected_ticker
    )
    st.plotly_chart(fig_decile, use_container_width=True)

    # Zone comparison
    col1, col2 = st.columns(2)

    with col1:
        fig_zones = create_zone_comparison_chart(
            analysis['cheap_zone_return'],
            analysis['expensive_zone_return'],
            selected_metric
        )
        st.plotly_chart(fig_zones, use_container_width=True)

    with col2:
        st.subheader("Statistical Tests")

        st.write("**Monotonicity Test** (Expecting decreasing trend)")
        mono = analysis['monotonicity']
        st.write(f"- Spearman Correlation: {mono['correlation']:.4f}")
        st.write(f"- P-value: {mono[P_VALUE]:.4f}")
        st.write(f"- Is Monotonic: {'✅' if mono['is_monotonic'] else '❌'}")

        st.write("\n**ANOVA Test** (Different returns across deciles?)")
        anova = analysis['anova']
        st.write(f"- F-statistic: {anova.get('f_stat', 'N/A'):.2f}")
        st.write(f"- P-value: {anova.get(P_VALUE, 'N/A'):.4f}")
        st.write(f"- Significant: {'✅' if anova.get('significant') else '❌'}")

    # Detailed decile table
    st.subheader("Detailed Decile Statistics")
    st.dataframe(
        analysis['decile_stats'].style.format({
            'mean': '{:.4f}',
            'std': '{:.4f}',
            'median': '{:.4f}',
            'count': '{:.0f}'
        }),
        use_container_width=True
    )

else:
    st.error(analysis['error'])

# Prediction tool
st.header("Return Prediction Tool")

st.markdown("""
Enter a percentile value to see expected forward return based on historical patterns.
""")

input_percentile = st.slider(
    f"Current {selected_metric.upper()} Percentile",
    0.0, 100.0,
    summary['percentiles'].get(selected_metric, 50.0) if summary['percentiles'].get(selected_metric) else 50.0
)

if st.button("Predict Forward Return"):
    prediction = predict_forward_return(df, input_percentile, percentile_col, forward_horizon)

    if 'error' not in prediction:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Expected Return", f"{prediction['expected_return']:.2%}")

        with col2:
            st.metric("Confidence Interval (95%)",
                     f"{prediction['confidence_low']:.2%} to {prediction['confidence_high']:.2%}")

        with col3:
            st.metric("Sample Size", f"{int(prediction['sample_size'])}")

        st.info(f"Based on percentile: {prediction['current_percentile']:.1f}% → Decile {prediction['decile']}")
    else:
        st.error(prediction['error'])

# Metric comparison
st.header("Compare Valuation Metrics")

comparison = compare_valuation_metrics(df, forward_horizon)

if comparison:
    comp_data = []
    for metric, results in comparison.items():
        comp_data.append({
            'Metric': metric.upper(),
            'Monotonicity Corr': results['monotonicity_correlation'],
            'Monotonicity P-val': results['monotonicity_pvalue'],
            'Cheap-Exp Spread': results['cheap_expensive_spread'],
            'ANOVA P-val': results['anova_pvalue']
        })

    comp_df = pd.DataFrame(comp_data)

    st.dataframe(
        comp_df.style.format({
            'Monotonicity Corr': '{:.4f}',
            'Monotonicity P-val': '{:.4f}',
            'Cheap-Exp Spread': '{:.2%}',
            'ANOVA P-val': '{:.4f}'
        }),
        use_container_width=True
    )

    st.caption("""
    **Interpretation**:
    - **Negative Monotonicity Correlation**: Lower percentile → Higher returns (good)
    - **Positive Cheap-Exp Spread**: Cheap outperforms expensive (good)
    - **Low P-values**: Statistically significant patterns
    """)

# Interpretation
st.header("Interpretation")

st.info("""
**How to use this analysis:**

- **Cheap Zone (0-20% percentile)**: Historically low valuation, potentially good entry point
- **Fair Zone (40-60% percentile)**: Average valuation
- **Expensive Zone (80-100% percentile)**: Historically high valuation, be cautious

**Positive Cheap-Expensive Spread** suggests a value effect: buying cheap works!

**Monotonic decreasing trend** in decile returns confirms the pattern.
""")

st.warning("""
⚠️ **Important Notes**:
- Valuation percentiles use 3-year rolling window (756 trading days)
- Past relationships may not hold in the future
- Consider other factors beyond valuation
- This is research, not investment advice
""")
