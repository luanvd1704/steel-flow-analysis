"""
Data validation module
Performs data quality checks and validation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import MIN_DATA_POINTS, MAX_MISSING_PCT
from utils.constants import *


def validate_required_columns(df: pd.DataFrame, required_cols: List[str], ticker: str = "") -> Tuple[bool, List[str]]:
    """
    Validate that required columns exist in DataFrame

    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        ticker: Ticker name for error messages

    Returns:
        Tuple of (is_valid, missing_columns)
    """
    missing_cols = [col for col in required_cols if col not in df.columns]

    is_valid = len(missing_cols) == 0

    if not is_valid:
        print(f"{'[' + ticker + '] ' if ticker else ''}Missing required columns: {missing_cols}")

    return is_valid, missing_cols


def validate_date_continuity(df: pd.DataFrame, date_col: str = DATE, ticker: str = "") -> Dict:
    """
    Check for gaps in date series

    Args:
        df: DataFrame with date column
        date_col: Name of date column
        ticker: Ticker name for messages

    Returns:
        Dictionary with validation results
    """
    df_sorted = df.sort_values(date_col).reset_index(drop=True)

    # Calculate gaps (in days)
    date_diffs = df_sorted[date_col].diff()
    large_gaps = date_diffs[date_diffs > pd.Timedelta(days=7)]  # Gaps > 1 week

    results = {
        'has_large_gaps': len(large_gaps) > 0,
        'num_large_gaps': len(large_gaps),
        'max_gap_days': date_diffs.max().days if len(df_sorted) > 1 else 0,
        'large_gap_dates': large_gaps.index.tolist()
    }

    if results['has_large_gaps']:
        print(f"{'[' + ticker + '] ' if ticker else ''}Found {results['num_large_gaps']} large gaps in dates")

    return results


def validate_missing_data(df: pd.DataFrame, columns: List[str], ticker: str = "") -> Dict:
    """
    Check for missing data in specified columns

    Args:
        df: DataFrame to validate
        columns: List of columns to check
        ticker: Ticker name for messages

    Returns:
        Dictionary with missing data statistics
    """
    results = {}

    for col in columns:
        if col not in df.columns:
            results[col] = {
                'missing_count': len(df),
                'missing_pct': 100.0,
                'status': 'COLUMN_NOT_FOUND'
            }
            continue

        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df)) * 100

        status = 'OK'
        if missing_pct > MAX_MISSING_PCT * 100:
            status = 'HIGH_MISSING'
        elif missing_pct > 10:
            status = 'MODERATE_MISSING'

        results[col] = {
            'missing_count': missing_count,
            'missing_pct': round(missing_pct, 2),
            'status': status
        }

        if status != 'OK':
            print(f"{'[' + ticker + '] ' if ticker else ''}{col}: {missing_pct:.1f}% missing ({status})")

    return results


def validate_data_sufficiency(df: pd.DataFrame, ticker: str = "") -> bool:
    """
    Check if there is sufficient data for analysis

    Args:
        df: DataFrame to validate
        ticker: Ticker name for messages

    Returns:
        True if sufficient data, False otherwise
    """
    if len(df) < MIN_DATA_POINTS:
        print(f"{'[' + ticker + '] ' if ticker else ''}Insufficient data: {len(df)} rows (minimum: {MIN_DATA_POINTS})")
        return False

    return True


def validate_numeric_ranges(df: pd.DataFrame, column_ranges: Dict[str, Tuple[float, float]], ticker: str = "") -> Dict:
    """
    Validate that numeric columns are within expected ranges

    Args:
        df: DataFrame to validate
        column_ranges: Dictionary mapping column names to (min, max) tuples
        ticker: Ticker name for messages

    Returns:
        Dictionary with validation results
    """
    results = {}

    for col, (min_val, max_val) in column_ranges.items():
        if col not in df.columns:
            results[col] = {'status': 'COLUMN_NOT_FOUND'}
            continue

        data = df[col].dropna()

        if len(data) == 0:
            results[col] = {'status': 'NO_DATA'}
            continue

        out_of_range = ((data < min_val) | (data > max_val)).sum()
        out_of_range_pct = (out_of_range / len(data)) * 100

        status = 'OK'
        if out_of_range_pct > 5:
            status = 'OUT_OF_RANGE'

        results[col] = {
            'out_of_range_count': out_of_range,
            'out_of_range_pct': round(out_of_range_pct, 2),
            'min': data.min(),
            'max': data.max(),
            'status': status
        }

        if status != 'OK':
            print(f"{'[' + ticker + '] ' if ticker else ''}{col}: {out_of_range_pct:.1f}% out of range ({status})")

    return results


def validate_no_duplicates(df: pd.DataFrame, subset: List[str] = None, ticker: str = "") -> bool:
    """
    Check for duplicate rows

    Args:
        df: DataFrame to validate
        subset: Columns to check for duplicates (default: all columns)
        ticker: Ticker name for messages

    Returns:
        True if no duplicates, False otherwise
    """
    duplicates = df.duplicated(subset=subset).sum()

    if duplicates > 0:
        print(f"{'[' + ticker + '] ' if ticker else ''}Found {duplicates} duplicate rows")
        return False

    return True


def validate_ticker_data(df: pd.DataFrame, ticker: str) -> Dict:
    """
    Perform comprehensive validation on ticker data

    Args:
        df: Merged DataFrame for a ticker
        ticker: Ticker name

    Returns:
        Dictionary with all validation results
    """
    print(f"\n{'='*60}")
    print(f"Validating data for {ticker}")
    print(f"{'='*60}")

    validation_results = {
        'ticker': ticker,
        'passed': True,
        'warnings': [],
        'errors': []
    }

    # 1. Check required columns
    required_cols = [DATE, CLOSE, MARKET_RETURN]
    is_valid, missing_cols = validate_required_columns(df, required_cols, ticker)

    if not is_valid:
        validation_results['passed'] = False
        validation_results['errors'].append(f"Missing required columns: {missing_cols}")

    # 2. Check data sufficiency
    if not validate_data_sufficiency(df, ticker):
        validation_results['passed'] = False
        validation_results['errors'].append(f"Insufficient data points: {len(df)}")

    # 3. Check for duplicates
    if not validate_no_duplicates(df, subset=[DATE], ticker=ticker):
        validation_results['warnings'].append("Duplicate dates found")

    # 4. Check date continuity
    date_check = validate_date_continuity(df, DATE, ticker)
    if date_check['has_large_gaps']:
        validation_results['warnings'].append(f"Large gaps in dates: {date_check['num_large_gaps']} gaps")

    # 5. Check missing data
    cols_to_check = [CLOSE, PE, PB, FOREIGN_NET_BUY_VAL]
    if SELF_NET_BUY_VAL in df.columns:
        cols_to_check.append(SELF_NET_BUY_VAL)

    missing_check = validate_missing_data(df, cols_to_check, ticker)

    for col, result in missing_check.items():
        if result['status'] == 'HIGH_MISSING':
            validation_results['warnings'].append(f"{col}: {result['missing_pct']:.1f}% missing")

    # 6. Validate numeric ranges
    ranges = {
        PE: (0, 200),          # PE ratio typically 0-200
        PB: (0, 50),           # PB ratio typically 0-50
        CLOSE: (0, 1e9),       # Price should be positive
    }

    range_check = validate_numeric_ranges(df, ranges, ticker)

    for col, result in range_check.items():
        if result.get('status') == 'OUT_OF_RANGE':
            validation_results['warnings'].append(f"{col}: {result['out_of_range_pct']:.1f}% out of range")

    # Print summary
    print(f"\nValidation Summary for {ticker}:")
    print(f"  Status: {'✓ PASSED' if validation_results['passed'] else '✗ FAILED'}")
    print(f"  Errors: {len(validation_results['errors'])}")
    print(f"  Warnings: {len(validation_results['warnings'])}")

    if validation_results['errors']:
        print(f"\n  Errors:")
        for error in validation_results['errors']:
            print(f"    - {error}")

    if validation_results['warnings']:
        print(f"\n  Warnings:")
        for warning in validation_results['warnings']:
            print(f"    - {warning}")

    return validation_results


def validate_all_data(merged_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """
    Validate all ticker data

    Args:
        merged_data: Dictionary of merged DataFrames

    Returns:
        Dictionary mapping ticker to validation results
    """
    all_results = {}

    for ticker, df in merged_data.items():
        results = validate_ticker_data(df, ticker)
        all_results[ticker] = results

    # Print overall summary
    print(f"\n{'='*60}")
    print("OVERALL VALIDATION SUMMARY")
    print(f"{'='*60}")

    total_tickers = len(all_results)
    passed_tickers = sum(1 for r in all_results.values() if r['passed'])
    failed_tickers = total_tickers - passed_tickers

    print(f"Total Tickers: {total_tickers}")
    print(f"Passed: {passed_tickers}")
    print(f"Failed: {failed_tickers}")

    if failed_tickers > 0:
        print(f"\nFailed tickers:")
        for ticker, results in all_results.items():
            if not results['passed']:
                print(f"  - {ticker}")

    return all_results


if __name__ == "__main__":
    # Test validation
    from data.loader import merge_all_data

    print("Loading data for validation...")
    data = merge_all_data()

    print("\nValidating data...")
    validation_results = validate_all_data(data)
