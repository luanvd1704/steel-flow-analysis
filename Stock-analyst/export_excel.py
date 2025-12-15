#!/usr/bin/env python3
"""
Steel Trading & Valuation Data Excel Export
Exports to 3 separate files for better organization:
- steel_foreign_trading.xlsx: CaféF Foreign data (5 years)
- steel_self_trading.xlsx: CaféF Self trading data (5 years)
- steel_valuation.xlsx: Smoney valuation data (P/E, P/B, P/CF)
"""

import pandas as pd
import re
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

# Configuration
STEEL_TICKERS = ["HPG", "HSG", "NKG", "TLH", "VIS", "SMC", "POM", "TVN"]

# Output files (3 separate files)
OUTPUT_FOREIGN = "steel_foreign_trading.xlsx"
OUTPUT_SELF = "steel_self_trading.xlsx"
OUTPUT_VALUATION = "steel_valuation.xlsx"

# Date range for CaféF (5 years)
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)
# CaféF API expects MM/DD/YYYY format (not DD/MM/YYYY)
start_date_str = start_date.strftime("%m/%d/%Y")
end_date_str = end_date.strftime("%m/%d/%Y")

# Delays to avoid rate limiting
TICKER_DELAY = 2.0
SOURCE_DELAY = 1.0

def main():
    print("=" * 60)
    print("STEEL TRADING & VALUATION DATA EXPORT")
    print("=" * 60)
    print(f"Tickers: {', '.join(STEEL_TICKERS)}")
    print(f"Output files:")
    print(f"  1. {OUTPUT_FOREIGN}")
    print(f"  2. {OUTPUT_SELF}")
    print(f"  3. {OUTPUT_VALUATION}")
    print(f"CaféF range: {start_date_str} to {end_date_str}")
    print("=" * 60)

    start_time = datetime.datetime.now()

    # Create 3 separate ExcelWriters
    with pd.ExcelWriter(OUTPUT_FOREIGN, engine='openpyxl') as writer_foreign, \
         pd.ExcelWriter(OUTPUT_SELF, engine='openpyxl') as writer_self, \
         pd.ExcelWriter(OUTPUT_VALUATION, engine='openpyxl') as writer_valuation:

        for idx, ticker in enumerate(STEEL_TICKERS, 1):
            print(f"\n[{idx}/{len(STEEL_TICKERS)}] Processing {ticker}...")

            # 1. CaféF Foreign Trading -> steel_foreign_trading.xlsx
            try:
                print(f"  Fetching CaféF Foreign...")
                cafef_foreign = fetch_cafef_foreign_trades(ticker, start_date_str, end_date_str)
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
                else:
                    print(f"    No data")
                time.sleep(SOURCE_DELAY)
            except Exception as e:
                print(f"    Error: {e}")

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
                else:
                    print(f"    No data")
                time.sleep(SOURCE_DELAY)
            except Exception as e:
                print(f"    Error: {e}")

            # 3. Smoney Valuation -> steel_valuation.xlsx
            try:
                print(f"  Fetching Smoney Valuation...")
                smoney_val = fetch_valuation_history(ticker)
                if not smoney_val.empty:
                    sheet_name = ticker  # Simplified sheet name
                    smoney_val.to_excel(writer_valuation, sheet_name=sheet_name, index=False)
                    print(f"    OK: {smoney_val.shape[0]} rows -> {OUTPUT_VALUATION}")
                else:
                    print(f"    No data")
            except Exception as e:
                print(f"    Error: {e}")

            # Delay between tickers
            if idx < len(STEEL_TICKERS):
                print(f"  Waiting {TICKER_DELAY}s...")
                time.sleep(TICKER_DELAY)

    # =========================
    # VNINDEX MARKET DATA
    # =========================
    print("\n" + "=" * 60)
    print("FETCHING VNINDEX MARKET DATA")
    print("=" * 60)

    try:
        # Fetch VNINDEX using existing function (returns DataFrame directly)
        vnindex_df = fetch_vnstock_adjusted_prices(
            symbol='VNINDEX',  # Note: singular 'symbol', not 'tickers'
            start_date='2020-12-14',
            end_date=end_date.strftime('%Y-%m-%d'),  # Convert datetime to string
            source='VCI'
        )

        # Rename columns for clarity (date is already renamed by function)
        vnindex_df = vnindex_df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        # Select relevant columns
        vnindex_df = vnindex_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        vnindex_df = vnindex_df.sort_values('Date').reset_index(drop=True)

        # Save to Excel
        output_file = Path(__file__).parent / 'vnindex_market.xlsx'

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            vnindex_df.to_excel(writer, sheet_name='VNINDEX', index=False)

        print(f"OK: VNINDEX: {len(vnindex_df)} sessions ({vnindex_df['Date'].min().date()} to {vnindex_df['Date'].max().date()})")
        print(f"    Saved: {output_file}")

    except Exception as e:
        print(f"    Error fetching VNINDEX: {e}")

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("EXPORT COMPLETED!")
    print("=" * 60)
    print(f"Files created:")
    print(f"  1. {OUTPUT_FOREIGN} (Foreign trading)")
    print(f"  2. {OUTPUT_SELF} (Self trading)")
    print(f"  3. {OUTPUT_VALUATION} (Valuation metrics)")
    print(f"  4. vnindex_market.xlsx (VNINDEX market data)")
    print(f"Tickers per file: {len(STEEL_TICKERS)}")
    print(f"Duration: {duration}")
    print("=" * 60)

if __name__ == "__main__":
    main()
