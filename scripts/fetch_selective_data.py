#!/usr/bin/env python3
"""
Custom Banking Data Fetch Script
- Foreign Trading: Only 5 significant stocks (ACB, OCB, VPB, SHB, SSB)
- Self Trading: SKIP (no statistical significance)
- Valuation: All 17 banks (needed for all tabs)
"""

import pandas as pd
import re
import sys
import os
import traceback
import importlib

# Add Stock-analyst directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Stock-analyst'))

# Force reload modules to avoid cache issues
for mod_name in ['fetch_cafef_trade_data', 'fetch_smoney_trade_data']:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

from fetch_cafef_trade_data import fetch_cafef_foreign_trades, fetch_vnstock_adjusted_prices
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

# Configuration
FOREIGN_TICKERS = ['ACB', 'OCB', 'VPB', 'SHB', 'SSB']  # 5 stocks with statistical significance
VALUATION_TICKERS = [
    "VCB", "TCB", "MBB", "ACB", "VPB", "BID", "CTG", "STB", "HDB",
    "TPB", "VIB", "SSB", "SHB", "MSB", "LPB", "OCB", "EIB"
]  # All 17 banks

# Output files
OUTPUT_FOREIGN = "data/bank_foreign_trading.xlsx"
OUTPUT_VALUATION = "data/bank_valuation.xlsx"
# NOTE: bank_self_trading.xlsx will NOT be updated

# Date range for CaféF (5 years)
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)
start_date_str = start_date.strftime("%d/%m/%Y")
end_date_str = end_date.strftime("%d/%m/%Y")

# Delays
TICKER_DELAY = 2.0
SOURCE_DELAY = 1.0

# Error logging
ERROR_LOG_FILE = "data/fetch_selective_errors.log"

