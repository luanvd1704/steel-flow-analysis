#!/usr/bin/env python3
"""
Calculate 9 Banking Metrics for 17 Banks
Input: 3 Excel files (raw_income_statements.xlsx, raw_balance_sheets.xlsx, raw_cash_flows.xlsx)
Output: 9 DataFrames (1 metric per DataFrame, showing all 17 banks)
"""

# Fix Windows console encoding
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from pathlib import Path
from vnstock import Vnstock
import time

# 17 Banks
TICKERS = [
    "VCB", "TCB", "MBB", "ACB", "VPB", "BID", "CTG", "STB",
    "HDB", "TPB", "VIB", "SSB", "SHB", "MSB", "LPB", "OCB", "EIB"
]

def load_excel_data(data_dir="verification_data"):
    """Load 3 Excel files with all sheets"""
    print("Loading Excel files...")

    income_path = Path(data_dir) / "raw_income_statements.xlsx"
    balance_path = Path(data_dir) / "raw_balance_sheets.xlsx"
    cashflow_path = Path(data_dir) / "raw_cash_flows.xlsx"

    income_dict = pd.read_excel(income_path, sheet_name=None)
    balance_dict = pd.read_excel(balance_path, sheet_name=None)
    cashflow_dict = pd.read_excel(cashflow_path, sheet_name=None)

    print(f"✓ Loaded {len(income_dict)} banks from Excel")
    return income_dict, balance_dict, cashflow_dict


def get_quarter_data(df, year, quarter):
    """Get data for specific quarter"""
    mask = (df['yearReport'] == year) & (df['lengthReport'] == quarter)
    result = df[mask]
    return result.iloc[0] if len(result) > 0 else None


def calculate_roa_from_api(ticker):
    """
    Fetch ROA from vnstock API (Q3 2025)
    ROA from API is already in percentage, no need to multiply by 100
    """
    try:
        print(f"      Fetching ROA from API for {ticker}...", end=" ")
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        ratio_df = stock.finance.ratio(period='quarter', lang='en', dropna=True)

        # Get Q3 2025 data (most recent)
        # Columns are MultiIndex: ('Meta', 'yearReport'), ('Meta', 'lengthReport')
        mask = (ratio_df[('Meta', 'yearReport')] == 2025) & (ratio_df[('Meta', 'lengthReport')] == 3)
        q3_data = ratio_df[mask]

        if len(q3_data) > 0:
            # ROA column: ('Chỉ tiêu khả năng sinh lợi', 'ROA (%)')
            roa_col = ('Chỉ tiêu khả năng sinh lợi', 'ROA (%)')
            if roa_col in q3_data.columns:
                roa_value = q3_data.iloc[0][roa_col]
                # Multiply by 100 as requested by user
                roa = float(roa_value) * 100 if roa_value is not None else None
                print(f"✓ ({roa:.2f}%)")
                time.sleep(2)  # Delay to avoid rate limit
                return roa
            else:
                print("✗ (ROA column not found)")
                time.sleep(2)
                return None
        else:
            print("✗ (Q3 2025 data not found)")
            time.sleep(2)
            return None

    except Exception as e:
        print(f"✗ ({e})")
        time.sleep(2)
        return None


def calculate_net_profit_yoy(ticker, income_dict):
    """
    Net Profit YoY (9M YTD) = (NetProfit_9M2025 - NetProfit_9M2024) / NetProfit_9M2024
    9M = Q1 + Q2 + Q3
    """
    try:
        income_df = income_dict[ticker]

        # 9M 2025 = Q1 + Q2 + Q3 2025
        np_q1_2025 = get_quarter_data(income_df, 2025, 1)
        np_q2_2025 = get_quarter_data(income_df, 2025, 2)
        np_q3_2025 = get_quarter_data(income_df, 2025, 3)

        # 9M 2024 = Q1 + Q2 + Q3 2024
        np_q1_2024 = get_quarter_data(income_df, 2024, 1)
        np_q2_2024 = get_quarter_data(income_df, 2024, 2)
        np_q3_2024 = get_quarter_data(income_df, 2024, 3)

        if any(x is None for x in [np_q1_2025, np_q2_2025, np_q3_2025,
                                     np_q1_2024, np_q2_2024, np_q3_2024]):
            return None

        np_9m_2025 = (
            np_q1_2025['Net Profit For the Year'] +
            np_q2_2025['Net Profit For the Year'] +
            np_q3_2025['Net Profit For the Year']
        )

        np_9m_2024 = (
            np_q1_2024['Net Profit For the Year'] +
            np_q2_2024['Net Profit For the Year'] +
            np_q3_2024['Net Profit For the Year']
        )

        if np_9m_2024 == 0:
            return None

        yoy = ((np_9m_2025 - np_9m_2024) / np_9m_2024) * 100
        return yoy

    except Exception as e:
        print(f"Error calculating Net Profit YoY for {ticker}: {e}")
        return None


