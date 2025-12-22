"""
Q4: Trang Phân Tích Định Giá
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
from config import config_banking
from config.config import CACHE_TTL
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

# All 17 banking tickers (Valuation analysis doesn't require foreign trading data)
BANKING_TICKERS = [
    'VCB', 'TCB', 'MBB', 'ACB', 'VPB', 'BID', 'CTG',
    'STB', 'HDB', 'TPB', 'VIB', 'SSB', 'SHB', 'MSB',
    'LPB', 'OCB', 'EIB'
]

st.set_page_config(page_title="Q4: Định Giá", page_icon="💰", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("💰 Q4: Phân Tích Phân Vị Định Giá")

st.markdown("""
**Câu Hỏi Nghiên Cứu**: Định giá rẻ (phân vị PE/PB thấp) có dự đoán lợi nhuận cao hơn không?

Phân tích này xem xét liệu mua cổ phiếu khi chúng rẻ về mặt lịch sử có dẫn đến lợi nhuận tốt hơn hay không.
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data(config_banking)

@st.cache_data(ttl=CACHE_TTL)
def prepare_valuation_data(ticker):
    data = load_all_data()
    df = data[ticker].copy()
    df = calculate_valuation_percentiles(df)
    df = identify_valuation_zones(df)
    return df

# Sidebar
st.sidebar.header("Bộ Lọc")
selected_ticker = st.sidebar.selectbox("Chọn Mã Cổ Phiếu", BANKING_TICKERS)
selected_metric = st.sidebar.selectbox("Chỉ Số Định Giá", [PE, PB, PCFS])
forward_horizon = st.sidebar.slider("Kỳ Hạn Lợi Nhuận (ngày)", 1, 60, 30)

# Load data
with st.spinner(f"Đang tải dữ liệu {selected_ticker}..."):
    df = prepare_valuation_data(selected_ticker)

# Current valuation summary
st.header(f"Định Giá Hiện Tại - {selected_ticker}")

summary = valuation_summary(df, metrics=[PE, PB, PCFS])

if 'date' in summary:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Ngày", str(summary['date'])[:10] if summary['date'] else "N/A")

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
st.header(f"Vị Trí Phân Vị {selected_metric.upper()}")

percentile_col = f'{selected_metric}_percentile'
if percentile_col in df.columns:
    current_pct = df[percentile_col].iloc[-1]

    if not pd.isna(current_pct):
        fig_gauge = create_valuation_gauge(current_pct, selected_metric)
        st.plotly_chart(fig_gauge, use_container_width=True)
    else:
        st.warning("Không có dữ liệu phân vị hiện tại")

# Historical percentile
st.header(f"Phân Vị Lịch Sử {selected_metric.upper()}")

fig_timeseries = create_percentile_timeseries(df, selected_metric, selected_ticker)
st.plotly_chart(fig_timeseries, use_container_width=True)

# Decile analysis
st.header(f"Lợi Nhuận Theo Phân Vị {selected_metric.upper()}")

with st.spinner("Đang phân tích lợi nhuận theo nhóm mười..."):
    analysis = analyze_percentile_returns(df, percentile_col, forward_horizon)

