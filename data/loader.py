"""
Data loader module
Loads and merges data from Excel files
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import (
    TICKERS, FOREIGN_TRADING_FILE, SELF_TRADING_FILE,
    VALUATION_FILE, VNINDEX_FILE, MA_WINDOW_REGIME
)
from utils.constants import *
from utils.date_utils import standardize_date_column


def load_foreign_trading() -> Dict[str, pd.DataFrame]:
    """
    Load foreign trading data from Excel

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    if not os.path.exists(FOREIGN_TRADING_FILE):
        raise FileNotFoundError(f"Foreign trading file not found: {FOREIGN_TRADING_FILE}")

    # Read Excel file with all sheets
    excel_file = pd.ExcelFile(FOREIGN_TRADING_FILE)

    data_dict = {}

    for ticker in TICKERS:
        if ticker in excel_file.sheet_names:
            df = pd.read_excel(FOREIGN_TRADING_FILE, sheet_name=ticker)

            # Column mapping from Vietnamese to English
            column_map = {
                'Ngay': DATE,
                'ngay': DATE,
                'KLGDRong': FOREIGN_NET_BUY_VOL,
                'klgdrong': FOREIGN_NET_BUY_VOL,
                'GTDGRong': FOREIGN_NET_BUY_VAL,
                'gtdgrong': FOREIGN_NET_BUY_VAL,
                'Close': CLOSE,
                'close': CLOSE,
                'TradingDate': DATE,
                'tradingdate': DATE,
                'date': DATE,
                'Date': DATE
            }

            df = df.rename(columns=column_map)

            # Check if date column exists
            if DATE not in df.columns:
                raise ValueError(f"No date column found for {ticker}. Available columns: {list(df.columns)}")

            df = standardize_date_column(df, DATE)

            # Ensure required columns exist
            required_cols = [FOREIGN_NET_BUY_VOL, FOREIGN_NET_BUY_VAL, CLOSE]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"Warning: Missing columns in {ticker} foreign trading: {missing_cols}")

            # Select only needed columns
            cols_to_keep = [DATE] + [col for col in [FOREIGN_NET_BUY_VOL, FOREIGN_NET_BUY_VAL, CLOSE] if col in df.columns]
            df = df[cols_to_keep]

            # Sort by date
            df = df.sort_values(DATE).reset_index(drop=True)

            data_dict[ticker] = df
        else:
            print(f"Warning: {ticker} sheet not found in foreign trading file")

    return data_dict


def load_self_trading() -> Dict[str, pd.DataFrame]:
    """
    Load self-trading (proprietary) data from Excel

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    if not os.path.exists(SELF_TRADING_FILE):
        raise FileNotFoundError(f"Self-trading file not found: {SELF_TRADING_FILE}")

    excel_file = pd.ExcelFile(SELF_TRADING_FILE)

    data_dict = {}

    for ticker in TICKERS:
        if ticker in excel_file.sheet_names:
            df = pd.read_excel(SELF_TRADING_FILE, sheet_name=ticker)

            # Column mapping
            column_map = {
                'Date': DATE,
                'date': DATE,
                'KLcpMua': 'self_buy_vol',
                'klcpmua': 'self_buy_vol',
                'KlcpBan': 'self_sell_vol',
                'klcpban': 'self_sell_vol',
                'GtMua': SELF_BUY_VAL,
                'gtmua': SELF_BUY_VAL,
                'GtBan': SELF_SELL_VAL,
                'gtban': SELF_SELL_VAL,
                'Close': CLOSE,
                'close': CLOSE
            }

            df = df.rename(columns=column_map)

            if DATE not in df.columns:
                raise ValueError(f"No date column found for {ticker}")

            df = standardize_date_column(df, DATE)

            # Calculate net values
            if SELF_BUY_VAL in df.columns and SELF_SELL_VAL in df.columns:
                df[SELF_NET_BUY_VAL] = df[SELF_BUY_VAL] - df[SELF_SELL_VAL]

            if 'self_buy_vol' in df.columns and 'self_sell_vol' in df.columns:
                df[SELF_NET_BUY_VOL] = df['self_buy_vol'] - df['self_sell_vol']

            # Select only needed columns
            cols_to_keep = [DATE]
            for col in [SELF_NET_BUY_VOL, SELF_NET_BUY_VAL, SELF_BUY_VAL, SELF_SELL_VAL]:
                if col in df.columns:
                    cols_to_keep.append(col)

            df = df[cols_to_keep]

            # Sort by date
            df = df.sort_values(DATE).reset_index(drop=True)

            data_dict[ticker] = df
        else:
            print(f"Warning: {ticker} sheet not found in self-trading file")

    return data_dict


def load_valuation() -> Dict[str, pd.DataFrame]:
    """
    Load valuation data (PE, PB, PCFS) from Excel

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    if not os.path.exists(VALUATION_FILE):
        raise FileNotFoundError(f"Valuation file not found: {VALUATION_FILE}")

    excel_file = pd.ExcelFile(VALUATION_FILE)

    data_dict = {}

    for ticker in TICKERS:
        if ticker in excel_file.sheet_names:
            df = pd.read_excel(VALUATION_FILE, sheet_name=ticker)

            # Standardize column names
            df.columns = df.columns.str.lower().str.strip()

            # Already has standard column names: date, pe, pb, pcfs
            if 'date' not in df.columns:
                raise ValueError(f"No date column found for {ticker}")

            df = df.rename(columns={'date': DATE})
            df = standardize_date_column(df, DATE)

            # Select only needed columns
            cols_to_keep = [DATE]
            for col in [PE, PB, PCFS]:
                if col in df.columns:
                    cols_to_keep.append(col)

            df = df[cols_to_keep]

            # Sort by date
            df = df.sort_values(DATE).reset_index(drop=True)

            data_dict[ticker] = df
        else:
            print(f"Warning: {ticker} sheet not found in valuation file")

    return data_dict


