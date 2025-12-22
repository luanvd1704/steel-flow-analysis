"""
Cross-sectional Ranking Analysis Module
Ranks tickers based on financial metrics (1 = best, 17 = worst)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats


def load_financial_metrics(financial_file: str, tickers: List[str]) -> pd.DataFrame:
    """
    Load financial metrics from Excel file

    Args:
        financial_file: Path to bank_financials.xlsx
        tickers: List of tickers to load

    Returns:
        DataFrame with all tickers' metrics
    """
    all_data = []

    for ticker in tickers:
        try:
            df = pd.read_excel(financial_file, sheet_name=ticker)
            if 'ticker' not in df.columns:
                df['ticker'] = ticker
            all_data.append(df)
        except Exception as e:
            print(f"Warning: Could not load {ticker}: {e}")

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    # Create date column from year + quarter
    if 'year' in combined.columns and 'quarter' in combined.columns:
        combined['date'] = pd.to_datetime(
            combined['year'].astype(str) + '-' +
            (combined['quarter'] * 3).astype(str) + '-01'
        )

    return combined


def calculate_cross_sectional_ranks(
    df: pd.DataFrame,
    metric: str,
    direction: str = 'higher_is_better',
    optimal_range: Optional[Tuple[float, float]] = None
) -> pd.DataFrame:
    """
    Calculate cross-sectional ranks for a metric

    Args:
        df: DataFrame with ticker, date, and metric columns
        metric: Metric column name
        direction: 'higher_is_better', 'lower_is_better', or 'optimal_range'
        optimal_range: (min, max) for optimal range metrics

    Returns:
        DataFrame with rank columns added
    """
    result = df.copy()

    # Group by date and calculate ranks
    for date, group in result.groupby('date'):
        valid_data = group[group[metric].notna()].copy()

        if len(valid_data) == 0:
            continue

        if direction == 'higher_is_better':
            # Higher value = better rank (1 is best)
            ranks = valid_data[metric].rank(ascending=False, method='min')
        elif direction == 'lower_is_better':
            # Lower value = better rank (1 is best)
            ranks = valid_data[metric].rank(ascending=True, method='min')
        elif direction == 'optimal_range' and optimal_range:
            # Distance from optimal range
            min_opt, max_opt = optimal_range
            distances = valid_data[metric].apply(
                lambda x: 0 if min_opt <= x <= max_opt else min(abs(x - min_opt), abs(x - max_opt))
            )
            ranks = distances.rank(ascending=True, method='min')
        else:
            ranks = pd.Series(np.nan, index=valid_data.index)

        result.loc[valid_data.index, f'{metric}_rank'] = ranks

    return result


def merge_with_returns(
    ranked_df: pd.DataFrame,
    price_data: Dict[str, pd.DataFrame],
    forward_periods: List[int] = [5, 10, 20]
) -> pd.DataFrame:
    """
    Merge ranked data with forward returns

    Args:
        ranked_df: DataFrame with rankings
        price_data: Dict of ticker -> DataFrame with date and close price
        forward_periods: List of forward return periods (in days)

    Returns:
        DataFrame with forward returns added
    """
    result = ranked_df.copy()

    for ticker in ranked_df['ticker'].unique():
        if ticker not in price_data:
            continue

        ticker_data = ranked_df[ranked_df['ticker'] == ticker].copy()
        prices = price_data[ticker].set_index('date')['close']

        for period in forward_periods:
            forward_returns = []

            for idx, row in ticker_data.iterrows():
                date = row['date']
                if date not in prices.index:
                    forward_returns.append(np.nan)
                    continue

                # Find forward date
                future_dates = prices.index[prices.index > date]
                if len(future_dates) < period:
                    forward_returns.append(np.nan)
                    continue

                future_date = future_dates[min(period - 1, len(future_dates) - 1)]
                current_price = prices[date]
                future_price = prices[future_date]

                fwd_return = (future_price / current_price - 1) * 100
                forward_returns.append(fwd_return)

            result.loc[ticker_data.index, f'fwd_return_{period}d'] = forward_returns

    return result


def calculate_information_coefficient(
    df: pd.DataFrame,
    metric: str,
    return_col: str = 'fwd_return_20d',
    method: str = 'spearman'
) -> Dict[str, float]:
    """
    Calculate Information Coefficient (IC)

    Args:
        df: DataFrame with metric and return columns
        metric: Metric column name
        return_col: Forward return column
        method: 'spearman' or 'pearson'

    Returns:
        Dict with IC, t-stat, and p-value
    """
    valid_data = df[[metric, return_col]].dropna()

    if len(valid_data) < 10:
        return {'ic': np.nan, 't_stat': np.nan, 'p_value': np.nan, 'n': 0}

    if method == 'spearman':
        ic, p_value = stats.spearmanr(valid_data[metric], valid_data[return_col])
    else:
        ic, p_value = stats.pearsonr(valid_data[metric], valid_data[return_col])

    n = len(valid_data)
    # t-statistic for correlation
    t_stat = ic * np.sqrt((n - 2) / (1 - ic ** 2)) if abs(ic) < 1 else np.inf

    return {
        'ic': ic,
        't_stat': t_stat,
        'p_value': p_value,
        'n': n
    }


def get_current_rankings(
    df: pd.DataFrame,
    metric: str,
    latest_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Get current rankings (most recent date)

    Args:
        df: DataFrame with rankings
        metric: Metric name
        latest_date: Specific date (default: most recent)

    Returns:
        DataFrame with current rankings sorted by rank
    """
    if latest_date is None:
        latest_date = df['date'].max()

    current = df[df['date'] == latest_date].copy()

    rank_col = f'{metric}_rank'
    if rank_col not in current.columns:
        return current

    current = current.sort_values(rank_col)

    # Select relevant columns
    cols = ['ticker', metric, f'{metric}_rank']
    cols = [c for c in cols if c in current.columns]

    return current[cols].reset_index(drop=True)