def calculate_loan_growth(ticker, balance_dict):
    """
    Loan Growth (End-Quarter) = (Loans_Q3/2025 - Loans_Q3/2024) / Loans_Q3/2024
    """
    try:
        balance_df = balance_dict[ticker]

        loans_q3_2025 = get_quarter_data(balance_df, 2025, 3)
        loans_q3_2024 = get_quarter_data(balance_df, 2024, 3)

        if loans_q3_2025 is None or loans_q3_2024 is None:
            return None

        loans_2025 = loans_q3_2025['Loans and advances to customers, net']
        loans_2024 = loans_q3_2024['Loans and advances to customers, net']

        if loans_2024 == 0:
            return None

        growth = ((loans_2025 - loans_2024) / loans_2024) * 100
        return growth

    except Exception as e:
        print(f"Error calculating Loan Growth for {ticker}: {e}")
        return None


def calculate_operating_income_yoy(ticker, income_dict):
    """
    Operating Income YoY (9M YTD) = (OpIncome_9M2025 - OpIncome_9M2024) / OpIncome_9M2024
    """
    try:
        income_df = income_dict[ticker]

        # 9M 2025
        oi_q1_2025 = get_quarter_data(income_df, 2025, 1)
        oi_q2_2025 = get_quarter_data(income_df, 2025, 2)
        oi_q3_2025 = get_quarter_data(income_df, 2025, 3)

        # 9M 2024
        oi_q1_2024 = get_quarter_data(income_df, 2024, 1)
        oi_q2_2024 = get_quarter_data(income_df, 2024, 2)
        oi_q3_2024 = get_quarter_data(income_df, 2024, 3)

        if any(x is None for x in [oi_q1_2025, oi_q2_2025, oi_q3_2025,
                                     oi_q1_2024, oi_q2_2024, oi_q3_2024]):
            return None

        oi_9m_2025 = (
            oi_q1_2025['Total operating revenue'] +
            oi_q2_2025['Total operating revenue'] +
            oi_q3_2025['Total operating revenue']
        )

        oi_9m_2024 = (
            oi_q1_2024['Total operating revenue'] +
            oi_q2_2024['Total operating revenue'] +
            oi_q3_2024['Total operating revenue']
        )

        if oi_9m_2024 == 0:
            return None

        yoy = ((oi_9m_2025 - oi_9m_2024) / oi_9m_2024) * 100
        return yoy

    except Exception as e:
        print(f"Error calculating Operating Income YoY for {ticker}: {e}")
        return None


def calculate_cir_ttm(ticker, income_dict):
    """
    CIR (TTM) = G&A_TTM / TotalOperatingRevenue_TTM
    TTM = Q4/2024 + Q1/2025 + Q2/2025 + Q3/2025
    """
    try:
        income_df = income_dict[ticker]

        q4_2024 = get_quarter_data(income_df, 2024, 4)
        q1_2025 = get_quarter_data(income_df, 2025, 1)
        q2_2025 = get_quarter_data(income_df, 2025, 2)
        q3_2025 = get_quarter_data(income_df, 2025, 3)

        if any(x is None for x in [q4_2024, q1_2025, q2_2025, q3_2025]):
            return None

        # G&A TTM
        ga_ttm = (
            q4_2024['General & Admin Expenses'] +
            q1_2025['General & Admin Expenses'] +
            q2_2025['General & Admin Expenses'] +
            q3_2025['General & Admin Expenses']
        )

        # Total Operating Revenue TTM
        revenue_ttm = (
            q4_2024['Total operating revenue'] +
            q1_2025['Total operating revenue'] +
            q2_2025['Total operating revenue'] +
            q3_2025['Total operating revenue']
        )

        if revenue_ttm == 0:
            return None

        # G&A is negative, so we need absolute value
        cir = (abs(ga_ttm) / revenue_ttm) * 100
        return cir

    except Exception as e:
        print(f"Error calculating CIR for {ticker}: {e}")
        return None


