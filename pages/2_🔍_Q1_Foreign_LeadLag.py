"""
Q1: Trang Phân Tích Dẫn/Trễ Của Nhà Đầu Tư Nước Ngoài
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
from config.config import get_sector_config, FORWARD_RETURN_HORIZONS, CACHE_TTL, QUINTILE_COLORS
from utils.constants import *
from utils.logo_helper import display_sidebar_logo

# Filtered bank tickers based on comprehensive quintile analysis across 6 timeframes
# Only banks with statistical significance (p-value <= 0.05, positive spread)
# Analysis: Tested T+1, T+3, T+5, T+10, T+20, T+30 horizons with 6-year data (2019-2025)
# Note: Zero values INCLUDED in quintile analysis (not filtered)
# Updated: 2025-12-23 with 6-year data analysis results
FILTERED_BANKING_TICKERS = [
    'OCB',  # 2/6 horizons - STRONGEST (p_min=0.0016, spread_max=3.15%)
    'VPB',  # 2/6 horizons - VERY STRONG (p_min=0.0033, spread_max=3.13%)
    'ACB',  # 2/6 horizons - MODERATE (p_min=0.0262, spread_max=1.40%)
    'SSB',  # 2/6 horizons - MARGINAL (p_min=0.0300, spread_max=1.53%)
    'EIB',  # 1/6 horizon - MODERATE (p_min=0.0155, spread_max=1.54%)
]

# Get banking config
config_banking = get_sector_config('banking')

st.set_page_config(page_title="Q1: Dẫn/Trễ NDTNN", page_icon="🔍", layout="wide")

# Display logo in sidebar
display_sidebar_logo()

st.title("🔍 Q1: Phân Tích Dẫn/Trễ Nhà Đầu Tư Nước Ngoài")

st.info("""
📊 **Lưu ý**: Tab này hiển thị 5 mã ngân hàng có dữ liệu khối ngoại có sức dự đoán có ý nghĩa thống kê.

**Tiêu chí lọc:**
- Dữ liệu: 6 năm (2019-2025) - match với date range của foreign trading data
- Quintile analysis trên 6 khung thời gian (T+1, T+3, T+5, T+10, T+20, T+30)
- P-value ≤ 0.05 (độ tin cậy ≥ 95%)
- Spread dương (Q5 > Q1)

**5 mã đạt chuẩn (xếp theo độ mạnh):**
1. **OCB**: MẠNH NHẤT - 2/6 horizons (p_min=0.0016, spread=3.15%)
2. **VPB**: RẤT MẠNH - 2/6 horizons (p_min=0.0033, spread=3.13%)
3. **ACB**: TRUNG BÌNH - 2/6 horizons (p_min=0.0262, spread=1.40%)
4. **SSB**: YẾU - 2/6 horizons (p_min=0.0300, spread=1.53%)
5. **EIB**: TRUNG BÌNH - 1/6 horizon (p_min=0.0155, spread=1.54%)

**12 mã không đạt:** VCB, TCB, MBB, BID, CTG, STB, HDB, TPB, VIB, SHB, MSB, LPB

*Cập nhật: 23/12/2025 - Phân tích lại với dữ liệu 6 năm (2019-2025)*
""")

st.markdown("""
**Câu Hỏi Nghiên Cứu**: Nhà đầu tư nước ngoài có dự đoán được lợi nhuận tương lai không?

