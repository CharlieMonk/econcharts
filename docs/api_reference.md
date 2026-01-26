# API Reference

Complete documentation for all econcharts classes and functions.

## Classes

### Data

A dataclass representing a data series for a chart.

```python
@dataclass
class Data:
    x: Any                              # X-axis values (dates, numbers, etc.)
    y: Any                              # Y-axis values
    name: str                           # Label shown in legend
    color: str | None = None            # Auto-assigned if not specified
    style: str = 'line'                 # 'line' or 'scatter'
    line_width: float | None = None     # Default: 1.5 from defaults.yaml
    line_style: str | None = None       # 'solid', 'dashed', 'dotted'
    marker_size: int | None = None      # Default: 6 from defaults.yaml
    visible: bool = True                # Show this data series
    show_in_legend: bool = True         # Include in legend
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | Any | (required) | X-axis values (dates, numbers, strings) |
| `y` | Any | (required) | Y-axis values (numbers) |
| `name` | str | (required) | Label shown in legend and hover tooltips |
| `color` | str \| None | None | Color for the trace. If None, auto-assigned alphabetically from palette |
| `style` | str | 'line' | Trace style: 'line' (connected points) or 'scatter' (markers only) |
| `line_width` | float \| None | None | Line width in pixels. Default: 1.5 |
| `line_style` | str \| None | None | Line dash style: 'solid', 'dashed', 'dotted', 'dashdot' |
| `marker_size` | int \| None | None | Marker size for scatter plots. Default: 6 |
| `visible` | bool | True | Whether to show this trace initially |
| `show_in_legend` | bool | True | Whether to include this trace in the legend |

#### Auto-Color Assignment

When `color` is not specified, colors are assigned in alphabetical order from the 68-color palette:
- 1st trace: amber
- 2nd trace: amethyst
- 3rd trace: apricot
- 4th trace: bear
- ... and so on

---

### EconChart

A single chart with data and axis configuration.

```python
class EconChart:
    def __init__(
        self,
        *data: Data,                        # Pass Data instances directly
        title: str | None = None,           # Chart title
        height: float = 1.0,                # Relative height in multi-chart layout
        y_label: str | None = None,         # Y-axis label
        y_label_color: str | None = None,   # Y-axis label color
        y_scale: str = 'linear',            # 'linear' or 'log'
        x_label: str | None = None,         # X-axis label
        x_tick_format: str | None = None,   # Format for tick labels
        x_range: tuple | None = None,       # (min, max) range for x-axis
        horizontal_line: float | None = None,       # Y-value for reference line
        horizontal_line_color: str | None = None,   # Reference line color
        horizontal_lines: list[dict] | None = None, # Multiple lines: [{y, color}, ...]
    ):
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `*data` | Data | (required) | One or more Data instances to display |
| `title` | str \| None | None | Chart title displayed above the subplot |
| `height` | float | 1.0 | Relative height in multi-chart layout (e.g., 2.0 = twice as tall) |
| `y_label` | str \| None | None | Y-axis label |
| `y_label_color` | str \| None | None | Y-axis label color (defaults to text color) |
| `y_scale` | str | 'linear' | Y-axis scale: 'linear' or 'log' |
| `x_label` | str \| None | None | X-axis label |
| `x_tick_format` | str \| None | None | Format string for x-axis tick labels (e.g., '%b %Y' for dates) |
| `x_range` | tuple \| None | None | (min, max) tuple to constrain x-axis range |
| `horizontal_line` | float \| None | None | Y-value for a horizontal reference line |
| `horizontal_line_color` | str \| None | None | Color for the horizontal line (defaults to zero_line color) |
| `horizontal_lines` | list[dict] \| None | None | Multiple horizontal lines: `[{'y': 0, 'color': 'gray'}, ...]` |

#### Example

```python
chart = EconChart(
    Data(x=dates, y=gdp, name='GDP', color='teal'),
    Data(x=dates, y=forecast, name='Forecast', color='coral', line_style='dashed'),
    title="GDP Growth",
    y_label='% YoY',
    y_scale='linear',
    horizontal_line=0,
)
```

---

### EconBoard

A container for multiple charts displayed together in a vertical stack.

```python
class EconBoard:
    def __init__(
        self,
        *charts: EconChart,                 # Pass charts directly
        title: str | None = None,           # Overall title
        height: int | None = None,          # Default: 600
        spacing: float | None = None,       # Default: 0.05
        share_x_axis: bool | None = None,   # Default: True
        legend: str | None = None,          # 'top', 'bottom', or 'right'
        legend_orientation: str | None = None,  # 'horizontal' or 'vertical'
        margin_top: int | None = None,      # Default: 55
        margin_bottom: int | None = None,   # Default: 35
        margin_left: int | None = None,     # Default: 55
        margin_right: int | None = None,    # Default: 55
        crosshair: bool = False,            # Show vertical line on hover
        crosshair_color: str | None = None, # Crosshair color
        show_recessions: bool = True,       # Shade recession periods
        recession_color: str | None = None, # Default: 'gray'
        recession_opacity: float | None = None,  # Default: 0.15
        colors: dict[str, str] | None = None,  # Custom color theme
    ):
```

#### Parameters

