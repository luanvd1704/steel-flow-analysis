"""
Statistical testing module
Provides hypothesis testing and statistical analysis functions
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Optional
from scipy import stats
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import SIGNIFICANCE_LEVEL, MIN_SAMPLE_SIZE
from utils.constants import *


def ttest_two_groups(group1: pd.Series, group2: pd.Series,
                     equal_var: bool = False) -> Dict:
    """
    Perform two-sample t-test

    Args:
        group1: First group data
        group2: Second group data
        equal_var: Assume equal variance

    Returns:
        Dictionary with test results
    """
    g1_clean = group1.dropna()
    g2_clean = group2.dropna()

    n1, n2 = len(g1_clean), len(g2_clean)

    if n1 < 2 or n2 < 2:
        return {
            T_STAT: np.nan,
            P_VALUE: np.nan,
            'n1': n1,
            'n2': n2,
            'mean1': np.nan,
            'mean2': np.nan,
            'mean_diff': np.nan,
            'significant': False,
            'warning': 'Insufficient sample size'
        }

    t_stat, p_val = stats.ttest_ind(g1_clean, g2_clean, equal_var=equal_var)

    mean1, mean2 = g1_clean.mean(), g2_clean.mean()
    mean_diff = mean1 - mean2

    results = {
        T_STAT: t_stat,
        P_VALUE: p_val,
        'n1': n1,
        'n2': n2,
        'mean1': mean1,
        'mean2': mean2,
        'mean_diff': mean_diff,
        'significant': p_val < SIGNIFICANCE_LEVEL,
        'warning': None
    }

    if n1 < MIN_SAMPLE_SIZE or n2 < MIN_SAMPLE_SIZE:
        results['warning'] = f'Small sample size (n1={n1}, n2={n2})'

    return results


def anova_test(groups: List[pd.Series]) -> Dict:
    """
    Perform one-way ANOVA test

    Args:
        groups: List of group data

    Returns:
        Dictionary with test results
    """
    clean_groups = [g.dropna() for g in groups]
    group_sizes = [len(g) for g in clean_groups]

    if any(n < 2 for n in group_sizes):
        return {
            'f_stat': np.nan,
            P_VALUE: np.nan,
            'group_sizes': group_sizes,
            'group_means': [np.nan] * len(groups),
            'significant': False,
            'warning': 'Insufficient sample size in one or more groups'
        }

    f_stat, p_val = stats.f_oneway(*clean_groups)

    group_means = [g.mean() for g in clean_groups]

    return {
        'f_stat': f_stat,
        P_VALUE: p_val,
        'group_sizes': group_sizes,
        'group_means': group_means,
        'significant': p_val < SIGNIFICANCE_LEVEL,
        'warning': None
    }


def test_monotonicity(values: List[float], increasing: bool = True) -> Dict:
    """
    Test if a sequence of values shows monotonic trend

    Uses Spearman rank correlation

    Args:
        values: List of values (e.g., mean returns by quintile)
        increasing: True for increasing, False for decreasing

    Returns:
        Dictionary with test results
    """
    if len(values) < 3:
        return {
            'is_monotonic': False,
            'correlation': np.nan,
            P_VALUE: np.nan,
            'warning': 'Too few points for monotonicity test'
        }

    ranks = list(range(1, len(values) + 1))

    if not increasing:
        ranks = ranks[::-1]

    corr, p_val = stats.spearmanr(ranks, values)

    return {
        'is_monotonic': (corr > 0 and p_val < SIGNIFICANCE_LEVEL),
        'correlation': corr,
        P_VALUE: p_val,
        'warning': None
    }


def granger_causality_test(x: pd.Series, y: pd.Series, max_lag: int = 10) -> pd.DataFrame:
    """
    Simplified Granger causality test

    Tests if x helps predict y

    Args:
        x: Potential leading series
        y: Dependent series
        max_lag: Maximum lag to test

    Returns:
        DataFrame with results for each lag
    """
    results = []

    # Align series
    df = pd.DataFrame({'x': x, 'y': y}).dropna()

    if len(df) < max_lag + 20:
        return pd.DataFrame({
            'lag': [1],
            'correlation': [np.nan],
            P_VALUE: [np.nan],
            'warning': ['Insufficient data for Granger test']
        })

    for lag in range(1, max_lag + 1):
        # Create lagged x
        df_lag = df.copy()
        df_lag[f'x_lag{lag}'] = df_lag['x'].shift(lag)
        df_lag = df_lag.dropna()

        if len(df_lag) < 20:
            continue

        # Simple correlation test as proxy for Granger
        corr, p_val = stats.pearsonr(df_lag[f'x_lag{lag}'], df_lag['y'])

        results.append({
            'lag': lag,
            'correlation': corr,
            P_VALUE: p_val,
            'significant': p_val < SIGNIFICANCE_LEVEL
        })

    return pd.DataFrame(results)


def calculate_information_coefficient(signal: pd.Series,
                                      forward_return: pd.Series,
                                      method: str = 'pearson') -> Dict:
    """
    Calculate Information Coefficient (IC)

    IC measures correlation between signal and forward return

    Args:
        signal: Trading signal
        forward_return: Forward return
        method: 'pearson' or 'spearman'

    Returns:
        Dictionary with IC and test results
    """
    df = pd.DataFrame({'signal': signal, 'return': forward_return}).dropna()

    if len(df) < 2:
        return {
            'ic': np.nan,
            P_VALUE: np.nan,
            'n': 0,
            'significant': False,
            'warning': 'Insufficient data'
        }

    if method == 'pearson':
        ic, p_val = stats.pearsonr(df['signal'], df['return'])
    else:
        ic, p_val = stats.spearmanr(df['signal'], df['return'])

    return {
        'ic': ic,
        P_VALUE: p_val,
        'n': len(df),
        'significant': p_val < SIGNIFICANCE_LEVEL,
        'warning': None if len(df) >= MIN_SAMPLE_SIZE else f'Small sample size (n={len(df)})'
    }


def test_quintile_spread(quintile_returns: Dict[str, pd.Series]) -> Dict:
    """
    Test if Q5 - Q1 spread is significant

    Args:
        quintile_returns: Dictionary mapping quintile labels to return series

    Returns:
        Dictionary with test results
    """
    q1_key = [k for k in quintile_returns.keys() if 'Q1' in k or 'Lowest' in k][0]
    q5_key = [k for k in quintile_returns.keys() if 'Q5' in k or 'Highest' in k][0]

    q1_returns = quintile_returns[q1_key]
    q5_returns = quintile_returns[q5_key]

    # Test difference
    test_results = ttest_two_groups(q5_returns, q1_returns)

    # Add spread info
    test_results['spread'] = test_results['mean1'] - test_results['mean2']
    test_results['q1_label'] = q1_key
    test_results['q5_label'] = q5_key

    return test_results


def calculate_sharpe_ratio_significance(returns: pd.Series,
                                        periods_per_year: int = 252) -> Dict:
    """
    Calculate Sharpe ratio and test if significantly different from zero

    Args:
        returns: Return series
        periods_per_year: Number of periods per year

    Returns:
        Dictionary with Sharpe ratio and test
    """
    clean_returns = returns.dropna()

    if len(clean_returns) < 2:
        return {
            SHARPE: np.nan,
            T_STAT: np.nan,
            P_VALUE: np.nan,
            'significant': False
        }

    mean_return = clean_returns.mean() * periods_per_year
    std_return = clean_returns.std() * np.sqrt(periods_per_year)

    if std_return == 0:
        sharpe = np.nan
    else:
        sharpe = mean_return / std_return

    # T-test against zero
    t_stat, p_val = stats.ttest_1samp(clean_returns, 0)

    return {
        SHARPE: sharpe,
        T_STAT: t_stat,
        P_VALUE: p_val,
        'significant': p_val < SIGNIFICANCE_LEVEL
    }


if __name__ == "__main__":
    # Test statistical functions
    print("Testing statistical functions...")

    # Test t-test
    g1 = pd.Series(np.random.normal(0, 1, 100))
    g2 = pd.Series(np.random.normal(0.5, 1, 100))

    results = ttest_two_groups(g1, g2)
    print(f"\nT-test results:")
    print(f"  t-stat: {results[T_STAT]:.3f}")
    print(f"  p-value: {results[P_VALUE]:.3f}")
    print(f"  Significant: {results['significant']}")

    # Test monotonicity
    values = [0.01, 0.02, 0.03, 0.04, 0.05]
    mono_results = test_monotonicity(values, increasing=True)
    print(f"\nMonotonicity test:")
    print(f"  Correlation: {mono_results['correlation']:.3f}")
    print(f"  Is monotonic: {mono_results['is_monotonic']}")
