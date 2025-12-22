"""
Banking Sector Configuration
Contains banking-specific tickers, file paths, and 11 financial metrics metadata
"""
import os

# ============================================
# SECTOR INFO
# ============================================
SECTOR_NAME = "Banking"
SECTOR_CODE = "banking"

# ============================================
# TICKERS - 17 Banks
# ============================================
TICKERS = [
    "VCB",  # Vietcombank
    "TCB",  # Techcombank
    "MBB",  # MB Bank
    "ACB",  # ACB
    "VPB",  # VPBank
    "BID",  # BIDV
    "CTG",  # VietinBank
    "STB",  # Sacombank
    "HDB",  # HDBank
    "TPB",  # TPBank
    "VIB",  # VIB
    "SSB",  # Southeast Asia Bank
    "SHB",  # SHB
    "MSB",  # MSB
    "LPB",  # LienVietPostBank
    "OCB",  # OCB
    "EIB"   # Eximbank
]

# ============================================
# FILE PATHS
# ============================================
# Base directory (root of steel-flow-analysis)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Data files
FOREIGN_TRADING_FILE = os.path.join(DATA_DIR, 'bank_foreign_trading.xlsx')
SELF_TRADING_FILE = os.path.join(DATA_DIR, 'bank_self_trading.xlsx')
VALUATION_FILE = os.path.join(DATA_DIR, 'bank_valuation.xlsx')
FINANCIAL_FILE = os.path.join(DATA_DIR, 'bank_financials.xlsx')

# Market index file (shared with steel)
VNINDEX_FILE = os.path.join(BASE_DIR, 'Stock-analyst', 'vnindex_market.xlsx')

# ============================================
# STREAMLIT CONFIG
# ============================================
PAGE_TITLE = "Banking Sector Analysis"
PAGE_ICON = "🏦"

# ============================================
# SECTOR-SPECIFIC PARAMETERS
# ============================================
# Banking sector uses financial metrics ranking
HAS_FINANCIAL_METRICS = True
HAS_RANKING_PAGE = True

