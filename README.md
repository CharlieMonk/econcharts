# econcharts

Sharp, professional charts for economic data with dark theme support.

## Features

- **Modern Dark Theme**: Beautiful dark-themed charts optimized for economic and financial data
- **Multi-subplot Support**: Easily create dashboards with multiple synchronized charts
- **Unified Crosshairs**: Vertical crosshairs that span all charts for easy data comparison
- **Recession Shading**: Automatic NBER recession period shading (1948-2020)
- **Named Color Palette**: 69 colors optimized for dark backgrounds
- **FRED Integration**: Built-in utilities for fetching Federal Reserve economic data
- **Interactive**: Built on Plotly with zoom, pan, and hover capabilities
- **Configurable**: YAML-based default configuration that's easy to customize

## Installation

```bash
pip install econcharts
```

## Quick Start

```python
from econcharts import EconChart, Data

# Create a simple chart
chart = EconChart(
    Data(x=dates, y=values, name='GDP', color='teal'),
    title="GDP Growth",
    y_label='% YoY',
    horizontal_line=0,
)
chart.show()
```

## Multi-Chart Dashboard

```python
from econcharts import EconBoard, EconChart, Data

# Create individual charts
gdp = EconChart(
    Data(x=dates, y=gdp_values, name='GDP', color='teal'),
    title="GDP Growth",
    y_label='% YoY',
    horizontal_line=0,
)

inflation = EconChart(
    Data(x=dates, y=cpi_values, name='Inflation', color='coral'),
    title="Inflation Rate",
    y_label='% YoY',
    horizontal_line=2,  # 2% target
)

unemployment = EconChart(
    Data(x=dates, y=unemp_values, name='Unemployment', color='gold'),
    title="Unemployment Rate",
    y_label='%',
)

# Combine into a dashboard
board = EconBoard(
    gdp, inflation, unemployment,
    height=700,
    crosshair=True,      # Enabled by default
    show_recessions=True, # Enabled by default
)
board.show()
```

## Using FRED Data

```python
from econcharts import EconBoard, EconChart, Data
from econcharts.fred import fetch_gdp, fetch_inflation, fetch_unemployment

# Fetch real economic data (cached locally)
gdp_dates, gdp_values = fetch_gdp(start="2000-01-01")
inf_dates, inf_values = fetch_inflation(start="2000-01-01")
unemp_dates, unemp_values = fetch_unemployment(start="2000-01-01")

# Create dashboard with real data
gdp = EconChart(
    Data(x=gdp_dates, y=gdp_values, name='GDP', color='teal'),
    title="GDP Growth",
    y_label='% QoQ',
    horizontal_line=0,
)

board = EconBoard(gdp)
board.show()
```

## Named Color Palette

Use color names instead of hex codes for cleaner, more readable code:

```python
from econcharts import EconChart, Data

# Available colors (69 total, optimized for dark theme):
# Primary:     teal, coral, gold, sky, violet, blue, orange, pink
# Secondary:   mint, salmon, lavender, peach, cyan, lime, rose, amber
# Neutral:     slate, silver, steel, gray
# Accent:      white, red, green, yellow, purple
# Finance:     bull, bear, neutral, dollar, recession
# Bright:      electric, neon, emerald, amethyst, tangerine, apricot, golden, orchid
# Plotly:      plotly_blue, plotly_red, plotly_teal, plotly_purple, plotly_orange,
#              plotly_cyan, plotly_pink, plotly_lime, plotly_magenta, plotly_yellow
# Colorscales: plasma_*, piyg_* (for diverging data)

# Use named colors
chart = EconChart(
    Data(x=dates, y=values, name='GDP', color='teal'),
    Data(x=dates, y=values2, name='Forecast', color='coral', line_style='dashed'),
)

# Hex codes and RGB also work
chart = EconChart(
    Data(x=dates, y=values, name='Custom', color='#ff00ff'),
    Data(x=dates, y=values2, name='RGB', color='rgb(255, 107, 107)'),
)
```

## API Reference

### Data

A data series for a chart.

```python
Data(
    x=dates,                    # X-axis values (required)
    y=values,                   # Y-axis values (required)
    name='GDP',                 # Legend label (required)
    color='teal',               # Color (optional, auto-assigned if omitted)
    style='line',               # 'line' or 'scatter'
    line_width=1.5,             # Line width
    line_style='dashed',        # 'solid', 'dashed', 'dotted', 'dashdot'
    marker_size=6,              # Marker size for scatter
    visible=True,               # Show/hide trace
    show_in_legend=True,        # Include in legend
)
```

### EconChart

A single chart with data and axis configuration.

```python
EconChart(
    *data,                      # One or more Data instances
    title='GDP Growth',         # Chart title
    height=300,                 # Height in pixels
    y_label='% YoY',            # Y-axis label
    y_scale='linear',           # 'linear' or 'log'
    x_label='Date',             # X-axis label
    x_tick_format='%Y',         # Tick format (e.g., '%b %Y')
    x_range=(start, end),       # Constrain x-axis range
    horizontal_line=0,          # Reference line y-value
    horizontal_line_color='gray', # Reference line color
)
```

**Methods:**
- `show(**board_kwargs)` - Display the chart
- `build(**board_kwargs)` - Return Plotly figure
- `to_html(path, **board_kwargs)` - Export to HTML

### EconBoard

Multiple charts displayed together in a vertical stack.

```python
EconBoard(
    *charts,                    # One or more EconChart instances
    title='Dashboard',          # Overall title
    height=700,                 # Total height (default: 200px per chart)
    spacing=0.05,               # Vertical spacing between charts
    share_x_axis=True,          # Sync x-axis zoom
    legend='bottom',            # 'top', 'bottom', or 'right'
    legend_orientation='horizontal', # 'horizontal' or 'vertical'
    crosshair=True,             # Show vertical crosshair on hover
    crosshair_color='white',    # Crosshair color
    show_recessions=True,       # Show NBER recession shading
    recession_color='gray',     # Recession shading color
    recession_opacity=0.15,     # Recession shading opacity
    margin_top=55,              # Margins in pixels
    margin_bottom=35,
    margin_left=55,
    margin_right=55,
    colors={...},               # Custom theme colors
)
```

**Methods:**
- `show()` - Display the dashboard
- `build()` - Return Plotly figure
- `to_html(path)` - Export to HTML

### resolve_color

Convert a color name to its hex value.

```python
from econcharts import resolve_color

resolve_color('teal')      # '#00d4aa'
resolve_color('#ff0000')   # '#ff0000' (unchanged)
```

## Customization

Override default theme colors:

```python
from econcharts import EconBoard, EconChart, Data

custom_colors = {
    'background': '#0a0a0a',
    'paper': '#1a1a1a',
    'grid': '#333333',
    'text': '#ffffff',
    'crosshair': 'rgba(255, 255, 255, 0.7)',
    'zero_line': 'rgba(255, 255, 255, 0.4)',
}

chart = EconChart(Data(x=dates, y=values, name='Data'))
board = EconBoard(chart, colors=custom_colors)
board.show()
```

## Documentation

- [Getting Started Guide](docs/getting_started.md) - Progressive examples from minimal to complex
- [API Reference](docs/api_reference.md) - Complete documentation for all classes and functions

## License

MIT License - see LICENSE file for details.
