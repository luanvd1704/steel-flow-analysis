"""
Date and business day utilities
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime, timedelta


def is_business_day(date: pd.Timestamp) -> bool:
    """
    Check if date is a business day (Monday-Friday)

    Args:
        date: Date to check

    Returns:
        True if business day, False otherwise
    """
    return date.weekday() < 5  # Monday=0, Friday=4


def get_business_days(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DatetimeIndex:
    """
    Get all business days between start and end dates

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        DatetimeIndex of business days
    """
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    business_days = all_dates[all_dates.weekday < 5]

    return business_days


def add_business_days(date: pd.Timestamp, days: int) -> pd.Timestamp:
    """
    Add business days to a date

    Args:
        date: Starting date
        days: Number of business days to add (can be negative)

    Returns:
        Resulting date
    """
    if days == 0:
        return date

    direction = 1 if days > 0 else -1
    days_to_add = abs(days)
    current_date = date

    while days_to_add > 0:
        current_date += timedelta(days=direction)
        if is_business_day(current_date):
            days_to_add -= 1

    return current_date


def get_trading_days_in_month(year: int, month: int) -> int:
    """
    Get number of trading days in a month (approximate, assuming ~21 days)

    Args:
        year: Year
        month: Month

    Returns:
        Number of trading days
    """
    start_date = pd.Timestamp(year=year, month=month, day=1)

    if month == 12:
        end_date = pd.Timestamp(year=year+1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = pd.Timestamp(year=year, month=month+1, day=1) - timedelta(days=1)

    business_days = get_business_days(start_date, end_date)

    return len(business_days)


def align_dates_to_trading_days(dates: pd.DatetimeIndex,
                                 trading_dates: pd.DatetimeIndex,
                                 method: str = 'nearest') -> pd.DatetimeIndex:
    """
    Align dates to actual trading dates

    Args:
        dates: Dates to align
        trading_dates: Actual trading dates
        method: Alignment method ('nearest', 'forward', 'backward')

    Returns:
        Aligned dates
    """
    if method == 'nearest':
        return pd.DatetimeIndex([trading_dates[trading_dates.get_indexer([d], method='nearest')[0]]
                                for d in dates])
    elif method == 'forward':
        return pd.DatetimeIndex([trading_dates[trading_dates.get_indexer([d], method='bfill')[0]]
                                for d in dates if trading_dates.get_indexer([d], method='bfill')[0] >= 0])
    elif method == 'backward':
        return pd.DatetimeIndex([trading_dates[trading_dates.get_indexer([d], method='ffill')[0]]
                                for d in dates if trading_dates.get_indexer([d], method='ffill')[0] >= 0])
    else:
        raise ValueError(f"Unknown method: {method}")


def get_month_start_dates(start_date: pd.Timestamp,
                          end_date: pd.Timestamp,
                          trading_dates: Optional[pd.DatetimeIndex] = None) -> pd.DatetimeIndex:
    """
    Get first trading day of each month

    Args:
        start_date: Start date
        end_date: End date
        trading_dates: Optional actual trading dates to align to

    Returns:
        DatetimeIndex of month start dates
    """
    month_starts = pd.date_range(start=start_date, end=end_date, freq='MS')

    if trading_dates is not None:
        month_starts = align_dates_to_trading_days(month_starts, trading_dates, method='forward')

    return month_starts


def parse_date_string(date_str: str, formats: Optional[List[str]] = None) -> pd.Timestamp:
    """
    Parse date string with multiple format attempts

    Args:
        date_str: Date string
        formats: List of formats to try

    Returns:
        Parsed timestamp
    """
    if formats is None:
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%Y%m%d'
        ]

    for fmt in formats:
        try:
            return pd.Timestamp(datetime.strptime(date_str, fmt))
        except ValueError:
            continue

    # If all formats fail, try pandas default parser
    try:
        return pd.Timestamp(date_str)
    except:
        raise ValueError(f"Cannot parse date string: {date_str}")


def standardize_date_column(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Standardize date column to datetime format

    Args:
        df: DataFrame with date column
        date_col: Name of date column

    Returns:
        DataFrame with standardized date column
    """
    df = df.copy()

    if df[date_col].dtype != 'datetime64[ns]':
        df[date_col] = pd.to_datetime(df[date_col])

    return df


def get_date_range_info(dates: pd.DatetimeIndex) -> dict:
    """
    Get information about a date range

    Args:
        dates: DatetimeIndex

    Returns:
        Dictionary with date range information
    """
    if len(dates) == 0:
        return {
            'start': None,
            'end': None,
            'days': 0,
            'trading_days': 0,
            'years': 0
        }

    start = dates.min()
    end = dates.max()
    total_days = (end - start).days
    trading_days = len(dates)
    years = total_days / 365.25

    return {
        'start': start,
        'end': end,
        'days': total_days,
        'trading_days': trading_days,
        'years': round(years, 2)
    }
