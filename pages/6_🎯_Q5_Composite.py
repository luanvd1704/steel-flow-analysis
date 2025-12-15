"""
Q5: Composite Score Page
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.loader import merge_all_data
from analysis.composite import build_composite_score, quintile_backtest, capm_analysis
from analysis.self_trading import check_data_availability
from config.config import TICKERS, CACHE_TTL, SELF_TRADING_WARNING, QUINTILE_COLORS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q5: Composite", page_icon="🎯", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("🎯 Q5: Composite Scoring Strategy")

st.markdown("""
**Research Question**: Can we combine signals for alpha generation?

**Composite Score Formula**:
```
Score = z(Foreign Net Buy) + z(Self Net Buy) - percentile(PE/PB)
```

Where:
- **z(Foreign)**: Z-score of foreign net buying (252-day window)
- **z(Self)**: Z-score of self net buying (252-day window)
- **percentile(PE/PB)**: Average percentile of PE and PB (3-year window, inverted)

**Strategy**: Long Q5 (highest scores), Short Q1 (lowest scores)
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data()

# Sidebar
st.sidebar.header("Settings")
use_self_trading = st.sidebar.checkbox(
    "Include Self-Trading in Score",
    value=True,
    help="Uncheck to use only Foreign + Valuation (5-year backtest)"
)

selected_tickers = st.sidebar.multiselect(
    "Select Tickers",
    TICKERS,
    default=TICKERS
)

holding_period = st.sidebar.slider(
    "Holding Period (days)",
    1, 30, 5
)

# Warning
if use_self_trading:
    st.warning(SELF_TRADING_WARNING)

# Load and prepare data
with st.spinner("Building composite scores..."):
    data = load_all_data()

    scores_data = {}
    for ticker in selected_tickers:
        df = data[ticker].copy()
        df = build_composite_score(df, use_self_trading=use_self_trading)
        scores_data[ticker] = df

# Current rankings
st.header("Current Rankings")

st.markdown("Latest composite scores for all selected tickers")

current_rankings = []
for ticker, df in scores_data.items():
    if COMPOSITE_SCORE in df.columns:
        latest = df.iloc[-1]
        current_rankings.append({
            'Ticker': ticker,
            'Composite Score': latest.get(COMPOSITE_SCORE, np.nan),
            'Date': str(latest.get(DATE, ''))[:10] if DATE in latest.index else 'N/A',
            'Foreign Z': latest.get(FOREIGN_ZSCORE, np.nan),
            'Self Z': latest.get(SELF_ZSCORE, np.nan) if use_self_trading else np.nan,
            'PE %ile': latest.get(PE_PERCENTILE, np.nan),
            'PB %ile': latest.get(PB_PERCENTILE, np.nan)
        })

if current_rankings:
    rank_df = pd.DataFrame(current_rankings).sort_values('Composite Score', ascending=False)

    # Color code
    def color_score(val):
        if pd.isna(val):
            return ''
        return 'background-color: lightgreen' if val > 0 else 'background-color: lightcoral'

    st.dataframe(
        rank_df.style.format({
            'Composite Score': '{:.2f}',
            'Foreign Z': '{:.2f}',
            'Self Z': '{:.2f}',
            'PE %ile': '{:.1f}',
            'PB %ile': '{:.1f}'
        }).applymap(color_score, subset=['Composite Score']),
        use_container_width=True
    )

# Backtest for each ticker
st.header("Quintile Backtest Results")

