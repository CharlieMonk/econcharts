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

# Cache directory for offline data
CACHE_DIR = Path(__file__).parent / "data"

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

    # Fetch from FRED using pandas_datareader
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

        # Cache the data
        if use_cache:
            _save_to_cache(series_id, dates, values)

        return dates, values

    except ImportError:
        raise ImportError(
            "pandas_datareader is required for FRED data. "
            "Install with: pip install pandas-datareader"
        )
    except Exception as e:
        # Try to fall back to cache
        if use_cache:
            cached = _load_from_cache(series_id)
            if cached is not None:
                print(f"Warning: Could not fetch {series_id}, using cached data: {e}")
                return cached
        raise RuntimeError(f"Failed to fetch {series_id} from FRED: {e}")


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
