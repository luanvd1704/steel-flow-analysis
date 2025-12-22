#!/usr/bin/env python3
"""
Banking Sector Financial Statements Fetcher - 17 Banks Vietnam
Fetches quarterly financial statements and calculates 8 banking metrics using TTM + YTD methodology

METHODOLOGY:
- TTM (Trailing Twelve Months): ROA, CIR, Fee Ratio, OCF/Net Profit
- YTD YoY (9 months year-to-date): Net Profit YoY, Operating Income YoY
- End-Quarter: Loan Growth, Equity/Assets

REMOVED METRICS (require detailed notes from financial statements):
- NIM (requires earning assets breakdown)
- Credit Cost (requires loan quality breakdown)
- LDR (requires deposits breakdown)

WEIGHT CONFIGURATION:
- Normal weight (1.0): ROA, Net Profit YoY, Operating Income YoY, CIR, Equity/Assets, Fee Ratio
- Medium weight (0.5): Loan Growth (high noise)
- Warning flag (0.25): OCF/Net Profit (very high noise in banking CFO)

Output: 17 sheets (one per ticker) in data/bank_financials.xlsx
"""

import time
import pandas as pd
import numpy as np
import argparse
import os
import traceback
from vnstock import Vnstock
from datetime import datetime

# 17 Banks Configuration
TICKERS = [
    "VCB",  # Vietcombank
    "TCB",  # Techcombank
    "MBB",  # MB Bank
    "ACB",  # ACB
    "VPB",  # VPBank
    "BID",  # BIDV
    "CTG",  # VietinBank
    "STB",  # Sacombank
    "HDB",  # HDBank
    "TPB",  # TPBank
    "VIB",  # VIB
    "SSB",  # Southeast Asia Bank
    "SHB",  # SHB
    "MSB",  # MSB
    "LPB",  # LienVietPostBank
    "OCB",  # OCB
    "EIB"   # Eximbank
]

QUARTERS = 8  # 8 quarters of data
SOURCE = "VCI"
DELAY = 4.0  # Delay between requests

# Banking Metrics Metadata
BANK_METRICS = {
    'roa': {'name': 'ROA', 'group': 'Profitability', 'direction': 'higher_is_better'},
    'nim': {'name': 'NIM', 'group': 'Profitability', 'direction': 'higher_is_better'},
    'credit_cost': {'name': 'Credit Cost', 'group': 'Asset Quality', 'direction': 'lower_is_better'},
    'net_profit_cagr': {'name': 'Net Profit CAGR', 'group': 'Growth', 'direction': 'higher_is_better'},
    'loan_growth': {'name': 'Loan Growth', 'group': 'Growth', 'direction': 'higher_is_better'},
    'operating_income_yoy': {'name': 'Operating Income YoY', 'group': 'Growth', 'direction': 'higher_is_better'},
    'cir': {'name': 'CIR', 'group': 'Efficiency', 'direction': 'lower_is_better'},
    'equity_assets': {'name': 'Equity/Assets', 'group': 'Capital & Liquidity', 'direction': 'optimal_range', 'optimal': (7, 12)},
    'ldr': {'name': 'LDR', 'group': 'Capital & Liquidity', 'direction': 'optimal_range', 'optimal': (70, 85)},
    'fee_ratio': {'name': 'Fee Ratio', 'group': 'Income Structure', 'direction': 'higher_is_better'},
    'ocf_net_profit': {'name': 'OCF/Net Profit', 'group': 'Cashflow Quality', 'direction': 'higher_is_better'}
}

# Error logging
ERROR_LOG_FILE = "data/fetch_bank_financials_errors.log"

