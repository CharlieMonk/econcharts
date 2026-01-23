"""Reusable economic chart class with dark theme support and multi-subplot capabilities."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Sequence

import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from econcharts.recessions import NBER_RECESSIONS, get_recessions_in_range


_MODULE_DIR = os.path.dirname(__file__)


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

    @staticmethod
    def _load_yaml(filename: str) -> dict:
        """Load a YAML file from the module directory."""
        with open(os.path.join(_MODULE_DIR, filename), 'r') as f:
            return yaml.safe_load(f)

    # Load YAML configuration as class variables
    _defaults = _load_yaml('defaults.yaml')
    palette = _load_yaml('colors.yaml')


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
        self.height = height or self._defaults['chart']['height']
        self._spike_enabled = False
        self._recession_enabled = True
        self._recession_config: dict[str, Any] = {}
        self._x_range: tuple | None = None

        # Merge custom colors with defaults
        self._colors = {**self._defaults['colors'], **(colors or {})}

        # Apply defaults
        shared_xaxes = shared_xaxes if shared_xaxes is not None else self._defaults['chart']['shared_xaxes']
        vertical_spacing = vertical_spacing if vertical_spacing is not None else self._defaults['chart']['vertical_spacing']
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
            paper_bgcolor=self._colors['paper'],
            plot_bgcolor=self._colors['background'],
            font=dict(color=self._colors['text'], size=self._defaults['fonts']['main']),
            hoverlabel=dict(
                bgcolor=self._colors['paper'],
                font_size=self._defaults['fonts']['hoverlabel'],
                font_color=self._colors['text'],
            ),
        )

        # Style subplot titles
        if subplot_titles:
            title_font = dict(size=self._defaults['fonts']['subplot_title'], color=self._colors['text'])
            for annotation in self.fig['layout']['annotations']:
                annotation['font'] = title_font

        # Apply default grid color to all axes
        for row in range(1, num_rows + 1):
            self.fig.update_xaxes(gridcolor=self._colors['grid'], row=row, col=1)
            self.fig.update_yaxes(gridcolor=self._colors['grid'], row=row, col=1)

    @staticmethod
    def resolve_color(color: str) -> str:
        """
        Resolve a color name to its hex value.

        Args:
            color: Either a hex/rgb color string or a named color
                   from the palette (e.g., 'teal', 'coral')

        Returns:
            Hex or rgb color string

        Examples:
            >>> EconChart.resolve_color('teal')
            '#00d4aa'
            >>> EconChart.resolve_color('#ff0000')
            '#ff0000'
        """
        if color.startswith(('#', 'rgb')):
            return color
        return EconChart.palette.get(color.lower(), color)

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
            'color': self.resolve_color(color),
            'width': width or self._defaults['line']['width'],
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
                'marker': dict(color=self.resolve_color(color), size=marker_size or self._defaults['scatter']['marker_size']),
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
                size=self._defaults['fonts']['axis_title'],
                color=title_color or self._colors['text'],
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
                size=self._defaults['fonts']['axis_title'],
                color=self._colors['text'],
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
            line_dash=dash or self._defaults['hline']['dash'],
            line_color=color or self._colors['zero_line'],
            line_width=width or self._defaults['hline']['width'],
            row=row,
            col=1,
        )
        return self

    def disable_recession_shading(self) -> EconChart:
        """
        Disable automatic recession shading.

        By default, recession shading is enabled and will be applied when
        the chart is built. Call this method to disable it.

        Returns:
            Self for method chaining.

        Example:
            chart = econcharts(num_rows=1)
            chart.add_line(row=1, x=dates, y=values, name='Data', color='teal')
            chart.disable_recession_shading()  # No recession shading
            chart.show()
        """
        self._recession_enabled = False
        return self

    def configure_recession_shading(
        self,
        row: int | str | list[int] = 'all',
        recessions: Sequence[tuple[datetime, datetime]] | None = None,
        color: str | None = None,
        opacity: float | None = None,
    ) -> EconChart:
        """
        Configure recession shading options.

        Recession shading is enabled by default. Use this method to customize
        the appearance or specify custom recession periods.

        Args:
            row: Row number (1-indexed), 'all' to apply to all rows, or a list
                of row numbers to apply to specific rows (e.g., [1, 3]).
            recessions: Custom list of (start, end) datetime tuples defining
                recession periods. If None, uses NBER recession dates.
            color: Fill color for recession shading. Defaults to gray.
            opacity: Fill opacity (0-1). Defaults from config.

        Returns:
            Self for method chaining.

        Example:
            # Custom recession periods with custom color
            from datetime import datetime
            custom = [
                (datetime(2007, 12, 1), datetime(2009, 6, 1)),
                (datetime(2020, 2, 1), datetime(2020, 4, 1)),
            ]
            chart.configure_recession_shading(recessions=custom, color='red', opacity=0.2)
        """
        self._recession_config = {
            'row': row,
            'recessions': recessions,
            'color': color,
            'opacity': opacity,
        }
        return self

    def _apply_recession_shading(self) -> None:
        """Apply recession shading to the chart."""
        # Get config or defaults
        config = self._recession_config
        row = config.get('row', 'all')
        recessions = config.get('recessions')
        color = config.get('color')
        opacity = config.get('opacity')

        # Get recession defaults
        recession_defaults = self._defaults.get('recession', {})
        fill_color = color or recession_defaults.get('color', 'gray')
        fill_opacity = opacity if opacity is not None else recession_defaults.get('opacity', 0.15)

        # Resolve named color
        fill_color = self.resolve_color(fill_color)

        # Use NBER recessions if not specified
        recession_periods = recessions if recessions is not None else NBER_RECESSIONS

        # Filter recessions to the current x-axis range if available
        if self._x_range is not None:
            try:
                start_dt = self._x_range[0]
                end_dt = self._x_range[1]
                # Convert to datetime if needed
                if hasattr(start_dt, 'to_pydatetime'):
                    start_dt = start_dt.to_pydatetime()
                if hasattr(end_dt, 'to_pydatetime'):
                    end_dt = end_dt.to_pydatetime()
                recession_periods = get_recessions_in_range(start_dt, end_dt, recession_periods)
            except (TypeError, AttributeError):
                # If x-axis isn't datetime-compatible, skip recession shading
                return

        # Add recession shading using add_vrect with row parameter
        # exclude_empty_subplots=False ensures shapes are added even after
        # traces are moved to the bottom axis by unified spikeline
        # Plotly's add_vrect doesn't accept a list, so we iterate when needed
        rows_to_shade = row if isinstance(row, list) else [row]
        for rec_start, rec_end in recession_periods:
            for r in rows_to_shade:
                self.fig.add_vrect(
                    x0=rec_start,
                    x1=rec_end,
                    fillcolor=fill_color,
                    opacity=fill_opacity,
                    layer='below',
                    line_width=0,
                    row=r,
                    col=1,
                    exclude_empty_subplots=False,
                )

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
            self._colors['spike'] = spike_color
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
            'font': dict(size=self._defaults['fonts']['legend'], color=self._colors['text']),
            'bgcolor': 'rgba(0,0,0,0)',
        }

        if position in self._defaults['legend_positions']:
            legend_kwargs.update(self._defaults['legend_positions'][position])

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
        margins = self._defaults['margins']
        self.fig.update_layout(margin=dict(
            t=top if top is not None else margins['top'],
            l=left if left is not None else margins['left'],
            r=right if right is not None else margins['right'],
            b=bottom if bottom is not None else margins['bottom'],
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
                font=dict(size=font_size or self._defaults['fonts']['chart_title'], color=self._colors['text']),
                y=0.99,
                yanchor='top',
            )
        )
        return self

    def build(self) -> go.Figure:
        """
        Finalize and return the Plotly figure.

        Applies recession shading (enabled by default) and unified spike line if enabled.

        Returns:
            Plotly Figure object
        """
        # Apply unified spikeline first (modifies axis bindings)
        if self._spike_enabled:
            self._apply_unified_spikeline()

        # Apply recession shading
        if self._recession_enabled:
            self._apply_recession_shading()

            # When unified spikeline is enabled, shapes reference axes that are
            # now "matched" to the bottom axis, causing them not to render.
            # Fix by updating all shapes to reference the bottom x-axis.
            if self._spike_enabled and self.fig.layout.shapes:
                bottom_xaxis = f'x{self.num_rows}'
                for shape in self.fig.layout.shapes:
                    shape.xref = bottom_xaxis

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
        # These must be bound to the bottom x-axis (like all other traces) so that
        # shapes with xref=bottom_xaxis and yref=y/y2 domain render correctly
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
                    xaxis=bottom_xaxis,
                    yaxis=f'y{axis_suffix}',
                ))

            # Explicitly constrain the bottom x-axis range to the data range.
            # This prevents Plotly's autorange from adding excessive padding when
            # multiple traces with different point densities share the same axis.
            # The range is set on all x-axes (will propagate via matches).
            self.fig.update_xaxes(range=x_range_list)

        # Sync upper x-axes to bottom x-axis
        for row in range(1, self.num_rows):
            self.fig.update_xaxes(row=row, col=1, matches=bottom_xaxis)

        # Apply spike settings to all x-axes
        self.fig.update_xaxes(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikecolor=self._colors['spike'],
            spikethickness=self._defaults['spike']['thickness'],
            spikedash=self._defaults['spike']['dash'],
        )


# Backward compatibility aliases
PALETTE = EconChart.palette
DEFAULT_COLORS = EconChart._defaults['colors'].copy()