| Parameter | Type | Default | Source |
|-----------|------|---------|--------|
| `*charts` | EconChart | (required) | One or more EconChart instances |
| `title` | str \| None | None | Overall title for the dashboard |
| `height` | int | 600 | Total figure height in pixels |
| `spacing` | float | 0.05 | Vertical spacing between charts (0-1) |
| `share_x_axis` | bool | True | Synchronize x-axis zoom across charts |
| `legend` | str | 'bottom' | Legend position: 'top', 'bottom', or 'right' |
| `legend_orientation` | str | 'horizontal' | Legend orientation: 'horizontal' or 'vertical' |
| `margin_top` | int | 55 | Top margin in pixels |
| `margin_bottom` | int | 35 | Bottom margin in pixels |
| `margin_left` | int | 55 | Left margin in pixels |
| `margin_right` | int | 55 | Right margin in pixels |
| `crosshair` | bool | False | Show vertical crosshair line on hover |
| `crosshair_color` | str | 'rgba(255,255,255,0.5)' | Crosshair line color |
| `show_recessions` | bool | True | Show NBER recession shading |
| `recession_color` | str | 'gray' | Recession shading color |
| `recession_opacity` | float | 0.15 | Recession shading opacity (0-1) |
| `colors` | dict | None | Custom theme colors dict |

#### Methods

##### `build() -> go.Figure`

Build and return the Plotly figure object for further customization.

```python
fig = board.build()
fig.update_layout(...)  # Further customization
fig.show()
```

##### `show() -> None`

Display the chart in a browser or Jupyter notebook.

```python
board.show()
```

##### `to_html(path: str, include_plotlyjs: bool | str = True) -> None`

Export the chart to an HTML file.

```python
board.to_html('dashboard.html')
board.to_html('dashboard.html', include_plotlyjs='cdn')  # Smaller file, requires internet
board.to_html('dashboard.html', include_plotlyjs=False)  # Requires plotly.js loaded separately
```

#### Class Attributes

##### `palette`

Access to the 68-color palette dict.

```python
print(EconBoard.palette['teal'])  # '#00d4aa'
```

##### `resolve_color(color: str) -> str`

Resolve a color name to its hex value.

```python
EconBoard.resolve_color('teal')     # '#00d4aa'
EconBoard.resolve_color('#ff0000')  # '#ff0000' (unchanged)
```

---

## Module Functions

### resolve_color

```python
def resolve_color(color: str) -> str:
```

Resolve a color name to its hex value.

```python
from econcharts import resolve_color

resolve_color('teal')      # '#00d4aa'
resolve_color('#ff0000')   # '#ff0000'
resolve_color('rgb(255,0,0)')  # 'rgb(255,0,0)'
```

---

## Theme Colors

The `colors` parameter accepts a dict with these keys:

| Key | Default | Description |
|-----|---------|-------------|
| `background` | '#1a1a2e' | Plot background color |
| `paper` | '#16213e' | Paper/border background color |
| `grid` | '#2a2a4a' | Grid line color |
| `text` | '#e8e8e8' | Text color |
| `spike` | 'rgba(255,255,255,0.5)' | Spike line color (legacy) |
| `crosshair` | 'rgba(255,255,255,0.5)' | Crosshair line color |
| `zero_line` | 'rgba(255,255,255,0.3)' | Horizontal reference line color |

### Light Theme Example

```python
light_colors = {
    'background': '#ffffff',
    'paper': '#f8f9fa',
    'grid': '#dee2e6',
    'text': '#212529',
    'crosshair': 'rgba(0,0,0,0.3)',
    'zero_line': 'rgba(0,0,0,0.2)',
}

board = EconBoard(chart, colors=light_colors)
```

---

## Named Colors

The palette includes 68 colors organized by category:

### Primary Colors (high visibility)
`teal`, `coral`, `gold`, `sky`, `violet`, `blue`, `orange`, `pink`

### Secondary Colors (softer tones)
`mint`, `salmon`, `lavender`, `peach`, `cyan`, `lime`, `rose`, `amber`

### Neutral/Muted
`slate`, `silver`, `steel`, `gray`

### High Contrast
`white`, `red`, `green`, `yellow`, `purple`

### Finance-Specific
`bull`, `bear`, `neutral`, `dollar`, `recession`

### Plotly Default Colors
`plotly_blue`, `plotly_red`, `plotly_teal`, `plotly_purple`, `plotly_orange`, `plotly_cyan`, `plotly_pink`, `plotly_lime`, `plotly_magenta`, `plotly_yellow`

### Bright/Vivid
`electric`, `neon`, `emerald`, `amethyst`, `tangerine`, `apricot`, `golden`, `orchid`

### Plasma Colorscale
`plasma_dark`, `plasma_purple`, `plasma_violet`, `plasma_magenta`, `plasma_pink`, `plasma_salmon`, `plasma_orange`, `plasma_amber`, `plasma_yellow`, `plasma_bright`

### PiYG Diverging Colorscale
`piyg_magenta`, `piyg_pink`, `piyg_rose`, `piyg_blush`, `piyg_light_pink`, `piyg_neutral`, `piyg_light_green`, `piyg_lime`, `piyg_green`, `piyg_olive`, `piyg_dark_green`

---

## Default Values

All defaults can be customized via `defaults.yaml`:

| Setting | Default | YAML Path |
|---------|---------|-----------|
| Line width | 1.5 | `line.width` |
| Marker size | 6 | `scatter.marker_size` |
| Chart height | 600 | `chart.height` |
| Vertical spacing | 0.05 | `chart.vertical_spacing` |
| Shared x-axes | True | `chart.shared_xaxes` |
| Legend position | 'bottom' | `legend.position` |
| Legend orientation | 'h' | `legend.orientation` |
| Margin top | 55 | `margins.top` |
| Margin bottom | 35 | `margins.bottom` |
| Margin left | 55 | `margins.left` |
| Margin right | 55 | `margins.right` |
| Recession color | 'gray' | `recession.color` |
| Recession opacity | 0.15 | `recession.opacity` |
| Crosshair thickness | 1 | `crosshair.thickness` |
| Crosshair dash | 'dot' | `crosshair.dash` |
