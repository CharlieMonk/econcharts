"""Reusable economic chart class with dark theme support and multi-subplot capabilities."""

from __future__ import annotations

import os
from typing import Any

import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Module-level constants
_MODULE_DIR = os.path.dirname(__file__)


def _load_yaml(filename: str) -> dict:
    """Load a YAML file from the module directory."""
    with open(os.path.join(_MODULE_DIR, filename), 'r') as f:
        return yaml.safe_load(f)


# Load configuration once at module import
_DEFAULTS = _load_yaml('defaults.yaml')
PALETTE = _load_yaml('colors.yaml')

# Cache commonly accessed defaults
_DEFAULT_COLORS = _DEFAULTS['colors']
_DEFAULT_FONTS = _DEFAULTS['fonts']
_DEFAULT_CHART = _DEFAULTS['chart']
_DEFAULT_MARGINS = _DEFAULTS['margins']
_DEFAULT_SPIKE = _DEFAULTS['spike']
_DEFAULT_HLINE = _DEFAULTS['hline']
_DEFAULT_LINE_WIDTH = _DEFAULTS['line']['width']
_DEFAULT_MARKER_SIZE = _DEFAULTS['scatter']['marker_size']
_LEGEND_POSITIONS = _DEFAULTS['legend_positions']

# Export DEFAULT_COLORS for backward compatibility
DEFAULT_COLORS = _DEFAULT_COLORS.copy()


def resolve_color(color: str) -> str:
    """
    Resolve a color name to its hex value.

    Args:
        color: Either a hex color string (e.g., '#ff0000') or a named color
               from the palette (e.g., 'teal', 'coral')

    Returns:
        Hex color string

    Examples:
        >>> resolve_color('teal')
        '#00d4aa'
        >>> resolve_color('#ff0000')
        '#ff0000'
    """
    if color.startswith(('#', 'rgb')):
        return color
    return PALETTE.get(color.lower(), color)


