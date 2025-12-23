"""
Q5: Trang Điểm Tổng Hợp
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
from config import config_steel
from config.config import CACHE_TTL, SELF_TRADING_WARNING, QUINTILE_COLORS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q5: Điểm Tổng Hợp", page_icon="🎯", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("🎯 Q5: Chiến Lược Điểm Tổng Hợp")

st.markdown("""
**Câu Hỏi Nghiên Cứu**: Chúng ta có thể kết hợp các tín hiệu để tạo alpha không?

**Công Thức Điểm Tổng Hợp**:
```
Điểm = z(Mua Ròng NN) + z(Mua Ròng Tự Doanh) - phân_vị(PE/PB)
```

Trong đó:
- **z(NN)**: Z-score của mua ròng nước ngoài (cửa sổ 252 ngày)
- **z(Tự Doanh)**: Z-score của mua ròng tự doanh (cửa sổ 252 ngày)
- **phân_vị(PE/PB)**: Phân vị trung bình của PE và PB (cửa sổ 3 năm, đảo ngược)

**Chiến Lược**: Long Q5 (điểm cao nhất), Short Q1 (điểm thấp nhất)
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data(config_steel)

# Sidebar
st.sidebar.header("Cài Đặt")
use_self_trading = st.sidebar.checkbox(
    "Bao Gồm Tự Doanh Trong Điểm",
    value=True,
    help="Bỏ chọn để chỉ dùng NN + Định Giá (backtest 5 năm)"
)

selected_tickers = st.sidebar.multiselect(
    "Chọn Mã Cổ Phiếu",
    TICKERS,
    default=TICKERS
)

holding_period = st.sidebar.slider(
    "Kỳ Hạn Nắm Giữ (ngày)",
    1, 30, 5
)

# Warning
if use_self_trading:
    st.warning(SELF_TRADING_WARNING)

# Load and prepare data
with st.spinner("Đang xây dựng điểm tổng hợp..."):
    data = load_all_data()

    scores_data = {}
    for ticker in selected_tickers:
        df = data[ticker].copy()
        df = build_composite_score(df, use_self_trading=use_self_trading)
        scores_data[ticker] = df

# Current rankings
st.header("Xếp Hạng Hiện Tại")

st.markdown("Điểm tổng hợp mới nhất cho tất cả các mã đã chọn")

current_rankings = []
for ticker, df in scores_data.items():
    if COMPOSITE_SCORE in df.columns:
        latest = df.iloc[-1]
        current_rankings.append({
            'Mã': ticker,
            'Điểm Tổng Hợp': latest.get(COMPOSITE_SCORE, np.nan),
            'Ngày': str(latest.get(DATE, ''))[:10] if DATE in latest.index else 'N/A',
            'Z NN': latest.get(FOREIGN_ZSCORE, np.nan),
            'Z Tự Doanh': latest.get(SELF_ZSCORE, np.nan) if use_self_trading else np.nan,
            'PE %ile': latest.get(PE_PERCENTILE, np.nan),
            'PB %ile': latest.get(PB_PERCENTILE, np.nan)
        })

if current_rankings:
    rank_df = pd.DataFrame(current_rankings).sort_values('Điểm Tổng Hợp', ascending=False)

    # Color code
    def color_score(val):
        if pd.isna(val):
            return ''
        return 'background-color: lightgreen' if val > 0 else 'background-color: lightcoral'

    st.dataframe(
        rank_df.style.format({
            'Điểm Tổng Hợp': '{:.2f}',
            'Z NN': '{:.2f}',
            'Z Tự Doanh': '{:.2f}',
            'PE %ile': '{:.1f}',
            'PB %ile': '{:.1f}'
        }).applymap(color_score, subset=['Điểm Tổng Hợp']),
        use_container_width=True
    )

# Backtest for each ticker
st.header("Kết Quả Backtest Theo Nhóm")

