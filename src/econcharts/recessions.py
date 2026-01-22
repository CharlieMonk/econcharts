"""NBER recession dates for recession shading in economic charts.

This module provides U.S. recession date ranges as defined by the
National Bureau of Economic Research (NBER).

Usage:
    from econcharts.recessions import NBER_RECESSIONS, get_recessions_in_range

    # Get all recessions
    recessions = NBER_RECESSIONS

    # Get recessions within a date range
    recessions = get_recessions_in_range(start_date, end_date)
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence


# NBER U.S. Business Cycle Expansions and Contractions
# Source: https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
# Format: (peak, trough) - recession runs from peak to trough
NBER_RECESSIONS: list[tuple[datetime, datetime]] = [
    # Post-WWII recessions
    (datetime(1948, 11, 1), datetime(1949, 10, 1)),
    (datetime(1953, 7, 1), datetime(1954, 5, 1)),
    (datetime(1957, 8, 1), datetime(1958, 4, 1)),
    (datetime(1960, 4, 1), datetime(1961, 2, 1)),
    (datetime(1969, 12, 1), datetime(1970, 11, 1)),
    (datetime(1973, 11, 1), datetime(1975, 3, 1)),
    (datetime(1980, 1, 1), datetime(1980, 7, 1)),
    (datetime(1981, 7, 1), datetime(1982, 11, 1)),
    (datetime(1990, 7, 1), datetime(1991, 3, 1)),
    (datetime(2001, 3, 1), datetime(2001, 11, 1)),
    (datetime(2007, 12, 1), datetime(2009, 6, 1)),  # Great Recession
    (datetime(2020, 2, 1), datetime(2020, 4, 1)),   # COVID-19 recession
]


def get_recessions_in_range(
    start: datetime | None = None,
    end: datetime | None = None,
    recessions: Sequence[tuple[datetime, datetime]] | None = None,
) -> list[tuple[datetime, datetime]]:
    """
    Get recession periods that overlap with a date range.

    Args:
        start: Start of date range (inclusive). If None, no lower bound.
        end: End of date range (inclusive). If None, no upper bound.
        recessions: Custom recession list. Defaults to NBER_RECESSIONS.

    Returns:
        List of (start, end) tuples for recessions overlapping the range.
        Recession dates are clipped to the specified range.

    Example:
        >>> from datetime import datetime
        >>> recessions = get_recessions_in_range(
        ...     datetime(2000, 1, 1),
        ...     datetime(2025, 1, 1)
        ... )
        >>> len(recessions)
        3
    """
    if recessions is None:
        recessions = NBER_RECESSIONS

    result = []
    for rec_start, rec_end in recessions:
        # Check if recession overlaps with the date range
        if start is not None and rec_end < start:
            continue
        if end is not None and rec_start > end:
            continue

        # Clip recession dates to the specified range
        clipped_start = rec_start
        clipped_end = rec_end

        if start is not None and rec_start < start:
            clipped_start = start
        if end is not None and rec_end > end:
            clipped_end = end

        result.append((clipped_start, clipped_end))

    return result
