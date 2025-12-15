"""
Q5: Composite Scoring
Combines signals for alpha generation
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import *
from utils.helpers import calculate_zscore, create_quintiles, calculate_sharpe_ratio
from analysis.normalization import normalize_all_signals


def build_composite_score(df: pd.DataFrame,
                          use_self_trading: bool = True) -> pd.DataFrame:
    """
    Build composite score

    Formula:
    Composite = z(Foreign) + z(Self) - percentile(PE/PB)

    Args:
        df: DataFrame with all signals
        use_self_trading: Include self-trading in score

    Returns:
        DataFrame with composite_score column
    """
    df = df.copy()

    # Ensure all signals are calculated
    df = normalize_all_signals(df)

    # Start with foreign z-score
    if FOREIGN_ZSCORE in df.columns:
        composite = df[FOREIGN_ZSCORE].fillna(0)
    else:
        composite = pd.Series(0, index=df.index)

    # Add self z-score if requested
    if use_self_trading and SELF_ZSCORE in df.columns:
        composite += df[SELF_ZSCORE].fillna(0)

    # Subtract valuation percentile (lower percentile = cheaper = better)
    # Use average of PE and PB percentiles, normalized to 0-1 scale
    val_score = 0
    val_count = 0

    if PE_PERCENTILE in df.columns:
        val_score += df[PE_PERCENTILE].fillna(50) / 100  # 0-1 scale
        val_count += 1

    if PB_PERCENTILE in df.columns:
        val_score += df[PB_PERCENTILE].fillna(50) / 100
        val_count += 1

    if val_count > 0:
        composite -= (val_score / val_count)

    df[COMPOSITE_SCORE] = composite

    return df


def quintile_backtest(df: pd.DataFrame,
                     horizon: int = 5) -> Dict:
    """
    Backtest quintile strategy

    Args:
        df: DataFrame with composite scores
        horizon: Rebalance/holding period

    Returns:
        Dictionary with backtest results
    """
    df = df.copy()

    if COMPOSITE_SCORE not in df.columns:
        return {'error': 'No composite score'}

    # Create quintiles
    df[QUINTILE] = create_quintiles(df[COMPOSITE_SCORE])

    # Calculate forward returns
    if CLOSE in df.columns:
        df[f'fwd_return_{horizon}d'] = df[CLOSE].pct_change(horizon).shift(-horizon)

    fwd_ret_col = f'fwd_return_{horizon}d'

    if fwd_ret_col not in df.columns:
        return {'error': 'Cannot calculate returns'}

    # Calculate returns by quintile
    quintile_returns = df.groupby(QUINTILE)[fwd_ret_col].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('count', 'count')
    ]).reset_index()

    # Calculate strategy returns (Long Q5, Short Q1)
    q5_returns = df[df[QUINTILE] == 'Q5'][fwd_ret_col].dropna()
    q1_returns = df[df[QUINTILE] == 'Q1'][fwd_ret_col].dropna()

    # Strategy metrics (difference of means for long-short strategy)
    strategy_returns_mean = q5_returns.mean() - q1_returns.mean()

    # For volatility, use pooled standard deviation
    # Assuming equal allocation to long and short
    q5_std = q5_returns.std()
    q1_std = q1_returns.std()
    strategy_returns_std = ((q5_std**2 + q1_std**2) ** 0.5) / (2 ** 0.5)

    # Sharpe ratio from strategy mean and std
    if strategy_returns_std > 0:
        periods_per_year = 252 // horizon
        sharpe = (strategy_returns_mean * periods_per_year) / (strategy_returns_std * (periods_per_year ** 0.5))
    else:
        sharpe = np.nan

    results = {
        'quintile_returns': quintile_returns,
        'strategy_returns_mean': strategy_returns_mean,
        'strategy_returns_std': strategy_returns_std,
        'sharpe_ratio': sharpe,
        'sample_size': len(df.dropna(subset=[COMPOSITE_SCORE, fwd_ret_col]))
    }

    return results


def capm_analysis(stock_returns: pd.Series,
                 market_returns: pd.Series) -> Dict:
    """
    Simple CAPM analysis

    Args:
        stock_returns: Strategy returns
        market_returns: Market returns

    Returns:
        Dictionary with alpha, beta, etc.
    """
    df = pd.DataFrame({
        'stock': stock_returns,
        'market': market_returns
    }).dropna()

    if len(df) < 10:
        return {'error': 'Insufficient data'}

    # Calculate beta
    covariance = df['stock'].cov(df['market'])
    market_var = df['market'].var()

    beta = covariance / market_var if market_var != 0 else 0

    # Calculate alpha
    mean_stock = df['stock'].mean()
    mean_market = df['market'].mean()

    alpha = mean_stock - beta * mean_market

    # Annualize
    periods_per_year = 252
    alpha_annual = alpha * periods_per_year
    mean_stock_annual = mean_stock * periods_per_year

    return {
        ALPHA: alpha_annual,
        BETA: beta,
        'mean_return': mean_stock_annual,
        'sample_size': len(df)
    }


if __name__ == "__main__":
    # Test composite scoring
    from data.loader import merge_all_data

    print("Testing composite scoring...")
    data = merge_all_data()

    ticker = 'HPG'
    print(f"\nAnalyzing {ticker}...")

    df = data[ticker].copy()

    # Build composite score
    df = build_composite_score(df, use_self_trading=True)

    print(f"\nComposite score stats:")
    print(df[COMPOSITE_SCORE].describe())

    # Backtest
    backtest = quintile_backtest(df, horizon=5)

    if 'error' not in backtest:
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS FOR {ticker}")
        print(f"{'='*60}")

        print(f"\nQuintile Returns:")
        print(backtest['quintile_returns'])

        print(f"\nStrategy Performance (Q5-Q1):")
        print(f"  Mean Return: {backtest['strategy_returns_mean']:.4f}")
        print(f"  Std Dev: {backtest['strategy_returns_std']:.4f}")
        print(f"  Sharpe Ratio: {backtest['sharpe_ratio']:.2f}")
        print(f"  Sample Size: {backtest['sample_size']}")
