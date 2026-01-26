"""econcharts - Reusable economic chart classes with dark theme support.

Usage:
    from econcharts import EconBoard, EconChart, Data

    # Single chart
    chart = EconChart(Data(x=dates, y=values, name='GDP'), title='GDP Growth')
    board = EconBoard(chart)
    board.show()

    # Multiple charts
    gdp = EconChart(Data(x=dates, y=gdp_values, name='GDP'), title='GDP')
    inflation = EconChart(Data(x=dates, y=cpi_values, name='CPI'), title='Inflation')
    board = EconBoard(gdp, inflation, crosshair=True)
    board.show()

    # FRED data utilities
    from econcharts.fred import fetch_gdp, fetch_unemployment

    # Recession data
    from econcharts.recessions import NBER_RECESSIONS
"""

from .chart import EconBase, EconBoard, EconChart, Data, palette, resolve_color

__all__ = ['EconBase', 'EconBoard', 'EconChart', 'Data', 'palette', 'resolve_color']
