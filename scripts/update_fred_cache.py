#!/usr/bin/env python3
"""Fetch and cache FRED data for offline use in examples and tests."""

from econcharts.fred import update_cache, SERIES_INFO

if __name__ == "__main__":
    print("Updating FRED data cache...")
    print(f"Series to fetch: {list(SERIES_INFO.keys())}")
    print()
    update_cache()
    print()
    print("Cache update complete!")