def calculate_equity_to_assets(ticker, balance_dict):
    """
    Equity / Assets = Equity_Q3/2025 / TotalAssets_Q3/2025
    """
    try:
        balance_df = balance_dict[ticker]

        q3_2025 = get_quarter_data(balance_df, 2025, 3)

        if q3_2025 is None:
            return None

        equity = q3_2025["OWNER'S EQUITY(Bn.VND)"]
        assets = q3_2025['TOTAL ASSETS (Bn. VND)']

        if assets == 0:
            return None

        ratio = (equity / assets) * 100
        return ratio

    except Exception as e:
        print(f"Error calculating Equity/Assets for {ticker}: {e}")
        return None


def calculate_ldr(ticker, balance_dict):
    """
    LDR (Loan-to-Deposit Ratio) Q3/2025 = (Loans / Deposits) × 100
    """
    try:
        balance_df = balance_dict[ticker]

        q3_2025 = get_quarter_data(balance_df, 2025, 3)

        if q3_2025 is None:
            return None

        loans = q3_2025['Loans and advances to customers, net']
        deposits = q3_2025['Deposits from customers']

        if deposits == 0:
            return None

        ldr = (loans / deposits) * 100
        return ldr

    except Exception as e:
        print(f"Error calculating LDR for {ticker}: {e}")
        return None


def calculate_fee_ratio_ttm(ticker, income_dict):
    """
    Fee Ratio (TTM) = NetFeeCommission_TTM / TotalOperatingRevenue_TTM
    """
    try:
        income_df = income_dict[ticker]

        q4_2024 = get_quarter_data(income_df, 2024, 4)
        q1_2025 = get_quarter_data(income_df, 2025, 1)
        q2_2025 = get_quarter_data(income_df, 2025, 2)
        q3_2025 = get_quarter_data(income_df, 2025, 3)

        if any(x is None for x in [q4_2024, q1_2025, q2_2025, q3_2025]):
            return None

        # Net Fee Commission TTM
        fee_ttm = (
            q4_2024['Net Fee and Commission Income'] +
            q1_2025['Net Fee and Commission Income'] +
            q2_2025['Net Fee and Commission Income'] +
            q3_2025['Net Fee and Commission Income']
        )

        # Total Operating Revenue TTM
        revenue_ttm = (
            q4_2024['Total operating revenue'] +
            q1_2025['Total operating revenue'] +
            q2_2025['Total operating revenue'] +
            q3_2025['Total operating revenue']
        )

        if revenue_ttm == 0:
            return None

        ratio = (fee_ttm / revenue_ttm) * 100
        return ratio

    except Exception as e:
        print(f"Error calculating Fee Ratio for {ticker}: {e}")
        return None


def calculate_ocf_to_np_ttm(ticker, income_dict, cashflow_dict):
    """
    OCF / Net Profit (TTM) = OCF_TTM / NetProfit_TTM
    """
    try:
        income_df = income_dict[ticker]
        cashflow_df = cashflow_dict[ticker]

        # Net Profit TTM
        np_q4_2024 = get_quarter_data(income_df, 2024, 4)
        np_q1_2025 = get_quarter_data(income_df, 2025, 1)
        np_q2_2025 = get_quarter_data(income_df, 2025, 2)
        np_q3_2025 = get_quarter_data(income_df, 2025, 3)

        # OCF TTM
        ocf_q4_2024 = get_quarter_data(cashflow_df, 2024, 4)
        ocf_q1_2025 = get_quarter_data(cashflow_df, 2025, 1)
        ocf_q2_2025 = get_quarter_data(cashflow_df, 2025, 2)
        ocf_q3_2025 = get_quarter_data(cashflow_df, 2025, 3)

        if any(x is None for x in [np_q4_2024, np_q1_2025, np_q2_2025, np_q3_2025,
                                     ocf_q4_2024, ocf_q1_2025, ocf_q2_2025, ocf_q3_2025]):
            return None

        np_ttm = (
            np_q4_2024['Net Profit For the Year'] +
            np_q1_2025['Net Profit For the Year'] +
            np_q2_2025['Net Profit For the Year'] +
            np_q3_2025['Net Profit For the Year']
        )

        ocf_ttm = (
            ocf_q4_2024['Net cash inflows/outflows from operating activities'] +
            ocf_q1_2025['Net cash inflows/outflows from operating activities'] +
            ocf_q2_2025['Net cash inflows/outflows from operating activities'] +
            ocf_q3_2025['Net cash inflows/outflows from operating activities']
        )

        if np_ttm == 0:
            return None

        ratio = ocf_ttm / np_ttm
        return ratio

    except Exception as e:
        print(f"Error calculating OCF/NP for {ticker}: {e}")
        return None


