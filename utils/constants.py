"""
Constants used throughout the application
"""

# ============================================
# COLUMN NAMES
# ============================================
# Foreign trading columns
FOREIGN_NET_BUY_VOL = 'foreign_net_buy_vol'
FOREIGN_NET_BUY_VAL = 'foreign_net_buy_val'
FOREIGN_BUY_VOL = 'foreign_buy_vol'
FOREIGN_SELL_VOL = 'foreign_sell_vol'

# Self-trading columns
SELF_NET_BUY_VOL = 'self_net_buy_vol'
SELF_NET_BUY_VAL = 'self_net_buy_val'
SELF_BUY_VAL = 'self_buy_val'
SELF_SELL_VAL = 'self_sell_val'

# Price and volume columns
CLOSE = 'close'
VOLUME = 'volume'
HIGH = 'high'
LOW = 'low'
OPEN = 'open'

# Valuation columns
PE = 'pe'
PB = 'pb'
PCFS = 'pcfs'

# Market columns
VNINDEX_CLOSE = 'vnindex_close'
MARKET_RETURN = 'market_return'
STOCK_RETURN = 'return'

# Derived columns
EXCESS_RETURN = 'excess_return'
MA200 = 'ma200'
BULL_MARKET = 'bull_market'

# Normalized signals
FOREIGN_SIGNAL_ADV20 = 'foreign_signal_adv20'
SELF_SIGNAL_ADV20 = 'self_signal_adv20'
SELF_SIGNAL_GTGD = 'self_signal_gtgd'

# Percentile columns
PE_PERCENTILE = 'pe_percentile'
PB_PERCENTILE = 'pb_percentile'
PCFS_PERCENTILE = 'pcfs_percentile'

# Z-score columns
FOREIGN_ZSCORE = 'foreign_zscore'
SELF_ZSCORE = 'self_zscore'

# Composite score
COMPOSITE_SCORE = 'composite_score'
COMPOSITE_RANK = 'composite_rank'

# Quintile/Tercile assignments
QUINTILE = 'quintile'
TERCILE = 'tercile'
DECILE = 'decile'

# Forward returns
FWD_RETURN_1D = 'fwd_return_1d'
FWD_RETURN_3D = 'fwd_return_3d'
FWD_RETURN_5D = 'fwd_return_5d'
FWD_RETURN_10D = 'fwd_return_10d'

# Conflict states
CONFLICT_STATE = 'conflict_state'

# ============================================
# CONFLICT STATES
# ============================================
BOTH_BUY = 'Both Buy'
FOREIGN_BUY_SELF_SELL = 'Foreign Buy, Self Sell'
FOREIGN_SELL_SELF_BUY = 'Foreign Sell, Self Buy'
BOTH_SELL = 'Both Sell'

# ============================================
# MARKET REGIMES
# ============================================
BULL = 'Bull'
BEAR = 'Bear'

# ============================================
# STATISTICAL TERMS
# ============================================
T_STAT = 't_statistic'
P_VALUE = 'p_value'
MEAN = 'mean'
STD = 'std'
SHARPE = 'sharpe_ratio'
ALPHA = 'alpha'
BETA = 'beta'
IR = 'information_ratio'

# ============================================
# QUINTILE/TERCILE LABELS
# ============================================
QUINTILE_LABELS = ['Q1 (Lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (Highest)']
TERCILE_LABELS = ['T1 (Sell)', 'T2 (Neutral)', 'T3 (Buy)']
DECILE_LABELS = [f'D{i+1}' for i in range(10)]

# ============================================
# DATE COLUMN
# ============================================
DATE = 'date'
TRADING_DATE = 'TradingDate'
