"""
Q3: Trang Xung Đột Nước Ngoài vs Tự Doanh
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
from config import config_steel
from config.config import CACHE_TTL, SELF_TRADING_WARNING
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q3: Xung Đột", page_icon="⚔️", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("⚔️ Q3: Xung Đột Nước Ngoài vs Tự Doanh")

st.markdown("""
**Câu Hỏi Nghiên Cứu**: Ai dẫn dắt khi dòng tiền nước ngoài và tự doanh bất đồng?

Phân tích này xem xét:
1. **Trạng Thái Xung Đột**: Lợi nhuận khi nhà đầu tư nước ngoài và tự doanh bất đồng
2. **Vai Trò Dẫn Dắt**: Ai dự đoán ai bằng nhân quả Granger
3. **Chế Độ Thị Trường**: Các mô hình có khác nhau trong thị trường tăng/giảm không?
""")

st.warning(SELF_TRADING_WARNING)

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data(config_steel)

# Sidebar
st.sidebar.header("Bộ Lọc")
selected_ticker = st.sidebar.selectbox("Chọn Mã Cổ Phiếu", TICKERS)
selected_horizon = st.sidebar.selectbox("Kỳ Hạn Lợi Nhuận", [5, 10], format_func=lambda x: f"T+{x}")

# Load data
with st.spinner("Đang tải dữ liệu..."):
    data = load_all_data()
    df = data[selected_ticker]

    # Check self-trading data availability
    availability = check_data_availability(df)

if not availability['available']:
    st.error(f"❌ {availability['reason']}")
    st.stop()

# Data info
st.info(f"📊 Dữ liệu tự doanh: {availability['data_points']:,} điểm | Phủ sóng: {availability['coverage']:.1%}")

# Conflict state analysis
st.header(f"Phân Tích Trạng Thái Xung Đột - T+{selected_horizon}")

@st.cache_data(ttl=CACHE_TTL)
def run_conflict_analysis(ticker):
    return analyze_conflict_returns(data[ticker])

results = run_conflict_analysis(selected_ticker)

horizon_key = f'T+{selected_horizon}'
if horizon_key in results and 'error' not in results[horizon_key]:
    result = results[horizon_key]
    state_returns = result['state_returns']

    # Conflict matrix heatmap
    st.subheader("Lợi Nhuận Theo Trạng Thái Xung Đột")

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
        title=f"{selected_ticker} - Lợi Nhuận Theo Trạng Thái Xung Đột (T+{selected_horizon})",
        xaxis_title="Trạng Thái Xung Đột",
        yaxis_title="Lợi Nhuận Trung Bình",
        yaxis_tickformat='.2%',
        height=500,
        template='plotly_white'
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.subheader("Thống Kê Chi Tiết")
    st.dataframe(
        state_returns.style.format({
            'mean': '{:.4f}',
            'std': '{:.4f}',
            'count': '{:.0f}'
        }),
        use_container_width=True
    )

    # Key insights
    st.subheader("Những Phát Hiện Chính")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Trạng Thái Xung Đột (Bất đồng)**:")
        fb_ss = matrix_data.get(FOREIGN_BUY_SELF_SELL, 0)
        fs_sb = matrix_data.get(FOREIGN_SELL_SELF_BUY, 0)

        st.write(f"- NN Mua, Tự Doanh Bán: {fb_ss:.2%}")
        st.write(f"- NN Bán, Tự Doanh Mua: {fs_sb:.2%}")

        if fb_ss > fs_sb:
            st.success("✅ Tín hiệu mua của NN mạnh hơn khi bất đồng")
        else:
            st.info("📊 Tín hiệu mua của tự doanh mạnh hơn khi bất đồng")

    with col2:
        st.write("**Trạng Thái Thống Nhất**:")
        both_buy = matrix_data.get(BOTH_BUY, 0)
        both_sell = matrix_data.get(BOTH_SELL, 0)

        st.write(f"- Cả Hai Mua: {both_buy:.2%}")
        st.write(f"- Cả Hai Bán: {both_sell:.2%}")

        if both_buy > 0:
            st.success("✅ Lợi nhuận dương khi cả hai mua")
        if both_sell < 0:
            st.info("📉 Lợi nhuận âm khi cả hai bán")

else:
    st.error("Không thể thực hiện phân tích xung đột")

# Leadership analysis
st.header("Phân Tích Vai Trò Dẫn Dắt (Nhân Quả Granger)")

st.markdown("""
Kiểm định này xem xét liệu giao dịch của một nhóm có giúp dự đoán giao dịch của nhóm kia hay không.
""")

@st.cache_data(ttl=CACHE_TTL)
def run_leadership_analysis(ticker):
    return identify_leader(data[ticker])

leadership = run_leadership_analysis(selected_ticker)

if 'error' not in leadership:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("NN → Tự Doanh")
        st.caption("NN có dự đoán được tự doanh không?")

        foreign_self = leadership['foreign_leads_self']

        if not foreign_self.empty:
            # Find most significant lag
            sig_lags = foreign_self[foreign_self['significant'] == True]

            if len(sig_lags) > 0:
                best_lag = sig_lags.iloc[0]
                st.success(f"✅ Có ý nghĩa tại độ trễ {int(best_lag['lag'])}")
                st.write(f"- Tương quan: {best_lag['correlation']:.4f}")
                st.write(f"- P-value: {best_lag[P_VALUE]:.4f}")
            else:
                st.info("Không tìm thấy độ trễ có ý nghĩa")

            st.dataframe(
                foreign_self.head(5).style.format({
                    'correlation': '{:.4f}',
                    P_VALUE: '{:.4f}'
                }),
                use_container_width=True
            )

    with col2:
        st.subheader("Tự Doanh → NN")
        st.caption("Tự doanh có dự đoán được NN không?")

        self_foreign = leadership['self_leads_foreign']

        if not self_foreign.empty:
            sig_lags = self_foreign[self_foreign['significant'] == True]

            if len(sig_lags) > 0:
                best_lag = sig_lags.iloc[0]
                st.success(f"✅ Có ý nghĩa tại độ trễ {int(best_lag['lag'])}")
                st.write(f"- Tương quan: {best_lag['correlation']:.4f}")
                st.write(f"- P-value: {best_lag[P_VALUE]:.4f}")
            else:
                st.info("Không tìm thấy độ trễ có ý nghĩa")

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
st.header("Phân Tích Theo Chế Độ Thị Trường")

@st.cache_data(ttl=CACHE_TTL)
def run_regime_analysis(ticker, horizon):
    return conflict_analysis_by_regime(data[ticker], horizon)

regime_results = run_regime_analysis(selected_ticker, selected_horizon)

if regime_results:
    col1, col2 = st.columns(2)

    for col, (regime_name, regime_result) in zip([col1, col2], regime_results.items()):
        with col:
            regime_vn = "Tăng" if "Bull" in regime_name else "Giảm"
            st.subheader(f"Thị Trường {regime_vn}")

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
                st.info(regime_result.get('error', 'Không có dữ liệu'))

# Interpretation
st.header("Giải Thích")

st.info("""
**Cách diễn giải kết quả:**

**Trạng Thái Xung Đột**:
- **Cả Hai Mua / Cả Hai Bán**: Thống nhất giữa NN và tự doanh
- **Trạng thái bất đồng**: Ai thắng khi họ xung đột?

**Vai Trò Dẫn Dắt (Nhân Quả Granger)**:
- **P-value có ý nghĩa**: Một nhóm giúp dự đoán nhóm kia
- **NN → Tự Doanh có ý nghĩa**: NN dẫn dắt
- **Tự Doanh → NN có ý nghĩa**: Tự doanh dẫn dắt

**Chế Độ Thị Trường**:
- Các mô hình có thể khác nhau trong thị trường tăng/giảm
""")

st.warning("""
⚠️ **Giới Hạn**:
- Dữ liệu tự doanh giới hạn ~3 năm
- Nhân quả Granger kiểm tra tương quan, không phải nhân quả thực sự
- Kết quả có thể khác nhau ở các điều kiện thị trường khác nhau
""")
