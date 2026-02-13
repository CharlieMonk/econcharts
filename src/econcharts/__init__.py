"""econcharts - Professional economic charts with dark theme support.

Usage:
    from econcharts import EconChart, EconBoard, Data

    # Single chart (simplest form)
    chart = EconChart(
        Data(x=dates, y=values, name='GDP', color='teal'),
        title='GDP Growth',
        y_label='% YoY',
        horizontal_line=0,
    )
    chart.show()

    # Multi-chart dashboard
    gdp = EconChart(Data(x=gdp_dates, y=gdp_values, name='GDP'), title='GDP')
    inflation = EconChart(Data(x=inf_dates, y=inf_values, name='CPI'), title='Inflation')
    board = EconBoard(
        gdp, inflation,
        crosshair=True,       # Enabled by default
        show_recessions=True, # Enabled by default
    )
    board.show()

    # FRED data utilities
    from econcharts.fred import fetch_gdp, fetch_inflation, fetch_unemployment

    # Recession data
    from econcharts.recessions import NBER_RECESSIONS
"""

from .chart import EconBase, EconBoard, EconChart, Data, resolve_color

__all__ = ['EconBase', 'EconBoard', 'EconChart', 'Data', 'resolve_color']
