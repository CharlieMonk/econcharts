"""EconChart - Reusable economic chart class with dark theme support."""

from .chart import EconChart, DEFAULT_COLORS, PALETTE

# Backward compatibility aliases
resolve_color = EconChart.resolve_color

__all__ = ['EconChart', 'DEFAULT_COLORS', 'PALETTE', 'resolve_color']
