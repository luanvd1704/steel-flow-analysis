"""
Q2: Trang Phân Tích Tự Doanh
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
from config import config_steel
from config.config import CACHE_TTL, SELF_TRADING_WARNING, TERCILE_LABELS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

st.set_page_config(page_title="Q2: Tự Doanh", page_icon="💼", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("💼 Q2: Phân Tích Tín Hiệu Tự Doanh")

st.markdown("""
**Câu Hỏi Nghiên Cứu**: Dòng tiền tự doanh có sinh lời không? Phương pháp chuẩn hóa nào hiệu quả hơn?

Phân tích này so sánh hai phương pháp chuẩn hóa:
- **ADV20**: Mua Ròng / Khối lượng trung bình 20 ngày
- **GTGD**: Mua Ròng / (Giá Trị Mua + Giá Trị Bán)
""")

# Warning banner
st.warning(SELF_TRADING_WARNING)

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data(config_steel)

# Sidebar
st.sidebar.header("Bộ Lọc")
selected_ticker = st.sidebar.selectbox("Chọn Mã Cổ Phiếu", TICKERS)
selected_horizon = st.sidebar.selectbox(
    "Kỳ Hạn Lợi Nhuận",
    [1, 3, 5, 10],
    index=2,
    format_func=lambda x: f"T+{x} ngày"
)

# Load and check data
with st.spinner("Đang tải dữ liệu..."):
    data = load_all_data()
    df = data[selected_ticker]

    availability = check_data_availability(df)

# Check if data is available
if not availability['available']:
    st.error(f"❌ {availability['reason']}")
    st.stop()

# Show data availability
st.header(f"Tình Trạng Dữ Liệu - {selected_ticker}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Điểm Dữ Liệu", f"{availability['data_points']:,}")

with col2:
    st.metric("Phủ Sóng", f"{availability['coverage']:.1%}")

with col3:
    st.metric("Ngày Bắt Đầu", str(availability['start_date'])[:10] if availability['start_date'] else "N/A")

with col4:
    st.metric("Ngày Kết Thúc", str(availability['end_date'])[:10] if availability['end_date'] else "N/A")

# Run analysis
@st.cache_data(ttl=CACHE_TTL)
def run_comparison(ticker):
    return compare_normalization_methods(data[ticker])

with st.spinner(f"Đang phân tích {selected_ticker}..."):
    comparison = run_comparison(selected_ticker)
    best_method = get_best_normalization_method(comparison)

# Method comparison summary
st.header("So Sánh Phương Pháp Chuẩn Hóa")

st.info(f"**Phương Pháp Đề Xuất**: {best_method} (dựa trên IC trung bình qua các kỳ hạn)")

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
                        'Phương Pháp': method,
                        'Kỳ Hạn': horizon_key,
                        'IC': result['ic']['ic'],
                        'IC P-value': result['ic'][P_VALUE],
                        'Kích Thước Mẫu': result['sample_size'],
                        'Đơn Điệu': '✅' if result['monotonicity'] else '❌'
                    })

if comp_data:
    comp_df = pd.DataFrame(comp_data)

    st.dataframe(
        comp_df.style.format({
            'IC': '{:.4f}',
            'IC P-value': '{:.4f}',
            'Kích Thước Mẫu': '{:.0f}'
        }),
        use_container_width=True
    )

# Detailed analysis for selected horizon
st.header(f"Phân Tích Chi Tiết - T+{selected_horizon}")

tabs = st.tabs(['Phương Pháp ADV20', 'Phương Pháp GTGD'])

for idx, method in enumerate(['ADV20', 'GTGD']):
    with tabs[idx]:
        horizon_key = f'T+{selected_horizon}'

        if horizon_key in comparison[method]:
            result = comparison[method][horizon_key]

            if 'error' in result:
                st.error(result['error'])
                continue

            # Tercile statistics
            st.subheader(f"Lợi Nhuận Theo Nhóm Ba Tín Hiệu {method}")

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
                title=f"{selected_ticker} - Lợi Nhuận Theo Tín Hiệu {method} (T+{selected_horizon})",
                xaxis_title="Nhóm Ba",
                yaxis_title="Lợi Nhuận Trung Bình",
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
                    "Hệ Số Thông Tin",
                    f"{ic_val:.4f}",
                    delta="Có ý nghĩa" if result['ic']['significant'] else "Không có ý nghĩa"
                )

            with col2:
                monotonic = result['monotonicity']
                st.metric(
                    "Xu Hướng Đơn Điệu",
                    "✅ Có" if monotonic else "❌ Không"
                )

            with col3:
                st.metric(
                    "Kích Thước Mẫu",
                    f"{result['sample_size']:,}"
                )

            # Detailed table
            st.subheader("Thống Kê Nhóm Ba")

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
            st.subheader("Kiểm Định Thống Kê")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Kiểm Định Hệ Số Thông Tin**")
                st.write(f"- IC: {result['ic']['ic']:.4f}")
                st.write(f"- P-value: {result['ic'][P_VALUE]:.4f}")
                st.write(f"- Có ý nghĩa: {'✅' if result['ic']['significant'] else '❌'}")
                st.write(f"- Mẫu: {result['ic']['n']}")

            with col2:
                st.write("**Kiểm Định ANOVA**")
                anova = result['anova']
                st.write(f"- F-statistic: {anova.get('f_stat', 'N/A'):.2f}")
                st.write(f"- P-value: {anova.get(P_VALUE, 'N/A'):.4f}")
                st.write(f"- Có ý nghĩa: {'✅' if anova.get('significant') else '❌'}")

# Interpretation
st.header("Giải Thích")

st.info(f"""
**Phát Hiện Chính Cho {selected_ticker}**:

- **Phương Pháp Đề Xuất**: {best_method}
- **Giai Đoạn Dữ Liệu**: {availability.get('start_date', 'N/A')} đến {availability.get('end_date', 'N/A')} (~{availability['data_points']} điểm)

**Cách diễn giải**:
- **IC Dương**: Tín hiệu tự doanh dự đoán lợi nhuận tương lai
- **Nhóm Ba Đơn Điệu**: T1 (Bán) < T2 (Trung lập) < T3 (Mua) → Tín hiệu hoạt động!
- **Kiểm định có ý nghĩa (p < 0.05)**: Mô hình đáng tin cậy

**ADV20 vs GTGD**:
- **ADV20**: Chuẩn hóa theo khối lượng giao dịch
- **GTGD**: Chuẩn hóa theo tổng giá trị giao dịch (có thể ổn định hơn)
""")

st.warning("""
⚠️ **Giới Hạn Quan Trọng**:

1. **Lịch Sử Giới Hạn**: Dữ liệu tự doanh chỉ có từ 2022-11 (~3 năm)
2. **Sức Mạnh Thống Kê**: Lịch sử ngắn hơn = mô hình kém tin cậy hơn
3. **Chế Độ Thị Trường**: Kết quả có thể khác nhau ở các điều kiện thị trường khác nhau
4. **Không Phải Lời Khuyên Đầu Tư**: Chỉ cho mục đích nghiên cứu

Dữ liệu giới hạn có nghĩa là kết quả nên được diễn giải với sự thận trọng cao hơn!
""")
