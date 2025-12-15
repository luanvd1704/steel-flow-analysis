"""
Q1: Foreign Lead/Lag Analysis
Analyzes if foreign investors predict future returns
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import FORWARD_RETURN_HORIZONS, ADV_WINDOW
from utils.constants import *
from utils.helpers import (
    calculate_excess_return, calculate_forward_returns,
    create_quintiles, perform_ttest
)
from analysis.statistics import ttest_two_groups, test_quintile_spread, calculate_information_coefficient


def prepare_lead_lag_data(df: pd.DataFrame,
                          horizons: List[int] = FORWARD_RETURN_HORIZONS) -> pd.DataFrame:
    """
    Prepare data for lead-lag analysis

    Args:
        df: DataFrame with price and trading data
        horizons: Forward return horizons

    Returns:
        DataFrame with forward returns and excess returns
    """
    df = df.copy()

    # Ensure we have excess returns
    if EXCESS_RETURN not in df.columns:
        if STOCK_RETURN in df.columns and MARKET_RETURN in df.columns:
            df[EXCESS_RETURN] = calculate_excess_return(
                df[STOCK_RETURN],
                df[MARKET_RETURN]
            )

    # Calculate forward returns
    if CLOSE in df.columns:
        fwd_returns = calculate_forward_returns(df[CLOSE], horizons)
        df = pd.concat([df, fwd_returns], axis=1)

        # Calculate forward excess returns
        for h in horizons:
            fwd_ret_col = f'fwd_return_{h}d'
            fwd_excess_col = f'fwd_excess_return_{h}d'

            if fwd_ret_col in df.columns:
                # Calculate forward market return
                if VNINDEX_CLOSE in df.columns:
                    fwd_market_ret = df[VNINDEX_CLOSE].pct_change(h).shift(-h)
                    df[fwd_excess_col] = df[fwd_ret_col] - fwd_market_ret
                else:
                    df[fwd_excess_col] = df[fwd_ret_col]

    return df


def create_quintiles_by_foreign_trading(df: pd.DataFrame,
                                        signal_col: str = FOREIGN_NET_BUY_VAL) -> pd.DataFrame:
    """
    Create quintiles based on foreign net buying

    Args:
        df: DataFrame with foreign trading data
        signal_col: Column to use for quintile assignment

    Returns:
        DataFrame with quintile column
    """
    df = df.copy()

    if signal_col in df.columns:
        df[QUINTILE] = create_quintiles(df[signal_col], labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])

    return df


def analyze_quintile_returns(df: pd.DataFrame,
                            horizon: int,
                            use_excess_return: bool = True) -> Dict:
    """
    Analyze forward returns by quintile

    Args:
        df: DataFrame with quintile assignments and forward returns
        horizon: Forward return horizon
        use_excess_return: Use excess return vs market return

    Returns:
        Dictionary with quintile analysis results
    """
    if use_excess_return:
        return_col = f'fwd_excess_return_{horizon}d'
    else:
        return_col = f'fwd_return_{horizon}d'

    if QUINTILE not in df.columns or return_col not in df.columns:
        return {
            'error': f'Missing required columns: {QUINTILE} or {return_col}'
        }

    # Calculate mean return by quintile
    quintile_stats = df.groupby(QUINTILE)[return_col].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('count', 'count'),
        ('median', 'median')
    ]).reset_index()

    # Test Q5 vs Q1
    q1_returns = df[df[QUINTILE] == 'Q1'][return_col]
    q5_returns = df[df[QUINTILE] == 'Q5'][return_col]

    spread_test = ttest_two_groups(q5_returns, q1_returns)

    results = {
        'horizon': horizon,
        'return_type': 'excess' if use_excess_return else 'total',
        'quintile_stats': quintile_stats,
        'q5_mean': quintile_stats[quintile_stats[QUINTILE] == 'Q5']['mean'].values[0],
        'q1_mean': quintile_stats[quintile_stats[QUINTILE] == 'Q1']['mean'].values[0],
        'spread': spread_test['mean_diff'],
        't_stat': spread_test[T_STAT],
        'p_value': spread_test[P_VALUE],
        'significant': spread_test['significant']
    }

    return results


def lead_lag_analysis_full(df: pd.DataFrame,
                           horizons: List[int] = FORWARD_RETURN_HORIZONS,
                           signal_col: str = FOREIGN_NET_BUY_VAL) -> Dict:
    """
    Complete lead-lag analysis for all horizons

    Args:
        df: DataFrame with trading and price data
        horizons: List of forward return horizons
        signal_col: Signal column for quintile creation

    Returns:
        Dictionary with results for all horizons
    """
    # Prepare data
    df = prepare_lead_lag_data(df, horizons)

    # Create quintiles
    df = create_quintiles_by_foreign_trading(df, signal_col)

    results = {}

    for horizon in horizons:
        # Analyze with excess returns
        results[f'T+{horizon}'] = analyze_quintile_returns(df, horizon, use_excess_return=True)

    # Calculate Information Coefficient for each horizon
    ic_results = {}
    for horizon in horizons:
        fwd_ret_col = f'fwd_excess_return_{horizon}d'
        if signal_col in df.columns and fwd_ret_col in df.columns:
            ic_results[f'T+{horizon}'] = calculate_information_coefficient(
                df[signal_col],
                df[fwd_ret_col]
            )

    results['ic_analysis'] = ic_results

    return results


def find_optimal_normalization_window(df: pd.DataFrame,
                                      horizon: int = 5,
                                      test_windows: List[int] = [5, 10, 20, 30, 60]) -> Dict:
    """
    Find optimal window for normalizing foreign trading signals

    Tests different rolling windows and finds which gives best IC

    Args:
        df: DataFrame with foreign trading data
        horizon: Forward return horizon to optimize for
        test_windows: List of window sizes to test

    Returns:
        Dictionary with results for each window
    """
    df = prepare_lead_lag_data(df, [horizon])

    fwd_ret_col = f'fwd_excess_return_{horizon}d'

    if FOREIGN_NET_BUY_VAL not in df.columns or fwd_ret_col not in df.columns:
        return {'error': 'Missing required data'}

    results = []

    for window in test_windows:
        # Normalize by rolling average
        rolling_avg = df[FOREIGN_NET_BUY_VAL].rolling(window=window, min_periods=window//2).mean()
        rolling_std = df[FOREIGN_NET_BUY_VAL].rolling(window=window, min_periods=window//2).std()

        normalized_signal = (df[FOREIGN_NET_BUY_VAL] - rolling_avg) / rolling_std.replace(0, np.nan)

        # Calculate IC
        ic_result = calculate_information_coefficient(normalized_signal, df[fwd_ret_col])

        results.append({
            'window': window,
            'ic': ic_result['ic'],
            'ic_abs': abs(ic_result['ic']),
            'p_value': ic_result[P_VALUE],
            'significant': ic_result['significant']
        })

    results_df = pd.DataFrame(results)

    # Find optimal window (highest absolute IC)
    if len(results_df) > 0:
        optimal_idx = results_df['ic_abs'].idxmax()
        optimal_window = results_df.loc[optimal_idx, 'window']
    else:
        optimal_window = ADV_WINDOW

    return {
        'results': results_df,
        'optimal_window': optimal_window,
        'horizon': horizon
    }


def analyze_by_regime(df: pd.DataFrame,
                     horizon: int = 5) -> Dict:
    """
    Analyze lead-lag by market regime (bull/bear)

    Args:
        df: DataFrame with regime classification
        horizon: Forward return horizon

    Returns:
        Dictionary with regime-specific results
    """
    if BULL_MARKET not in df.columns:
        return {'error': 'No regime classification available'}

    results = {}

    for regime_val, regime_name in [(1, 'Bull'), (0, 'Bear')]:
        regime_df = df[df[BULL_MARKET] == regime_val].copy()

        if len(regime_df) < 30:
            results[regime_name] = {'error': 'Insufficient data'}
            continue

        regime_results = lead_lag_analysis_full(regime_df, [horizon])

        results[regime_name] = regime_results.get(f'T+{horizon}', {})

    return results


if __name__ == "__main__":
    # Test lead-lag analysis
    from data.loader import merge_all_data

    print("Testing lead-lag analysis...")
    data = merge_all_data()

    ticker = 'HPG'
    print(f"\nAnalyzing {ticker}...")

    results = lead_lag_analysis_full(data[ticker])

    print(f"\n{'='*60}")
    print(f"LEAD-LAG ANALYSIS RESULTS FOR {ticker}")
    print(f"{'='*60}")

    for horizon_key, result in results.items():
        if horizon_key == 'ic_analysis':
            continue

        print(f"\n{horizon_key}:")
        print(f"  Q5 Mean: {result['q5_mean']:.4f}")
        print(f"  Q1 Mean: {result['q1_mean']:.4f}")
        print(f"  Spread: {result['spread']:.4f}")
        print(f"  T-stat: {result['t_stat']:.2f}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Significant: {result['significant']}")

    print(f"\nInformation Coefficients:")
    for horizon_key, ic_result in results['ic_analysis'].items():
        print(f"  {horizon_key}: IC={ic_result['ic']:.4f}, p={ic_result[P_VALUE]:.4f}")
