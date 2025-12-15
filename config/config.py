"""
Configuration file for Steel Flow Analysis Platform
Contains paths, tickers, and analysis parameters
"""
import os

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

# ============================================
# ANALYSIS PARAMETERS
# ============================================
# Event windows for analysis
EVENT_WINDOWS = [(1, 5), (1, 10)]

# Forward return horizons (in trading days)
FORWARD_RETURN_HORIZONS = [1, 3, 5, 10, 20, 30]

# Rolling window parameters
ADV_WINDOW = 20              # Average daily volume window
ZSCORE_WINDOW = 252          # Z-score window (1 year trading days)
PERCENTILE_WINDOW = 756      # Percentile window (3 years trading days)

# Statistical parameters
SIGNIFICANCE_LEVEL = 0.05    # Alpha for hypothesis testing
MIN_SAMPLE_SIZE = 30         # Minimum sample size for t-tests

# Market regime parameters
MA_WINDOW_REGIME = 200       # Moving average for bull/bear classification

# Backtest parameters
REBALANCE_FREQ = 'M'         # Monthly rebalancing
MIN_HOLDING_PERIOD = 1       # Minimum holding period in days

# Normalization methods for self-trading
NORMALIZATION_METHODS = ['ADV20', 'GTGD']

# ============================================
# VISUALIZATION PARAMETERS
# ============================================
# Color schemes
COLOR_PALETTE = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff9800',
    'info': '#17a2b8',
    'neutral': '#7f7f7f'
}

# Quintile colors (for Q1, Q5 analysis)
QUINTILE_COLORS = ['#d62728', '#ff7f0e', '#7f7f7f', '#2ca02c', '#1f77b4']

# Tercile labels (for Q2 self-trading analysis)
TERCILE_LABELS = ['T1', 'T2', 'T3']

# Chart defaults
CHART_HEIGHT = 500
CHART_WIDTH = 800

# ============================================
# DATA QUALITY PARAMETERS
# ============================================
# Maximum allowed missing data percentage
MAX_MISSING_PCT = 0.5  # 50%

# Minimum required data points per ticker
MIN_DATA_POINTS = 100

# ============================================
# STREAMLIT CONFIG
# ============================================
PAGE_TITLE = "Steel Flow Analysis"
PAGE_ICON = "📊"
LAYOUT = "wide"

# Cache TTL (Time To Live) in seconds
CACHE_TTL = 3600  # 1 hour

# ============================================
# WARNINGS AND DISCLAIMERS
# ============================================
SELF_TRADING_WARNING = """
⚠️ **Lưu ý về dữ liệu Tự Doanh**: Dữ liệu chỉ có từ 2022-11 trở đi (3 năm).
Các phân tích liên quan đến tự doanh có thể thiếu sức mạnh thống kê.
"""

BACKTEST_DISCLAIMER = """
⚠️ **Disclaimer**: Kết quả backtest là phân tích lịch sử và không đảm bảo hiệu suất tương lai.
Không nên sử dụng làm khuyến nghị đầu tư.
"""

DATA_LIMITATION_WARNING = """
⚠️ **Giới hạn dữ liệu**: Một số thời kỳ có thể thiếu dữ liệu giao dịch.
Các giá trị bị thiếu được forward-fill cho giá, nhưng dữ liệu giao dịch giữ nguyên NaN.
"""
