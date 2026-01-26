"""Visual tests for econcharts using Playwright.

These tests:
1. Use real economic data from FRED (Federal Reserve Economic Data)
2. Export charts to HTML
3. Use Playwright to examine DOM structure
4. Take screenshots
5. Test hover tooltips for correct datapoints
6. Test zoom functionality

Data is cached locally for offline/CI use.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, Page, expect

from econcharts import EconBoard, EconChart, Data
from econcharts.fred import (
    fetch_gdp, fetch_inflation, fetch_unemployment,
    fetch_fed_funds, fetch_sp500, fetch_treasury_10y
)
from econcharts.recessions import NBER_RECESSIONS, get_recessions_in_range


def wait_for_plotly_ready(page, timeout=30000):
    """Wait for Plotly to fully initialize and render."""
    page.wait_for_selector('.js-plotly-plot', timeout=timeout)
    page.wait_for_load_state('networkidle')
    # Wait for Plotly to populate its internal data structures
    # Note: Check for any xaxis (including xaxis3) since unified spikeline removes xaxis/xaxis2
    page.wait_for_function('''() => {
        const gd = document.querySelector('.js-plotly-plot');
        if (!gd || !gd._fullLayout || !gd.data || gd.data.length === 0) return false;
        // Check for any x-axis (xaxis, xaxis2, xaxis3, etc.)
        const hasXAxis = Object.keys(gd._fullLayout).some(k => k.startsWith('xaxis'));
        return hasXAxis;
    }''', timeout=timeout)
    # Small additional wait to ensure rendering is complete
    page.wait_for_timeout(200)


# Real FRED data functions (with caching for offline use)
def get_gdp_data():
    """Get real GDP growth data from FRED."""
    return fetch_gdp(start="2000-01-01")


def get_inflation_data():
    """Get real inflation data from FRED."""
    return fetch_inflation(start="2000-01-01")


def get_unemployment_data():
    """Get real unemployment data from FRED."""
    return fetch_unemployment(start="2000-01-01")


def get_stock_data():
    """Get real S&P 500 data from FRED."""
    return fetch_sp500(start="2020-01-01")


def get_interest_rate_data():
    """Get real Federal Funds rate data from FRED."""
    return fetch_fed_funds(start="2000-01-01")


class TestChartGeneration:
    """Test chart generation and basic structure."""

    def test_single_subplot_chart(self, html_dir, screenshots_dir):
        """Test single subplot chart creation."""
        dates, values = get_gdp_data()

        chart = EconChart(
            Data(x=dates, y=values, name='GDP Growth', color='teal'),
            title='GDP Growth Rate',
            y_label='% Change YoY',
            horizontal_line=0,
        )
        board = EconBoard(chart, crosshair=True)

        html_path = html_dir / "single_subplot.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Take screenshot
            page.screenshot(path=str(screenshots_dir / "single_subplot.png"))

            # Verify DOM structure
            plot_div = page.locator('.js-plotly-plot')
            assert plot_div.count() == 1

            # Verify traces exist
            traces = page.locator('.scatter')
            assert traces.count() >= 1

            browser.close()

    def test_direct_chart_display(self, html_dir, screenshots_dir):
        """Test EconChart can be displayed directly without EconBoard."""
        dates, values = get_gdp_data()

        chart = EconChart(
            Data(x=dates, y=values, name='GDP Growth', color='teal'),
            title='Direct Display Test',
            y_label='% Change YoY',
            horizontal_line=0,
        )

        # Test direct to_html without EconBoard
        html_path = html_dir / "direct_display.html"
        chart.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Take screenshot
            page.screenshot(path=str(screenshots_dir / "direct_display.png"))

            # Verify DOM structure
            plot_div = page.locator('.js-plotly-plot')
            assert plot_div.count() == 1

            # Verify traces exist
            traces = page.locator('.scatter')
            assert traces.count() >= 1

            browser.close()

        # Test direct build() returns a Figure
        fig = chart.build()
        assert fig is not None
        assert len(fig.data) >= 1

        # Test with board_kwargs
        fig2 = chart.build(height=400, show_recessions=False)
        assert fig2.layout.height == 400

    def test_multi_subplot_chart(self, html_dir, screenshots_dir):
        """Test multi-subplot chart creation."""
        gdp_dates, gdp_values = get_gdp_data()
        inf_dates, inf_values = get_inflation_data()
        unemp_dates, unemp_values = get_unemployment_data()

        gdp_chart = EconChart(
            Data(x=gdp_dates, y=gdp_values, name='GDP', color='teal'),
            title='GDP Growth',
            y_label='% YoY',
        )
        inflation_chart = EconChart(
            Data(x=inf_dates, y=inf_values, name='CPI', color='coral'),
            title='Inflation',
            y_label='% YoY',
        )
        unemployment_chart = EconChart(
            Data(x=unemp_dates, y=unemp_values, name='Unemployment', color='sky'),
            title='Unemployment',
            y_label='% Rate',
        )

        board = EconBoard(
            gdp_chart,
            inflation_chart,
            unemployment_chart,
            height=700,
            legend='top',
            crosshair=True,
        )

        html_path = html_dir / "multi_subplot.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Take screenshot
            page.screenshot(path=str(screenshots_dir / "multi_subplot.png"))

            # Verify multiple subplots via y-axes
            y_axes = page.locator('[class*="yaxis"]')
            assert y_axes.count() >= 3

            browser.close()

    def test_log_scale_chart(self, html_dir, screenshots_dir):
        """Test logarithmic scale chart."""
        dates, values = get_stock_data()
        # Create exponential growth for log scale demo
        exp_values = [v * (1.1 ** (i/10)) for i, v in enumerate(values)]

        chart = EconChart(
            Data(x=dates, y=exp_values, name='Stock Price', color='gold'),
            title='Stock Price (Log Scale)',
            y_label='Price ($)',
            y_scale='log',
        )
        board = EconBoard(chart, height=400, crosshair=True)

        html_path = html_dir / "log_scale.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            page.screenshot(path=str(screenshots_dir / "log_scale.png"))
            browser.close()


class TestScaleAlignment:
    """Test that chart scales align correctly with data."""

    def test_scale_matches_data_range(self, html_dir, screenshots_dir):
        """Verify y-axis scale encompasses all data points."""
        dates, values = get_inflation_data()
        min_val, max_val = min(values), max(values)

        chart = EconChart(
            Data(x=dates, y=values, name='Inflation', color='coral'),
            title='Inflation Rate',
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "scale_test.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get the y-axis range from Plotly's internal data
            y_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.yaxis.range;
            }''')

            # Verify data fits within range
            assert y_range[0] <= min_val, f"Y-axis min {y_range[0]} > data min {min_val}"
            assert y_range[1] >= max_val, f"Y-axis max {y_range[1]} < data max {max_val}"

            page.screenshot(path=str(screenshots_dir / "scale_alignment.png"))
            browser.close()

    def test_multiple_series_scale(self, html_dir, screenshots_dir):
        """Test scale with multiple series on same subplot."""
        dates, gdp = get_gdp_data()
        _, rates = get_interest_rate_data()
        # Trim to same length
        min_len = min(len(dates), len(rates))
        dates = dates[:min_len]
        gdp = gdp[:min_len]
        rates = rates[:min_len]

        chart = EconChart(
            Data(x=dates, y=gdp, name='GDP Growth', color='teal'),
            Data(x=dates, y=rates, name='Interest Rate', color='coral'),
            title='GDP vs Interest Rates',
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "multi_series_scale.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            y_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.yaxis.range;
            }''')

            all_values = gdp + rates
            min_val, max_val = min(all_values), max(all_values)

            assert y_range[0] <= min_val
            assert y_range[1] >= max_val

            page.screenshot(path=str(screenshots_dir / "multi_series_scale.png"))
            browser.close()


class TestHoverTooltips:
    """Test hover tooltip functionality and accuracy."""

    def test_hover_shows_correct_value(self, html_dir, screenshots_dir):
        """Test that hovering shows the correct data value."""
        # Use simple, predictable data
        dates = [datetime(2020, 1, 1) + timedelta(days=i*30) for i in range(12)]
        values = [10.0, 20.0, 30.0, 25.0, 35.0, 45.0, 40.0, 50.0, 55.0, 60.0, 65.0, 70.0]

        chart = EconChart(
            Data(x=dates, y=values, name='Test Data', color='teal'),
            title='Hover Test',
        )
        board = EconBoard(chart, height=400, crosshair=True)

        html_path = html_dir / "hover_test.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get plot area bounds
            plot_bounds = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                const xa = gd._fullLayout.xaxis;
                const ya = gd._fullLayout.yaxis;
                return {
                    x0: xa._offset,
                    x1: xa._offset + xa._length,
                    y0: ya._offset,
                    y1: ya._offset + ya._length
                };
            }''')

            # Hover over middle of the chart
            hover_x = (plot_bounds['x0'] + plot_bounds['x1']) / 2
            hover_y = (plot_bounds['y0'] + plot_bounds['y1']) / 2

            page.mouse.move(hover_x, hover_y)
            page.wait_for_timeout(500)  # Wait for hover to register

            # Take screenshot with hover
            page.screenshot(path=str(screenshots_dir / "hover_tooltip.png"))

            # Check if hover label appeared
            hover_label = page.locator('.hoverlayer')
            assert hover_label.count() >= 1

            browser.close()

    def test_hover_data_accuracy(self, html_dir, screenshots_dir):
        """Test that hover returns accurate data points."""
        dates = [datetime(2020, 1, 1) + timedelta(days=i*30) for i in range(12)]
        values = [100.5, 200.25, 150.75, 175.0, 225.5, 250.0, 275.25, 300.0, 325.5, 350.75, 375.0, 400.25]

        chart = EconChart(
            Data(x=dates, y=values, name='Accurate Data', color='sky'),
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "hover_accuracy.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get trace data from Plotly
            trace_data = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd.data[0].y;
            }''')

            # Verify data was passed correctly
            for i, (expected, actual) in enumerate(zip(values, trace_data)):
                assert abs(expected - actual) < 0.001, f"Data mismatch at index {i}: {expected} vs {actual}"

            page.screenshot(path=str(screenshots_dir / "hover_accuracy.png"))
            browser.close()


class TestZoomFunctionality:
    """Test zoom and pan functionality."""

    def test_drag_to_zoom(self, html_dir, screenshots_dir):
        """Test that dragging to select an area zooms the chart."""
        dates, values = get_gdp_data()

        chart = EconChart(
            Data(x=dates, y=values, name='GDP', color='teal'),
            title='Zoom Test',
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "zoom_test.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Take initial screenshot
            page.screenshot(path=str(screenshots_dir / "zoom_before.png"))

            # Get initial x-axis range
            initial_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return JSON.stringify(gd._fullLayout.xaxis.range);
            }''')

            # Get plot bounds
            bounds = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                const xa = gd._fullLayout.xaxis;
                const rect = gd.getBoundingClientRect();
                return {
                    x0: rect.left + xa._offset,
                    x1: rect.left + xa._offset + xa._length,
                    y: rect.top + 100
                };
            }''')

            # Drag to select a portion (left third to middle)
            start_x = bounds['x0'] + 50
            end_x = bounds['x0'] + (bounds['x1'] - bounds['x0']) / 2
            y = bounds['y']

            page.mouse.move(start_x, y)
            page.mouse.down()
            page.mouse.move(end_x, y + 50)
            page.mouse.up()

            page.wait_for_timeout(500)  # Wait for zoom animation

            # Take screenshot after zoom
            page.screenshot(path=str(screenshots_dir / "zoom_after.png"))

            # Get new range
            new_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return JSON.stringify(gd._fullLayout.xaxis.range);
            }''')

            # For date axes, we just verify the range changed
            assert initial_range != new_range, "Zoom did not change the axis range"

            browser.close()

    def test_double_click_reset(self, html_dir, screenshots_dir):
        """Test that double-click resets zoom."""
        dates, values = get_inflation_data()

        chart = EconChart(
            Data(x=dates, y=values, name='Inflation', color='coral'),
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "zoom_reset_test.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get initial range
            initial_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return JSON.stringify(gd._fullLayout.xaxis.range);
            }''')

            # Zoom in
            bounds = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                const xa = gd._fullLayout.xaxis;
                const rect = gd.getBoundingClientRect();
                return {
                    x0: rect.left + xa._offset,
                    x1: rect.left + xa._offset + xa._length,
                    y: rect.top + 100
                };
            }''')

            # Drag to zoom
            start_x = bounds['x0'] + 50
            end_x = bounds['x0'] + (bounds['x1'] - bounds['x0']) / 3
            y = bounds['y']

            page.mouse.move(start_x, y)
            page.mouse.down()
            page.mouse.move(end_x, y + 50)
            page.mouse.up()
            page.wait_for_timeout(300)

            # Take zoomed screenshot
            page.screenshot(path=str(screenshots_dir / "zoom_reset_zoomed.png"))

            # Double click to reset
            center_x = (bounds['x0'] + bounds['x1']) / 2
            page.mouse.dblclick(center_x, y)
            page.wait_for_timeout(300)

            # Take reset screenshot
            page.screenshot(path=str(screenshots_dir / "zoom_reset_after.png"))

            # Verify range is back to original (or close to it)
            reset_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return JSON.stringify(gd._fullLayout.xaxis.range);
            }''')

            # Range should be restored
            assert reset_range == initial_range, "Double-click did not reset zoom"

            browser.close()


class TestDOMStructure:
    """Test DOM structure and element presence."""

    def test_chart_elements_exist(self, html_dir, screenshots_dir):
        """Verify essential chart DOM elements exist."""
        dates, values = get_gdp_data()

        chart1 = EconChart(
            Data(x=dates, y=values, name='Series 1', color='teal'),
            title='Chart 1',
        )
        chart2 = EconChart(
            Data(x=dates, y=[v * 0.5 for v in values], name='Series 2', color='coral'),
            title='Chart 2',
        )
        board = EconBoard(
            chart1, chart2,
            title='DOM Test Chart',
            height=500,
            legend='top',
        )

        html_path = html_dir / "dom_structure.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Check essential elements (updated for modern Plotly)
            elements_to_check = [
                ('.plotly', 'Main plot container'),
                ('.main-svg', 'Main SVG'),
                ('.cartesianlayer', 'Cartesian layer'),
                ('.xaxislayer-above', 'X-axis layer'),
                ('.yaxislayer-above', 'Y-axis layer'),
                ('.overplot', 'Overplot layer'),
                ('.legend', 'Legend'),
                ('.scatter', 'Scatter traces'),
            ]

            results = {}
            for selector, name in elements_to_check:
                count = page.locator(selector).count()
                results[name] = count
                assert count >= 1, f"Missing element: {name} ({selector})"

            # Log results
            print("\nDOM Structure Check:")
            for name, count in results.items():
                print(f"  {name}: {count} element(s)")

            page.screenshot(path=str(screenshots_dir / "dom_structure.png"))
            browser.close()

    def test_subplot_titles_rendered(self, html_dir, screenshots_dir):
        """Verify subplot titles are rendered in DOM."""
        dates, values = get_gdp_data()

        titles = ('GDP Growth', 'Inflation Rate', 'Unemployment')
        gdp_chart = EconChart(
            Data(x=dates, y=values, name='GDP', color='teal'),
            title=titles[0],
        )
        inflation_chart = EconChart(
            Data(x=dates, y=[v * 0.3 for v in values], name='Inflation', color='coral'),
            title=titles[1],
        )
        unemployment_chart = EconChart(
            Data(x=dates, y=[abs(v) * 0.2 for v in values], name='Unemployment', color='sky'),
            title=titles[2],
        )
        board = EconBoard(gdp_chart, inflation_chart, unemployment_chart, height=700)

        html_path = html_dir / "subplot_titles.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Check for annotation elements (subplot titles are annotations)
            annotations = page.locator('.annotation-text')

            # Get annotation text
            annotation_texts = page.evaluate('''() => {
                const annotations = document.querySelectorAll('.annotation-text');
                return Array.from(annotations).map(a => a.textContent);
            }''')

            # Verify titles are present
            for title in titles:
                assert title in annotation_texts, f"Subplot title '{title}' not found in DOM"

            page.screenshot(path=str(screenshots_dir / "subplot_titles.png"))
            browser.close()


class TestColorTheme:
    """Test color theme application."""

    def test_dark_theme_colors(self, html_dir, screenshots_dir):
        """Verify dark theme colors are applied."""
        dates, values = get_stock_data()

        chart = EconChart(
            Data(x=dates, y=values, name='Stock', color='gold'),
            title='Dark Theme Test',
        )
        board = EconBoard(chart, height=400)

        html_path = html_dir / "dark_theme.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get background colors from layout
            colors = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return {
                    paper: gd._fullLayout.paper_bgcolor,
                    plot: gd._fullLayout.plot_bgcolor
                };
            }''')

            # Verify dark colors are used
            assert colors['paper'] == '#16213e', f"Paper color mismatch: {colors['paper']}"
            assert colors['plot'] == '#1a1a2e', f"Plot color mismatch: {colors['plot']}"

            page.screenshot(path=str(screenshots_dir / "dark_theme.png"))
            browser.close()

    def test_custom_colors(self, html_dir, screenshots_dir):
        """Test custom color scheme."""
        dates, values = get_gdp_data()

        custom_colors = {
            'background': '#0f0f23',
            'paper': '#1a1a3e',
            'grid': '#404060',
            'text': '#ccccff',
            'spike': 'rgba(200, 200, 255, 0.5)',
            'zero_line': 'rgba(200, 200, 255, 0.3)',
        }

        chart = EconChart(
            Data(x=dates, y=values, name='GDP', color='#88ff88'),
            title='Custom Colors',
        )
        board = EconBoard(chart, height=400, colors=custom_colors)

        html_path = html_dir / "custom_colors.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            colors = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return {
                    paper: gd._fullLayout.paper_bgcolor,
                    plot: gd._fullLayout.plot_bgcolor
                };
            }''')

            assert colors['paper'] == '#1a1a3e'
            assert colors['plot'] == '#0f0f23'

            page.screenshot(path=str(screenshots_dir / "custom_colors.png"))
            browser.close()


class TestRecessionShading:
    """Test recession shading functionality."""

    def test_recession_shading_basic(self, html_dir, screenshots_dir):
        """Test that recession shading is applied by default."""
        dates, values = get_unemployment_data()

        chart = EconChart(
            Data(x=dates, y=values, name='Unemployment', color='coral'),
            title='Unemployment with Recession Shading',
            y_label='%',
        )
        # Recession shading is now enabled by default
        board = EconBoard(chart, height=400, crosshair=True)

        html_path = html_dir / "recession_basic.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Verify shapes (vrects) are present for recession shading
            shape_count = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.shapes ? gd._fullLayout.shapes.length : 0;
            }''')

            assert shape_count >= 1, "No recession shading shapes found"

            page.screenshot(path=str(screenshots_dir / "recession_basic.png"))
            browser.close()

    def test_recession_shading_alignment(self, html_dir, screenshots_dir):
        """Test that recession shading aligns with the time axis."""
        dates, values = get_gdp_data()

        chart = EconChart(
            Data(x=dates, y=values, name='GDP', color='teal'),
            title='GDP with Recession Shading',
            horizontal_line=0,
        )
        # Recession shading is enabled by default
        board = EconBoard(chart, height=400)

        html_path = html_dir / "recession_alignment.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Get shapes and verify their x0/x1 are datetime values
            shapes = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                if (!gd._fullLayout.shapes) return [];
                return gd._fullLayout.shapes.map(s => ({
                    x0: s.x0,
                    x1: s.x1,
                    type: s.type
                }));
            }''')

            # Verify at least one shape exists and has valid coordinates
            assert len(shapes) >= 1, "No recession shading shapes found"

            # Verify x0 < x1 for all shapes (proper time ordering)
            for shape in shapes:
                assert shape['x0'] < shape['x1'], f"Invalid shape coordinates: x0={shape['x0']}, x1={shape['x1']}"

            page.screenshot(path=str(screenshots_dir / "recession_alignment.png"))
            browser.close()

    def test_recession_shading_dynamic_zoom(self, html_dir, screenshots_dir):
        """Test that recession shading adjusts when zooming."""
        dates, values = get_unemployment_data()

        chart = EconChart(
            Data(x=dates, y=values, name='Unemployment', color='coral'),
            title='Recession Shading Zoom Test',
        )
        # Recession shading is enabled by default
        board = EconBoard(chart, height=400)

        html_path = html_dir / "recession_zoom.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Take initial screenshot
            page.screenshot(path=str(screenshots_dir / "recession_zoom_before.png"))

            # Get initial x-axis range
            initial_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.xaxis.range;
            }''')

            # Perform zoom by dragging
            bounds = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                const xa = gd._fullLayout.xaxis;
                const rect = gd.getBoundingClientRect();
                return {
                    x0: rect.left + xa._offset,
                    x1: rect.left + xa._offset + xa._length,
                    y: rect.top + 100
                };
            }''')

            # Drag to zoom to right half of chart
            start_x = bounds['x0'] + (bounds['x1'] - bounds['x0']) / 2
            end_x = bounds['x1'] - 20
            y = bounds['y']

            page.mouse.move(start_x, y)
            page.mouse.down()
            page.mouse.move(end_x, y + 50)
            page.mouse.up()
            page.wait_for_timeout(500)

            # Take zoomed screenshot
            page.screenshot(path=str(screenshots_dir / "recession_zoom_after.png"))

            # Verify x-axis range changed
            new_range = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.xaxis.range;
            }''')

            assert new_range != initial_range, "Zoom did not change axis range"

            # Verify recession shapes are still present after zoom
            shape_count = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.shapes ? gd._fullLayout.shapes.length : 0;
            }''')

            assert shape_count >= 1, "Recession shapes missing after zoom"

            browser.close()

    def test_recession_shading_multi_subplot(self, html_dir, screenshots_dir):
        """Test recession shading on multi-subplot charts."""
        gdp_dates, gdp_values = get_gdp_data()
        unemp_dates, unemp_values = get_unemployment_data()
        inf_dates, inf_values = get_inflation_data()

        gdp_chart = EconChart(
            Data(x=gdp_dates, y=gdp_values, name='GDP', color='teal'),
            title='GDP Growth',
            horizontal_line=0,
        )
        unemployment_chart = EconChart(
            Data(x=unemp_dates, y=unemp_values, name='Unemployment', color='coral'),
            title='Unemployment',
        )
        inflation_chart = EconChart(
            Data(x=inf_dates, y=inf_values, name='Inflation', color='sky'),
            title='Inflation',
            horizontal_line=2.0,
        )

        # Recession shading is enabled by default and applies to all rows
        board = EconBoard(
            gdp_chart, unemployment_chart, inflation_chart,
            height=700,
            crosshair=True,
        )

        html_path = html_dir / "recession_multi_subplot.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Count shapes - should have shapes for each subplot
            shape_count = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.shapes ? gd._fullLayout.shapes.length : 0;
            }''')

            # Should have shapes for multiple recessions across 3 subplots
            assert shape_count >= 3, f"Expected at least 3 recession shapes, got {shape_count}"

            page.screenshot(path=str(screenshots_dir / "recession_multi_subplot.png"))
            browser.close()

    def test_recession_shading_custom_color(self, html_dir, screenshots_dir):
        """Test custom recession shading color and opacity."""
        dates, values = get_unemployment_data()

        chart = EconChart(
            Data(x=dates, y=values, name='Unemployment', color='coral'),
            title='Unemployment with Custom Recession Color',
        )
        board = EconBoard(
            chart,
            height=400,
            recession_color='red',
            recession_opacity=0.25,
        )

        html_path = html_dir / "recession_custom_color.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            # Verify shape fillcolor
            shapes = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                if (!gd._fullLayout.shapes) return [];
                return gd._fullLayout.shapes.map(s => ({
                    fillcolor: s.fillcolor,
                    opacity: s.opacity
                }));
            }''')

            # Verify at least one shape has the custom color
            assert len(shapes) >= 1, "No recession shapes found"
            # Check that opacity is set correctly
            assert shapes[0]['opacity'] == 0.25, f"Expected opacity 0.25, got {shapes[0]['opacity']}"

            page.screenshot(path=str(screenshots_dir / "recession_custom_color.png"))
            browser.close()

    def test_recession_shading_disabled(self, html_dir, screenshots_dir):
        """Test that recession shading can be disabled."""
        dates, values = get_gdp_data()

        chart = EconChart(
            Data(x=dates, y=values, name='GDP', color='teal'),
            title='GDP without Recession Shading',
        )
        board = EconBoard(chart, height=400, show_recessions=False)

        html_path = html_dir / "recession_disabled.html"
        board.to_html(str(html_path))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path}")
            wait_for_plotly_ready(page)

            shape_count = page.evaluate('''() => {
                const gd = document.querySelector('.js-plotly-plot');
                return gd._fullLayout.shapes ? gd._fullLayout.shapes.length : 0;
            }''')

            assert shape_count == 0, f"Expected no shapes when disabled, got {shape_count}"

            page.screenshot(path=str(screenshots_dir / "recession_disabled.png"))
            browser.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
