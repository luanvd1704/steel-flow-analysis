"""
Q4: Valuation Analysis
Analyzes relationship between valuation percentiles and forward returns
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import PERCENTILE_WINDOW, FORWARD_RETURN_HORIZONS
from utils.constants import *
from utils.helpers import calculate_percentile, calculate_forward_returns, create_deciles
from analysis.statistics import test_monotonicity, anova_test


def calculate_valuation_percentiles(df: pd.DataFrame,
                                    window: int = PERCENTILE_WINDOW) -> pd.DataFrame:
    """
    Calculate rolling percentiles for valuation metrics

    Args:
        df: DataFrame with valuation data
        window: Rolling window (default: 756 days = 3 years)

    Returns:
        DataFrame with percentile columns added
    """
    df = df.copy()

    if PE in df.columns:
        df[PE_PERCENTILE] = calculate_percentile(df[PE], window=window)

    if PB in df.columns:
        df[PB_PERCENTILE] = calculate_percentile(df[PB], window=window)

    if PCFS in df.columns:
        df[PCFS_PERCENTILE] = calculate_percentile(df[PCFS], window=window)

    return df


def analyze_percentile_returns(df: pd.DataFrame,
                               percentile_col: str,
                               horizon: int = 30) -> Dict:
    """
    Analyze forward returns by valuation percentile deciles

    Args:
        df: DataFrame with percentiles and returns
        percentile_col: Percentile column to analyze (PE_PERCENTILE, PB_PERCENTILE)
        horizon: Forward return horizon in days

    Returns:
        Dictionary with analysis results
    """
    # Prepare data
    df = df.copy()

    # Ensure forward returns exist
    if CLOSE in df.columns:
        fwd_returns = calculate_forward_returns(df[CLOSE], [horizon])
        df = pd.concat([df, fwd_returns], axis=1)

    fwd_ret_col = f'fwd_return_{horizon}d'

    if percentile_col not in df.columns or fwd_ret_col not in df.columns:
        return {'error': f'Missing required columns'}

    # Create deciles based on percentile
    valid_data = df[[percentile_col, fwd_ret_col]].dropna()

    if len(valid_data) < 100:
        return {'error': 'Insufficient data'}

    # Create decile labels
    valid_data[DECILE] = create_deciles(valid_data[percentile_col])

    # Calculate statistics by decile
    decile_stats = valid_data.groupby(DECILE)[fwd_ret_col].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('count', 'count'),
        ('median', 'median')
    ]).reset_index()

    # Test monotonicity (expecting negative relationship: low percentile → high return)
    mean_returns = decile_stats['mean'].tolist()
    monotonicity = test_monotonicity(mean_returns, increasing=False)

    # Test ANOVA
    decile_groups = [valid_data[valid_data[DECILE] == d][fwd_ret_col] for d in decile_stats[DECILE]]
    anova_results = anova_test(decile_groups)

    # Identify cheap (low percentile) and expensive (high percentile) zones
    cheap_zone = valid_data[valid_data[percentile_col] <= 20][fwd_ret_col].mean()
    expensive_zone = valid_data[valid_data[percentile_col] >= 80][fwd_ret_col].mean()

    results = {
        'percentile_metric': percentile_col,
        'horizon': horizon,
        'decile_stats': decile_stats,
        'monotonicity': monotonicity,
        'anova': anova_results,
        'cheap_zone_return': cheap_zone,
        'expensive_zone_return': expensive_zone,
        'cheap_expensive_spread': cheap_zone - expensive_zone,
        'sample_size': len(valid_data)
    }

    return results


def identify_valuation_zones(df: pd.DataFrame,
                             percentile_col: str = PE_PERCENTILE) -> pd.DataFrame:
    """
    Classify current valuation into zones

    Args:
        df: DataFrame with percentile data
        percentile_col: Percentile column

    Returns:
        DataFrame with zone classification
    """
    df = df.copy()

    if percentile_col not in df.columns:
        return df

    def classify_zone(percentile):
        if pd.isna(percentile):
            return 'Unknown'
        elif percentile <= 20:
            return 'Very Cheap'
        elif percentile <= 40:
            return 'Cheap'
        elif percentile <= 60:
            return 'Fair'
        elif percentile <= 80:
            return 'Expensive'
        else:
            return 'Very Expensive'

    zone_col = percentile_col.replace('_percentile', '_zone')
    df[zone_col] = df[percentile_col].apply(classify_zone)

    return df


def valuation_summary(df: pd.DataFrame,
                     metrics: List[str] = [PE, PB]) -> Dict:
    """
    Get current valuation summary

    Args:
        df: DataFrame with valuation data
        metrics: List of valuation metrics

    Returns:
        Dictionary with current valuation info
    """
    if len(df) == 0:
        return {'error': 'No data'}

    latest = df.iloc[-1]

    summary = {
        'date': latest.get(DATE),
        'valuations': {},
        'percentiles': {},
        'zones': {}
    }

    for metric in metrics:
        if metric in df.columns:
            summary['valuations'][metric] = latest.get(metric)

        percentile_col = f'{metric}_percentile'
        if percentile_col in df.columns:
            summary['percentiles'][metric] = latest.get(percentile_col)

        zone_col = f'{metric}_zone'
        if zone_col in df.columns:
            summary['zones'][metric] = latest.get(zone_col)

    return summary


def compare_valuation_metrics(df: pd.DataFrame,
                              horizon: int = 30) -> Dict:
    """
    Compare predictive power of different valuation metrics

    Args:
        df: DataFrame with all valuation data
        horizon: Forward return horizon

    Returns:
        Dictionary comparing PE, PB, PCFS
    """
    results = {}

    for metric in [PE, PB, PCFS]:
        percentile_col = f'{metric}_percentile'

        if percentile_col in df.columns:
            analysis = analyze_percentile_returns(df, percentile_col, horizon)

            if 'error' not in analysis:
                results[metric] = {
                    'monotonicity_correlation': analysis['monotonicity']['correlation'],
                    'monotonicity_pvalue': analysis['monotonicity'][P_VALUE],
                    'cheap_expensive_spread': analysis['cheap_expensive_spread'],
                    'anova_pvalue': analysis['anova'][P_VALUE]
                }

    return results


def predict_forward_return(df: pd.DataFrame,
                          current_percentile: float,
                          percentile_col: str = PE_PERCENTILE,
                          horizon: int = 30) -> Dict:
    """
    Predict expected forward return based on current percentile

    Args:
        df: Historical DataFrame
        current_percentile: Current percentile value
        percentile_col: Which percentile to use
        horizon: Forward return horizon

    Returns:
        Dictionary with prediction
    """
    # Get historical relationship
    analysis = analyze_percentile_returns(df, percentile_col, horizon)

    if 'error' in analysis:
        return analysis

    # Find which decile current percentile falls into
    decile_num = int(current_percentile / 10) + 1
    if decile_num > 10:
        decile_num = 10

    decile_label = f'D{decile_num}'

    # Get expected return for that decile
    decile_stats = analysis['decile_stats']
    matching_decile = decile_stats[decile_stats[DECILE] == decile_label]

    if len(matching_decile) == 0:
        return {'error': 'No historical data for this percentile range'}

    expected_return = matching_decile['mean'].values[0]
    std_dev = matching_decile['std'].values[0]
    sample_size = matching_decile['count'].values[0]

    return {
        'current_percentile': current_percentile,
        'decile': decile_label,
        'expected_return': expected_return,
        'std_dev': std_dev,
        'sample_size': sample_size,
        'confidence_low': expected_return - 1.96 * std_dev / np.sqrt(sample_size),
        'confidence_high': expected_return + 1.96 * std_dev / np.sqrt(sample_size)
    }


if __name__ == "__main__":
    # Test valuation analysis
    from data.loader import merge_all_data

    print("Testing valuation analysis...")
    data = merge_all_data()

    ticker = 'HPG'
    print(f"\nAnalyzing {ticker}...")

    df = data[ticker].copy()

    # Calculate percentiles
    df = calculate_valuation_percentiles(df)

    # Analyze PE percentile
    results = analyze_percentile_returns(df, PE_PERCENTILE, horizon=30)

    print(f"\n{'='*60}")
    print(f"VALUATION ANALYSIS RESULTS FOR {ticker}")
    print(f"{'='*60}")

    if 'error' not in results:
        print(f"\nDecile Analysis (30-day forward returns):")
        print(results['decile_stats'])

        print(f"\nMonotonicity Test:")
        print(f"  Correlation: {results['monotonicity']['correlation']:.4f}")
        print(f"  P-value: {results['monotonicity'][P_VALUE]:.4f}")
        print(f"  Is Monotonic (decreasing): {results['monotonicity']['is_monotonic']}")

        print(f"\nZone Analysis:")
        print(f"  Cheap Zone (0-20%): {results['cheap_zone_return']:.4f}")
        print(f"  Expensive Zone (80-100%): {results['expensive_zone_return']:.4f}")
        print(f"  Spread: {results['cheap_expensive_spread']:.4f}")

        # Get current valuation
        summary = valuation_summary(df)
        print(f"\nCurrent Valuation:")
        print(f"  Date: {summary['date']}")
        print(f"  PE: {summary['valuations'].get(PE, 'N/A')}")
        print(f"  PE Percentile: {summary['percentiles'].get(PE, 'N/A'):.1f}%")
