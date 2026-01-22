# econcharts

Sharp, professional charts for economic data with dark theme support.

## Features

- **Modern Dark Theme**: Beautiful dark-themed charts optimized for economic and financial data
- **Multi-subplot Support**: Easily create charts with multiple synchronized subplots
- **Unified Spike Lines**: Vertical crosshairs that span all subplots for easy data comparison
- **Named Color Palette**: 68 colors optimized for dark backgrounds
- **Fluent API**: Chainable methods for intuitive chart building
- **Interactive**: Built on Plotly with zoom, pan, and hover capabilities
- **Configurable**: YAML-based default configuration that's easy to customize

## Installation

```bash
pip install econcharts
```

## Quick Start

```python
import pandas as pd
import econcharts

# Sample data
dates = pd.date_range('2020-01-01', periods=100, freq='D')
values = [100 + i * 0.5 + (i % 10) for i in range(100)]

# Create a simple chart using named colors
chart = econcharts(num_rows=1, height=400)
chart.add_line(row=1, x=dates, y=values, name='GDP Growth', color='teal')
chart.set_title('Economic Indicator')
chart.enable_unified_spikeline()
fig = chart.build()
fig.show()
```

## Multi-subplot Example

```python
import econcharts

chart = econcharts(
    num_rows=3,
    subplot_titles=('GDP', 'Inflation', 'Unemployment'),
    height=700,
)

# Add data to each subplot using named colors
chart.add_line(row=1, x=dates, y=gdp_data, name='GDP', color='teal')
chart.add_line(row=2, x=dates, y=inflation_data, name='Inflation', color='coral')
chart.add_line(row=3, x=dates, y=unemployment_data, name='Unemployment', color='sky')

# Add reference lines
chart.add_hline(row=2, y=2.0)  # 2% inflation target

# Configure appearance
chart.set_yaxis(row=1, title='Billions USD')
chart.set_yaxis(row=2, title='% YoY')
chart.set_yaxis(row=3, title='% Rate')
chart.set_legend(orientation='h', position='top')
chart.enable_unified_spikeline()

fig = chart.build()
fig.show()
```

## Named Color Palette

Use color names instead of hex codes for cleaner, more readable code:

```python
import econcharts

# Available colors (68 total, optimized for dark theme):
# Primary:     teal, coral, gold, sky, violet, blue, orange, pink
# Secondary:   mint, salmon, lavender, peach, cyan, lime, rose, amber
# Neutral:     slate, silver, steel, gray
# Accent:      white, red, green, yellow, purple
# Finance:     bull, bear, neutral, dollar
# Bright:      electric, neon, emerald, amethyst, tangerine, apricot, golden, orchid
# Plotly:      plotly_blue, plotly_red, plotly_teal, plotly_purple, plotly_orange,
#              plotly_cyan, plotly_pink, plotly_lime, plotly_magenta, plotly_yellow
# Colorscales: plasma_*, piyg_* (for diverging data)

# Use in charts
chart = econcharts(num_rows=1, height=400)
chart.add_line(row=1, x=dates, y=values, name='GDP', color='teal')

# Hex codes still work
chart.add_line(row=1, x=dates, y=values2, name='Custom', color='#ff00ff')

# View all 68 colors
print(econcharts.PALETTE)  # {'teal': '#00d4aa', 'coral': '#ff6b6b', ...}
```

## API Reference

### econcharts

The main chart class with fluent interface for building economic charts.

#### Constructor

```python
import econcharts

chart = econcharts(
    num_rows: int,                          # Number of subplot rows
    row_heights: list[float] | None = None, # Relative heights for each row
    subplot_titles: tuple[str, ...] | None = None,
    colors: dict[str, str] | None = None,   # Custom color scheme
    shared_xaxes: bool = True,              # Share x-axes across subplots
    vertical_spacing: float = 0.05,         # Spacing between subplots
    height: int = 600,                      # Chart height in pixels
)
```

#### Methods

- `add_line(row, x, y, name, color, ...)` - Add a line trace
- `add_scatter(row, x, y, name, color, ...)` - Add a scatter (markers) trace
- `set_yaxis(row, title, scale_type, ...)` - Configure y-axis
- `set_xaxis(row, title, tick_format, ...)` - Configure x-axis
- `add_hline(row, y, color, ...)` - Add horizontal reference line
- `enable_unified_spikeline(spike_color)` - Enable cross-subplot spike lines
- `set_legend(orientation, position)` - Configure legend
- `set_margins(top, left, right, bottom)` - Set margins
- `set_title(text, font_size)` - Set chart title
- `build()` - Finalize and return Plotly figure
- `show()` - Display the chart
- `to_html(path, include_plotlyjs)` - Export to HTML

#### Class Attributes

- `econcharts.PALETTE` - Dictionary of 68 named colors
- `econcharts.DEFAULT_COLORS` - Default theme colors
- `econcharts.resolve_color(name)` - Convert color name to hex

## Customization

Default settings are stored in `defaults.yaml` and can be overridden:

```python
import econcharts

custom_colors = {
    'background': '#0a0a0a',
    'paper': '#1a1a1a',
    'grid': '#333333',
    'text': '#ffffff',
    'spike': 'rgba(255, 255, 255, 0.7)',
    'zero_line': 'rgba(255, 255, 255, 0.4)',
}

chart = econcharts(num_rows=2, colors=custom_colors)
```

## License

MIT License - see LICENSE file for details.