if 'error' not in analysis:
    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "LN Vùng Rẻ (0-20%)",
            f"{analysis['cheap_zone_return']:.2%}",
            delta=None
        )

    with col2:
        st.metric(
            "LN Vùng Đắt (80-100%)",
            f"{analysis['expensive_zone_return']:.2%}",
            delta=None
        )

    with col3:
        spread = analysis['cheap_expensive_spread']
        st.metric(
            "Chênh Lệch Rẻ - Đắt",
            f"{spread:.2%}",
            delta="Dương là tốt" if spread > 0 else "Âm là xấu"
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
        st.subheader("Kiểm Định Thống Kê")

        st.write("**Kiểm Định Đơn Điệu** (Kỳ vọng xu hướng giảm)")
        mono = analysis['monotonicity']
        st.write(f"- Tương quan Spearman: {mono['correlation']:.4f}")
        st.write(f"- P-value: {mono[P_VALUE]:.4f}")
        st.write(f"- Đơn điệu: {'✅' if mono['is_monotonic'] else '❌'}")

        st.write("\n**Kiểm Định ANOVA** (LN khác nhau giữa các nhóm?)")
        anova = analysis['anova']
        st.write(f"- F-statistic: {anova.get('f_stat', 'N/A'):.2f}")
        st.write(f"- P-value: {anova.get(P_VALUE, 'N/A'):.4f}")
        st.write(f"- Có ý nghĩa: {'✅' if anova.get('significant') else '❌'}")

    # Detailed decile table
    st.subheader("Thống Kê Nhóm Mười Chi Tiết")
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
st.header("Công Cụ Dự Đoán Lợi Nhuận")

st.markdown("""
Nhập giá trị phân vị để xem lợi nhuận kỳ vọng dựa trên các mô hình lịch sử.
""")

input_percentile = st.slider(
    f"Phân Vị {selected_metric.upper()} Hiện Tại",
    0.0, 100.0,
    summary['percentiles'].get(selected_metric, 50.0) if summary['percentiles'].get(selected_metric) else 50.0
)

if st.button("Dự Đoán Lợi Nhuận"):
    prediction = predict_forward_return(df, input_percentile, percentile_col, forward_horizon)

    if 'error' not in prediction:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Lợi Nhuận Kỳ Vọng", f"{prediction['expected_return']:.2%}")

        with col2:
            st.metric("Khoảng Tin Cậy (95%)",
                     f"{prediction['confidence_low']:.2%} đến {prediction['confidence_high']:.2%}")

        with col3:
            st.metric("Kích Thước Mẫu", f"{int(prediction['sample_size'])}")

        st.info(f"Dựa trên phân vị: {prediction['current_percentile']:.1f}% → Nhóm mười {prediction['decile']}")
    else:
        st.error(prediction['error'])

# Metric comparison
st.header("So Sánh Các Chỉ Số Định Giá")

comparison = compare_valuation_metrics(df, forward_horizon)

if comparison:
    comp_data = []
    for metric, results in comparison.items():
        comp_data.append({
            'Chỉ Số': metric.upper(),
            'Tương Quan Đơn Điệu': results['monotonicity_correlation'],
            'P-val Đơn Điệu': results['monotonicity_pvalue'],
            'Chênh Lệch Rẻ-Đắt': results['cheap_expensive_spread'],
            'P-val ANOVA': results['anova_pvalue']
        })

    comp_df = pd.DataFrame(comp_data)

    st.dataframe(
        comp_df.style.format({
            'Tương Quan Đơn Điệu': '{:.4f}',
            'P-val Đơn Điệu': '{:.4f}',
            'Chênh Lệch Rẻ-Đắt': '{:.2%}',
            'P-val ANOVA': '{:.4f}'
        }),
        use_container_width=True
    )

    st.caption("""
    **Giải Thích**:
    - **Tương Quan Đơn Điệu Âm**: Phân vị thấp → LN cao hơn (tốt)
    - **Chênh Lệch Rẻ-Đắt Dương**: Rẻ vượt trội hơn đắt (tốt)
    - **P-value Thấp**: Mô hình có ý nghĩa thống kê
    """)

# Current PE/PB comparison across all banks
st.header("So Sánh PE/PB Hiện Tại - Tất Cả 17 Ngân Hàng")

st.markdown("""
Biểu đồ dưới đây hiển thị PE và PB hiện tại của tất cả 17 ngân hàng, sắp xếp theo thứ tự giảm dần.
""")

@st.cache_data(ttl=CACHE_TTL)
def get_all_banks_current_valuation():
    """Get current PE and PB for all banks"""
    data = load_all_data()

    results = []
    for ticker in BANKING_TICKERS:
        if ticker in data:
            df = data[ticker]
            if not df.empty:
                # Get most recent data
                latest = df.iloc[-1]

                pe_val = latest.get(PE, None)
                pb_val = latest.get(PB, None)
                date_val = latest.get(DATE, None)

                results.append({
                    'Ticker': ticker,
                    'PE': pe_val if not pd.isna(pe_val) else None,
                    'PB': pb_val if not pd.isna(pb_val) else None,
                    'Date': date_val
                })

    return pd.DataFrame(results)

with st.spinner("Đang tải dữ liệu định giá tất cả ngân hàng..."):
    all_banks_df = get_all_banks_current_valuation()

# Filter out None values and sort
pe_data = all_banks_df[all_banks_df['PE'].notna()].sort_values('PE', ascending=False)
pb_data = all_banks_df[all_banks_df['PB'].notna()].sort_values('PB', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("PE Theo Thứ Tự Giảm Dần")

    if not pe_data.empty:
        import plotly.graph_objects as go

        fig_pe = go.Figure()

        fig_pe.add_trace(go.Bar(
            x=pe_data['Ticker'],
            y=pe_data['PE'],
            marker_color='steelblue',
            text=pe_data['PE'].apply(lambda x: f'{x:.2f}'),
            textposition='outside'
        ))

        fig_pe.update_layout(
            title='PE Hiện Tại - 17 Ngân Hàng',
            xaxis_title='Mã Cổ Phiếu',
            yaxis_title='PE',
            height=500,
            template='plotly_white',
            showlegend=False
        )

        st.plotly_chart(fig_pe, use_container_width=True)

        # Show latest date
        latest_date = pe_data['Date'].iloc[0]
        st.caption(f"Dữ liệu mới nhất: {str(latest_date)[:10] if latest_date else 'N/A'}")
    else:
        st.warning("Không có dữ liệu PE")

with col2:
    st.subheader("PB Theo Thứ Tự Giảm Dần")

    if not pb_data.empty:
        fig_pb = go.Figure()

        fig_pb.add_trace(go.Bar(
            x=pb_data['Ticker'],
            y=pb_data['PB'],
            marker_color='coral',
            text=pb_data['PB'].apply(lambda x: f'{x:.2f}'),
            textposition='outside'
        ))

        fig_pb.update_layout(
            title='PB Hiện Tại - 17 Ngân Hàng',
            xaxis_title='Mã Cổ Phiếu',
            yaxis_title='PB',
            height=500,
            template='plotly_white',
            showlegend=False
        )

        st.plotly_chart(fig_pb, use_container_width=True)

        # Show latest date
        latest_date = pb_data['Date'].iloc[0]
        st.caption(f"Dữ liệu mới nhất: {str(latest_date)[:10] if latest_date else 'N/A'}")
    else:
        st.warning("Không có dữ liệu PB")

# Summary statistics
st.subheader("Thống Kê Tổng Hợp")

col1, col2, col3 = st.columns(3)

with col1:
    if not pe_data.empty:
        st.metric("PE Trung Bình", f"{pe_data['PE'].mean():.2f}")
        st.metric("PE Trung Vị", f"{pe_data['PE'].median():.2f}")

with col2:
    if not pb_data.empty:
        st.metric("PB Trung Bình", f"{pb_data['PB'].mean():.2f}")
        st.metric("PB Trung Vị", f"{pb_data['PB'].median():.2f}")

with col3:
    if not pe_data.empty and not pb_data.empty:
        st.metric("Số Ngân Hàng Có PE", f"{len(pe_data)}/17")
        st.metric("Số Ngân Hàng Có PB", f"{len(pb_data)}/17")

# Interpretation
st.header("Giải Thích")

st.info("""
**Cách sử dụng phân tích này:**

- **Vùng Rẻ (phân vị 0-20%)**: Định giá thấp về mặt lịch sử, có thể là điểm vào tốt
- **Vùng Hợp Lý (phân vị 40-60%)**: Định giá trung bình
- **Vùng Đắt (phân vị 80-100%)**: Định giá cao về mặt lịch sử, cần thận trọng

**Chênh Lệch Rẻ-Đắt Dương** gợi ý hiệu ứng giá trị: mua rẻ hiệu quả!

**Xu hướng giảm đơn điệu** trong lợi nhuận nhóm mười xác nhận mô hình.
""")

st.warning("""
⚠️ **Lưu Ý Quan Trọng**:
- Phân vị định giá sử dụng cửa sổ trượt 3 năm (756 ngày giao dịch)
- Mối quan hệ trong quá khứ có thể không duy trì trong tương lai
- Xem xét các yếu tố khác ngoài định giá
- Đây là nghiên cứu, không phải lời khuyên đầu tư
""")