def log_error(ticker, error_msg, tb_str):
    """Log error to file with timestamp and full traceback"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] {ticker}\n")
        f.write(f"Error: {error_msg}\n")
        f.write(f"Traceback:\n{tb_str}\n")
        f.write(f"{'='*80}\n")


def fetch_statement(ticker, stmt_type, period='quarter', max_periods=8):
    """Fetch single financial statement for a ticker"""
    try:
        print(f"  [FETCH] {ticker} - {stmt_type} ({period})...")

        st = Vnstock().stock(ticker, source=SOURCE)

        # Call API
        if stmt_type == "income_statement":
            df = st.finance.income_statement(period=period, lang="en", dropna=True)
        elif stmt_type == "balance_sheet":
            df = st.finance.balance_sheet(period=period, lang="en", dropna=True)
        elif stmt_type == "cash_flow":
            df = st.finance.cash_flow(period=period, dropna=True)
        else:
            return pd.DataFrame()

        if df.empty:
            print(f"  [FAIL] {ticker} - No data")
            return pd.DataFrame()

        # Sort and limit
        if period == "quarter" and {'yearReport', 'lengthReport'}.issubset(df.columns):
            df = df.sort_values(["yearReport", "lengthReport"], ascending=[False, False]).head(max_periods)
        elif period == "year" and "yearReport" in df.columns:
            df = df.sort_values("yearReport", ascending=False).head(max_periods)

        print(f"  [OK] {ticker} - Got {len(df)} records")
        return df

    except Exception as e:
        print(f"  [ERROR] {ticker} - Error: {str(e)[:100]}")
        return pd.DataFrame()


def calculate_banking_metrics(ticker_data):
    """
    Calculate 8 banking metrics from raw financial statements using TTM + YTD methodology

    TTM (Trailing Twelve Months): ROA, CIR, Fee Ratio, OCF/Net Profit
    YTD YoY (9 months): Net Profit YoY, Operating Income YoY
    End-Quarter: Loan Growth, Equity/Assets

    REMOVED: NIM, Credit Cost, LDR (require detailed notes from financial statements)

    Args:
        ticker_data: dict with keys 'income_statement', 'balance_sheet', 'cash_flow'

    Returns:
        DataFrame with calculated metrics per quarter (TTM basis)
    """
    is_df = ticker_data.get('income_statement', pd.DataFrame())
    bs_df = ticker_data.get('balance_sheet', pd.DataFrame())
    cf_df = ticker_data.get('cash_flow', pd.DataFrame())

    if is_df.empty or bs_df.empty:
        return pd.DataFrame()

    # Merge all statements on yearReport + lengthReport
    merged = is_df.copy()

    if not bs_df.empty:
        merged = merged.merge(
            bs_df,
            on=['yearReport', 'lengthReport'],
            how='left',
            suffixes=('', '_bs')
        )

    if not cf_df.empty:
        merged = merged.merge(
            cf_df,
            on=['yearReport', 'lengthReport'],
            how='left',
            suffixes=('', '_cf')
        )

    # CRITICAL: Sort by year and quarter DESCENDING (latest first)
    merged = merged.sort_values(['yearReport', 'lengthReport'], ascending=[False, False]).reset_index(drop=True)

    # Initialize metrics DataFrame
    metrics_df = pd.DataFrame()
    metrics_df['year'] = merged['yearReport']
    metrics_df['quarter'] = merged['lengthReport']

    # Helper function to safely get column value (returns Series)
    def safe_get(df, col_name, default=np.nan):
        if col_name in df.columns:
            return df[col_name].fillna(default)
        return pd.Series([default] * len(df), index=df.index)

    # Extract key financial metrics using vnstock field names
    # Income Statement fields
    net_profit = safe_get(merged, 'Net Profit For the Year', 0)
    interest_income = safe_get(merged, 'Interest and Similar Income', 0)
    interest_expense = safe_get(merged, 'Interest and Similar Expenses', 0)
    fee_income = safe_get(merged, 'Net Fee and Commission Income', 0)
    operating_income = safe_get(merged, 'Total operating revenue', 1)
    operating_expense = safe_get(merged, 'General & Admin Expenses', 0).abs()
    provision = safe_get(merged, 'Provision for credit losses', 0).abs()

    # Balance Sheet fields
    total_assets = safe_get(merged, 'TOTAL ASSETS (Bn. VND)', 1)
    equity = safe_get(merged, "OWNER'S EQUITY(Bn.VND)", 0)
    total_loans = safe_get(merged, 'Loans and advances to customers, net', 1)
    deposits = safe_get(merged, 'Deposits from customers', 1)

    # Cash Flow fields
    ocf = safe_get(merged, 'Cash flows from Operating Activities', 0)

    # ========================================================================
    # TTM METRICS (Trailing Twelve Months) - Sum of last 4 quarters
    # ========================================================================

    # Rolling sum for TTM calculation (4 quarters)
    net_profit_ttm = net_profit.rolling(window=4, min_periods=4).sum()
    net_interest_ttm = (interest_income + interest_expense).rolling(window=4, min_periods=4).sum()
    provision_ttm = provision.rolling(window=4, min_periods=4).sum()
    operating_expense_ttm = operating_expense.rolling(window=4, min_periods=4).sum()
    operating_income_ttm = operating_income.rolling(window=4, min_periods=4).sum()
    fee_income_ttm = fee_income.rolling(window=4, min_periods=4).sum()
    ocf_ttm = ocf.rolling(window=4, min_periods=4).sum()

    # Average total assets for TTM (use average of first and last quarter in TTM window)
    total_assets_avg = total_assets.rolling(window=4, min_periods=4).mean()
    total_loans_avg = total_loans.rolling(window=4, min_periods=4).mean()

    # 1. ROA (TTM) = Total Net Profit Last 4Q / Avg Total Assets * 100
    metrics_df['roa'] = (net_profit_ttm / total_assets_avg * 100).round(2)

    # 2. NIM (TTM) = Total Net Interest Last 4Q / Avg Total Assets * 100
    # REMOVED: Requires detailed notes from financial statements (earning assets breakdown)
    # metrics_df['nim'] = (net_interest_ttm / total_assets_avg * 100).round(2)

    # 3. Credit Cost (TTM) = Total Provision Last 4Q / Avg Total Loans * 100
    # REMOVED: Requires detailed notes from financial statements (loan quality breakdown)
    # metrics_df['credit_cost'] = (provision_ttm / total_loans_avg * 100).round(2)

    # 4. CIR (TTM) = Total Operating Expense Last 4Q / Total Operating Income Last 4Q * 100
    metrics_df['cir'] = (operating_expense_ttm / operating_income_ttm * 100).round(2)

    # 7. Fee Ratio (TTM) = Total Fee Income Last 4Q / Total Operating Income Last 4Q * 100
    metrics_df['fee_ratio'] = (fee_income_ttm / operating_income_ttm * 100).round(2)

    # 8. OCF/Net Profit (TTM) = Total OCF Last 4Q / Total Net Profit Last 4Q
    metrics_df['ocf_net_profit'] = (ocf_ttm / net_profit_ttm.replace(0, np.nan)).round(2)

    # ========================================================================
    # END-QUARTER METRICS (Point-in-time from Balance Sheet)
    # ========================================================================

    # 5. Equity/Assets ratio (End-Quarter)
    metrics_df['equity_assets'] = (equity / total_assets * 100).round(2)

    # 6. LDR = Loan-to-Deposit Ratio (End-Quarter)
    # REMOVED: Requires detailed notes from financial statements (deposits breakdown)
    # metrics_df['ldr'] = (total_loans / deposits * 100).round(2)

    # ========================================================================
    # GROWTH METRICS
    # ========================================================================

    # Helper function to calculate 9T (9-month YTD) sum
    def calc_9m_ytd(series):
        """Calculate 9-month YTD for each row based on quarter"""
        result = pd.Series(index=series.index, dtype=float)
        for idx in series.index:
            year = merged.loc[idx, 'yearReport']
            quarter = merged.loc[idx, 'lengthReport']

            if quarter >= 3:  # Q3 or Q4
                # Sum Q1 + Q2 + Q3 of current year
                mask = (merged['yearReport'] == year) & (merged['lengthReport'].isin([1, 2, 3]))
                result.loc[idx] = series[mask].sum() if mask.any() else np.nan
            else:
                result.loc[idx] = np.nan

        return result

    # Net Profit 9T YTD
    net_profit_9m = calc_9m_ytd(net_profit)
    net_profit_9m_lastyear = calc_9m_ytd(net_profit).shift(-4)  # Same quarters last year

    # Operating Income 9T YTD
    operating_income_9m = calc_9m_ytd(operating_income)
    operating_income_9m_lastyear = calc_9m_ytd(operating_income).shift(-4)

    # 9. Net Profit YoY (9T YTD)
    metrics_df['net_profit_yoy'] = ((net_profit_9m - net_profit_9m_lastyear) / net_profit_9m_lastyear.abs().replace(0, np.nan) * 100).round(2)

    # 10. Operating Income YoY (9T YTD)
    metrics_df['operating_income_yoy'] = ((operating_income_9m - operating_income_9m_lastyear) / operating_income_9m_lastyear.abs().replace(0, np.nan) * 100).round(2)

    # 11. Loan Growth YoY (End-Quarter comparison)
    # Compare End-Q3 2024 vs End-Q3 2023
    total_loans_lastyear = total_loans.shift(-4)
    metrics_df['loan_growth'] = ((total_loans - total_loans_lastyear) / total_loans_lastyear.replace(0, np.nan) * 100).round(2)

    # Clean up infinities and NaN
    metrics_df = metrics_df.replace([np.inf, -np.inf], np.nan)

    return metrics_df


def fetch_ticker_data(ticker):
    """Fetch all financial statements for a ticker and calculate metrics"""
    print(f"\n{'='*60}")
    print(f"Processing: {ticker}")
    print(f"{'='*60}")

    ticker_data = {}

    # Fetch 3 statements
    for stmt_type in ['income_statement', 'balance_sheet', 'cash_flow']:
        df = fetch_statement(ticker, stmt_type, period='quarter', max_periods=QUARTERS)
        if not df.empty:
            ticker_data[stmt_type] = df
        time.sleep(DELAY)

    # Calculate metrics
    if ticker_data:
        metrics_df = calculate_banking_metrics(ticker_data)
        if not metrics_df.empty:
            metrics_df.insert(0, 'ticker', ticker)
            print(f"  [SUCCESS] Calculated {len(metrics_df)} quarters of metrics")
            return metrics_df

    print(f"  [FAIL] Could not calculate metrics for {ticker}")
    return pd.DataFrame()


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

def main():
    parser = argparse.ArgumentParser(
        description='Banking Sector - Financial Metrics Fetcher (17 Banks)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all 17 banks
  python fetch_bank_financials.py

  # Retry mode: Only fetch tickers missing from existing file
  python fetch_bank_financials.py --retry

  # Fetch specific ticker
  python fetch_bank_financials.py --ticker VCB

  # Fetch multiple tickers
  python fetch_bank_financials.py --tickers VCB,TCB,MBB
        """
    )

    parser.add_argument('--retry', action='store_true',
                       help='Only fetch tickers missing from existing file')
    parser.add_argument('--ticker', help='Single ticker to fetch (e.g., VCB)')
    parser.add_argument('--tickers', help='Multiple tickers comma-separated (e.g., VCB,TCB,MBB)')
    args = parser.parse_args()

    # Output file path
    output_file = "data/bank_financials.xlsx"

    # Determine which tickers to fetch
    if args.ticker:
        tickers_to_fetch = [args.ticker.upper()]
        print(f"[MODE] Single ticker: {tickers_to_fetch[0]}")
        mode = "append"
    elif args.tickers:
        tickers_to_fetch = [t.strip().upper() for t in args.tickers.split(',')]
        print(f"[MODE] Multiple tickers ({len(tickers_to_fetch)}): {', '.join(tickers_to_fetch)}")
        mode = "append"
    elif args.retry:
        # Retry mode: find missing tickers
        print(f"[MODE] Retry - checking existing file...")
        existing_tickers = get_existing_tickers(output_file)
        missing_tickers = [t for t in TICKERS if t not in existing_tickers]

        if not missing_tickers:
            print("✅ All 17 tickers already exist in file. Nothing to fetch!")
            return

        tickers_to_fetch = missing_tickers
        print(f"  Existing: {len(existing_tickers)} tickers - {', '.join(existing_tickers)}")
        print(f"  Missing: {len(missing_tickers)} tickers - {', '.join(missing_tickers)}")
        print(f"  Will fetch: {', '.join(tickers_to_fetch)}")
        mode = "append"
    else:
        tickers_to_fetch = TICKERS
        print(f"[MODE] All 17 banks: {', '.join(TICKERS)}")
        mode = "overwrite"

    print(f"Quarters: {QUARTERS} | Source: {SOURCE}")
    print()

    # Clear previous error log
    if os.path.exists(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)

    # Track successes and failures
    all_results = {}
    failed_tickers = []

    for i, ticker in enumerate(tickers_to_fetch, 1):
        print(f"\n[{i}/{len(tickers_to_fetch)}] Processing {ticker}...")
        try:
            metrics_df = fetch_ticker_data(ticker)
            if not metrics_df.empty:
                all_results[ticker] = metrics_df
            else:
                failed_tickers.append(ticker)
        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()
            print(f"  ❌ ERROR: {error_msg}")
            print(f"  (Chi tiết lỗi đã lưu vào {ERROR_LOG_FILE})")
            log_error(ticker, error_msg, tb_str)
            failed_tickers.append(ticker)

    # Save to Excel - 17 sheets (one per ticker)
    if all_results:
        # Create data folder if not exists
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Load existing data if in append mode
        existing_data = {}
        if mode == "append" and os.path.exists(output_file):
            print(f"\nLoading existing data from {output_file}...")
            xl = pd.ExcelFile(output_file)
            for sheet in xl.sheet_names:
                existing_data[sheet] = pd.read_excel(output_file, sheet_name=sheet)
            print(f"  Loaded {len(existing_data)} existing sheets")

        print(f"\n{'='*60}")
        print("EXPORTING TO EXCEL")
        print(f"{'='*60}")

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write existing data first if in append mode
                if mode == "append" and existing_data:
                    print("\nWriting existing data...")
                    for ticker, df in existing_data.items():
                        df.to_excel(writer, sheet_name=ticker, index=False)

                # Write new data
                print(f"\nWriting {len(all_results)} new sheets...")
                for ticker, df in all_results.items():
                    df.to_excel(writer, sheet_name=ticker, index=False)
                    print(f"[SAVED] {ticker}: {len(df)} quarters")

            print(f"\n{'='*60}")
            print(f"📊 SUMMARY")
            print(f"{'='*60}")

            # Success summary
            print(f"\n✅ SUCCESSES: {len(all_results)}/{len(tickers_to_fetch)} banks fetched")
            if all_results:
                print(f"   {', '.join(all_results.keys())}")

            # Failure summary
            if failed_tickers:
                print(f"\n❌ FAILURES: {len(failed_tickers)} banks")
                print(f"   {', '.join(failed_tickers)}")
                print(f"\n📝 Chi tiết lỗi đã lưu vào: {ERROR_LOG_FILE}")
            else:
                print(f"\n✅ No failures!")

            # Final file statistics
            if mode == "append":
                total_sheets = len(existing_data) + len(all_results)
                print(f"\n📊 Total sheets in file: {total_sheets}")
                print(f"   Existing: {len(existing_data)}")
                print(f"   Newly added: {len(all_results)}")

            print(f"\n{'='*60}")
            print(f"SUCCESS! File {'updated' if mode == 'append' else 'saved'}: {output_file}")
            print(f"{'='*60}")
            print(f"Banks fetched: {len(all_results)}/{len(tickers_to_fetch)}")
            if mode == "overwrite":
                print(f"Total sheets in Excel: {len(all_results)}")
            else:
                print(f"Total sheets in Excel: {len(existing_data) + len(all_results)}")

        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()
            print(f"\n❌ [ERROR] Failed to save Excel file: {error_msg}")
            print(f"Traceback:\n{tb_str}")
    else:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: No data collected")
        print(f"{'='*60}")
        if failed_tickers:
            print(f"Failed tickers ({len(failed_tickers)}): {', '.join(failed_tickers)}")
            print(f"Chi tiết lỗi: {ERROR_LOG_FILE}")


if __name__ == "__main__":
    main()