class EconChart:
    """
    A configurable multi-subplot chart builder with dark theme support.

    Provides a fluent interface for building economic/financial charts with
    consistent styling, unified spike lines, and flexible layout options.

    Example usage:
        chart = EconChart(
            num_rows=3,
            subplot_titles=('Revenue', 'Costs', 'Profit'),
            height=700,
        )
        chart.add_line(row=1, x=dates, y=revenue, name='Revenue', color='teal')
        chart.add_line(row=2, x=dates, y=costs, name='Costs', color='coral')
        chart.add_line(row=3, x=dates, y=profit, name='Profit', color='gold')
        chart.add_hline(row=3, y=0)
        chart.enable_unified_spikeline()
        fig = chart.build()
        fig.show()
    """

    def __init__(
        self,
        num_rows: int,
        row_heights: list[float] | None = None,
        subplot_titles: tuple[str, ...] | None = None,
        colors: dict[str, str] | None = None,
        shared_xaxes: bool | None = None,
        vertical_spacing: float | None = None,
        height: int | None = None,
    ) -> None:
        """
        Initialize an EconChart.

        Args:
            num_rows: Number of subplot rows
            row_heights: List of relative heights for each row. Auto-equal if None.
            subplot_titles: Tuple of titles for each subplot
            colors: Theme colors dict (defaults to colors from defaults.yaml)
            shared_xaxes: Whether to share x-axes across subplots
            vertical_spacing: Spacing between subplots (0-1)
            height: Chart height in pixels
        """
        self.num_rows = num_rows
        self._colors = colors or _DEFAULT_COLORS.copy()
        self.height = height or _DEFAULT_CHART['height']
        self._spike_enabled = False
        self._spike_color = self._colors.get('spike', _DEFAULT_COLORS['spike'])
        self._x_range: tuple | None = None

        # Cache frequently used colors
        self._text_color = self._colors.get('text', _DEFAULT_COLORS['text'])
        self._grid_color = self._colors.get('grid', _DEFAULT_COLORS['grid'])
        self._paper_color = self._colors.get('paper', _DEFAULT_COLORS['paper'])
        self._bg_color = self._colors.get('background', _DEFAULT_COLORS['background'])
        self._zero_line_color = self._colors.get('zero_line', _DEFAULT_COLORS['zero_line'])

        # Apply defaults
        shared_xaxes = shared_xaxes if shared_xaxes is not None else _DEFAULT_CHART['shared_xaxes']
        vertical_spacing = vertical_spacing if vertical_spacing is not None else _DEFAULT_CHART['vertical_spacing']
        row_heights = row_heights or [1.0 / num_rows] * num_rows

        self.fig = make_subplots(
            rows=num_rows,
            cols=1,
            row_heights=row_heights,
            shared_xaxes=shared_xaxes,
            vertical_spacing=vertical_spacing,
            subplot_titles=subplot_titles,
        )

        # Apply default dark theme layout
        self.fig.update_layout(
            height=self.height,
            hovermode='x unified',
            paper_bgcolor=self._paper_color,
            plot_bgcolor=self._bg_color,
            font=dict(color=self._text_color, size=_DEFAULT_FONTS['main']),
            hoverlabel=dict(
                bgcolor=self._paper_color,
                font_size=_DEFAULT_FONTS['hoverlabel'],
                font_color=self._text_color,
            ),
        )

        # Style subplot titles
        if subplot_titles:
            title_font = dict(size=_DEFAULT_FONTS['subplot_title'], color=self._text_color)
            for annotation in self.fig['layout']['annotations']:
                annotation['font'] = title_font

        # Apply default grid color to all axes
        for row in range(1, num_rows + 1):
            self.fig.update_xaxes(gridcolor=self._grid_color, row=row, col=1)
            self.fig.update_yaxes(gridcolor=self._grid_color, row=row, col=1)

    @property
    def colors(self) -> dict[str, str]:
        """Theme colors dictionary."""
        return self._colors

    def _add_trace(
        self,
        row: int,
        x: Any,
        y: Any,
        name: str,
        trace_kwargs: dict[str, Any],
        hover_template: str | None,
        legendgroup: str | None,
    ) -> None:
        """Add a trace to the chart with common options."""
        if hover_template:
            trace_kwargs['hovertemplate'] = hover_template
        if legendgroup:
            trace_kwargs['legendgroup'] = legendgroup

        self.fig.add_trace(go.Scatter(x=x, y=y, name=name, **trace_kwargs), row=row, col=1)
        self._update_x_range(x)

    def add_line(
        self,
        row: int,
        x: Any,
        y: Any,
        name: str,
        color: str,
        width: float | None = None,
        dash: str | None = None,
        hover_template: str | None = None,
        visible: bool | str = True,
        legendgroup: str | None = None,
        showlegend: bool = True,
    ) -> EconChart:
        """
        Add a line trace to the chart.

        Args:
            row: Row number (1-indexed)
            x: X-axis data
            y: Y-axis data
            name: Trace name for legend
            color: Line color (hex like '#ff0000' or name like 'teal', 'coral')
            width: Line width
            dash: Line dash style ('solid', 'dot', 'dash', 'longdash', 'dashdot')
            hover_template: Custom hover template
            visible: True, False, or 'legendonly'
            legendgroup: Group name for synchronized legend toggling
            showlegend: Whether to show in legend

        Returns:
            Self for method chaining
        """
        line_dict: dict[str, Any] = {
            'color': resolve_color(color),
            'width': width or _DEFAULT_LINE_WIDTH,
        }
        if dash:
            line_dict['dash'] = dash

        self._add_trace(
            row=row,
            x=x,
            y=y,
            name=name,
            trace_kwargs={'line': line_dict, 'visible': visible, 'showlegend': showlegend},
            hover_template=hover_template,
            legendgroup=legendgroup,
        )
        return self

    def add_scatter(
        self,
        row: int,
        x: Any,
        y: Any,
        name: str,
        color: str,
        marker_size: int | None = None,
        hover_template: str | None = None,
        visible: bool | str = True,
        legendgroup: str | None = None,
        showlegend: bool = True,
    ) -> EconChart:
        """
        Add a scatter (markers only) trace to the chart.

        Args:
            row: Row number (1-indexed)
            x: X-axis data
            y: Y-axis data
            name: Trace name for legend
            color: Marker color (hex like '#ff0000' or name like 'teal', 'coral')
            marker_size: Marker size
            hover_template: Custom hover template
            visible: True, False, or 'legendonly'
            legendgroup: Group name for synchronized legend toggling
            showlegend: Whether to show in legend

        Returns:
            Self for method chaining
        """
        self._add_trace(
            row=row,
            x=x,
            y=y,
            name=name,
            trace_kwargs={
                'mode': 'markers',
                'marker': dict(color=resolve_color(color), size=marker_size or _DEFAULT_MARKER_SIZE),
                'visible': visible,
                'showlegend': showlegend,
            },
            hover_template=hover_template,
            legendgroup=legendgroup,
        )
        return self

    def set_yaxis(
        self,
        row: int,
        title: str | None = None,
        title_color: str | None = None,
        scale_type: str = 'linear',
        gridcolor: str | None = None,
    ) -> EconChart:
        """
        Configure y-axis for a specific row.

        Args:
            row: Row number (1-indexed)
            title: Axis title
            title_color: Title color (defaults to text color)
            scale_type: 'linear' or 'log'
            gridcolor: Grid line color

        Returns:
            Self for method chaining
        """
        update_kwargs: dict[str, Any] = {'type': scale_type}

        if title:
            update_kwargs['title_text'] = title
            update_kwargs['title_font'] = dict(
                size=_DEFAULT_FONTS['axis_title'],
                color=title_color or self._text_color,
            )

        if gridcolor:
            update_kwargs['gridcolor'] = gridcolor

        self.fig.update_yaxes(row=row, col=1, **update_kwargs)
        return self

    def set_xaxis(
        self,
        row: int,
        title: str | None = None,
        tick_format: str | None = None,
        hover_format: str | None = None,
        range: tuple | None = None,
        gridcolor: str | None = None,
    ) -> EconChart:
        """
        Configure x-axis for a specific row.

        Args:
            row: Row number (1-indexed)
            title: Axis title
            tick_format: Tick label format (e.g., '%b %Y' for dates)
            hover_format: Hover label format
            range: Tuple of (min, max) for axis range
            gridcolor: Grid line color

        Returns:
            Self for method chaining
        """
        update_kwargs: dict[str, Any] = {}

        if title:
            update_kwargs['title_text'] = title
            update_kwargs['title_font'] = dict(
                size=_DEFAULT_FONTS['axis_title'],
                color=self._text_color,
            )

        if tick_format:
            update_kwargs['tickformat'] = tick_format
        if hover_format:
            update_kwargs['hoverformat'] = hover_format
        if range:
            update_kwargs['range'] = range
        if gridcolor:
            update_kwargs['gridcolor'] = gridcolor

        if update_kwargs:
            self.fig.update_xaxes(row=row, col=1, **update_kwargs)
        return self

    def add_hline(
        self,
        row: int,
        y: float,
        color: str | None = None,
        dash: str | None = None,
        width: float | None = None,
    ) -> EconChart:
        """
        Add a horizontal reference line to a subplot.

        Args:
            row: Row number (1-indexed)
            y: Y-value for the line
            color: Line color (defaults to zero_line color)
            dash: Line dash style
            width: Line width

        Returns:
            Self for method chaining
        """
        self.fig.add_hline(
            y=y,
            line_dash=dash or _DEFAULT_HLINE['dash'],
            line_color=color or self._zero_line_color,
            line_width=width or _DEFAULT_HLINE['width'],
            row=row,
            col=1,
        )
        return self

    def enable_unified_spikeline(self, spike_color: str | None = None) -> EconChart:
        """
        Enable spike lines that span all subplots.

        Args:
            spike_color: Color for the spike line

        Returns:
            Self for method chaining
        """
        self._spike_enabled = True
        if spike_color:
            self._spike_color = spike_color
        return self

    def set_legend(
        self,
        orientation: str = 'h',
        position: str = 'top',
    ) -> EconChart:
        """
        Configure legend position and orientation.

        Args:
            orientation: 'h' for horizontal, 'v' for vertical
            position: 'top', 'bottom', or 'right'

        Returns:
            Self for method chaining
        """
        legend_kwargs: dict[str, Any] = {
            'orientation': orientation,
            'font': dict(size=_DEFAULT_FONTS['legend'], color=self._text_color),
            'bgcolor': 'rgba(0,0,0,0)',
        }

        if position in _LEGEND_POSITIONS:
            legend_kwargs.update(_LEGEND_POSITIONS[position])

        self.fig.update_layout(legend=legend_kwargs)
        return self

    def set_margins(
        self,
        top: int | None = None,
        left: int | None = None,
        right: int | None = None,
        bottom: int | None = None,
    ) -> EconChart:
        """
        Set chart margins.

        Args:
            top: Top margin in pixels
            left: Left margin in pixels
            right: Right margin in pixels
            bottom: Bottom margin in pixels

        Returns:
            Self for method chaining
        """
        self.fig.update_layout(margin=dict(
            t=top if top is not None else _DEFAULT_MARGINS['top'],
            l=left if left is not None else _DEFAULT_MARGINS['left'],
            r=right if right is not None else _DEFAULT_MARGINS['right'],
            b=bottom if bottom is not None else _DEFAULT_MARGINS['bottom'],
        ))
        return self

    def set_title(self, text: str, font_size: int | None = None) -> EconChart:
        """
        Set chart title.

        Args:
            text: Title text
            font_size: Font size

        Returns:
            Self for method chaining
        """
        self.fig.update_layout(
            title=dict(
                text=text,
                font=dict(size=font_size or _DEFAULT_FONTS['chart_title'], color=self._text_color),
                y=0.99,
                yanchor='top',
            )
        )
        return self

    def build(self) -> go.Figure:
        """
        Finalize and return the Plotly figure.

        Applies unified spike line if enabled.

        Returns:
            Plotly Figure object
        """
        if self._spike_enabled:
            self._apply_unified_spikeline()
        return self.fig

    def show(self) -> None:
        """Display the chart."""
        self.build().show()

    def to_html(self, path: str, include_plotlyjs: bool | str = True) -> None:
        """
        Export chart to HTML file.

        Args:
            path: Output file path
            include_plotlyjs: Whether to include plotly.js ('cdn', True, False)
        """
        self.build().write_html(path, include_plotlyjs=include_plotlyjs)

    def _update_x_range(self, x: Any) -> None:
        """Update tracked x-axis range for unified spikeline."""
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
        """
        Apply spike lines that span all subplots.

        This is a workaround for Plotly 4.0+ where make_subplots creates separate
        x-axes, preventing spike lines from spanning all subplots.
        See: https://github.com/plotly/plotly.py/issues/1677
        """
        bottom_xaxis = f'x{self.num_rows}'

        # Bind all traces to the bottom x-axis
        self.fig.update_traces(xaxis=bottom_xaxis)

        # Add invisible traces to upper axes to force tick label rendering
        if self._x_range is not None:
            invisible_marker = dict(opacity=0)
            x_range_list = list(self._x_range)
            for row in range(1, self.num_rows):
                axis_suffix = str(row) if row > 1 else ''
                self.fig.add_trace(go.Scatter(
                    x=x_range_list,
                    y=[0, 0],
                    mode='markers',
                    marker=invisible_marker,
                    showlegend=False,
                    hoverinfo='skip',
                    xaxis=f'x{axis_suffix}',
                    yaxis=f'y{axis_suffix}',
                ))

        # Sync upper x-axes to bottom x-axis
        for row in range(1, self.num_rows):
            self.fig.update_xaxes(row=row, col=1, matches=bottom_xaxis)

        # Apply spike settings to all x-axes
        self.fig.update_xaxes(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikecolor=self._spike_color,
            spikethickness=_DEFAULT_SPIKE['thickness'],
            spikedash=_DEFAULT_SPIKE['dash'],
        )