def load_vnindex() -> pd.DataFrame:
    """
    Load VN-Index market data from Excel

    Returns:
        DataFrame with VN-Index data
    """
    if not os.path.exists(VNINDEX_FILE):
        raise FileNotFoundError(f"VN-Index file not found: {VNINDEX_FILE}")

    df = pd.read_excel(VNINDEX_FILE)

    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()

    # Standardize date column
    if 'tradingdate' in df.columns:
        df = df.rename(columns={'tradingdate': DATE})
    elif 'date' not in df.columns:
        raise ValueError("No date column found in VN-Index file")

    df = standardize_date_column(df, DATE)

    # Rename close column to vnindex_close
    if CLOSE in df.columns:
        df = df.rename(columns={CLOSE: VNINDEX_CLOSE})

    # Sort by date
    df = df.sort_values(DATE).reset_index(drop=True)

    return df


def merge_all_data(tickers: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """
    Load and merge all data sources for each ticker

    Merge strategy:
    - Outer join on date (preserve all dates)
    - Forward fill prices (close, vnindex)
    - Leave trading data as NaN where missing

    Args:
        tickers: List of tickers to load (default: all tickers from config)

    Returns:
        Dictionary mapping ticker to merged DataFrame
    """
    if tickers is None:
        tickers = TICKERS

    print("Loading data files...")
    foreign_data = load_foreign_trading()
    self_data = load_self_trading()
    valuation_data = load_valuation()
    vnindex_data = load_vnindex()

    print("Merging data...")
    merged_data = {}

    for ticker in tickers:
        print(f"Processing {ticker}...")

        # Start with foreign trading data (has price and date)
        if ticker not in foreign_data:
            print(f"Warning: No foreign trading data for {ticker}, skipping...")
            continue

        df = foreign_data[ticker].copy()

        # Merge valuation
        if ticker in valuation_data:
            df = df.merge(
                valuation_data[ticker],
                on=DATE,
                how='outer'
            )

        # Merge self-trading
        if ticker in self_data:
            df = df.merge(
                self_data[ticker],
                on=DATE,
                how='outer'
            )

        # Merge VN-Index
        df = df.merge(
            vnindex_data[[DATE, VNINDEX_CLOSE]],
            on=DATE,
            how='outer'
        )

        # Sort by date
        df = df.sort_values(DATE).reset_index(drop=True)

        # Forward fill prices only (NOT trading data)
        price_cols = [CLOSE, VNINDEX_CLOSE, PE, PB]
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].ffill()

        # Calculate returns
        df[STOCK_RETURN] = df[CLOSE].pct_change()
        df[MARKET_RETURN] = df[VNINDEX_CLOSE].pct_change()

        # Calculate excess return
        df[EXCESS_RETURN] = df[STOCK_RETURN] - df[MARKET_RETURN]

        # Calculate MA200 for bull/bear regime
        df[MA200] = df[VNINDEX_CLOSE].rolling(window=MA_WINDOW_REGIME, min_periods=1).mean()
        df[BULL_MARKET] = (df[VNINDEX_CLOSE] > df[MA200]).astype(int)

        merged_data[ticker] = df

    print(f"Data loading complete. Loaded {len(merged_data)} tickers.")

    return merged_data


def get_data_summary(merged_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Get summary statistics of loaded data

    Args:
        merged_data: Dictionary of merged DataFrames

    Returns:
        Summary DataFrame
    """
    summary_data = []

    for ticker, df in merged_data.items():
        summary = {
            'Ticker': ticker,
            'Start Date': df[DATE].min(),
            'End Date': df[DATE].max(),
            'Total Days': len(df),
            'Foreign Data Points': df[FOREIGN_NET_BUY_VAL].notna().sum(),
            'Self Data Points': df[SELF_NET_BUY_VAL].notna().sum() if SELF_NET_BUY_VAL in df.columns else 0,
            'Valuation Data Points': df[PE].notna().sum() if PE in df.columns else 0,
            'Missing Price %': f"{(df[CLOSE].isna().sum() / len(df) * 100):.1f}%"
        }
        summary_data.append(summary)

    return pd.DataFrame(summary_data)


if __name__ == "__main__":
    # Test data loading
    print("Testing data loader...")
    data = merge_all_data()
    summary = get_data_summary(data)
    print("\n" + "="*80)
    print("DATA SUMMARY")
    print("="*80)
    print(summary.to_string(index=False))
    print("="*80)
