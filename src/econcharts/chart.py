"""Reusable economic chart classes with dark theme support and multi-chart capabilities.

Classes:
    Data: A data series for a chart (x, y, name, styling options)
    EconBase: Base class for EconChart and EconBoard with common functionality
    EconChart: A single chart with data and axis configuration
    EconBoard: Multiple charts displayed together in a vertical stack
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Sequence

import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from econcharts.recessions import NBER_RECESSIONS, get_recessions_in_range


_MODULE_DIR = os.path.dirname(__file__)


def _load_yaml(filename: str) -> dict:
    """Load a YAML file from the module directory."""
    with open(os.path.join(_MODULE_DIR, filename), 'r') as f:
        return yaml.safe_load(f)


# Load YAML configuration as module-level variables
_defaults = _load_yaml('defaults.yaml')
_palette = _load_yaml('colors.yaml')

# Create sorted color list for auto-assignment
_sorted_colors = sorted(_palette.keys())


def resolve_color(color: str) -> str:
    """
    Resolve a color name to its hex value.

    Args:
        color: Either a hex/rgb color string or a named color
               from the palette (e.g., 'teal', 'coral')

    Returns:
        Hex or rgb color string

    Examples:
        >>> resolve_color('teal')
        '#00d4aa'
        >>> resolve_color('#ff0000')
        '#ff0000'
    """
    if color.startswith(('#', 'rgb')):
        return color
    return _palette.get(color.lower(), color)


class EconBase(ABC):
    """Base class for economic chart components.

    Provides common functionality for EconChart and EconBoard:
    - Color palette access and resolution
    - Display methods (show, to_html)
    - Abstract build method for Plotly figure generation
    """

    # Class-level access to color palette
    _palette = _palette

    # Common attributes
    title: str | None

    @staticmethod
    def resolve_color(color: str) -> str:
        """Resolve a color name to its hex value.

        Args:
            color: Either a hex/rgb color string or a named color
                   from the palette (e.g., 'teal', 'coral')

        Returns:
            Hex or rgb color string
        """
        return resolve_color(color)

    @abstractmethod
    def build(self, **kwargs) -> go.Figure:
        """Build and return the Plotly figure.

        Args:
            **kwargs: Subclass-specific arguments

        Returns:
            Plotly Figure object
        """
        pass

    def show(self, **kwargs) -> None:
        """Display the chart in a browser or Jupyter notebook.

        Args:
            **kwargs: Arguments passed to build()
        """
        self.build(**kwargs).show()

    def to_html(self, path: str, include_plotlyjs: bool | str = True, **kwargs) -> None:
        """Export chart to HTML file.

        Args:
            path: Output file path
            include_plotlyjs: Whether to include Plotly JS library
            **kwargs: Arguments passed to build()
        """
        self.build(**kwargs).write_html(path, include_plotlyjs=include_plotlyjs)


@dataclass
class Data:
    """A data series for a chart.

    Args:
        x: X-axis values (dates, numbers, etc.)
        y: Y-axis values
        name: Label shown in legend
        color: Color for the trace. Auto-assigned if not specified.
        style: 'line' or 'scatter'
        line_width: Line width. Default from defaults.yaml: line.width
        line_style: 'solid', 'dashed', 'dotted', etc.
        marker_size: Marker size for scatter. Default from defaults.yaml: scatter.marker_size
        visible: Show this data series
        show_in_legend: Include in legend
    """
    x: Any
    y: Any
    name: str
    color: str | None = None
    style: str = 'line'
    line_width: float | None = None
    line_style: str | None = None
    marker_size: int | None = None
    visible: bool = True
    show_in_legend: bool = True


class EconChart(EconBase):
    """A single chart with data and axis configuration.

    Args:
        *data: Data instances to display on this chart
        title: Chart title (displayed above the subplot)
        height: Figure height in pixels. Default: 600 from defaults.yaml
        y_label: Y-axis label
        y_label_color: Y-axis label color
        y_scale: 'linear' or 'log'
        x_label: X-axis label
        x_tick_format: Format for tick labels (e.g., '%b %Y')
        x_range: (min, max) range for x-axis
        horizontal_line: Y-value for a horizontal reference line
        horizontal_line_color: Color for the horizontal line
        horizontal_lines: Multiple lines: [{y, color}, ...]

    Example:
        chart = EconChart(
            Data(x=dates, y=values, name='GDP'),
            title="GDP Growth",
            y_label='% YoY',
            horizontal_line=0,
        )
        chart.show()  # Display directly
    """

    def __init__(
        self,
        *data: Data,
        title: str | None = None,
        height: int | None = None,
        y_label: str | None = None,
        y_label_color: str | None = None,
        y_scale: str = 'linear',
        x_label: str | None = None,
        x_tick_format: str | None = None,
        x_range: tuple | None = None,
        horizontal_line: float | None = None,
        horizontal_line_color: str | None = None,
        horizontal_lines: list[dict] | None = None,
    ) -> None:
        self.data = list(data)
        self.title = title
        self.height = height if height is not None else _defaults['chart']['single_chart_height']
        self.y_label = y_label
        self.y_label_color = y_label_color
        self.y_scale = y_scale
        self.x_label = x_label
        self.x_tick_format = x_tick_format
        self.x_range = x_range
        self.horizontal_line = horizontal_line
        self.horizontal_line_color = horizontal_line_color
        self.horizontal_lines = horizontal_lines or []

    def _compute_x_range(self) -> tuple | None:
        """Compute the x range from all data series."""
        x_min = None
        x_max = None
        for d in self.data:
            try:
                if hasattr(d.x, '__len__') and len(d.x) > 0:
                    curr_min, curr_max = min(d.x), max(d.x)
                    if x_min is None or curr_min < x_min:
                        x_min = curr_min
                    if x_max is None or curr_max > x_max:
                        x_max = curr_max
            except (TypeError, ValueError):
                pass
        if x_min is not None and x_max is not None:
            return (x_min, x_max)
        return None

    def build(self, **board_kwargs) -> go.Figure:
        """Build and return the Plotly figure.

        Args:
            **board_kwargs: Optional arguments passed to EconBoard (e.g., height, crosshair)

        Returns:
            Plotly Figure object
        """
        # Pass chart's height to EconBoard unless explicitly overridden
        if 'height' not in board_kwargs:
            board_kwargs['height'] = self.height
        return EconBoard(self, **board_kwargs).build()


class EconBoard(EconBase):
    """Multiple charts displayed together in a vertical stack.

    Args:
        *charts: EconChart instances to display
        title: Overall title for all charts
        height: Total figure height in pixels. Default: 600 from defaults.yaml
        spacing: Vertical spacing between charts. Default: 0.05 from defaults.yaml
        share_x_axis: Sync x-axis zoom across charts. Default: True from defaults.yaml
        legend: Legend position: 'top', 'bottom', or 'right'. Default: 'bottom'
        legend_orientation: 'horizontal' or 'vertical'. Default: 'horizontal'
        margin_top: Top margin in pixels. Default: 55 from defaults.yaml
        margin_bottom: Bottom margin in pixels. Default: 35 from defaults.yaml
        margin_left: Left margin in pixels. Default: 55 from defaults.yaml
        margin_right: Right margin in pixels. Default: 55 from defaults.yaml
        crosshair: Show vertical line on hover. Default: True from defaults.yaml
        crosshair_color: Crosshair color. Default from defaults.yaml: colors.crosshair
        show_recessions: Shade recession periods. Default: True
        recession_color: Recession shading color. Default: 'gray' from defaults.yaml
        recession_opacity: Recession shading opacity. Default: 0.15 from defaults.yaml
        colors: Custom color theme dict

    Example:
        gdp = EconChart(Data(x=dates, y=gdp_values, name='GDP'), title="GDP")
        inflation = EconChart(Data(x=dates, y=cpi_values, name='CPI'), title="Inflation")
        board = EconBoard(gdp, inflation)
        board.show()
    """

    def __init__(
        self,
        *charts: EconChart,
        title: str | None = None,
        height: int | None = None,
        spacing: float | None = None,
        share_x_axis: bool | None = None,
        legend: str | None = None,
        legend_orientation: str | None = None,
        margin_top: int | None = None,
        margin_bottom: int | None = None,
        margin_left: int | None = None,
        margin_right: int | None = None,
        crosshair: bool | None = None,
        crosshair_color: str | None = None,
        show_recessions: bool = True,
        recession_color: str | None = None,
        recession_opacity: float | None = None,
        colors: dict[str, str] | None = None,
    ) -> None:
        self.charts = list(charts)
        self.title = title
        self._initialize_height(height)
        self.spacing = spacing if spacing is not None else _defaults['chart']['vertical_spacing']
        self.share_x_axis = share_x_axis if share_x_axis is not None else _defaults['chart']['shared_xaxes']
        self.crosshair = crosshair if crosshair is not None else _defaults['crosshair']['showCrosshair']
        self.show_recessions = show_recessions

        # Legend settings
        self.legend_position = legend or _defaults['legend']['position']
        self.legend_orientation = legend_orientation or _defaults['legend']['orientation']

        # Margins
        self.margin_top = margin_top if margin_top is not None else _defaults['margins']['top']
        self.margin_bottom = margin_bottom if margin_bottom is not None else _defaults['margins']['bottom']
        self.margin_left = margin_left if margin_left is not None else _defaults['margins']['left']
        self.margin_right = margin_right if margin_right is not None else _defaults['margins']['right']

        # Crosshair settings
        crosshair_defaults = _defaults.get('crosshair', {})
        self.crosshair_color = crosshair_color or _defaults['colors'].get('crosshair') or _defaults['colors']['spike']

        # Recession settings
        self.recession_color = recession_color or _defaults['recession']['color']
        self.recession_opacity = recession_opacity if recession_opacity is not None else _defaults['recession']['opacity']

        # Theme colors
        self._colors = {**_defaults['colors'], **(colors or {})}

        # Figure will be created in build()
        self.fig: go.Figure | None = None
        self._x_range: tuple | None = None

    def _initialize_height(self, height: int | None) -> None:
        """Set the figure height based on user input and number of charts."""
        if height is not None:
            self.height = height
        elif len(self.charts) > 1:
            self.height = _defaults['chart']['board_height_per_plot'] * len(self.charts)
        else:
            self.height = _defaults['chart']['single_chart_height']

    def _compute_global_x_range(self) -> tuple | None:
        """Compute x range across all charts."""
        x_min = None
        x_max = None
        for chart in self.charts:
            chart_range = chart._compute_x_range()
            if chart_range:
                if x_min is None or chart_range[0] < x_min:
                    x_min = chart_range[0]
                if x_max is None or chart_range[1] > x_max:
                    x_max = chart_range[1]
        if x_min is not None and x_max is not None:
            return (x_min, x_max)
        return None

    def build(self, **kwargs) -> go.Figure:
        """Build and return the Plotly figure.

        Args:
            **kwargs: Ignored (accepted for compatibility with EconBase interface)

        Returns:
            Plotly Figure object
        """
        num_rows = len(self.charts)
        if num_rows == 0:
            raise ValueError("EconBoard requires at least one EconChart")

        # Calculate row heights from chart.height values
        total_height = sum(c.height for c in self.charts)
        row_heights = [c.height / total_height for c in self.charts]

        # Collect subplot titles
        subplot_titles = tuple(c.title or '' for c in self.charts)

        # Create subplots
        self.fig = make_subplots(
            rows=num_rows,
            cols=1,
            row_heights=row_heights,
            shared_xaxes=self.share_x_axis,
            vertical_spacing=self.spacing,
            subplot_titles=subplot_titles if any(subplot_titles) else None,
        )

        # Apply theme layout
        self.fig.update_layout(
            height=self.height,
            hovermode='x unified',
            paper_bgcolor=self._colors['paper'],
            plot_bgcolor=self._colors['background'],
            font=dict(color=self._colors['text'], size=_defaults['fonts']['main']),
            hoverlabel=dict(
                bgcolor=self._colors['paper'],
                font_size=_defaults['fonts']['hoverlabel'],
                font_color=self._colors['text'],
            ),
        )

        # Apply margins
        self.fig.update_layout(margin=dict(
            t=self.margin_top,
            l=self.margin_left,
            r=self.margin_right,
            b=self.margin_bottom,
        ))

        # Apply title
        if self.title:
            self.fig.update_layout(
                title=dict(
                    text=self.title,
                    font=dict(size=_defaults['fonts']['chart_title'], color=self._colors['text']),
                    y=0.99,
                    yanchor='top',
                )
            )

        # Style subplot titles
        if any(subplot_titles):
            title_font = dict(size=_defaults['fonts']['subplot_title'], color=self._colors['text'])
            for annotation in self.fig['layout']['annotations']:
                annotation['font'] = title_font

        # Apply grid color to all axes
        for row in range(1, num_rows + 1):
            self.fig.update_xaxes(gridcolor=self._colors['grid'], row=row, col=1)
            self.fig.update_yaxes(gridcolor=self._colors['grid'], row=row, col=1)

        # Apply legend settings
        self._apply_legend()

        # Add traces from each chart
        color_index = 0  # Global color index for auto-assignment
        for row_idx, chart in enumerate(self.charts, start=1):
            for data in chart.data:
                # Auto-assign color if not specified
                trace_color = data.color
                if trace_color is None:
                    trace_color = _sorted_colors[color_index % len(_sorted_colors)]
                    color_index += 1
                trace_color = resolve_color(trace_color)

                # Create trace based on style
                if data.style == 'scatter':
                    self.fig.add_trace(
                        go.Scatter(
                            x=data.x,
                            y=data.y,
                            name=data.name,
                            mode='markers',
                            marker=dict(
                                color=trace_color,
                                size=data.marker_size or _defaults['scatter']['marker_size'],
                            ),
                            visible=data.visible,
                            showlegend=data.show_in_legend,
                        ),
                        row=row_idx,
                        col=1,
                    )
                else:  # line (default)
                    line_dict: dict[str, Any] = {
                        'color': trace_color,
                        'width': data.line_width or _defaults['line']['width'],
                    }
                    if data.line_style:
                        # Map common names to Plotly dash values
                        dash_map = {
                            'solid': 'solid',
                            'dashed': 'dash',
                            'dotted': 'dot',
                            'dash': 'dash',
                            'dot': 'dot',
                            'dashdot': 'dashdot',
                        }
                        line_dict['dash'] = dash_map.get(data.line_style, data.line_style)

                    self.fig.add_trace(
                        go.Scatter(
                            x=data.x,
                            y=data.y,
                            name=data.name,
                            line=line_dict,
                            visible=data.visible,
                            showlegend=data.show_in_legend,
                        ),
                        row=row_idx,
                        col=1,
                    )

                # Track x range
                self._update_x_range(data.x)

            # Apply y-axis settings
            y_kwargs: dict[str, Any] = {'type': chart.y_scale}
            if chart.y_label:
                y_kwargs['title_text'] = chart.y_label
                y_kwargs['title_font'] = dict(
                    size=_defaults['fonts']['axis_title'],
                    color=chart.y_label_color or self._colors['text'],
                )
            self.fig.update_yaxes(row=row_idx, col=1, **y_kwargs)

            # Apply x-axis settings
            x_kwargs: dict[str, Any] = {}
            if chart.x_label:
                x_kwargs['title_text'] = chart.x_label
                x_kwargs['title_font'] = dict(
                    size=_defaults['fonts']['axis_title'],
                    color=self._colors['text'],
                )
            if chart.x_tick_format:
                x_kwargs['tickformat'] = chart.x_tick_format
            if chart.x_range:
                x_kwargs['range'] = chart.x_range
            if x_kwargs:
                self.fig.update_xaxes(row=row_idx, col=1, **x_kwargs)

            # Add horizontal lines
            if chart.horizontal_line is not None:
                self.fig.add_hline(
                    y=chart.horizontal_line,
                    line_dash=_defaults['hline']['dash'],
                    line_color=resolve_color(chart.horizontal_line_color) if chart.horizontal_line_color else self._colors['zero_line'],
                    line_width=_defaults['hline']['width'],
                    row=row_idx,
                    col=1,
                )

            for hline in chart.horizontal_lines:
                self.fig.add_hline(
                    y=hline.get('y', 0),
                    line_dash=_defaults['hline']['dash'],
                    line_color=resolve_color(hline.get('color', 'gray')),
                    line_width=_defaults['hline']['width'],
                    row=row_idx,
                    col=1,
                )

        # Apply crosshair (unified spikeline) if enabled
        if self.crosshair:
            self._apply_unified_spikeline()

        # Apply recession shading
        if self.show_recessions:
            self._apply_recession_shading()

            # Fix shape xref when crosshair is enabled
            if self.crosshair and self.fig.layout.shapes:
                bottom_xaxis = f'x{num_rows}'
                for shape in self.fig.layout.shapes:
                    shape.xref = bottom_xaxis

        return self.fig

    def _apply_legend(self) -> None:
        """Apply legend configuration."""
        orientation = self.legend_orientation
        position = self.legend_position

        # Map orientation names
        orientation_map = {'horizontal': 'h', 'vertical': 'v', 'h': 'h', 'v': 'v'}
        orientation = orientation_map.get(orientation, 'h')

        legend_kwargs: dict[str, Any] = {
            'orientation': orientation,
            'xanchor': _defaults['legend']['xanchor'],
            'font': dict(size=_defaults['fonts']['legend'], color=self._colors['text']),
            'bgcolor': 'rgba(0,0,0,0)',
        }

        if position in _defaults['legend_positions']:
            legend_kwargs.update(_defaults['legend_positions'][position])

        self.fig.update_layout(legend=legend_kwargs)

    def _update_x_range(self, x: Any) -> None:
        """Update tracked x-axis range."""
        try:
            if hasattr(x, '__len__') and len(x) > 0:
                x_min, x_max = min(x), max(x)
                if self._x_range is None:
                    self._x_range = (x_min, x_max)
                else:
                    self._x_range = (
                        min(self._x_range[0], x_min),
                        max(self._x_range[1], x_max),
                    )
        except (TypeError, ValueError):
            pass

    def _apply_unified_spikeline(self) -> None:
        """Apply spike lines that span all charts."""
        num_rows = len(self.charts)
        bottom_xaxis = f'x{num_rows}'

        # Bind all traces to the bottom x-axis
        self.fig.update_traces(xaxis=bottom_xaxis)

        # Add invisible traces to upper axes to force tick label rendering
        if self._x_range is not None:
            invisible_marker = dict(opacity=0)
            x_range_list = list(self._x_range)
            for row in range(1, num_rows):
                axis_suffix = str(row) if row > 1 else ''
                self.fig.add_trace(go.Scatter(
                    x=x_range_list,
                    y=[0, 0],
                    mode='markers',
                    marker=invisible_marker,
                    showlegend=False,
                    hoverinfo='skip',
                    xaxis=bottom_xaxis,
                    yaxis=f'y{axis_suffix}',
                ))

            # Constrain x-axis range
            self.fig.update_xaxes(range=x_range_list)

        # Sync upper x-axes to bottom x-axis
        for row in range(1, num_rows):
            self.fig.update_xaxes(row=row, col=1, matches=bottom_xaxis)

        # Apply spike settings
        crosshair_config = _defaults.get('crosshair', {})
        self.fig.update_xaxes(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikecolor=resolve_color(self.crosshair_color),
            spikethickness=crosshair_config.get('thickness') or _defaults['spike']['thickness'],
            spikedash=crosshair_config.get('dash') or _defaults['spike']['dash'],
        )

    def _apply_recession_shading(self) -> None:
        """Apply recession shading to all charts."""
        fill_color = resolve_color(self.recession_color)
        fill_opacity = self.recession_opacity

        recession_periods = NBER_RECESSIONS

        # Filter recessions to the current x-axis range
        if self._x_range is not None:
            try:
                start_dt = self._x_range[0]
                end_dt = self._x_range[1]
                if hasattr(start_dt, 'to_pydatetime'):
                    start_dt = start_dt.to_pydatetime()
                if hasattr(end_dt, 'to_pydatetime'):
                    end_dt = end_dt.to_pydatetime()
                recession_periods = get_recessions_in_range(start_dt, end_dt, recession_periods)
            except (TypeError, AttributeError):
                return

        # Add recession shading to all rows
        num_rows = len(self.charts)
        for rec_start, rec_end in recession_periods:
            for row in range(1, num_rows + 1):
                self.fig.add_vrect(
                    x0=rec_start,
                    x1=rec_end,
                    fillcolor=fill_color,
                    opacity=fill_opacity,
                    layer='below',
                    line_width=0,
                    row=row,
                    col=1,
                    exclude_empty_subplots=False,
                )
