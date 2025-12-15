"""
Q3: Foreign vs Self Conflicts Analysis
Analyzes who leads when foreign and self-trading disagree
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.constants import *
from utils.helpers import calculate_forward_returns
from analysis.statistics import granger_causality_test


def create_conflict_states(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify each day into conflict states

    States:
    1. Both Buy
    2. Foreign Buy, Self Sell
    3. Foreign Sell, Self Buy
    4. Both Sell

    Args:
        df: DataFrame with foreign and self trading data

    Returns:
        DataFrame with conflict_state column
    """
    df = df.copy()

    if FOREIGN_NET_BUY_VAL not in df.columns or SELF_NET_BUY_VAL not in df.columns:
        return df

    def classify_state(row):
        foreign = row[FOREIGN_NET_BUY_VAL]
        self_val = row[SELF_NET_BUY_VAL]

        if pd.isna(foreign) or pd.isna(self_val):
            return None

        if foreign > 0 and self_val > 0:
            return BOTH_BUY
        elif foreign > 0 and self_val < 0:
            return FOREIGN_BUY_SELF_SELL
        elif foreign < 0 and self_val > 0:
            return FOREIGN_SELL_SELF_BUY
        else:  # both < 0
            return BOTH_SELL

    df[CONFLICT_STATE] = df.apply(classify_state, axis=1)

    return df


def analyze_conflict_returns(df: pd.DataFrame,
                             horizons: List[int] = [5, 10]) -> Dict:
    """
    Analyze forward returns by conflict state

    Args:
        df: DataFrame with conflict states
        horizons: Forward return horizons

    Returns:
        Dictionary with conflict analysis results
    """
    df = create_conflict_states(df)

    # Ensure forward returns
    if CLOSE in df.columns:
        fwd_returns = calculate_forward_returns(df[CLOSE], horizons)
        df = pd.concat([df, fwd_returns], axis=1)

    results = {}

    for horizon in horizons:
        fwd_ret_col = f'fwd_return_{horizon}d'

        if CONFLICT_STATE not in df.columns or fwd_ret_col not in df.columns:
            results[f'T+{horizon}'] = {'error': 'Missing required columns'}
            continue

        # Calculate mean return by state
        state_returns = df.groupby(CONFLICT_STATE)[fwd_ret_col].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('count', 'count')
        ]).reset_index()

        results[f'T+{horizon}'] = {
            'state_returns': state_returns,
            'sample_size': len(df[df[CONFLICT_STATE].notna()])
        }

    return results


def identify_leader(df: pd.DataFrame, max_lag: int = 10) -> Dict:
    """
    Use Granger causality to identify who leads

    Args:
        df: DataFrame with foreign and self data
        max_lag: Maximum lag to test

    Returns:
        Dictionary with leadership results
    """
    if FOREIGN_NET_BUY_VAL not in df.columns or SELF_NET_BUY_VAL not in df.columns:
        return {'error': 'Missing trading data'}

    # Test Foreign → Self
    foreign_leads_self = granger_causality_test(
        df[FOREIGN_NET_BUY_VAL],
        df[SELF_NET_BUY_VAL],
        max_lag=max_lag
    )

    # Test Self → Foreign
    self_leads_foreign = granger_causality_test(
        df[SELF_NET_BUY_VAL],
        df[FOREIGN_NET_BUY_VAL],
        max_lag=max_lag
    )

    return {
        'foreign_leads_self': foreign_leads_self,
        'self_leads_foreign': self_leads_foreign
    }


def conflict_analysis_by_regime(df: pd.DataFrame,
                                horizon: int = 5) -> Dict:
    """
    Analyze conflicts separately for bull and bear markets

    Args:
        df: DataFrame with regime classification
        horizon: Forward return horizon

    Returns:
        Dictionary with regime-specific results
    """
    if BULL_MARKET not in df.columns:
        return {'error': 'No regime classification'}

    results = {}

    for regime_val, regime_name in [(1, 'Bull'), (0, 'Bear')]:
        regime_df = df[df[BULL_MARKET] == regime_val].copy()

        if len(regime_df) < 30:
            results[regime_name] = {'error': 'Insufficient data'}
            continue

        conflict_results = analyze_conflict_returns(regime_df, [horizon])

        results[regime_name] = conflict_results.get(f'T+{horizon}', {})

    return results


if __name__ == "__main__":
    # Test conflict analysis
    from data.loader import merge_all_data

    print("Testing conflict analysis...")
    data = merge_all_data()

    ticker = 'HPG'
    print(f"\nAnalyzing {ticker}...")

    df = data[ticker].copy()

    # Analyze conflicts
    results = analyze_conflict_returns(df)

    print(f"\n{'='*60}")
    print(f"CONFLICT ANALYSIS RESULTS FOR {ticker}")
    print(f"{'='*60}")

    for horizon_key, result in results.items():
        if 'error' not in result:
            print(f"\n{horizon_key}:")
            print(result['state_returns'])

    # Leadership test
    leadership = identify_leader(df)
    print(f"\nLeadership Analysis:")
    print("Foreign → Self:")
    print(leadership['foreign_leads_self'].head())
    print("\nSelf → Foreign:")
    print(leadership['self_leads_foreign'].head())