def log_error(ticker, source, error_msg, tb_str):
    """Log error to file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] {ticker} - {source}\n")
        f.write(f"Error: {error_msg}\n")
        f.write(f"Traceback:\n{tb_str}\n")
        f.write(f"{'='*80}\n")

def main():
    print("=" * 60)
    print("SELECTIVE BANKING DATA FETCH")
    print("=" * 60)
    print(f"\nForeign Trading: {len(FOREIGN_TICKERS)} stocks - {', '.join(FOREIGN_TICKERS)}")
    print(f"Self Trading: SKIPPED")
    print(f"Valuation: {len(VALUATION_TICKERS)} stocks")
    print(f"Date range: {start_date_str} to {end_date_str}")
    print("=" * 60)

    start_time = datetime.datetime.now()
    os.makedirs("data", exist_ok=True)

    # Clear error log
    if os.path.exists(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)

    # Track results
    error_summary = {'foreign': [], 'valuation': []}
    success_summary = {'foreign': [], 'valuation': []}

    # Load existing data to preserve other sheets
    existing_foreign = {}
    existing_valuation = {}

    if os.path.exists(OUTPUT_FOREIGN):
        try:
            xl = pd.ExcelFile(OUTPUT_FOREIGN)
            for sheet in xl.sheet_names:
                if sheet not in FOREIGN_TICKERS:  # Keep sheets we're not updating
                    existing_foreign[sheet] = pd.read_excel(OUTPUT_FOREIGN, sheet_name=sheet)
            print(f"\nLoaded {len(existing_foreign)} existing foreign trading sheets")
        except Exception as e:
            print(f"Warning: Could not load existing foreign data: {e}")

    if os.path.exists(OUTPUT_VALUATION):
        try:
            xl = pd.ExcelFile(OUTPUT_VALUATION)
            for sheet in xl.sheet_names:
                if sheet not in VALUATION_TICKERS:  # Keep sheets we're not updating
                    existing_valuation[sheet] = pd.read_excel(OUTPUT_VALUATION, sheet_name=sheet)
            print(f"Loaded {len(existing_valuation)} existing valuation sheets")
        except Exception as e:
            print(f"Warning: Could not load existing valuation data: {e}")

    # ===== PART 1: FETCH FOREIGN TRADING (5 stocks) =====
    print("\n" + "=" * 60)
    print("PART 1: FOREIGN TRADING (5 stocks)")
    print("=" * 60)

    foreign_data = {}
    for idx, ticker in enumerate(FOREIGN_TICKERS, 1):
        print(f"\n[{idx}/{len(FOREIGN_TICKERS)}] Fetching {ticker} foreign trading...")

        try:
            cafef_foreign = fetch_cafef_foreign_trades(ticker, start_date_str, end_date_str)
            print(f"  Received {len(cafef_foreign)} records")

            if not cafef_foreign.empty:
                # Parse ThayDoi
                cafef_foreign[['Close', 'ChangePct']] = cafef_foreign['ThayDoi'].apply(
                    lambda x: pd.Series(split_thaydoi(x))
                )

                # Fetch adjusted prices
                try:
                    vnstock_prices = fetch_vnstock_adjusted_prices(
                        ticker,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        source='VCI'
                    )
                    cafef_foreign = cafef_foreign.merge(
                        vnstock_prices[['date', 'adj_close']],
                        left_on='Ngay',
                        right_on='date',
                        how='left'
                    )
                    cafef_foreign['Close'] = cafef_foreign['adj_close']
                    cafef_foreign = cafef_foreign.drop(['date', 'adj_close'], axis=1, errors='ignore')
                except Exception as e:
                    print(f"  Warning: Could not merge adjusted prices: {e}")

                cafef_foreign = cafef_foreign.drop(['ChangePct', 'Close_Unadjusted'], axis=1, errors='ignore')
                foreign_data[ticker] = cafef_foreign
                success_summary['foreign'].append(ticker)
                print(f"  OK: {len(cafef_foreign)} rows")
            else:
                print(f"  No data")
                error_summary['foreign'].append(f"{ticker} (No data)")

            time.sleep(SOURCE_DELAY)
        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()
            print(f"  ERROR: {error_msg}")
            log_error(ticker, "Foreign Trading", error_msg, tb_str)
            error_summary['foreign'].append(ticker)

        if idx < len(FOREIGN_TICKERS):
            time.sleep(TICKER_DELAY)

    # Write foreign trading file
    print(f"\nWriting {OUTPUT_FOREIGN}...")
    with pd.ExcelWriter(OUTPUT_FOREIGN, engine='openpyxl') as writer:
        # Write existing sheets first
        for sheet_name, df in existing_foreign.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        # Write new data
        for ticker, df in foreign_data.items():
            df.to_excel(writer, sheet_name=ticker, index=False)
    print(f"  {len(existing_foreign) + len(foreign_data)} sheets written")

    # ===== PART 2: FETCH VALUATION (17 stocks) =====
    print("\n" + "=" * 60)
    print("PART 2: VALUATION (17 stocks)")
    print("=" * 60)

    valuation_data = {}
    for idx, ticker in enumerate(VALUATION_TICKERS, 1):
        print(f"\n[{idx}/{len(VALUATION_TICKERS)}] Fetching {ticker} valuation...")

        try:
            smoney_val = fetch_valuation_history(ticker)

            if not smoney_val.empty:
                valuation_data[ticker] = smoney_val
                success_summary['valuation'].append(ticker)
                print(f"  OK: {len(smoney_val)} rows")
            else:
                print(f"  No data")
                error_summary['valuation'].append(f"{ticker} (No data)")
        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()
            print(f"  ERROR: {error_msg}")
            log_error(ticker, "Valuation", error_msg, tb_str)
            error_summary['valuation'].append(ticker)

        if idx < len(VALUATION_TICKERS):
            time.sleep(TICKER_DELAY)

    # Write valuation file
    print(f"\nWriting {OUTPUT_VALUATION}...")
    with pd.ExcelWriter(OUTPUT_VALUATION, engine='openpyxl') as writer:
        # Write existing sheets first
        for sheet_name, df in existing_valuation.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        # Write new data
        for ticker, df in valuation_data.items():
            df.to_excel(writer, sheet_name=ticker, index=False)
    print(f"  {len(existing_valuation) + len(valuation_data)} sheets written")

    # ===== SUMMARY =====
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\nForeign Trading: {len(success_summary['foreign'])}/{len(FOREIGN_TICKERS)} fetched")
    if success_summary['foreign']:
        print(f"  {', '.join(success_summary['foreign'])}")

    print(f"\nValuation: {len(success_summary['valuation'])}/{len(VALUATION_TICKERS)} fetched")
    if success_summary['valuation']:
        print(f"  {', '.join(success_summary['valuation'])}")

    total_errors = len(error_summary['foreign']) + len(error_summary['valuation'])
    if total_errors > 0:
        print("\nERRORS:")
        if error_summary['foreign']:
            print(f"  Foreign: {', '.join(error_summary['foreign'])}")
        if error_summary['valuation']:
            print(f"  Valuation: {', '.join(error_summary['valuation'])}")
        print(f"\nError log: {ERROR_LOG_FILE}")
    else:
        print("\nNo errors!")

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"Updated files:")
    print(f"  1. {OUTPUT_FOREIGN} ({len(existing_foreign) + len(foreign_data)} sheets)")
    print(f"  2. {OUTPUT_VALUATION} ({len(existing_valuation) + len(valuation_data)} sheets)")
    print(f"  3. bank_self_trading.xlsx - NOT UPDATED")
    print(f"\nDuration: {duration}")
    print("=" * 60)

if __name__ == "__main__":
    main()