for ticker in selected_tickers:
    with st.expander(f"📊 {ticker} - Backtest Results"):
        df = scores_data[ticker]

        # Check data availability
        if use_self_trading:
            avail = check_data_availability(df)
            if not avail['available']:
                st.warning(f"⚠️ {avail['reason']}")
                continue

        # Run backtest
        backtest = quintile_backtest(df, horizon=holding_period)

        if 'error' in backtest:
            st.error(backtest['error'])
            continue

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Strategy Return (Q5-Q1)", f"{backtest['strategy_returns_mean']:.2%}")

        with col2:
            st.metric("Volatility", f"{backtest['strategy_returns_std']:.2%}")

        with col3:
            st.metric("Sharpe Ratio", f"{backtest['sharpe_ratio']:.2f}")

        with col4:
            st.metric("Sample Size", f"{backtest['sample_size']:,}")

        # Quintile returns chart
        quintile_returns = backtest['quintile_returns']

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=quintile_returns[QUINTILE],
            y=quintile_returns['mean'],
            marker_color=QUINTILE_COLORS,
            text=quintile_returns['mean'].apply(lambda x: f"{x:.2%}"),
            textposition='outside'
        ))

        fig.update_layout(
            title=f"{ticker} - Returns by Composite Score Quintile (Hold {holding_period}d)",
            xaxis_title="Quintile",
            yaxis_title="Mean Return",
            yaxis_tickformat='.2%',
            height=400,
            template='plotly_white'
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig, use_container_width=True)

        # Detailed stats
        st.dataframe(
            quintile_returns.style.format({
                'mean': '{:.4f}',
                'std': '{:.4f}',
                'count': '{:.0f}'
            }),
            use_container_width=True
        )

        # CAPM analysis
        if STOCK_RETURN in df.columns and MARKET_RETURN in df.columns:
            # Get Q5-Q1 returns
            df_with_quintiles = df.copy()
            from utils.helpers import create_quintiles
            df_with_quintiles[QUINTILE] = create_quintiles(df_with_quintiles[COMPOSITE_SCORE])

            fwd_ret_col = f'fwd_return_{holding_period}d'
            if fwd_ret_col in df_with_quintiles.columns:
                q5_mask = df_with_quintiles[QUINTILE] == 'Q5'
                strategy_rets = df_with_quintiles[q5_mask][fwd_ret_col].dropna()
                market_rets = df_with_quintiles[q5_mask][MARKET_RETURN].shift(-holding_period).dropna()

                # Align
                common_idx = strategy_rets.index.intersection(market_rets.index)
                if len(common_idx) > 10:
                    capm = capm_analysis(strategy_rets[common_idx], market_rets[common_idx])

                    if 'error' not in capm:
                        st.subheader("CAPM Analysis (Q5 vs Market)")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Alpha (annual)", f"{capm[ALPHA]:.2%}")

                        with col2:
                            st.metric("Beta", f"{capm[BETA]:.2f}")

                        with col3:
                            st.metric("Mean Return (annual)", f"{capm['mean_return']:.2%}")

# Aggregate performance
st.header("Aggregate Performance Summary")

st.markdown(f"""
**Settings**:
- Include Self-Trading: {'Yes (3-year backtest)' if use_self_trading else 'No (5-year backtest)'}
- Holding Period: {holding_period} days
- Tickers: {', '.join(selected_tickers)}
""")

agg_data = []
for ticker in selected_tickers:
    df = scores_data[ticker]
    backtest = quintile_backtest(df, horizon=holding_period)

    if 'error' not in backtest:
        agg_data.append({
            'Ticker': ticker,
            'Mean Return (Q5-Q1)': backtest['strategy_returns_mean'],
            'Sharpe Ratio': backtest['sharpe_ratio'],
            'Sample Size': backtest['sample_size']
        })

if agg_data:
    agg_df = pd.DataFrame(agg_data)

    st.dataframe(
        agg_df.style.format({
            'Mean Return (Q5-Q1)': '{:.2%}',
            'Sharpe Ratio': '{:.2f}',
            'Sample Size': '{:.0f}'
        }),
        use_container_width=True
    )

    # Average metrics
    col1, col2 = st.columns(2)

    with col1:
        avg_return = agg_df['Mean Return (Q5-Q1)'].mean()
        st.metric("Average Return Across Tickers", f"{avg_return:.2%}")

    with col2:
        avg_sharpe = agg_df['Sharpe Ratio'].mean()
        st.metric("Average Sharpe Ratio", f"{avg_sharpe:.2f}")

# Interpretation
st.header("Interpretation")

st.info("""
**How to use this strategy**:

1. **High Scores (Q5)**:
   - Strong foreign/self buying
   - Low valuation percentiles (cheap)
   - → Long candidates

2. **Low Scores (Q1)**:
   - Weak/negative flows
   - High valuation percentiles (expensive)
   - → Short candidates or avoid

3. **Performance Metrics**:
   - **Positive Mean Return**: Strategy works
   - **Sharpe > 1**: Good risk-adjusted performance
   - **Positive Alpha**: Beats market after risk adjustment

**Without Self-Trading**: Longer backtest (5 years) but fewer signals
**With Self-Trading**: Shorter backtest (3 years) but more complete signal
""")

st.warning("""
⚠️ **Critical Disclaimers**:

1. **Past Performance ≠ Future Results**: Historical patterns may not continue
2. **Transaction Costs**: Not included in backtest (slippage, commissions, impact)
3. **Limited Data**: Especially self-trading (3 years only)
4. **Market Regime**: Results may vary in different market conditions
5. **Not Investment Advice**: This is research/educational only

**DO NOT use this as sole basis for investment decisions!**
""")
