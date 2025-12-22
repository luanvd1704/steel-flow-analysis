#!/usr/bin/env python3
"""
Banking Sector Trading & Valuation Data Excel Export
Exports to 3 separate files for better organization:
- bank_foreign_trading.xlsx: CaféF Foreign data (5 years)
- bank_self_trading.xlsx: CaféF Self trading data (5 years)
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
# Add Stock-analyst directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Stock-analyst'))

# Force reload modules to avoid cache issues
for mod_name in ['fetch_cafef_trade_data', 'fetch_smoney_trade_data']:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

from fetch_cafef_trade_data import fetch_cafef_foreign_trades, fetch_cafef_self_trades, fetch_vnstock_adjusted_prices
from fetch_smoney_trade_data import fetch_valuation_history
import datetime
import time
from pathlib import Path

# Helper function to parse ThayDoi column
def split_thaydoi(value):
    """Parse ThayDoi column format: '26.4(-1.31 %)' -> (26.4, -1.31)"""
    if pd.isna(value):
        return None, None
    pattern = r'([0-9.]+)\(([+-]?[0-9.]+)\s*%\)'
    match = re.match(pattern, str(value))
    if match:
        close = float(match.group(1))
        change_pct = float(match.group(2))
        return close, change_pct
    else:
        return None, None

# Configuration - 17 Banks
BANK_TICKERS = [
    "VCB", "TCB", "MBB", "ACB", "VPB", "BID", "CTG", "STB", "HDB",
    "TPB", "VIB", "SSB", "SHB", "MSB", "LPB", "OCB", "EIB"
]

# Output files (3 separate files) - saved to data/ folder
OUTPUT_FOREIGN = "data/bank_foreign_trading.xlsx"
OUTPUT_SELF = "data/bank_self_trading.xlsx"
OUTPUT_VALUATION = "data/bank_valuation.xlsx"

# Date range for CaféF (5 years)
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)
# CaféF API expects DD/MM/YYYY format (Vietnamese format)
start_date_str = start_date.strftime("%d/%m/%Y")
end_date_str = end_date.strftime("%d/%m/%Y")

# Delays to avoid rate limiting
TICKER_DELAY = 2.0
SOURCE_DELAY = 1.0

# Error logging
ERROR_LOG_FILE = "data/fetch_bank_data_errors.log"

def log_error(ticker, source, error_msg, tb_str):
    """Log error to file with timestamp and full traceback"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] {ticker} - {source}\n")
        f.write(f"Error: {error_msg}\n")
        f.write(f"Traceback:\n{tb_str}\n")
        f.write(f"{'='*80}\n")

def get_existing_tickers(file_path):
    """Get list of tickers already in Excel file"""
    if not os.path.exists(file_path):
        return []
    try:
        xl = pd.ExcelFile(file_path)
        return xl.sheet_names
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return []

