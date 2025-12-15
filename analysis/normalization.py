"""
Normalization module
Provides various normalization methods for trading signals
"""
import pandas as pd
import numpy as np
from typing import Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import ADV_WINDOW, ZSCORE_WINDOW, PERCENTILE_WINDOW
from utils.constants import *
from utils.helpers import calculate_zscore, calculate_percentile


def normalize_by_adv(net_buy_value: pd.Series,
                     close: pd.Series,
                     window: int = ADV_WINDOW) -> pd.Series:
    """
    Normalize net buy value by Average Daily Volume (ADV)

    Formula: Net Buy Value / (Average Daily Volume * Average Price)

    Args:
        net_buy_value: Net buying value series
        close: Closing price series
        window: Rolling window for average calculation

    Returns:
        Normalized signal series
    """
    # Estimate volume from value
    volume = net_buy_value / close

    # Calculate rolling average volume
    avg_volume = volume.abs().rolling(window=window, min_periods=window//2).mean()

    # Normalize
    normalized = volume / avg_volume

    return normalized


def normalize_by_gtgd(net_buy_value: pd.Series,
                      buy_value: pd.Series,
                      sell_value: pd.Series) -> pd.Series:
    """
    Normalize net buy by GTGD (Giá trị giao dịch - Total trading value)

    Formula: Net Buy Value / (Buy Value + Sell Value)

    Args:
        net_buy_value: Net buying value
        buy_value: Total buy value
        sell_value: Total sell value

    Returns:
        Normalized signal (-1 to 1)
    """
    total_value = buy_value + sell_value

    # Avoid division by zero
    normalized = net_buy_value / total_value.replace(0, np.nan)

    return normalized


def calculate_foreign_signals(df: pd.DataFrame, window: int = ADV_WINDOW) -> pd.DataFrame:
    """
    Calculate normalized foreign trading signals

    Args:
        df: DataFrame with foreign trading data
        window: Window for ADV calculation

    Returns:
        DataFrame with added signal columns
    """
    df = df.copy()

    if FOREIGN_NET_BUY_VAL in df.columns and CLOSE in df.columns:
        df[FOREIGN_SIGNAL_ADV20] = normalize_by_adv(
            df[FOREIGN_NET_BUY_VAL],
            df[CLOSE],
            window=window
        )

        # Also calculate z-score for composite scoring
        df[FOREIGN_ZSCORE] = calculate_zscore(
            df[FOREIGN_NET_BUY_VAL],
            window=ZSCORE_WINDOW
        )

    return df


def calculate_self_signals(df: pd.DataFrame,
                          window: int = ADV_WINDOW) -> pd.DataFrame:
    """
    Calculate normalized self-trading signals using both methods

    Args:
        df: DataFrame with self-trading data
        window: Window for ADV calculation

    Returns:
        DataFrame with added signal columns
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

    # Also calculate z-score for composite scoring
    if SELF_NET_BUY_VAL in df.columns:
        df[SELF_ZSCORE] = calculate_zscore(
            df[SELF_NET_BUY_VAL],
            window=ZSCORE_WINDOW
        )

    return df


def calculate_valuation_percentiles(df: pd.DataFrame,
                                    window: int = PERCENTILE_WINDOW) -> pd.DataFrame:
    """
    Calculate rolling percentiles for valuation metrics

    Args:
        df: DataFrame with valuation data
        window: Rolling window (3 years = 756 trading days)

    Returns:
        DataFrame with percentile columns
    """
    df = df.copy()

    if PE in df.columns:
        df[PE_PERCENTILE] = calculate_percentile(df[PE], window=window)

    if PB in df.columns:
        df[PB_PERCENTILE] = calculate_percentile(df[PB], window=window)

    if PCFS in df.columns:
        df[PCFS_PERCENTILE] = calculate_percentile(df[PCFS], window=window)

    return df


def normalize_all_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all normalization methods to a DataFrame

    Args:
        df: Merged DataFrame with all data

    Returns:
        DataFrame with all normalized signals
    """
    df = df.copy()

    # Foreign signals
    df = calculate_foreign_signals(df)

    # Self-trading signals
    df = calculate_self_signals(df)

    # Valuation percentiles
    df = calculate_valuation_percentiles(df)

    return df


if __name__ == "__main__":
    # Test normalization
    from data.loader import merge_all_data

    print("Testing normalization...")
    data = merge_all_data()

    for ticker, df in data.items():
        print(f"\nNormalizing {ticker}...")
        normalized_df = normalize_all_signals(df)

        print(f"Added columns:")
        new_cols = [col for col in normalized_df.columns if col not in df.columns]
        for col in new_cols:
            non_na = normalized_df[col].notna().sum()
            print(f"  - {col}: {non_na} non-NA values")
