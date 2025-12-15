"""
Helper functions used across multiple modules
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import stats


def calculate_return(prices: pd.Series, periods: int = 1) -> pd.Series:
    """
    Calculate return over specified periods

    Args:
        prices: Price series
        periods: Number of periods for return calculation

    Returns:
        Return series
    """
    return prices.pct_change(periods)


def calculate_excess_return(stock_return: pd.Series, market_return: pd.Series) -> pd.Series:
    """
    Calculate excess return (stock return - market return)

    Args:
        stock_return: Stock return series
        market_return: Market return series

    Returns:
        Excess return series
    """
    return stock_return - market_return


def create_quintiles(series: pd.Series, labels: Optional[List[str]] = None) -> pd.Series:
    """
    Create quintiles from a series

    Args:
        series: Input series
        labels: Optional labels for quintiles

    Returns:
        Quintile assignments
    """
    if labels is None:
        labels = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']

    # Drop NaN values for binning
    series_clean = series.dropna()

    if len(series_clean) == 0:
        return pd.Series(index=series.index, dtype='category')

    try:
        result = pd.qcut(series_clean, q=5, labels=labels, duplicates='drop')
    except (ValueError, TypeError):
        # If duplicates='drop' causes label mismatch, use rank-based approach
        percentiles = series_clean.rank(pct=True)
        result = pd.cut(percentiles, bins=5, labels=labels, include_lowest=True)

    # Reindex to match original series (NaN values will be NaN in result)
    return result.reindex(series.index)


def create_terciles(series: pd.Series, labels: Optional[List[str]] = None) -> pd.Series:
    """
    Create terciles from a series

    Args:
        series: Input series
        labels: Optional labels for terciles

    Returns:
        Tercile assignments
    """
    if labels is None:
        labels = ['T1', 'T2', 'T3']

    # Drop NaN values for binning
    series_clean = series.dropna()

    if len(series_clean) == 0:
        return pd.Series(index=series.index, dtype='category')

    try:
        result = pd.qcut(series_clean, q=3, labels=labels, duplicates='drop')
    except (ValueError, TypeError):
        percentiles = series_clean.rank(pct=True)
        result = pd.cut(percentiles, bins=3, labels=labels, include_lowest=True)

    # Reindex to match original series
    return result.reindex(series.index)


def create_deciles(series: pd.Series, labels: Optional[List[str]] = None) -> pd.Series:
    """
    Create deciles from a series

    Args:
        series: Input series
        labels: Optional labels for deciles

    Returns:
        Decile assignments
    """
    if labels is None:
        labels = [f'D{i+1}' for i in range(10)]

    # Drop NaN values for binning
    series_clean = series.dropna()

    if len(series_clean) == 0:
        return pd.Series(index=series.index, dtype='category')

    try:
        result = pd.qcut(series_clean, q=10, labels=labels, duplicates='drop')
    except (ValueError, TypeError):
        percentiles = series_clean.rank(pct=True)
        result = pd.cut(percentiles, bins=10, labels=labels, include_lowest=True)

    # Reindex to match original series
    return result.reindex(series.index)


def calculate_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """
    Calculate rolling z-score

    Args:
        series: Input series
        window: Rolling window size

    Returns:
        Z-score series
    """
    rolling_mean = series.rolling(window=window, min_periods=window//2).mean()
    rolling_std = series.rolling(window=window, min_periods=window//2).std()

    return (series - rolling_mean) / rolling_std


def calculate_percentile(series: pd.Series, window: int = 756) -> pd.Series:
    """
    Calculate rolling percentile rank (0-100)

    Args:
        series: Input series
        window: Rolling window size

    Returns:
        Percentile series (0-100)
    """
    def percentile_rank(x):
        if len(x) < 2:
            return np.nan
        return stats.percentileofscore(x[:-1], x.iloc[-1])

    return series.rolling(window=window, min_periods=window//2).apply(percentile_rank, raw=False)


def calculate_forward_returns(prices: pd.Series, horizons: List[int]) -> pd.DataFrame:
    """
    Calculate forward returns for multiple horizons

    Args:
        prices: Price series
        horizons: List of forward periods

    Returns:
        DataFrame with forward returns for each horizon
    """
    fwd_returns = pd.DataFrame(index=prices.index)

    for h in horizons:
        fwd_returns[f'fwd_return_{h}d'] = prices.pct_change(h).shift(-h)

    return fwd_returns


def calculate_sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculate annualized Sharpe ratio

    Args:
        returns: Return series
        periods_per_year: Number of periods in a year (252 for daily)

    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return np.nan

    mean_return = returns.mean() * periods_per_year
    std_return = returns.std() * np.sqrt(periods_per_year)

    return mean_return / std_return


def calculate_information_coefficient(signal: pd.Series, forward_return: pd.Series) -> float:
    """
    Calculate Information Coefficient (IC) - correlation between signal and forward return

    Args:
        signal: Trading signal
        forward_return: Forward return

    Returns:
        IC (correlation coefficient)
    """
    valid_data = pd.DataFrame({'signal': signal, 'return': forward_return}).dropna()

    if len(valid_data) < 2:
        return np.nan

    return valid_data['signal'].corr(valid_data['return'])


def perform_ttest(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """
    Perform two-sample t-test

    Args:
        group1: First group
        group2: Second group

    Returns:
        Tuple of (t-statistic, p-value)
    """
    group1_clean = group1.dropna()
    group2_clean = group2.dropna()

    if len(group1_clean) < 2 or len(group2_clean) < 2:
        return np.nan, np.nan

    t_stat, p_val = stats.ttest_ind(group1_clean, group2_clean)

    return t_stat, p_val


def calculate_drawdown(equity_curve: pd.Series) -> pd.Series:
    """
    Calculate drawdown series

    Args:
        equity_curve: Equity curve series

    Returns:
        Drawdown series (as negative percentages)
    """
    cumulative_max = equity_curve.expanding().max()
    drawdown = (equity_curve - cumulative_max) / cumulative_max

    return drawdown


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown

    Args:
        equity_curve: Equity curve series

    Returns:
        Maximum drawdown (as negative percentage)
    """
    drawdown = calculate_drawdown(equity_curve)
    return drawdown.min()


def winsorize_series(series: pd.Series, lower_pct: float = 0.01, upper_pct: float = 0.99) -> pd.Series:
    """
    Winsorize series to handle outliers

    Args:
        series: Input series
        lower_pct: Lower percentile to clip
        upper_pct: Upper percentile to clip

    Returns:
        Winsorized series
    """
    lower_bound = series.quantile(lower_pct)
    upper_bound = series.quantile(upper_pct)

    return series.clip(lower=lower_bound, upper=upper_bound)


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage

    Args:
        value: Input value (e.g., 0.1 for 10%)
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """
    Format number with thousands separator

    Args:
        value: Input value
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"
