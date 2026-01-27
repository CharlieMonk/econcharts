# Getting Started with econcharts

This guide walks you through creating economic charts with `econcharts`, from minimal examples to fully configured dashboards.

## Installation

```bash
pip install econcharts
```

## Quick Start

```python
from econcharts import EconChart, Data

# Create and display a chart
chart = EconChart(Data(x=dates, y=values, name='GDP'))
chart.show()
```

## Progressive Examples

### Level 1: Minimal - Single Chart with One Data Series

The minimum required: x values, y values, and a name for the legend.

```python
from econcharts import EconChart, Data

# Minimum required: x, y, and name
chart = EconChart(Data(x=dates, y=values, name='GDP'))
chart.show()
```

### Level 2: Add Title and Y-Axis Label

```python
chart = EconChart(
    Data(x=dates, y=values, name='GDP'),
    title="GDP Growth",
    y_label='% YoY',
)
chart.show()
```

### Level 3: Add Reference Line and Explicit Color

```python
chart = EconChart(
    Data(x=dates, y=values, name='GDP', color='teal'),
    title="GDP Growth",
    y_label='% YoY',
    horizontal_line=0,
)
chart.show()
```

### Level 4: Multiple Data Series (Auto-Colors)

If you don't specify colors, they're auto-assigned alphabetically from the 68-color palette.

```python
chart = EconChart(
    Data(x=dates, y=gdp_values, name='GDP'),       # Auto: amber
    Data(x=dates, y=cpi_values, name='CPI'),       # Auto: amethyst
    Data(x=dates, y=unemp_values, name='Unemp'),   # Auto: apricot
    title="Economic Indicators",
    y_label='% Change',
)
chart.show()
```

### Level 5: Multiple Charts (Dashboard)

Create separate `EconChart` instances and combine them in an `EconBoard`.

```python
gdp = EconChart(
    Data(x=dates, y=gdp_values, name='GDP'),
    title="GDP Growth",
    y_label='% YoY',
    horizontal_line=0,
)

inflation = EconChart(
    Data(x=dates, y=cpi_values, name='Inflation'),
    title="Inflation Rate",
    y_label='% YoY',
    horizontal_line=2,  # Target inflation
)

unemployment = EconChart(
    Data(x=dates, y=unemp_values, name='Unemployment'),
    title="Unemployment Rate",
    y_label='%',
)

board = EconBoard(gdp, inflation, unemployment)
board.show()
```

### Level 6: Legend Position

Crosshair is enabled by default. Customize the legend position.

```python
board = EconBoard(
    gdp, inflation, unemployment,
    legend='bottom',
    legend_orientation='horizontal',
)
board.show()
```

### Level 7: Recession Shading and Custom Height

Recession shading is enabled by default using NBER recession dates. Customize the appearance.

```python
board = EconBoard(
    gdp, inflation, unemployment,
    height=800,
    recession_color='gray',
    recession_opacity=0.2,
)
board.show()
```

### Level 8: Custom Margins and Spacing

Fine-tune the layout with margins and chart spacing.

```python
board = EconBoard(
    gdp, inflation, unemployment,
    height=900,
    spacing=0.08,
    margin_top=80,
    margin_bottom=50,
)
board.show()
```

### Level 9: Line Styling and Scatter

Customize line appearance and add scatter points.

```python
chart = EconChart(
    Data(x=dates, y=gdp_values, name='GDP', color='teal', line_width=2),
    Data(x=dates, y=forecast, name='Forecast', color='coral', line_style='dashed'),
    Data(x=event_dates, y=event_values, name='Events', color='gold',
         style='scatter', marker_size=12),
    title="GDP with Forecast",
    y_label='% Change',
    y_scale='linear',
)
chart.show()
```

### Level 10: Full Configuration

```python
from econcharts import EconBoard, EconChart, Data

# Fully configured charts
gdp = EconChart(
    Data(x=dates, y=gdp_values, name='Real GDP', color='teal', line_width=2),
    Data(x=dates, y=gdp_nominal, name='Nominal GDP', color='coral', line_style='dashed'),
    title="Gross Domestic Product",
    y_label='$ Billions',
    y_scale='log',
    x_tick_format='%Y',
    horizontal_line=0,
    horizontal_line_color='gray',
)

inflation = EconChart(
    Data(x=dates, y=cpi_values, name='CPI'),
    Data(x=dates, y=pce_values, name='PCE', line_style='dashed'),
    title="Inflation Measures",
    y_label='% YoY',
    horizontal_line=2,
    horizontal_line_color='red',
)

# Fully configured board
board = EconBoard(
    gdp, inflation,
    title="Economic Dashboard",
    height=700,
    spacing=0.06,
    share_x_axis=True,
    legend='bottom',
    legend_orientation='horizontal',
    margin_top=70,
    margin_bottom=40,
    margin_left=60,
    margin_right=60,
    crosshair_color='white',
    recession_color='gray',
    recession_opacity=0.15,
)
board.show()
board.to_html('dashboard.html')
```

## Using FRED Data

econcharts includes utilities for fetching economic data from FRED.

```python
from econcharts import EconChart, Data
from econcharts.fred import fetch_gdp, fetch_inflation, fetch_unemployment

# Fetch real data (cached locally)
gdp_dates, gdp_values = fetch_gdp(start="2000-01-01")
inf_dates, inf_values = fetch_inflation(start="2000-01-01")
unemp_dates, unemp_values = fetch_unemployment(start="2000-01-01")

# Create and display a chart
chart = EconChart(
    Data(x=gdp_dates, y=gdp_values, name='GDP', color='teal'),
    title="GDP Growth",
    y_label='% QoQ',
    horizontal_line=0,
)
chart.show()
```

## Color Palette

econcharts includes a 68-color palette optimized for dark themes. Colors can be specified by name:

```python
Data(x=dates, y=values, name='GDP', color='teal')
Data(x=dates, y=values, name='CPI', color='coral')
Data(x=dates, y=values, name='Stock', color='gold')
```

Or by hex/RGB:

```python
Data(x=dates, y=values, name='Custom', color='#ff6b6b')
Data(x=dates, y=values, name='RGB', color='rgb(255, 107, 107)')
```

Available named colors include: `teal`, `coral`, `gold`, `sky`, `violet`, `blue`, `orange`, `pink`, `mint`, `salmon`, `lavender`, `peach`, `cyan`, `lime`, `rose`, `amber`, and many more.

## Export Options

```python
# Display a single chart
chart.show()

# Export to HTML file
chart.to_html('chart.html')

# Get the Plotly figure for further customization
fig = chart.build()

# Pass board options when displaying a single chart
chart.show(height=400, show_recessions=False)

# For multiple charts, use EconBoard
board = EconBoard(chart1, chart2, chart3)
board.show()
board.to_html('dashboard.html')
```

## Next Steps

- See [API Reference](api_reference.md) for complete parameter documentation
- Check out the demo notebook: `notebooks/econ_charts_demo.ipynb`
