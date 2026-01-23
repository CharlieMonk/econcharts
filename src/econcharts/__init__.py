"""econcharts - Reusable economic chart class with dark theme support.

Usage:
    from econcharts import EconChart
    chart = EconChart(num_rows=1, height=400)
    chart.add_line(row=1, x=dates, y=values, name='GDP', color='teal')
    chart.show()

    # FRED data utilities
    from econcharts.fred import fetch_gdp, fetch_unemployment

    # Recession data
    from econcharts.recessions import NBER_RECESSIONS
"""

from .chart import EconChart, DEFAULT_COLORS, PALETTE

# Make PALETTE and DEFAULT_COLORS accessible as class attributes
EconChart.PALETTE = PALETTE
EconChart.DEFAULT_COLORS = DEFAULT_COLORS

# Export main class and constants
__all__ = ['EconChart', 'DEFAULT_COLORS', 'PALETTE']
