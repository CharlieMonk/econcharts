"""econcharts - Reusable economic chart class with dark theme support.

Usage:
    import econcharts
    chart = econcharts(num_rows=1, height=400)
    chart.add_line(row=1, x=dates, y=values, name='GDP', color='teal')
    chart.show()
"""

import sys
from .chart import EconChart, DEFAULT_COLORS, PALETTE

# Make PALETTE and DEFAULT_COLORS accessible as class attributes
EconChart.PALETTE = PALETTE
EconChart.DEFAULT_COLORS = DEFAULT_COLORS

# Replace module with EconChart class so 'import econcharts' is callable
sys.modules[__name__] = EconChart