def calculate_all_metrics(data_dir="verification_data"):
    """Calculate all 8 metrics for all 17 banks → 8 DataFrames"""

    # Load data
    income_dict, balance_dict, cashflow_dict = load_excel_data(data_dir)

    # Initialize result dictionaries
    results = {
        'ROA': {},  # Q3/2025 from API
        'NetProfit_YoY': {},  # 9M YoY
        'LoanGrowth_YoY': {},  # YoY
        'OperatingIncome_YoY': {},  # 9M YoY
        'CIR_TTM': {},  # TTM
        'Equity_to_Assets': {},  # Q3/2025
        'LDR': {},  # Q3/2025
        'FeeRatio_TTM': {},  # TTM
        'OCF_to_NP_TTM': {}  # TTM
    }

    print("\nCalculating metrics for 17 banks...")
    print("="*60)

    for ticker in TICKERS:
        print(f"Processing {ticker}...", end=" ")

        if ticker not in income_dict:
            print(f"SKIP (no data)")
            continue

        # Calculate each metric
        results['ROA'][ticker] = calculate_roa_from_api(ticker)
        results['NetProfit_YoY'][ticker] = calculate_net_profit_yoy(ticker, income_dict)
        results['LoanGrowth_YoY'][ticker] = calculate_loan_growth(ticker, balance_dict)
        results['OperatingIncome_YoY'][ticker] = calculate_operating_income_yoy(ticker, income_dict)
        results['CIR_TTM'][ticker] = calculate_cir_ttm(ticker, income_dict)
        results['Equity_to_Assets'][ticker] = calculate_equity_to_assets(ticker, balance_dict)
        results['LDR'][ticker] = calculate_ldr(ticker, balance_dict)
        results['FeeRatio_TTM'][ticker] = calculate_fee_ratio_ttm(ticker, income_dict)
        results['OCF_to_NP_TTM'][ticker] = calculate_ocf_to_np_ttm(ticker, income_dict, cashflow_dict)

        print("✓")

    # Convert to DataFrames
    print("\n" + "="*60)
    print("Creating DataFrames...")
    print("="*60)

    dfs = {}
    for metric_name, data in results.items():
        df = pd.DataFrame([data]).T
        df.columns = ['Value']
        df.index.name = 'Ticker'
        dfs[metric_name] = df
        print(f"✓ {metric_name}: {len(df)} banks")

    return dfs


def main():
    """Main function"""
    print("="*70)
    print("BANKING METRICS CALCULATOR")
    print("Calculate 9 Metrics for 17 Banks")
    print("="*70)

    # Calculate metrics
    dfs = calculate_all_metrics()

    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    for i, (metric_name, df) in enumerate(dfs.items(), 1):
        print(f"\n[{i}/9] {metric_name}")
        print("-" * 60)
        print(df.round(2))

    # Create consolidated DataFrame: 17 banks × 9 metrics
    print(f"\n{'='*70}")
    print("Creating consolidated table...")
    print("="*70)

    consolidated = pd.DataFrame(index=TICKERS)
    consolidated.index.name = 'Ticker'

    for metric_name, df in dfs.items():
        consolidated[metric_name] = df['Value']

    print(f"✓ Created table: {len(consolidated)} banks × {len(consolidated.columns)} metrics")
    print()
    print(consolidated.round(2))

    # Save to CSV (easy to view)
    csv_file = "banking_metrics.csv"
    consolidated.to_csv(csv_file, encoding='utf-8-sig')
    print(f"\n✓ Saved to: {csv_file}")

    # Save to Excel (single sheet)
    excel_file = "banking_metrics.xlsx"
    consolidated.to_excel(excel_file, engine='openpyxl')
    print(f"✓ Saved to: {excel_file}")

    print("\nDone! 🎉")
    return consolidated


if __name__ == "__main__":
    dfs = main()