# ============================================
# BANKING FINANCIAL METRICS (8 metrics)
# ============================================
# REMOVED: NIM, Credit Cost, LDR (require detailed notes from financial statements)
# WEIGHT 1.0 (Normal): ROA, Net Profit YoY, Operating Income YoY, CIR, Equity/Assets, Fee Ratio
# WEIGHT 0.5 (Medium): Loan Growth (high noise)
# WEIGHT 0.25 (Warning flag): OCF/Net Profit (very high noise in banking CFO)
BANK_METRICS = {
    'roa': {
        'name': 'ROA',
        'full_name': 'Return on Assets (TTM)',
        'group': 'Profitability',
        'direction': 'higher_is_better',
        'unit': '%',
        'formula': 'Σ Net Profit (4Q) / Avg Total Assets * 100',
        'description': 'TTM return on assets - measures profitability efficiency over last 12 months',
        'weight': 1.0
    },
    'net_profit_yoy': {
        'name': 'Net Profit YoY',
        'full_name': 'Net Profit YoY Growth (9M YTD)',
        'group': 'Growth',
        'direction': 'higher_is_better',
        'unit': '%',
        'formula': '(9M This Year - 9M Last Year) / 9M Last Year * 100',
        'description': 'Year-to-date net profit growth (9 months) - more stable than quarterly comparison',
        'weight': 1.0
    },
    'loan_growth': {
        'name': 'Loan Growth',
        'full_name': 'Loan Growth YoY (End-Quarter)',
        'group': 'Growth',
        'direction': 'higher_is_better',
        'unit': '%',
        'formula': '(Loans End-Q This Year - Loans End-Q Last Year) / Loans Last Year * 100',
        'description': 'Year-over-year loan portfolio growth comparing same quarter end-points (lower weight due to noise)',
        'weight': 0.5
    },
    'operating_income_yoy': {
        'name': 'Operating Income YoY',
        'full_name': 'Operating Income Growth (9M YTD)',
        'group': 'Growth',
        'direction': 'higher_is_better',
        'unit': '%',
        'formula': '(9M This Year - 9M Last Year) / 9M Last Year * 100',
        'description': 'Year-to-date operating income growth (9 months) - more stable than quarterly',
        'weight': 1.0
    },
    'cir': {
        'name': 'CIR',
        'full_name': 'Cost-to-Income Ratio (TTM)',
        'group': 'Efficiency',
        'direction': 'lower_is_better',
        'unit': '%',
        'formula': 'Σ Operating Expense (4Q) / Σ Operating Income (4Q) * 100',
        'description': 'TTM operating efficiency - lower is better, calculated over last 12 months',
        'weight': 1.0
    },
    'equity_assets': {
        'name': 'Equity/Assets',
        'full_name': 'Equity to Assets Ratio (End-Quarter)',
        'group': 'Capital & Liquidity',
        'direction': 'optimal_range',
        'optimal_range': (7, 12),
        'unit': '%',
        'formula': 'Equity End-Q / Total Assets End-Q * 100',
        'description': 'Capital adequacy at quarter-end - optimal range 7-12%',
        'weight': 1.0
    },
    'fee_ratio': {
        'name': 'Fee Ratio',
        'full_name': 'Fee Income Ratio (TTM)',
        'group': 'Income Structure',
        'direction': 'higher_is_better',
        'unit': '%',
        'formula': 'Σ Fee Income (4Q) / Σ Operating Income (4Q) * 100',
        'description': 'TTM non-interest income diversification over last 12 months',
        'weight': 1.0
    },
    'ocf_net_profit': {
        'name': 'OCF/Net Profit',
        'full_name': 'Operating Cash Flow to Net Profit (TTM)',
        'group': 'Cashflow Quality',
        'direction': 'higher_is_better',
        'unit': 'ratio',
        'formula': 'Σ OCF (4Q) / Σ Net Profit (4Q)',
        'description': 'TTM cash generation quality - warning flag only, not main driver (very high noise in banking CFO)',
        'weight': 0.25
    },
    'ldr': {
        'name': 'LDR',
        'full_name': 'Loan-to-Deposit Ratio (End-Quarter)',
        'group': 'Capital & Liquidity',
        'direction': 'lower_is_better',
        'unit': '%',
        'formula': 'Loans End-Q / Deposits End-Q * 100',
        'description': 'Tỷ lệ cho vay trên huy động - thấp hơn = thanh khoản tốt hơn',
        'weight': 0.10
    }
}

# Metric groups for UI organization
METRIC_GROUPS = {
    'Profitability': ['roa'],
    'Growth': ['net_profit_yoy', 'loan_growth', 'operating_income_yoy'],
    'Efficiency': ['cir'],
    'Capital & Liquidity': ['equity_assets', 'ldr'],
    'Income Structure': ['fee_ratio'],
    'Cashflow Quality': ['ocf_net_profit']
}

# Default metric for ranking page
DEFAULT_RANKING_METRIC = 'roa'

# ============================================
# WARNINGS AND DISCLAIMERS
# ============================================
SECTOR_WARNING = """
⚠️ **Lưu ý về dữ liệu Banking - 8 Metrics với TTM + YTD Methodology**:
- **TTM (Trailing Twelve Months)**: ROA, CIR, Fee Ratio, OCF/Net Profit
  → Tổng 4 quý gần nhất, phản ánh performance thực tế 12 tháng
- **9M YTD (Year-to-Date)**: Net Profit YoY, Operating Income YoY
  → So sánh 9 tháng năm nay vs 9 tháng năm trước, ổn định hơn quarterly YoY
- **End-Quarter**: Loan Growth, Equity/Assets
  → Snapshot cuối quý, balance sheet metrics
- **Đã loại bỏ**: NIM, Credit Cost, LDR (cần dữ liệu thuyết minh BCTC)
- **Trọng số phân tầng**:
  - **1.0 (Bình thường)**: ROA, Net Profit YoY, Operating Income YoY, CIR, Equity/Assets, Fee Ratio
  - **0.5 (Tham khảo)**: Loan Growth (độ nhiễu cao)
  - **0.25 (Cờ cảnh báo)**: OCF/Net Profit (CFO ngân hàng rất nhiễu, chỉ dùng để cảnh báo)
- Dữ liệu BCTC quarterly được forward-fill sang daily cho ranking
- Cần ít nhất 4-5 quarters dữ liệu lịch sử để tính TTM và YTD chính xác
"""
