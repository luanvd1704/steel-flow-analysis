# Steel Flow Analysis Platform

Nền tảng phân tích định lượng luồng giao dịch cho 3 cổ phiếu thép: **HPG, HSG, NKG**

## 📋 Tổng quan

Platform này phân tích 5 câu hỏi nghiên cứu quan trọng:

### Q1: Foreign Lead/Lag 🔍
- Khối ngoại có dự đoán lợi nhuận T+1/T+3/T+5/T+10 không?
- Phân tích quintile và kiểm định thống kê
- Information Coefficient (IC) analysis

### Q2: Self-Trading Signals 💼
- Tự doanh có sinh lợi không?
- So sánh ADV20 vs GTGD normalization
- Tercile analysis

### Q3: Foreign vs Self Conflicts ⚔️
- Ai dẫn dắt khi có xung đột?
- Granger causality test
- Event window analysis

### Q4: Valuation Percentiles 💰
- PE/PB thấp → lợi nhuận cao hơn?
- Decile analysis
- Cheap/expensive zones

### Q5: Composite Score 🎯
- Kết hợp: z(Foreign) + z(Self) - percentile(PE/PB)
- Quintile backtest
- CAPM alpha analysis

## 📊 Dữ liệu

| Dataset | Thời gian | Records |
|---------|-----------|---------|
| Foreign Trading | 2020-12 → 2025-12 | ~1,239 sessions |
| Self-Trading | 2022-11 → 2025-12 | ~510-778 sessions |
| Valuation | 2019-12 → 2025-12 | ~1,487 sessions |
| VN-Index | 2020-12 → 2025-12 | ~1,248 sessions |

⚠️ **Lưu ý**: Dữ liệu tự doanh chỉ có 3 năm → Q2, Q3, Q5 có giới hạn

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8+
- pip

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## 💻 Sử dụng

### Chạy ứng dụng

```bash
cd steel-flow-analysis
streamlit run app.py
```

Ứng dụng sẽ chạy tại: http://localhost:8501

### Cấu trúc thư mục

```
steel-flow-analysis/
├── app.py                 # Entry point
├── requirements.txt       # Dependencies
├── README.md
│
├── config/               # Cấu hình
│   ├── __init__.py
│   └── config.py
│
├── data/                 # Data loading
│   ├── __init__.py
│   ├── loader.py
│   └── validator.py
│
├── analysis/             # Analysis modules
│   ├── __init__.py
│   ├── normalization.py
│   ├── lead_lag.py      # Q1
│   ├── statistics.py
│   └── ... (Q2-Q5 modules)
│
├── visualization/        # Charts
│   ├── __init__.py
│   ├── common.py
│   └── ... (Q1-Q5 charts)
│
└── pages/               # Streamlit pages
    ├── 1_📊_Overview.py
    ├── 2_🔍_Q1_Foreign_LeadLag.py
    └── ... (Q2-Q5 pages)
```

## 📈 Tính năng (100% Complete!)

### ✅ Phase 1: Foundation
- ✅ Config và constants
- ✅ Utils (helpers, date_utils)
- ✅ Data loader với column mapping tiếng Việt
- ✅ Data validator

### ✅ Phase 2: Q1 Foreign Lead/Lag
- ✅ Normalization module
- ✅ Statistics module (t-tests, IC)
- ✅ Lead-lag analysis với multiple horizons
- ✅ Streamlit page với interactive charts
- ✅ Information Coefficient analysis

### ✅ Phase 3: Q4 Valuation Analysis
- ✅ Valuation percentiles module (3-year rolling)
- ✅ Decile analysis
- ✅ Cheap vs Expensive zone comparison
- ✅ Prediction tool
- ✅ Gauge charts và timeseries
- ✅ Streamlit page đầy đủ

### ✅ Phase 4: Q2 Self-Trading
- ✅ Self-trading signals (ADV20 vs GTGD)
- ✅ Tercile analysis
- ✅ Method comparison
- ✅ Data availability checks
- ✅ Streamlit page với warnings

### ✅ Phase 5: Q3 Conflicts
- ✅ Conflict matrix (4 states)
- ✅ Granger causality tests
- ✅ Regime-specific analysis
- ✅ Leadership identification
- ✅ Streamlit page với heatmaps

### ✅ Phase 6: Q5 Composite
- ✅ Composite scoring (Foreign + Self + Valuation)
- ✅ Quintile backtest
- ✅ CAPM alpha analysis
- ✅ Current rankings
- ✅ Aggregate performance metrics
- ✅ Streamlit page hoàn chỉnh

### ✅ Phase 7: Integration
- ✅ Main app.py
- ✅ Overview page với data summary
- ✅ All 6 analysis pages
- ✅ Requirements.txt
- ✅ Complete README.md

## 📝 Methodology

### Statistical Testing
- T-tests cho quintile spreads
- P-values với significance level = 0.05
- Minimum sample size = 30

### Normalization
- ADV20: Net Buy / 20-day average volume
- Z-scores: 252-day rolling window
- Percentiles: 756-day rolling window (3 years)

### Event Studies
- Forward returns: T+1, T+3, T+5, T+10
- Excess returns = Stock return - Market return
- Business days only

## ⚠️ Disclaimers

1. **Dữ liệu giới hạn**: Tự doanh chỉ 3 năm (2022-11 onwards)
2. **Missing data**: Forward-fill cho giá, NaN cho trading data
3. **Nghiên cứu**: Không phải khuyến nghị đầu tư
4. **Past performance**: Không đảm bảo kết quả tương lai

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Data**: Pandas, NumPy
- **Visualization**: Plotly
- **Statistics**: SciPy, Statsmodels
- **Excel**: openpyxl

## 📧 Contact

Questions? Issues? Please file an issue or contact the development team.

---

**Version**: 1.0 (COMPLETE - All 6 Research Questions + Overview)
**Last Updated**: 2025-12-14
**Status**: ✅ Production Ready
