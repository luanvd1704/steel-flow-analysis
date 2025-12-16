"""
Steel Flow Analysis Platform
Main entry point for Streamlit application
"""
import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config import PAGE_TITLE, PAGE_ICON, LAYOUT

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# Logo in sidebar (compatible with all Streamlit versions)
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.jpg")

# Main landing page
st.title(f"{PAGE_ICON} Nền tảng Phân tích Luồng Giao dịch Thép")

st.markdown("""
## Chào mừng đến với Nền tảng Phân tích Luồng Giao dịch Thép

Platform này phân tích 5 câu hỏi nghiên cứu quan trọng về 3 cổ phiếu thép: **HPG, HSG, NKG**

### 📋 Các Câu hỏi Nghiên cứu:

#### **Q1: Foreign Lead/Lag** 🔍
- Khối ngoại có thể dự đoán lợi nhuận T+1/T+3/T+5/T+10 không?
- Phân tích quintile và kiểm định thống kê
- Tìm cửa sổ normalization tối ưu

#### **Q2: Self-Trading Signals** 💼
- Tự doanh có sinh lợi không?
- So sánh ADV20 vs GTGD normalization
- Information Coefficient analysis

#### **Q3: Foreign vs Self Conflicts** ⚔️
- Ai dẫn dắt khi có xung đột?
- Granger causality test
- Event window analysis

#### **Q4: Valuation Percentiles** 💰
- PE/PB thấp → lợi nhuận cao hơn?
- Phân tích percentile và decile
- Zone identification (cheap/expensive)

#### **Q5: Composite Score** 🎯
- Kết hợp tín hiệu: z(Foreign) + z(Self) - percentile(PE/PB)
- Quintile backtest
- CAPM alpha analysis

---

### 📊 Dữ liệu:

| Dataset | Thời gian | Records |
|---------|-----------|---------|
| **Foreign Trading** | 2020-12 → 2025-12 | ~1,239 sessions |
| **Self-Trading** | 2022-11 → 2025-12 | ~510-778 sessions ⚠️ |
| **Valuation** | 2019-12 → 2025-12 | ~1,487 sessions |
| **VN-Index** | 2020-12 → 2025-12 | ~1,248 sessions |

⚠️ **Lưu ý**: Dữ liệu tự doanh chỉ có 3 năm → Q2, Q3, Q5 có giới hạn

---

### 🚀 Bắt đầu:

👈 **Chọn trang phân tích từ sidebar bên trái**

---

### ℹ️ Thông tin:

- **Mã cổ phiếu**: HPG (Hòa Phát), HSG (Hoa Sen), NKG (Nam Kim)
- **Phương pháp**: Event study, phân tích quintile, kiểm định thống kê
- **Độ chính xác**: T-tests, p-values, khoảng tin cậy

---

⚠️ **Disclaimer**: Đây là nghiên cứu định lượng, không phải khuyến nghị đầu tư.
""")

# Sidebar info
with st.sidebar:
    # Display logo at top of sidebar
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)  # Old parameter name for compatibility
        st.markdown("---")

    st.info("""
    **Steel Flow Analysis v1.0**

    Nền tảng phân tích định lượng
    luồng giao dịch cổ phiếu thép

    📈 3 Tickers: HPG, HSG, NKG
    📊 5 Research Questions
    🔬 Statistical rigor
    """)

    st.markdown("---")
    st.caption("© 2025 Steel Flow Analysis")
