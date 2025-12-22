"""
Banking Sector Analysis Platform
Main entry point for Streamlit application
"""
import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_banking import PAGE_TITLE, PAGE_ICON
from config.config import LAYOUT

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# Logo in sidebar (compatible with all Streamlit versions)
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.jpg")

# Main landing page
st.title(f"{PAGE_ICON} Nền tảng Phân tích Ngành Ngân hàng")

st.markdown("""
## Chào mừng đến với Nền tảng Phân tích Ngành Ngân hàng

Platform này phân tích **17 ngân hàng** với 6 câu hỏi nghiên cứu + Ranking theo 8 chỉ số tài chính

### 🏦 17 Ngân hàng:
VCB, TCB, MBB, ACB, VPB, BID, CTG, STB, HDB, TPB, VIB, SSB, SHB, MSB, LPB, OCB, EIB

---

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

#### **NEW: Ranking by Financial Metrics** 🏆
- Xếp hạng theo 11 chỉ số tài chính
- Cross-sectional analysis
- Quintile performance comparison

---

### 💰 8 Chỉ Số Tài Chính (TTM + YTD Methodology):

**Profitability (Trọng số 1.0):**
- ROA (Return on Assets) - TTM

**Growth:**
- Net Profit YoY (Trọng số 1.0) - 9M YTD
- Operating Income YoY (Trọng số 1.0) - 9M YTD
- Loan Growth (Trọng số 0.5) - End-Quarter

**Efficiency (Trọng số 1.0):**
- CIR (Cost-to-Income Ratio) - TTM

**Capital & Liquidity (Trọng số 1.0):**
- Equity/Assets - End-Quarter

**Income Structure (Trọng số 1.0):**
- Fee Ratio - TTM

**Cashflow Quality (Trọng số 0.25 - Cờ cảnh báo):**
- OCF/Net Profit - TTM

**Đã loại bỏ:** NIM, Credit Cost, LDR (cần dữ liệu thuyết minh BCTC)

---

### 📊 Dữ liệu:

| Dataset | Thời gian | Tickers |
|---------|-----------|---------|
| **Foreign Trading** | 2020-12 → 2025-12 | 17 banks |
| **Self-Trading** | 2022-11 → 2025-12 | 17 banks ⚠️ |
| **Valuation** | 2019-12 → 2025-12 | 17 banks |
| **Financial Metrics** | Quarterly (8Q) | 17 banks |

⚠️ **Lưu ý**: Dữ liệu tự doanh chỉ có 3 năm → Q2, Q3, Q5 có giới hạn

---

### 🚀 Bắt đầu:

👈 **Chọn trang phân tích từ sidebar bên trái**

---

### ℹ️ Thông tin:

- **Số lượng**: 17 ngân hàng hàng đầu Việt Nam
- **Phương pháp**: Event study, phân tích quintile, kiểm định thống kê, cross-sectional ranking
- **Độ chính xác**: T-tests, p-values, khoảng tin cậy
- **Tần suất**: Dữ liệu tài chính quarterly, giao dịch daily

---

⚠️ **Disclaimer**: Đây là nghiên cứu định lượng, không phải khuyến nghị đầu tư.
""")

# Sidebar info
with st.sidebar:
    # Display logo at top of sidebar
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)
        st.markdown("---")

    st.info("""
    **Banking Sector Analysis v1.0**

    Nền tảng phân tích định lượng
    ngành ngân hàng Việt Nam

    🏦 17 Banks
    📊 6 Research Questions
    💰 11 Financial Metrics
    🏆 Cross-sectional Ranking
    """)

    st.markdown("---")
    st.caption("© 2025 Banking Sector Analysis")
