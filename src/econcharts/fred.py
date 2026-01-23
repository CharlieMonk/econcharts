"""FRED (Federal Reserve Economic Data) utilities for econcharts.

This module provides functions to fetch real economic data from FRED
for use in examples and tests. Data can be cached locally for offline use.

Common FRED Series IDs:
    - GDP: A191RL1Q225SBEA (Real GDP growth, quarterly)
    - CPI: CPIAUCSL (Consumer Price Index, monthly)
    - Unemployment: UNRATE (Unemployment Rate, monthly)
    - Fed Funds: FEDFUNDS (Federal Funds Rate, monthly)
    - 10Y Treasury: DGS10 (10-Year Treasury Rate, daily)
    - S&P 500: SP500 (S&P 500 Index, daily)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# Cache directory for offline data
CACHE_DIR = Path(__file__).parent / "data"

# FRED public CSV endpoint (no API key required)
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# Common economic series with metadata
SERIES_INFO = {
    "GDP": {
        "id": "A191RL1Q225SBEA",
        "name": "Real GDP Growth",
        "frequency": "quarterly",
        "unit": "% Change",
    },
    "CPI": {
        "id": "CPIAUCSL",
        "name": "Consumer Price Index",
        "frequency": "monthly",
        "unit": "Index",
    },
    "INFLATION": {
        "id": "CPALTT01USM657N",
        "name": "Inflation Rate",
        "frequency": "monthly",
        "unit": "% YoY",
    },
    "UNEMPLOYMENT": {
        "id": "UNRATE",
        "name": "Unemployment Rate",
        "frequency": "monthly",
        "unit": "%",
    },
    "FEDFUNDS": {
        "id": "FEDFUNDS",
        "name": "Federal Funds Rate",
        "frequency": "monthly",
        "unit": "%",
    },
    "TREASURY_10Y": {
        "id": "DGS10",
        "name": "10-Year Treasury Rate",
        "frequency": "daily",
        "unit": "%",
    },
    "SP500": {
        "id": "SP500",
        "name": "S&P 500 Index",
        "frequency": "daily",
        "unit": "Index",
    },
}


def _get_cache_path(series_id: str) -> Path:
    """Get the cache file path for a series."""
    return CACHE_DIR / f"{series_id}.json"


def _load_from_cache(series_id: str) -> Optional[tuple[list, list]]:
    """Load data from local cache if available.

    Returns:
        Tuple of (dates, values) or None if not cached.
    """
    cache_path = _get_cache_path(series_id)
    if not cache_path.exists():
        return None

    with open(cache_path) as f:
        data = json.load(f)

    dates = [datetime.fromisoformat(d) for d in data["dates"]]
    values = data["values"]
    return dates, values


def _save_to_cache(series_id: str, dates: list, values: list) -> None:
    """Save data to local cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = _get_cache_path(series_id)

    data = {
        "series_id": series_id,
        "cached_at": datetime.now().isoformat(),
        "dates": [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in dates],
        "values": [float(v) if v is not None else None for v in values],
    }

    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)


