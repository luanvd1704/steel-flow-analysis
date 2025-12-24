#!/usr/bin/env python3
"""
Banking Sector Trading & Valuation Data Excel Export
Exports to 2 separate files for better organization:
- bank_foreign_trading.xlsx: CaféF Foreign data (5 years)
- bank_valuation.xlsx: Smoney valuation data (P/E, P/B, P/CF)

RETRY MODE: Use --retry to only fetch tickers missing from existing files
"""

import pandas as pd
import re
import sys
import os
import traceback
import argparse
import importlib
import datetime
import time
from pathlib import Path

# Add Stock-analyst directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Stock-analyst'))

# Force reload modules to avoid cache issues
for mod_name in ['fetch_cafef_trade_data', 'fetch_smoney_trade_data']:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

from fetch_cafef_trade_data import fetch_cafef_foreign_trades, fetch_vnstock_adjusted_prices
from fetch_smoney_trade_data import fetch_valuation_history

# Configuration - 17 Banks
BANK_TICKERS = [
    "VCB", "TCB", "MBB", "ACB", "VPB", "BID", "CTG", "STB", "HDB",
    "TPB", "VIB", "SSB", "SHB", "MSB", "LPB", "OCB", "EIB"
]

# Output files
OUTPUT_FOREIGN = "data/bank_foreign_trading.xlsx"
OUTPUT_VALUATION = "data/bank_valuation.xlsx"

# Date range for CaféF (5 years)
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)
start_date_str = start_date.strftime("%d/%m/%Y")
end_date_str = end_date.strftime("%d/%m/%Y")

# Delays to avoid rate limiting
TICKER_DELAY = 2.0
SOURCE_DELAY = 1.0

# Error logging
ERROR_LOG_FILE = "data/fetch_bank_data_errors.log"

# Ticker groups to avoid timeout
TICKER_GROUPS = [
    ['VCB', 'TCB', 'MBB', 'ACB', 'VPB', 'BID'],
    ['CTG', 'STB', 'HDB', 'TPB', 'VIB', 'SSB'],
    ['SHB', 'MSB', 'LPB', 'OCB', 'EIB']
]


def split_thaydoi(value):
    """Parse ThayDoi column format: '26.4(-1.31 %)' -> (26.4, -1.31)"""
    if pd.isna(value):
        return None, None
    pattern = r'([0-9.]+)\(([+-]?[0-9.]+)\s*%\)'
    match = re.match(pattern, str(value))
    return (float(match.group(1)), float(match.group(2))) if match else (None, None)