Phân tích này xem xét liệu mua ròng của nhà đầu tư nước ngoài hôm nay có dự đoán được lợi nhuận cổ phiếu tại T+1, T+3, T+5 và T+10 hay không.
""")

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_all_data():
    return merge_all_data(config_banking, tickers=FILTERED_BANKING_TICKERS)

with st.spinner("Đang tải dữ liệu..."):
    data = load_all_data()

# Sidebar filters
st.sidebar.header("Bộ Lọc")
selected_ticker = st.sidebar.selectbox("Chọn Mã Cổ Phiếu", FILTERED_BANKING_TICKERS)
selected_horizon = st.sidebar.selectbox(
    "Kỳ Hạn Lợi Nhuận",
    FORWARD_RETURN_HORIZONS,
    format_func=lambda x: f"T+{x} ngày"
)

# Run analysis
@st.cache_data(ttl=CACHE_TTL)
def run_lead_lag_analysis(ticker):
    return lead_lag_analysis_full(data[ticker])

with st.spinner(f"Đang phân tích {selected_ticker}..."):
    results = run_lead_lag_analysis(selected_ticker)

# Display results
horizon_key = f'T+{selected_horizon}'

if horizon_key in results:
    result = results[horizon_key]

    # Summary metrics
    st.header(f"Kết Quả Cho {selected_ticker} Tại T+{selected_horizon}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "LN Trung Bình Q5",
            f"{result['q5_mean']:.4f}",
            delta=f"{result['q5_mean']:.2%}"
        )

    with col2:
        st.metric(
            "LN Trung Bình Q1",
            f"{result['q1_mean']:.4f}",
            delta=f"{result['q1_mean']:.2%}"
        )

    with col3:
        st.metric(
            "Chênh Lệch Q5 - Q1",
            f"{result['spread']:.4f}",
            delta=f"{result['spread']:.2%}"
        )

    with col4:
        significance = "✅ Có Ý Nghĩa" if result['significant'] else "❌ Không Có Ý Nghĩa"
        st.metric(
            "Kiểm Định Thống Kê",
            significance,
            delta=f"p={result['p_value']:.4f}"
        )

    # Quintile bar chart
    st.header("Lợi Nhuận Vượt Trội Trung Bình Theo Nhóm")

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
        title=f"Lợi Nhuận Vượt Trội TB Theo Nhóm Mua Ròng NN (T+{selected_horizon})",
        xaxis_title="Nhóm (Q1 = Mua Ròng NN Thấp Nhất, Q5 = Cao Nhất)",
        yaxis_title="Lợi Nhuận Vượt Trội TB",
        yaxis_tickformat='.2%',
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Detailed statistics table
    st.header("Thống Kê Chi Tiết")

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
    st.header("Phân Tích Hệ Số Thông Tin (IC)")

    st.markdown("""
    IC đo lường tương quan giữa mua ròng nước ngoài và lợi nhuận tương lai.
    IC tuyệt đối cao hơn cho thấy sức mạnh dự đoán mạnh hơn.
    """)

    ic_data = []
    for horizon_key, ic_result in results['ic_analysis'].items():
        ic_data.append({
            'Kỳ Hạn': horizon_key,
            'IC': ic_result['ic'],
            'P-Value': ic_result[P_VALUE],
            'Có Ý Nghĩa': '✅' if ic_result['significant'] else '❌',
            'Kích Thước Mẫu': ic_result['n']
        })

    ic_df = pd.DataFrame(ic_data)

    col1, col2 = st.columns([2, 1])

    with col1:
        # IC chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=ic_df['Kỳ Hạn'],
            y=ic_df['IC'],
            marker_color=['green' if x > 0 else 'red' for x in ic_df['IC']],
            text=ic_df['IC'].apply(lambda x: f"{x:.4f}"),
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Hệ Số Thông Tin Theo Kỳ Hạn - {selected_ticker}",
            xaxis_title="Kỳ Hạn",
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
                'Kích Thước Mẫu': '{:.0f}'
            }),
            use_container_width=True
        )

# All horizons comparison
st.header("So Sánh Tất Cả Các Kỳ Hạn")

comparison_data = []
for horizon in FORWARD_RETURN_HORIZONS:
    hkey = f'T+{horizon}'
    if hkey in results:
        r = results[hkey]
        comparison_data.append({
            'Kỳ Hạn': hkey,
            'TB Q5': r['q5_mean'],
            'TB Q1': r['q1_mean'],
            'Chênh Lệch': r['spread'],
            'T-Stat': r['t_stat'],
            'P-Value': r['p_value'],
            'Có Ý Nghĩa': '✅' if r['significant'] else '❌'
        })

comp_df = pd.DataFrame(comparison_data)

st.dataframe(
    comp_df.style.format({
        'TB Q5': '{:.4f}',
        'TB Q1': '{:.4f}',
        'Chênh Lệch': '{:.4f}',
        'T-Stat': '{:.2f}',
        'P-Value': '{:.4f}'
    }),
    use_container_width=True
)

# Interpretation
st.header("Giải Thích")

st.info("""
**Cách diễn giải kết quả:**

- **Chênh Lệch Dương (Q5 > Q1)**: Mua ròng NN dự đoán lợi nhuận cao hơn trong tương lai
- **Chênh Lệch Âm (Q5 < Q1)**: Mua ròng NN dự đoán lợi nhuận thấp hơn (nghịch chiều)
- **Ý Nghĩa Thống Kê**: p-value < 0.05 cho thấy mô hình đáng tin cậy
- **IC gần 0**: Sức mạnh dự đoán yếu
- **|IC| > 0.05**: Sức mạnh dự đoán trung bình
- **|IC| > 0.10**: Sức mạnh dự đoán mạnh
""")

st.warning("""
⚠️ **Tuyên Bố Miễn Trừ**: Hiệu suất trong quá khứ không đảm bảo kết quả trong tương lai.
Phân tích này chỉ cho mục đích nghiên cứu và không nên được coi là lời khuyên đầu tư.
""")