def _fetch_from_csv(
    series_id: str,
    start: str = "2000-01-01",
    end: Optional[str] = None,
) -> tuple[list, list]:
    """Fetch data directly from FRED's public CSV endpoint.

    This method doesn't require an API key and works as a reliable fallback
    when pandas_datareader or fredapi are unavailable or broken.

    Args:
        series_id: FRED series identifier.
        start: Start date in 'YYYY-MM-DD' format.
        end: End date in 'YYYY-MM-DD' format (defaults to today).

    Returns:
        Tuple of (dates, values) where dates are datetime objects.

    Raises:
        RuntimeError: If the CSV download fails.
    """
    end_dt = end if end else datetime.now().strftime("%Y-%m-%d")

    params = {
        "id": series_id,
        "cosd": start,
        "coed": end_dt,
    }

    try:
        response = requests.get(FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download CSV for {series_id}: {e}")

    # Parse CSV content
    lines = response.text.strip().split('\n')
    if len(lines) < 2:
        raise RuntimeError(f"No data returned for {series_id}")

    dates = []
    values = []

    for line in lines[1:]:  # Skip header row
        parts = line.split(',')
        if len(parts) >= 2:
            date_str = parts[0].strip()
            value_str = parts[1].strip()

            # Skip missing values (FRED uses '.' for missing data)
            if value_str and value_str != '.':
                try:
                    # Parse date (YYYY-MM-DD format)
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    val = float(value_str)
                    dates.append(dt)
                    values.append(val)
                except (ValueError, TypeError):
                    # Skip malformed rows
                    pass

    if not dates:
        raise RuntimeError(f"No valid data points found for {series_id}")

    return dates, values


def fetch_fred(
    series_id: str,
    start: str = "2000-01-01",
    end: Optional[str] = None,
    use_cache: bool = True,
) -> tuple[list, list]:
    """Fetch data from FRED (Federal Reserve Economic Data).

    Args:
        series_id: FRED series identifier (e.g., 'UNRATE', 'GDP').
                  Can also use friendly names like 'UNEMPLOYMENT', 'GDP'.
        start: Start date in 'YYYY-MM-DD' format.
        end: End date in 'YYYY-MM-DD' format (defaults to today).
        use_cache: If True, try cache first and cache fetched data.

    Returns:
        Tuple of (dates, values) where dates are datetime objects
        and values are floats.

    Example:
        >>> dates, values = fetch_fred('UNRATE', '2020-01-01')
        >>> chart.add_line(row=1, x=dates, y=values, name='Unemployment')
    """
    # Resolve friendly names to series IDs
    if series_id.upper() in SERIES_INFO:
        series_id = SERIES_INFO[series_id.upper()]["id"]

    # Try cache first
    if use_cache:
        cached = _load_from_cache(series_id)
        if cached is not None:
            dates, values = cached
            # Filter to requested date range
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end) if end else datetime.now()
            filtered = [(d, v) for d, v in zip(dates, values)
                       if start_dt <= d <= end_dt and v is not None]
            if filtered:
                return [d for d, _ in filtered], [v for _, v in filtered]

    # Try multiple methods to fetch data from FRED
    # Priority: 1) fredapi, 2) pandas_datareader, 3) CSV download, 4) cache
    fetched = False
    dates = None
    values = None
    last_error = None

    # Method 1: Try fredapi (requires API key)
    try:
        from fredapi import Fred
        import os

        api_key = os.environ.get("FRED_API_KEY")
        if api_key:
            fred = Fred(api_key=api_key)
            end_dt = end if end else datetime.now().strftime("%Y-%m-%d")
            series = fred.get_series(series_id, observation_start=start, observation_end=end_dt)

            dates = series.index.to_pydatetime().tolist()
            values = series.tolist()

            # Remove NaN values
            filtered = [(d, v) for d, v in zip(dates, values) if v == v]  # NaN != NaN
            dates = [d for d, _ in filtered]
            values = [v for _, v in filtered]
            fetched = True
    except Exception as e:
        last_error = e

    # Method 2: Try pandas_datareader
    if not fetched:
        try:
            import pandas_datareader.data as web

            end_dt = end if end else datetime.now().strftime("%Y-%m-%d")
            df = web.DataReader(series_id, "fred", start, end_dt)

            # Convert to lists
            dates = df.index.to_pydatetime().tolist()
            values = df[series_id].tolist()

            # Remove NaN values
            filtered = [(d, v) for d, v in zip(dates, values) if v == v]  # NaN != NaN
            dates = [d for d, _ in filtered]
            values = [v for _, v in filtered]
            fetched = True
        except Exception as e:
            last_error = e

    # Method 3: Try direct CSV download (no API key required)
    if not fetched:
        try:
            dates, values = _fetch_from_csv(series_id, start, end)
            fetched = True
        except Exception as e:
            last_error = e

    # Success - cache and return the data
    if fetched and dates and values:
        if use_cache:
            _save_to_cache(series_id, dates, values)
        return dates, values

    # Method 4: Final fallback to cache
    if use_cache:
        cached = _load_from_cache(series_id)
        if cached is not None:
            dates, values = cached
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end) if end else datetime.now()
            filtered = [(d, v) for d, v in zip(dates, values)
                       if start_dt <= d <= end_dt and v is not None]
            if filtered:
                print(f"Warning: Using cached data for {series_id}")
                return [d for d, _ in filtered], [v for _, v in filtered]

    # All methods failed
    raise RuntimeError(
        f"Failed to fetch {series_id} from FRED: {last_error}"
    )


def fetch_gdp(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch Real GDP Growth rate from FRED.

    Returns quarterly data showing percent change from previous period.
    """
    return fetch_fred("A191RL1Q225SBEA", start, end)


def fetch_inflation(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch Inflation Rate (CPI YoY change) from FRED."""
    return fetch_fred("CPALTT01USM657N", start, end)


def fetch_unemployment(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch Unemployment Rate from FRED."""
    return fetch_fred("UNRATE", start, end)


def fetch_fed_funds(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch Federal Funds Rate from FRED."""
    return fetch_fred("FEDFUNDS", start, end)


def fetch_treasury_10y(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch 10-Year Treasury Rate from FRED."""
    return fetch_fred("DGS10", start, end)


def fetch_sp500(start: str = "2000-01-01", end: Optional[str] = None) -> tuple[list, list]:
    """Fetch S&P 500 Index from FRED."""
    return fetch_fred("SP500", start, end)


def list_series() -> dict:
    """List available pre-configured FRED series.

    Returns:
        Dictionary of series with their IDs and descriptions.
    """
    return SERIES_INFO.copy()


def update_cache(series_ids: Optional[list[str]] = None) -> None:
    """Update cache for specified series (or all pre-configured series).

    Args:
        series_ids: List of series to update. If None, updates all in SERIES_INFO.
    """
    if series_ids is None:
        series_ids = [info["id"] for info in SERIES_INFO.values()]

    for series_id in series_ids:
        try:
            print(f"Fetching {series_id}...")
            # Fetch fresh data and force save to cache
            dates, values = fetch_fred(series_id, start="2000-01-01", use_cache=False)
            _save_to_cache(series_id, dates, values)
            print(f"  Cached {series_id}")
        except Exception as e:
            print(f"  Failed to fetch {series_id}: {e}")
