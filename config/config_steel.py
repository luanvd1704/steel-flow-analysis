"""
Steel Sector Configuration
Contains steel-specific tickers, file paths, and parameters
"""
import os

# ============================================
# SECTOR INFO
# ============================================
SECTOR_NAME = "Steel"
SECTOR_CODE = "steel"

# ============================================
# TICKERS
# ============================================
TICKERS = ['HPG', 'HSG', 'NKG']

# ============================================
# FILE PATHS
# ============================================
# Base directory (root of steel-flow-analysis)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'Stock-analyst')

# Data files
FOREIGN_TRADING_FILE = os.path.join(DATA_DIR, 'steel_foreign_trading.xlsx')
SELF_TRADING_FILE = os.path.join(DATA_DIR, 'steel_self_trading.xlsx')
VALUATION_FILE = os.path.join(DATA_DIR, 'steel_valuation.xlsx')
VNINDEX_FILE = os.path.join(DATA_DIR, 'vnindex_market.xlsx')

# Financial data file (not used for steel currently)
FINANCIAL_FILE = None

# ============================================
# STREAMLIT CONFIG
# ============================================
PAGE_TITLE = "Steel Flow Analysis"
PAGE_ICON = "📊"

# ============================================
# SECTOR-SPECIFIC PARAMETERS
# ============================================
# Steel sector doesn't use financial metrics ranking
HAS_FINANCIAL_METRICS = False
HAS_RANKING_PAGE = False

# ============================================
# WARNINGS AND DISCLAIMERS
# ============================================
SECTOR_WARNING = """
⚠️ **Lưu ý về dữ liệu Tự Doanh**: Dữ liệu chỉ có từ 2022-11 trở đi (3 năm).
Các phân tích liên quan đến tự doanh có thể thiếu sức mạnh thống kê.
"""
