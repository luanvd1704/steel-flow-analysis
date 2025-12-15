"""
Q2: Self-Trading Signal Analysis
Analyzes profitability of proprietary trading signals
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import ADV_WINDOW, FORWARD_RETURN_HORIZONS
from utils.constants import *
from utils.helpers import calculate_forward_returns, create_terciles
from analysis.normalization import normalize_by_adv, normalize_by_gtgd
from analysis.statistics import calculate_information_coefficient, anova_test


def calculate_self_trading_signals(df: pd.DataFrame,
                                   window: int = ADV_WINDOW) -> pd.DataFrame:
    """
    Calculate self-trading signals using both normalization methods

    Args:
        df: DataFrame with self-trading data
        window: Window for ADV calculation

    Returns:
        DataFrame with signal columns
    """
    df = df.copy()

    # Method 1: ADV20
    if SELF_NET_BUY_VAL in df.columns and CLOSE in df.columns:
        df[SELF_SIGNAL_ADV20] = normalize_by_adv(
            df[SELF_NET_BUY_VAL],
            df[CLOSE],
            window=window
        )

    # Method 2: GTGD
    if (SELF_NET_BUY_VAL in df.columns and
        SELF_BUY_VAL in df.columns and
        SELF_SELL_VAL in df.columns):

        df[SELF_SIGNAL_GTGD] = normalize_by_gtgd(
            df[SELF_NET_BUY_VAL],
            df[SELF_BUY_VAL],
            df[SELF_SELL_VAL]
        )

    return df


def analyze_signal_terciles(df: pd.DataFrame,
                            signal_col: str,
                            horizon: int = 5) -> Dict:
    """
    Analyze forward returns by signal terciles

    Args:
        df: DataFrame with signal and return data
        signal_col: Signal column name
        horizon: Forward return horizon

    Returns:
        Dictionary with tercile analysis
    """
    df = df.copy()

    # Ensure forward returns exist
    if CLOSE in df.columns:
        fwd_returns = calculate_forward_returns(df[CLOSE], [horizon])
        df = pd.concat([df, fwd_returns], axis=1)

    fwd_ret_col = f'fwd_return_{horizon}d'

    if signal_col not in df.columns or fwd_ret_col not in df.columns:
        return {'error': 'Missing required columns'}

    # Create terciles
    valid_data = df[[signal_col, fwd_ret_col]].dropna()

    if len(valid_data) < 30:
        return {'error': 'Insufficient data', 'sample_size': len(valid_data)}

    valid_data[TERCILE] = create_terciles(
        valid_data[signal_col],
        labels=['T1 (Sell)', 'T2 (Neutral)', 'T3 (Buy)']
    )

    # Calculate statistics by tercile
    tercile_stats = valid_data.groupby(TERCILE)[fwd_ret_col].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('count', 'count'),
        ('median', 'median')
    ]).reset_index()

    # Test ANOVA
    tercile_groups = [valid_data[valid_data[TERCILE] == t][fwd_ret_col]
                     for t in tercile_stats[TERCILE]]
    anova_results = anova_test(tercile_groups)

    # Calculate IC
    ic_result = calculate_information_coefficient(
        valid_data[signal_col],
        valid_data[fwd_ret_col]
    )

    results = {
        'signal_method': signal_col,
        'horizon': horizon,
        'tercile_stats': tercile_stats,
        'anova': anova_results,
        'ic': ic_result,
        'sample_size': len(valid_data),
        'monotonicity': _check_monotonicity(tercile_stats['mean'].tolist())
    }

    return results


def _check_monotonicity(values: List[float]) -> bool:
    """Check if tercile returns are monotonically increasing"""
    if len(values) < 3:
        return False
    return values[2] > values[1] > values[0]


def compare_normalization_methods(df: pd.DataFrame,
                                  horizons: List[int] = [1, 3, 5, 10]) -> Dict:
    """
    Compare ADV20 vs GTGD normalization methods

    Args:
        df: DataFrame with self-trading data
        horizons: Forward return horizons to test

    Returns:
        Dictionary comparing both methods
    """
    # Calculate signals
    df = calculate_self_trading_signals(df)

    results = {
        'ADV20': {},
        'GTGD': {}
    }

    for method, signal_col in [('ADV20', SELF_SIGNAL_ADV20), ('GTGD', SELF_SIGNAL_GTGD)]:
        if signal_col not in df.columns:
            results[method] = {'error': f'{method} signal not available'}
            continue

        for horizon in horizons:
            analysis = analyze_signal_terciles(df, signal_col, horizon)
            results[method][f'T+{horizon}'] = analysis

    return results


def get_best_normalization_method(comparison_results: Dict) -> str:
    """
    Determine which normalization method is better based on IC

    Args:
        comparison_results: Results from compare_normalization_methods

    Returns:
        'ADV20' or 'GTGD'
    """
    adv20_ics = []
    gtgd_ics = []

    for method_results in comparison_results.get('ADV20', {}).values():
        if isinstance(method_results, dict) and 'ic' in method_results:
            adv20_ics.append(abs(method_results['ic'].get('ic', 0)))

    for method_results in comparison_results.get('GTGD', {}).values():
        if isinstance(method_results, dict) and 'ic' in method_results:
            gtgd_ics.append(abs(method_results['ic'].get('ic', 0)))

    adv20_avg = np.mean(adv20_ics) if adv20_ics else 0
    gtgd_avg = np.mean(gtgd_ics) if gtgd_ics else 0

    return 'ADV20' if adv20_avg > gtgd_avg else 'GTGD'


def check_data_availability(df: pd.DataFrame) -> Dict:
    """
    Check if self-trading data is available and sufficient

    Args:
        df: DataFrame

    Returns:
        Dictionary with availability info
    """
    has_self_data = SELF_NET_BUY_VAL in df.columns

    if not has_self_data:
        return {
            'available': False,
            'reason': 'No self-trading data columns'
        }

    self_data_points = df[SELF_NET_BUY_VAL].notna().sum()
    total_points = len(df)

    if self_data_points < 100:
        return {
            'available': False,
            'reason': f'Insufficient self-trading data: {self_data_points} points',
            'data_points': self_data_points
        }

    # Check date range
    valid_dates = df[df[SELF_NET_BUY_VAL].notna()][DATE]
    if len(valid_dates) > 0:
        start_date = valid_dates.min()
        end_date = valid_dates.max()
    else:
        start_date = None
        end_date = None

    return {
        'available': True,
        'data_points': self_data_points,
        'total_points': total_points,
        'coverage': self_data_points / total_points,
        'start_date': start_date,
        'end_date': end_date
    }


if __name__ == "__main__":
    # Test self-trading analysis
    from data.loader import merge_all_data

    print("Testing self-trading analysis...")
    data = merge_all_data()

    ticker = 'HPG'
    print(f"\nAnalyzing {ticker}...")

    df = data[ticker].copy()

    # Check availability
    availability = check_data_availability(df)
    print(f"\nData Availability:")
    print(f"  Available: {availability['available']}")
    if availability['available']:
        print(f"  Data Points: {availability['data_points']}")
        print(f"  Coverage: {availability['coverage']:.1%}")
        print(f"  Date Range: {availability['start_date']} to {availability['end_date']}")

        # Compare methods
        comparison = compare_normalization_methods(df)

        print(f"\n{'='*60}")
        print(f"SELF-TRADING ANALYSIS RESULTS FOR {ticker}")
        print(f"{'='*60}")

        for method in ['ADV20', 'GTGD']:
            print(f"\n{method} Method:")
            for horizon_key, result in comparison[method].items():
                if 'error' not in result:
                    print(f"  {horizon_key}:")
                    print(f"    IC: {result['ic']['ic']:.4f} (p={result['ic'][P_VALUE]:.4f})")
                    print(f"    Monotonic: {result['monotonicity']}")
                    print(f"    Sample Size: {result['sample_size']}")

        best = get_best_normalization_method(comparison)
        print(f"\nBest Method: {best}")
    else:
        print(f"  Reason: {availability['reason']}")