for ticker in selected_tickers:
    with st.expander(f"📊 {ticker} - Kết Quả Backtest"):
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
            st.metric("LN Chiến Lược (Q5-Q1)", f"{backtest['strategy_returns_mean']:.2%}")

        with col2:
            st.metric("Độ Biến Động", f"{backtest['strategy_returns_std']:.2%}")

        with col3:
            st.metric("Tỷ Số Sharpe", f"{backtest['sharpe_ratio']:.2f}")

        with col4:
            st.metric("Kích Thước Mẫu", f"{backtest['sample_size']:,}")

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
            title=f"{ticker} - LN Theo Nhóm Điểm Tổng Hợp (Nắm giữ {holding_period} ngày)",
            xaxis_title="Nhóm",
            yaxis_title="LN Trung Bình",
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
                        st.subheader("Phân Tích CAPM (Q5 vs Thị Trường)")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Alpha (hàng năm)", f"{capm[ALPHA]:.2%}")

                        with col2:
                            st.metric("Beta", f"{capm[BETA]:.2f}")

                        with col3:
                            st.metric("LN TB (hàng năm)", f"{capm['mean_return']:.2%}")

# Aggregate performance
st.header("Tóm Tắt Hiệu Suất Tổng Hợp")

st.markdown(f"""
**Cài Đặt**:
- Bao Gồm Tự Doanh: {'Có (backtest 3 năm)' if use_self_trading else 'Không (backtest 5 năm)'}
- Kỳ Hạn Nắm Giữ: {holding_period} ngày
- Mã Cổ Phiếu: {', '.join(selected_tickers)}
""")

agg_data = []
for ticker in selected_tickers:
    df = scores_data[ticker]
    backtest = quintile_backtest(df, horizon=holding_period)

    if 'error' not in backtest:
        agg_data.append({
            'Mã': ticker,
            'LN TB (Q5-Q1)': backtest['strategy_returns_mean'],
            'Tỷ Số Sharpe': backtest['sharpe_ratio'],
            'Kích Thước Mẫu': backtest['sample_size']
        })

if agg_data:
    agg_df = pd.DataFrame(agg_data)

    st.dataframe(
        agg_df.style.format({
            'LN TB (Q5-Q1)': '{:.2%}',
            'Tỷ Số Sharpe': '{:.2f}',
            'Kích Thước Mẫu': '{:.0f}'
        }),
        use_container_width=True
    )

    # Average metrics
    col1, col2 = st.columns(2)

    with col1:
        avg_return = agg_df['LN TB (Q5-Q1)'].mean()
        st.metric("LN TB Qua Các Mã", f"{avg_return:.2%}")

    with col2:
        avg_sharpe = agg_df['Tỷ Số Sharpe'].mean()
        st.metric("Tỷ Số Sharpe TB", f"{avg_sharpe:.2f}")

# Interpretation
st.header("Giải Thích")

st.info("""
**Cách sử dụng chiến lược này**:

1. **Điểm Cao (Q5)**:
   - Mua ròng mạnh từ NN/tự doanh
   - Phân vị định giá thấp (rẻ)
   - → Ứng viên Long

2. **Điểm Thấp (Q1)**:
   - Dòng tiền yếu/âm
   - Phân vị định giá cao (đắt)
   - → Ứng viên Short hoặc tránh

3. **Chỉ Số Hiệu Suất**:
   - **LN TB Dương**: Chiến lược hoạt động
   - **Sharpe > 1**: Hiệu suất điều chỉnh rủi ro tốt
   - **Alpha Dương**: Vượt thị trường sau khi điều chỉnh rủi ro

**Không Có Tự Doanh**: Backtest dài hơn (5 năm) nhưng ít tín hiệu hơn
**Có Tự Doanh**: Backtest ngắn hơn (3 năm) nhưng tín hiệu đầy đủ hơn
""")

st.warning("""
⚠️ **Tuyên Bố Miễn Trừ Quan Trọng**:

1. **Hiệu Suất Quá Khứ ≠ Kết Quả Tương Lai**: Các mô hình lịch sử có thể không tiếp tục
2. **Chi Phí Giao Dịch**: Không bao gồm trong backtest (trượt giá, hoa hồng, tác động)
3. **Dữ Liệu Giới Hạn**: Đặc biệt tự doanh (chỉ 3 năm)
4. **Chế Độ Thị Trường**: Kết quả có thể khác nhau ở các điều kiện thị trường khác nhau
5. **Không Phải Lời Khuyên Đầu Tư**: Đây chỉ là nghiên cứu/giáo dục

**ĐỪNG sử dụng đây làm cơ sở duy nhất cho quyết định đầu tư!**
""")