def log_error(ticker, source, error_msg, tb_str):
    """Log error to file with timestamp and full traceback"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n[{timestamp}] {ticker} - {source}\nError: {error_msg}\nTraceback:\n{tb_str}\n{'='*80}\n")


def get_existing_tickers(file_path):
    """Get list of tickers already in Excel file"""
    if not os.path.exists(file_path):
        return []
    try:
        return pd.ExcelFile(file_path).sheet_names
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return []


def get_missing_tickers(all_tickers, existing_tickers):
    """Get tickers that are in all_tickers but not in existing_tickers"""
    return [t for t in all_tickers if t not in existing_tickers]


def load_excel_data(file_path, data_key):
    """Load existing Excel data into dictionary"""
    data = {}
    if os.path.exists(file_path):
        try:
            xl = pd.ExcelFile(file_path)
            for sheet in xl.sheet_names:
                data[sheet] = pd.read_excel(file_path, sheet_name=sheet)
            print(f"  Loaded {len(data)} sheets from {file_path}")
        except Exception as e:
            print(f"  Warning: Could not load {file_path}: {e}")
    return data


def write_excel_data(writer, data_dict):
    """Write dictionary of dataframes to Excel writer"""
    for ticker, df in data_dict.items():
        df.to_excel(writer, sheet_name=ticker, index=False)


def fetch_foreign_data(ticker):
    """Fetch and process foreign trading data for a ticker"""
    cafef_foreign = fetch_cafef_foreign_trades(ticker, start_date_str, end_date_str)

    if cafef_foreign.empty:
        return None

    # Parse ThayDoi column
    cafef_foreign[['Close', 'ChangePct']] = cafef_foreign['ThayDoi'].apply(
        lambda x: pd.Series(split_thaydoi(x))
    )

    # Fetch and merge adjusted prices
    try:
        vnstock_prices = fetch_vnstock_adjusted_prices(
            ticker, start_date=start_date.strftime('%Y-%m-%d'), source='VCI'
        )
        cafef_foreign = cafef_foreign.merge(
            vnstock_prices[['date', 'adj_close']],
            left_on='Ngay', right_on='date', how='left'
        )
        cafef_foreign['Close'] = cafef_foreign['adj_close']
        cafef_foreign = cafef_foreign.drop(['date', 'adj_close'], axis=1, errors='ignore')
    except Exception as e:
        print(f"    Warning: Could not fetch adjusted prices: {e}")

    # Drop unwanted columns
    return cafef_foreign.drop(['ChangePct', 'Close_Unadjusted'], axis=1, errors='ignore')


def process_ticker(ticker, writer_foreign, writer_valuation, success_summary, error_summary):
    """Process a single ticker: fetch foreign and valuation data"""
    # 1. Foreign Trading
    try:
        print(f"  Fetching CaféF Foreign...")
        cafef_foreign = fetch_foreign_data(ticker)

        if cafef_foreign is not None:
            cafef_foreign.to_excel(writer_foreign, sheet_name=ticker, index=False)
            print(f"    OK: {cafef_foreign.shape[0]} rows -> {OUTPUT_FOREIGN}")
            success_summary['foreign'].append(ticker)
        else:
            print(f"    No data")
            error_summary['foreign'].append(f"{ticker} (No data)")
        time.sleep(SOURCE_DELAY)
    except Exception as e:
        error_msg = str(e)
        print(f"    ❌ ERROR: {error_msg}")
        log_error(ticker, "Foreign Trading", error_msg, traceback.format_exc())
        error_summary['foreign'].append(ticker)

    # 2. Valuation
    try:
        print(f"  Fetching Smoney Valuation...")
        smoney_val = fetch_valuation_history(ticker)

        if not smoney_val.empty:
            smoney_val.to_excel(writer_valuation, sheet_name=ticker, index=False)
            print(f"    OK: {smoney_val.shape[0]} rows -> {OUTPUT_VALUATION}")
            success_summary['valuation'].append(ticker)
        else:
            print(f"    No data")
            error_summary['valuation'].append(f"{ticker} (No data)")
    except Exception as e:
        error_msg = str(e)
        print(f"    ❌ ERROR: {error_msg}")
        log_error(ticker, "Valuation", error_msg, traceback.format_exc())
        error_summary['valuation'].append(ticker)


def print_summary(tickers_to_fetch, success_summary, error_summary, existing_data, mode, duration):
    """Print final summary of the fetch operation"""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Success summary
    print("\nSUCCESSES:")
    for key in ['foreign', 'valuation']:
        count = len(success_summary[key])
        total = len(tickers_to_fetch)
        label = "Foreign Trading" if key == 'foreign' else "Valuation"
        print(f"  {label}: {count}/{total} tickers fetched")
        if success_summary[key]:
            print(f"    {', '.join(success_summary[key])}")

    # File statistics
    if mode == "append":
        total_foreign = len(existing_data['foreign']) + len(success_summary['foreign'])
        total_val = len(existing_data['valuation']) + len(success_summary['valuation'])
        print(f"\nTotal sheets in files:")
        print(f"  Foreign: {total_foreign} sheets")
        print(f"  Valuation: {total_val} sheets")

    # Error summary
    total_errors = len(error_summary['foreign']) + len(error_summary['valuation'])
    if total_errors > 0:
        print("\nERRORS:")
        for key in ['foreign', 'valuation']:
            if error_summary[key]:
                label = "Foreign Trading" if key == 'foreign' else "Valuation"
                print(f"  {label} ({len(error_summary[key])} failed): {', '.join(error_summary[key])}")
        print(f"\nChi tiet loi da luu vao: {ERROR_LOG_FILE}")
    else:
        print("\nNo errors!")

    # Final status
    print("\n" + "=" * 60)
    print("EXPORT COMPLETED!")
    print("=" * 60)
    print(f"Files {'updated' if mode == 'append' else 'created'}:")
    print(f"  1. {OUTPUT_FOREIGN} (Foreign trading)")
    print(f"  2. {OUTPUT_VALUATION} (Valuation metrics)")
    print(f"Tickers processed: {len(tickers_to_fetch)}")
    print(f"Duration: {duration}")
    print("=" * 60)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Banking Sector Trading & Valuation Data Fetcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_bank_data.py                    # Fetch all 17 banks
  python fetch_bank_data.py --retry            # Fetch missing tickers only
  python fetch_bank_data.py --tickers VCB,TCB  # Fetch specific tickers
        """
    )
    parser.add_argument('--retry', action='store_true',
                       help='Only fetch tickers missing from existing files')
    parser.add_argument('--tickers', type=str,
                       help='Comma-separated list of specific tickers (e.g., VCB,TCB,MBB)')
    args = parser.parse_args()

    print("=" * 60)
    print("BANKING SECTOR TRADING & VALUATION DATA EXPORT")
    print("=" * 60)

    # Determine which tickers to fetch
    if args.tickers:
        tickers_to_fetch = [t.strip().upper() for t in args.tickers.split(',')]
        print(f"[MODE] Specific tickers: {', '.join(tickers_to_fetch)}")
        mode = "append"
    elif args.retry:
        print(f"[MODE] Retry - checking existing files...")
        existing_foreign = get_existing_tickers(OUTPUT_FOREIGN)
        existing_val = get_existing_tickers(OUTPUT_VALUATION)

        missing_foreign = set(get_missing_tickers(BANK_TICKERS, existing_foreign))
        missing_val = set(get_missing_tickers(BANK_TICKERS, existing_val))
        tickers_to_fetch = sorted(missing_foreign | missing_val)

        if not tickers_to_fetch:
            print("✅ All tickers already exist in files. Nothing to fetch!")
            return

        print(f"  Missing from Foreign: {len(missing_foreign)} - {', '.join(sorted(missing_foreign)) if missing_foreign else 'None'}")
        print(f"  Missing from Valuation: {len(missing_val)} - {', '.join(sorted(missing_val)) if missing_val else 'None'}")
        print(f"  Will fetch: {', '.join(tickers_to_fetch)}")
        mode = "append"
    else:
        tickers_to_fetch = BANK_TICKERS
        print(f"[MODE] Full fetch - all {len(BANK_TICKERS)} banks")
        mode = "overwrite"

    print(f"Tickers to fetch: {', '.join(tickers_to_fetch)}")
    print(f"Output files:")
    print(f"  1. {OUTPUT_FOREIGN}")
    print(f"  2. {OUTPUT_VALUATION}")
    print(f"CaféF range: {start_date_str} to {end_date_str}")
    print(f"Mode: {mode.upper()}")
    print("=" * 60)

    start_time = datetime.datetime.now()

    # Setup
    os.makedirs("data", exist_ok=True)
    if os.path.exists(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)

    # Track results
    error_summary = {'foreign': [], 'valuation': []}
    success_summary = {'foreign': [], 'valuation': []}
    existing_data = {'foreign': {}, 'valuation': {}}

    # Load existing data if in append mode
    if mode == "append":
        print("\nLoading existing data...")
        existing_data['foreign'] = load_excel_data(OUTPUT_FOREIGN, 'foreign')
        existing_data['valuation'] = load_excel_data(OUTPUT_VALUATION, 'valuation')

    # Create Excel writers and process tickers
    with pd.ExcelWriter(OUTPUT_FOREIGN, engine='openpyxl') as writer_foreign, \
         pd.ExcelWriter(OUTPUT_VALUATION, engine='openpyxl') as writer_valuation:

        # Write existing data if in append mode
        if mode == "append":
            print("\nWriting existing data to new files...")
            write_excel_data(writer_foreign, existing_data['foreign'])
            write_excel_data(writer_valuation, existing_data['valuation'])

        # Filter ticker groups to only include tickers we're fetching
        groups = [[t for t in group if t in tickers_to_fetch] for group in TICKER_GROUPS]
        groups = [g for g in groups if g]  # Remove empty groups

        # Process tickers in groups
        ticker_counter = 0
        for group_idx, group_tickers in enumerate(groups, 1):
            if group_idx > 1:
                print(f"\n{'='*60}")
                print(f"[PAUSE] Waiting 60 seconds before Group {group_idx}...")
                print(f"{'='*60}")
                time.sleep(60)

            print(f"\n{'='*60}")
            print(f"GROUP {group_idx}/{len(groups)} - {len(group_tickers)} tickers: {', '.join(group_tickers)}")
            print(f"{'='*60}")

            for ticker in group_tickers:
                ticker_counter += 1
                print(f"\n[{ticker_counter}/{len(tickers_to_fetch)}] Processing {ticker}...")

                process_ticker(ticker, writer_foreign, writer_valuation, success_summary, error_summary)

                # Delay between tickers
                if ticker_counter < len(tickers_to_fetch):
                    print(f"  Waiting {TICKER_DELAY}s...")
                    time.sleep(TICKER_DELAY)

    # Print summary
    duration = datetime.datetime.now() - start_time
    print_summary(tickers_to_fetch, success_summary, error_summary, existing_data, mode, duration)


if __name__ == "__main__":
    main()