def get_missing_tickers(all_tickers, existing_tickers):
    """Get tickers that are in all_tickers but not in existing_tickers"""
    return [t for t in all_tickers if t not in existing_tickers]

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Banking Sector Trading & Valuation Data Fetcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all 17 banks (default)
  python fetch_bank_data.py

  # Retry mode: Only fetch tickers missing from existing files
  python fetch_bank_data.py --retry

  # Fetch specific tickers only
  python fetch_bank_data.py --tickers VCB,TCB,MBB
        """
    )
    parser.add_argument('--retry', action='store_true',
                       help='Only fetch tickers missing from existing files')
    parser.add_argument('--tickers', type=str,
                       help='Comma-separated list of specific tickers to fetch (e.g., VCB,TCB,MBB)')
    args = parser.parse_args()

    print("=" * 60)
    print("BANKING SECTOR TRADING & VALUATION DATA EXPORT")
    print("=" * 60)

    # Determine which tickers to fetch
    if args.tickers:
        # User specified tickers
        tickers_to_fetch = [t.strip().upper() for t in args.tickers.split(',')]
        print(f"[MODE] Specific tickers: {', '.join(tickers_to_fetch)}")
        mode = "append"  # Append to existing file
    elif args.retry:
        # Retry mode: find missing tickers
        print(f"[MODE] Retry - checking existing files...")
        existing_foreign = get_existing_tickers(OUTPUT_FOREIGN)
        existing_self = get_existing_tickers(OUTPUT_SELF)
        existing_val = get_existing_tickers(OUTPUT_VALUATION)

        # Get union of all missing tickers
        missing_foreign = set(get_missing_tickers(BANK_TICKERS, existing_foreign))
        missing_self = set(get_missing_tickers(BANK_TICKERS, existing_self))
        missing_val = set(get_missing_tickers(BANK_TICKERS, existing_val))

        tickers_to_fetch = sorted(missing_foreign | missing_self | missing_val)

        if not tickers_to_fetch:
            print("✅ All tickers already exist in files. Nothing to fetch!")
            return

        print(f"  Missing from Foreign: {len(missing_foreign)} - {', '.join(sorted(missing_foreign)) if missing_foreign else 'None'}")
        print(f"  Missing from Self: {len(missing_self)} - {', '.join(sorted(missing_self)) if missing_self else 'None'}")
        print(f"  Missing from Valuation: {len(missing_val)} - {', '.join(sorted(missing_val)) if missing_val else 'None'}")
        print(f"  Will fetch: {', '.join(tickers_to_fetch)}")
        mode = "append"
    else:
        # Default: fetch all
        tickers_to_fetch = BANK_TICKERS
        print(f"[MODE] Full fetch - all {len(BANK_TICKERS)} banks")
        mode = "overwrite"

    print(f"Tickers to fetch: {', '.join(tickers_to_fetch)}")
    print(f"Output files:")
    print(f"  1. {OUTPUT_FOREIGN}")
    print(f"  2. {OUTPUT_SELF}")
    print(f"  3. {OUTPUT_VALUATION}")
    print(f"CaféF range: {start_date_str} to {end_date_str}")
    print(f"Mode: {mode.upper()}")
    print("=" * 60)

    start_time = datetime.datetime.now()

    # Create data folder if not exists
    os.makedirs("data", exist_ok=True)

    # Clear previous error log
    if os.path.exists(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)

    # Track errors and successes
    error_summary = {
        'foreign': [],
        'self': [],
        'valuation': []
    }
    success_summary = {
        'foreign': [],
        'self': [],
        'valuation': []
    }

    # Load existing data if in append mode
    existing_data = {
        'foreign': {},
        'self': {},
        'valuation': {}
    }

    if mode == "append":
        print("\nLoading existing data...")
        # Load existing foreign data
        if os.path.exists(OUTPUT_FOREIGN):
            try:
                xl = pd.ExcelFile(OUTPUT_FOREIGN)
                for sheet in xl.sheet_names:
                    existing_data['foreign'][sheet] = pd.read_excel(OUTPUT_FOREIGN, sheet_name=sheet)
                print(f"  Loaded {len(existing_data['foreign'])} sheets from {OUTPUT_FOREIGN}")
            except Exception as e:
                print(f"  Warning: Could not load {OUTPUT_FOREIGN}: {e}")

        # Load existing self data
        if os.path.exists(OUTPUT_SELF):
            try:
                xl = pd.ExcelFile(OUTPUT_SELF)
                for sheet in xl.sheet_names:
                    existing_data['self'][sheet] = pd.read_excel(OUTPUT_SELF, sheet_name=sheet)
                print(f"  Loaded {len(existing_data['self'])} sheets from {OUTPUT_SELF}")
            except Exception as e:
                print(f"  Warning: Could not load {OUTPUT_SELF}: {e}")

        # Load existing valuation data
        if os.path.exists(OUTPUT_VALUATION):
            try:
                xl = pd.ExcelFile(OUTPUT_VALUATION)
                for sheet in xl.sheet_names:
                    existing_data['valuation'][sheet] = pd.read_excel(OUTPUT_VALUATION, sheet_name=sheet)
                print(f"  Loaded {len(existing_data['valuation'])} sheets from {OUTPUT_VALUATION}")
            except Exception as e:
                print(f"  Warning: Could not load {OUTPUT_VALUATION}: {e}")

    # Create 3 separate ExcelWriters
    with pd.ExcelWriter(OUTPUT_FOREIGN, engine='openpyxl') as writer_foreign, \
         pd.ExcelWriter(OUTPUT_SELF, engine='openpyxl') as writer_self, \
         pd.ExcelWriter(OUTPUT_VALUATION, engine='openpyxl') as writer_valuation:

        # First, write existing data if in append mode
        if mode == "append":
            print("\nWriting existing data to new files...")
            for ticker, df in existing_data['foreign'].items():
                df.to_excel(writer_foreign, sheet_name=ticker, index=False)
            for ticker, df in existing_data['self'].items():
                df.to_excel(writer_self, sheet_name=ticker, index=False)
            for ticker, df in existing_data['valuation'].items():
                df.to_excel(writer_valuation, sheet_name=ticker, index=False)

        # Split tickers into 3 groups to avoid timeout
        # Group 1: 6 tickers, Group 2: 6 tickers, Group 3: 5 tickers
        group1 = ['VCB', 'TCB', 'MBB', 'ACB', 'VPB', 'BID']
        group2 = ['CTG', 'STB', 'HDB', 'TPB', 'VIB', 'SSB']
        group3 = ['SHB', 'MSB', 'LPB', 'OCB', 'EIB']

        # Filter to only include tickers we're actually fetching
        groups = []
        for group_tickers in [group1, group2, group3]:
            filtered_group = [t for t in group_tickers if t in tickers_to_fetch]
            if filtered_group:
                groups.append(filtered_group)

        # Now fetch and write new data in batches
        ticker_counter = 0
        for group_idx, group_tickers in enumerate(groups, 1):
            if group_idx > 1:
                # Add 60-second delay between groups
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

                # 1. CaféF Foreign Trading -> steel_foreign_trading.xlsx
                try:
                    print(f"  Fetching CaféF Foreign (from {start_date_str} to {end_date_str})...")
                    cafef_foreign = fetch_cafef_foreign_trades(ticker, start_date_str, end_date_str)
                    print(f"    Received {len(cafef_foreign)} records")
                    if not cafef_foreign.empty:
                        # Parse ThayDoi column to get Close and ChangePct
                        cafef_foreign[['Close', 'ChangePct']] = cafef_foreign['ThayDoi'].apply(
                            lambda x: pd.Series(split_thaydoi(x))
                        )

                        # Fetch adjusted prices from vnstock
                        try:
                            print(f"  Fetching vnstock adjusted prices...")
                            vnstock_prices = fetch_vnstock_adjusted_prices(
                                ticker,
                                start_date=start_date.strftime('%Y-%m-%d'),
                                source='VCI'
                            )

                            # Merge with foreign trading data
                            cafef_foreign = cafef_foreign.merge(
                                vnstock_prices[['date', 'adj_close']],
                                left_on='Ngay',
                                right_on='date',
                                how='left'
                            )

                            # Replace Close with adjusted price
                            cafef_foreign['Close'] = cafef_foreign['adj_close']
                            cafef_foreign = cafef_foreign.drop(['date', 'adj_close'], axis=1, errors='ignore')

                            print(f"    Merged with adjusted prices")
                        except Exception as e:
                            print(f"    Warning: Could not fetch adjusted prices: {e}")

                        # Drop unwanted columns
                        cafef_foreign = cafef_foreign.drop(['ChangePct', 'Close_Unadjusted'], axis=1, errors='ignore')

                        # Export to Excel
                        sheet_name = ticker  # Simplified sheet name
                        cafef_foreign.to_excel(writer_foreign, sheet_name=sheet_name, index=False)
                        print(f"    OK: {cafef_foreign.shape[0]} rows -> {OUTPUT_FOREIGN}")
                        success_summary['foreign'].append(ticker)
                    else:
                        print(f"    No data")
                        error_summary['foreign'].append(f"{ticker} (No data)")
                    time.sleep(SOURCE_DELAY)
                except Exception as e:
                    error_msg = str(e)
                    tb_str = traceback.format_exc()
                    print(f"    ❌ ERROR: {error_msg}")
                    print(f"    (Chi tiết lỗi đã lưu vào {ERROR_LOG_FILE})")
                    log_error(ticker, "Foreign Trading", error_msg, tb_str)
                    error_summary['foreign'].append(ticker)

                # 2. CaféF Self Trading -> steel_self_trading.xlsx
                try:
                    print(f"  Fetching CaféF Self...")
                    cafef_self = fetch_cafef_self_trades(ticker, start_date_str, end_date_str)
                    if not cafef_self.empty:
                        # Fetch adjusted prices from vnstock
                        try:
                            print(f"  Fetching vnstock adjusted prices for Self...")
                            vnstock_prices = fetch_vnstock_adjusted_prices(
                                ticker,
                                start_date=start_date.strftime('%Y-%m-%d'),
                                source='VCI'
                            )

                            # Merge with self trading data (Date column instead of Ngay)
                            cafef_self = cafef_self.merge(
                                vnstock_prices[['date', 'adj_close']],
                                left_on='Date',
                                right_on='date',
                                how='left'
                            )

                            # Add Close column from adjusted price
                            cafef_self['Close'] = cafef_self['adj_close']
                            cafef_self = cafef_self.drop(['date', 'adj_close'], axis=1, errors='ignore')

                            print(f"    Merged with adjusted prices")
                        except Exception as e:
                            print(f"    Warning: Could not fetch adjusted prices: {e}")

                        # Drop unwanted columns
                        cafef_self = cafef_self.drop(['ChangePct', 'Close_Unadjusted'], axis=1, errors='ignore')

                        # Export to Excel
                        sheet_name = ticker  # Simplified sheet name
                        cafef_self.to_excel(writer_self, sheet_name=sheet_name, index=False)
                        print(f"    OK: {cafef_self.shape[0]} rows -> {OUTPUT_SELF}")
                        success_summary['self'].append(ticker)
                    else:
                        print(f"    No data")
                        error_summary['self'].append(f"{ticker} (No data)")
                    time.sleep(SOURCE_DELAY)
                except Exception as e:
                    error_msg = str(e)
                    tb_str = traceback.format_exc()
                    print(f"    ❌ ERROR: {error_msg}")
                    print(f"    (Chi tiết lỗi đã lưu vào {ERROR_LOG_FILE})")
                    log_error(ticker, "Self Trading", error_msg, tb_str)
                    error_summary['self'].append(ticker)

                # 3. Smoney Valuation -> steel_valuation.xlsx
                try:
                    print(f"  Fetching Smoney Valuation...")
                    smoney_val = fetch_valuation_history(ticker)
                    if not smoney_val.empty:
                        sheet_name = ticker  # Simplified sheet name
                        smoney_val.to_excel(writer_valuation, sheet_name=sheet_name, index=False)
                        print(f"    OK: {smoney_val.shape[0]} rows -> {OUTPUT_VALUATION}")
                        success_summary['valuation'].append(ticker)
                    else:
                        print(f"    No data")
                        error_summary['valuation'].append(f"{ticker} (No data)")
                except Exception as e:
                    error_msg = str(e)
                    tb_str = traceback.format_exc()
                    print(f"    ❌ ERROR: {error_msg}")
                    print(f"    (Chi tiết lỗi đã lưu vào {ERROR_LOG_FILE})")
                    log_error(ticker, "Valuation", error_msg, tb_str)
                    error_summary['valuation'].append(ticker)

                # Delay between tickers (within same group)
                if ticker_counter < len(tickers_to_fetch):
                    print(f"  Waiting {TICKER_DELAY}s...")
                    time.sleep(TICKER_DELAY)

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Success summary
    print("\nSUCCESSES:")
    print(f"  Foreign Trading: {len(success_summary['foreign'])}/{len(tickers_to_fetch)} tickers fetched")
    if success_summary['foreign']:
        print(f"    {', '.join(success_summary['foreign'])}")
    print(f"  Self Trading: {len(success_summary['self'])}/{len(tickers_to_fetch)} tickers fetched")
    if success_summary['self']:
        print(f"    {', '.join(success_summary['self'])}")
    print(f"  Valuation: {len(success_summary['valuation'])}/{len(tickers_to_fetch)} tickers fetched")
    if success_summary['valuation']:
        print(f"    {', '.join(success_summary['valuation'])}")

    # Final file statistics
    if mode == "append":
        total_foreign = len(existing_data['foreign']) + len(success_summary['foreign'])
        total_self = len(existing_data['self']) + len(success_summary['self'])
        total_val = len(existing_data['valuation']) + len(success_summary['valuation'])
        print(f"\nTotal sheets in files:")
        print(f"  Foreign: {total_foreign} sheets")
        print(f"  Self: {total_self} sheets")
        print(f"  Valuation: {total_val} sheets")

    # Error summary
    total_errors = len(error_summary['foreign']) + len(error_summary['self']) + len(error_summary['valuation'])
    if total_errors > 0:
        print("\nERRORS:")
        if error_summary['foreign']:
            print(f"  Foreign Trading ({len(error_summary['foreign'])} failed): {', '.join(error_summary['foreign'])}")
        if error_summary['self']:
            print(f"  Self Trading ({len(error_summary['self'])} failed): {', '.join(error_summary['self'])}")
        if error_summary['valuation']:
            print(f"  Valuation ({len(error_summary['valuation'])} failed): {', '.join(error_summary['valuation'])}")
        print(f"\nChi tiet loi da luu vao: {ERROR_LOG_FILE}")
    else:
        print("\nNo errors!")

    print("\n" + "=" * 60)
    print("EXPORT COMPLETED!")
    print("=" * 60)
    print(f"Files {'updated' if mode == 'append' else 'created'}:")
    print(f"  1. {OUTPUT_FOREIGN} (Foreign trading)")
    print(f"  2. {OUTPUT_SELF} (Self trading)")
    print(f"  3. {OUTPUT_VALUATION} (Valuation metrics)")
    print(f"Tickers processed: {len(tickers_to_fetch)}")
    print(f"Duration: {duration}")
    print("=" * 60)

if __name__ == "__main__":
    main()
