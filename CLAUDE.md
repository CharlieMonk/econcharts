# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**econcharts** is a Python library for creating professional economic charts with dark theme support. Built on Plotly, it provides a fluent builder API for multi-subplot charts with unified spike lines and recession shading.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_charts_visual.py

# Run with verbose output
pytest tests/ -v

# Update FRED data cache
python scripts/update_fred_cache.py

# Run demo notebook
jupyter notebook notebooks/econ_charts_demo.ipynb
```

## Architecture

### Core Components

- **`src/econcharts/chart.py`** - `EconChart` class implementing a fluent builder pattern for chart construction. Handles multi-subplot layout, spike lines, recession shading, and Plotly figure generation.

- **`src/econcharts/fred.py`** - FRED data fetching using public CSV endpoint (no API key required). Includes caching to `src/econcharts/data/` as JSON files.

- **`src/econcharts/recessions.py`** - NBER recession date ranges (1948-2020) used for automatic recession shading.

### Configuration (YAML)

- **`defaults.yaml`** - Chart styling: colors, fonts, margins, spike line settings, recession shading opacity
- **`colors.yaml`** - 68-color dark-theme palette organized by category (primary, secondary, finance, etc.)

### Key Patterns

**Fluent Builder API:**
```python
chart = EconChart(num_rows=3)
chart.add_line(row=1, x=dates, y=values, color='teal')
chart.set_yaxis(row=1, title='GDP')
chart.enable_unified_spikeline()
fig = chart.build()
```

**Color Resolution:** Named colors from `colors.yaml`, hex codes, or RGB strings are all supported via `resolve_color()`.

**Recession Shading:** Enabled by default. Configure with `configure_recession_shading()` or disable with `disable_recession_shading()`.

### Plotly Workarounds

The codebase includes workarounds for Plotly limitations:
- Custom unified spike line implementation for multi-subplot charts (Plotly #1677)
- Invisible marker traces to force tick rendering on upper axes
- Shape xref adjustment for proper axis binding

### Testing

Tests use Playwright for browser automation with real FRED data (not mocked). Visual tests export HTML, load in browser, verify DOM structure, and can capture screenshots.

Key fixture directories in `tests/`:
- `test_output/screenshots/` - Browser screenshots
- `test_output/html/` - Exported HTML files
