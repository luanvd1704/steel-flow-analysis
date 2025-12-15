import requests
import pandas as pd
import datetime
from typing import List, Dict, Any, Optional


def _fetch_json_rows(
    url: str,
    symbol: str,
    list_key: str,
    start_date: str = "",
    end_date: str = "",
    page_size: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Internal helper to iterate through CaféF's paginated JSON API.

    - Không bắt buộc truyền StartDate/EndDate (giống request trên web).
    - Phân trang đến khi API trả về records rỗng.
    """
    page_index = 1
    rows: List[Dict[str, Any]] = []
    total_count = None

    while True:
        # Các tham số cơ bản giống như request trên web
        params: Dict[str, Any] = {
            "Symbol": symbol,
            "PageIndex": page_index,
            "PageSize": page_size,
        }

        # Chỉ truyền StartDate/EndDate nếu có thiết lập
        if start_date:
            params["StartDate"] = start_date  # dd/MM/yyyy
        if end_date:
            params["EndDate"] = end_date      # dd/MM/yyyy

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Referer": "https://cafef.vn/",
            "Accept": "application/json, text/plain, */*",
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data_json = response.json()
        data_section = data_json.get("Data", {})

        if total_count is None:
            total_count = data_section.get("TotalCount", 0)

        # Lấy danh sách record theo cấu trúc JSON của CafeF
        if list_key in data_section:
            records = data_section.get(list_key, [])
        else:
            inner = data_section.get("Data", {})
            records = inner.get(list_key, [])

        # Nếu page hiện tại không còn bản ghi -> dừng
        if not records:
            break

        rows.extend(records)

        # Nếu TotalCount là tổng số bản ghi thật sự thì điều kiện này giúp tránh gọi thừa
        if total_count and len(rows) >= total_count:
            break

        page_index += 1

    return rows


def fetch_cafef_foreign_trades(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
    page_size: int = 2000,
) -> pd.DataFrame:
    """
    Download all foreign trading records for a given ticker from CaféF.

    API: https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx
    """
    base_url = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx"

    rows = _fetch_json_rows(
        base_url,
        symbol,
        list_key="Data",
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
    )

    df = pd.DataFrame(rows)

    if not df.empty and "Ngay" in df.columns:
        # Cột Ngày dạng dd/MM/yyyy
        df["Ngay"] = pd.to_datetime(df["Ngay"], format="%d/%m/%Y")

    return df


def fetch_cafef_self_trades(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
    page_size: int = 1000,
) -> pd.DataFrame:
    """
    Download all proprietary trading records (tự doanh) from CaféF.

    API: https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDTuDoanh.ashx
    """
    base_url = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDTuDoanh.ashx"

    rows = _fetch_json_rows(
        base_url,
        symbol,
        list_key="ListDataTudoanh",
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
    )

    df = pd.DataFrame(rows)

    if not df.empty and "Date" in df.columns:
        # Cột Date dạng dd/MM/yyyy
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    return df


def fetch_vnstock_adjusted_prices(
    symbol: str,
    start_date: str = "2020-01-01",
    end_date: Optional[str] = None,
    source: str = "VCI",
) -> pd.DataFrame:
    """
    Fetch historical adjusted prices from vnstock API.

    Args:
        symbol: Stock ticker (HPG, HSG, NKG, etc.)
        start_date: Start date (YYYY-MM-DD format), default='2020-01-01'
        end_date: End date (YYYY-MM-DD format), default=today
        source: Data source ('VCI' or 'TCBS'), default='VCI'

    Returns:
        DataFrame with columns: ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']

    Example:
        df = fetch_vnstock_adjusted_prices('HPG', start_date='2023-01-01')
    """
    try:
        from vnstock import Vnstock
    except ImportError:
        raise ImportError("vnstock not installed. Install: pip install vnstock")

    if end_date is None:
        end_date = pd.Timestamp.now().strftime('%Y-%m-%d')

    # Fetch historical data from vnstock
    stock = Vnstock().stock(symbol=symbol, source=source)
    df = stock.quote.history(start=start_date, end=end_date)

    # Rename columns to standard format
    df = df.rename(columns={'time': 'date'})

    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Add ticker column
    df['ticker'] = symbol

    # VCI source's 'close' is already adjusted price
    # Rename close to adj_close for clarity
    df['adj_close'] = df['close']

    # Select and order columns
    columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']

    return df[columns].reset_index(drop=True)
