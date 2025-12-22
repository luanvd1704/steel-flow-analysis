"""
Configuration file for Multi-Sector Flow Analysis Platform
Contains common analysis parameters shared across all sectors
For sector-specific configs, see config_steel.py and config_banking.py
"""
import os
from typing import Any

# ============================================
# SECTOR CONFIGURATION LOADER
# ============================================
def get_sector_config(sector: str = 'steel'):
    """
    Load sector-specific configuration

    Args:
        sector: 'steel' or 'banking'

    Returns:
        Module object with sector-specific configuration
    """
    if sector.lower() == 'steel':
        from config import config_steel
        return config_steel
    elif sector.lower() == 'banking':
        from config import config_banking
        return config_banking
    else:
        raise ValueError(f"Unknown sector: {sector}. Choose 'steel' or 'banking'")


# ============================================
# COMMON PATHS (kept for backward compatibility)
# ============================================
# Base directory (root of steel-flow-analysis)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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
# STREAMLIT CONFIG (Common across sectors)
# ============================================
LAYOUT = "wide"

# Cache TTL (Time To Live) in seconds
CACHE_TTL = 3600  # 1 hour

# ============================================
# COMMON WARNINGS AND DISCLAIMERS
# ============================================
BACKTEST_DISCLAIMER = """
⚠️ **Disclaimer**: Kết quả backtest là phân tích lịch sử và không đảm bảo hiệu suất tương lai.
Không nên sử dụng làm khuyến nghị đầu tư.
"""

DATA_LIMITATION_WARNING = """
⚠️ **Giới hạn dữ liệu**: Một số thời kỳ có thể thiếu dữ liệu giao dịch.
Các giá trị bị thiếu được forward-fill cho giá, nhưng dữ liệu giao dịch giữ nguyên NaN.
"""
