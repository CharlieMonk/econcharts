#!/usr/bin/env python3
"""Fetch and cache FRED data for offline use in examples and tests."""

import sys
from pathlib import Path

# Add src to path - import fred module directly due to non-standard __init__
src_path = Path(__file__).parent.parent / "src" / "econcharts"
sys.path.insert(0, str(src_path))

from fred import update_cache, SERIES_INFO

if __name__ == "__main__":
    print("Updating FRED data cache...")
    print(f"Series to fetch: {list(SERIES_INFO.keys())}")
    print()
    update_cache()
    print()
    print("Cache update complete!")
