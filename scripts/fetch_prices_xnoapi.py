"""
Fetch prices using xnoapi - match foreign trading date ranges
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime
import time

# Import xnoapi
try:
    from xnoapi import client
    from xnoapi.vn.data.stocks import Quote
except ImportError:
    print("Installing xnoapi...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xnoapi"])
    from xnoapi import client
    from xnoapi.vn.data.stocks import Quote

# Initialize xnoapi client
API_KEY = "hISmRkUzEcJigCEnKkOWWlvz0LXiIyRJZZDGMYAACHj2jWaONUerMW1mjlQuaQD5CCVDsQuvh9khkiRynJ3JVzVJ6XkD-eMYLE0itZJ0xsZLQS2ntS0YPM1TXIWVs4JM"
client(apikey=API_KEY)

FOREIGN_FILE = 'data/bank_foreign_trading.xlsx'

# All 17 tickers in 3 batches
BATCH_1 = ['VCB', 'TCB', 'MBB', 'ACB', 'VPB', 'BID']
BATCH_2 = ['CTG', 'STB', 'HDB', 'TPB', 'VIB', 'SSB']
BATCH_3 = ['SHB', 'MSB', 'LPB', 'OCB', 'EIB']

print("=" * 80)
print("FETCHING PRICES WITH XNOAPI - MATCHED DATE RANGES")
print("=" * 80)

# Load existing foreign trading data
print("\nLoading foreign trading data...")
excel_file = pd.ExcelFile(FOREIGN_FILE)
foreign_data = {}
for ticker in excel_file.sheet_names:
    df = pd.read_excel(FOREIGN_FILE, sheet_name=ticker)
    df['Ngay'] = pd.to_datetime(df['Ngay'])
    foreign_data[ticker] = df

print(f"Loaded {len(foreign_data)} stocks\n")

def fetch_prices_batch(batch_name, tickers):
    """Fetch prices for one batch"""
    print(f"{'=' * 60}")
    print(f"{batch_name}: {len(tickers)} stocks")
    print('=' * 60)

    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] {ticker}...", end=" ")

        try:
            # Get foreign data
            foreign_df = foreign_data.get(ticker)
            if foreign_df is None:
                print("SKIP (no foreign data)")
                continue

            # Get EXACT date range from foreign data
            start_date = foreign_df['Ngay'].min()
            end_date = foreign_df['Ngay'].max()

            print(f"({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})", end=" ")

            # Fetch prices using xnoapi
            q = Quote(ticker)
            price_df = q.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1D'
            )

            if price_df is not None and not price_df.empty:
                # Process price data
                # xnoapi returns 'time' and 'close' columns
                if 'time' in price_df.columns:
                    price_df['Ngay'] = pd.to_datetime(price_df['time'])
                else:
                    price_df['Ngay'] = pd.to_datetime(price_df.index)

                if 'close' in price_df.columns:
                    price_df['Close'] = price_df['close']

                price_df = price_df[['Ngay', 'Close']].copy()

                # Merge with foreign data
                merged_df = pd.merge(foreign_df, price_df, on='Ngay', how='left')
                foreign_data[ticker] = merged_df

                close_count = merged_df['Close'].notna().sum()
                total = len(merged_df)
                pct = (close_count / total * 100) if total > 0 else 0

                print(f"OK ({len(price_df)} prices, {close_count}/{total} merged = {pct:.1f}%)")
            else:
                print("FAIL (no data)")

        except Exception as e:
            print(f"ERROR: {str(e)[:60]}")

        # Delay between requests
        if i < len(tickers):
            time.sleep(15)

# Process all batches
print(f"\n{'=' * 80}")
print("BATCH 1/3")
print('=' * 80)
fetch_prices_batch("BATCH 1", BATCH_1)

print(f"\n\nWaiting 120 seconds before next batch...")
time.sleep(120)

print(f"\n{'=' * 80}")
print("BATCH 2/3")
print('=' * 80)
fetch_prices_batch("BATCH 2", BATCH_2)

print(f"\n\nWaiting 120 seconds before next batch...")
time.sleep(120)

print(f"\n{'=' * 80}")
print("BATCH 3/3")
print('=' * 80)
fetch_prices_batch("BATCH 3", BATCH_3)

# Save updated data
print(f"\n{'=' * 80}")
print("SAVING UPDATED DATA")
print('=' * 80)

with pd.ExcelWriter(FOREIGN_FILE, engine='openpyxl') as writer:
    for ticker in sorted(foreign_data.keys()):
        df = foreign_data[ticker]
        df.to_excel(writer, sheet_name=ticker, index=False)

        has_close = 'Close' in df.columns
        close_count = df['Close'].notna().sum() if has_close else 0
        total = len(df)
        pct = (close_count / total * 100) if total > 0 else 0

        print(f"  {ticker}: {total} rows, {close_count} with Close ({pct:.1f}%)")

print(f"\nOK Successfully saved to {FOREIGN_FILE}")

# Summary
print(f"\n{'=' * 80}")
print("SUMMARY")
print('=' * 80)

success_count = sum(1 for ticker, df in foreign_data.items()
                    if 'Close' in df.columns and df['Close'].notna().sum() > 0)

print(f"Stocks with prices: {success_count}/17")
print(f"Success rate: {success_count/17*100:.1f}%")

print('=' * 80)
