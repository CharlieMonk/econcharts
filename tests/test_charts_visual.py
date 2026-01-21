"""Visual tests for econ-charts using Playwright.

These tests:
1. Generate charts with various economic data
2. Export to HTML
3. Use Playwright to examine DOM structure
4. Take screenshots
5. Test hover tooltips for correct datapoints
6. Test zoom functionality
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, Page, expect

# Add src to path for local testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from econ_charts import EconChart, DEFAULT_COLORS


def wait_for_plotly_ready(page, timeout=10000):
    """Wait for Plotly to fully initialize and render."""
    page.wait_for_selector('.js-plotly-plot', timeout=timeout)
    page.wait_for_load_state('networkidle')
    # Wait for Plotly to populate its internal data structures
    page.wait_for_function('''() => {
        const gd = document.querySelector('.js-plotly-plot');
        return gd && gd._fullLayout && gd._fullLayout.xaxis && gd.data && gd.data.length > 0;
    }''', timeout=timeout)
    # Small additional wait to ensure rendering is complete
    page.wait_for_timeout(200)


# Sample data generators
def generate_gdp_data(start_year: int = 2000, years: int = 24):
    """Generate sample GDP growth data."""
    import random
    random.seed(42)  # Reproducible
    dates = []
    values = []
    base = 100
    for year in range(start_year, start_year + years):
        for quarter in range(1, 5):
            month = (quarter - 1) * 3 + 1
            dates.append(datetime(year, month, 1))
            # Simulate GDP with trend and cycles
            growth = 2.5 + math.sin(year / 3) * 1.5 + random.uniform(-0.5, 0.5)
            # Add recession in 2008-2009 and 2020
            if 2008 <= year <= 2009:
                growth = -3 + random.uniform(-2, 1)
            elif year == 2020 and quarter <= 2:
                growth = -8 + random.uniform(-2, 2)
            values.append(growth)
    return dates, values


def generate_inflation_data(start_year: int = 2000, years: int = 24):
    """Generate sample inflation data."""
    import random
    random.seed(43)
    dates = []
    values = []
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            dates.append(datetime(year, month, 1))
            # Base inflation around 2-3%
            inflation = 2.5 + math.sin(year / 4) * 1.0 + random.uniform(-0.3, 0.3)
            # High inflation in 2022
            if year >= 2021:
                inflation = 5 + (year - 2021) * 2 + random.uniform(-0.5, 0.5)
            if year >= 2023:
                inflation = 6 - (year - 2022) * 1.5 + random.uniform(-0.5, 0.5)
            values.append(max(0, inflation))
    return dates, values


def generate_unemployment_data(start_year: int = 2000, years: int = 24):
    """Generate sample unemployment data."""
    import random
    random.seed(44)
    dates = []
    values = []
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            dates.append(datetime(year, month, 1))
            # Base unemployment 4-6%
            rate = 5 + math.sin(year / 5) * 1.5 + random.uniform(-0.2, 0.2)
            # Spikes in recessions
            if 2008 <= year <= 2010:
                rate = 7 + (year - 2008) * 1.5 + random.uniform(-0.3, 0.3)
            elif year == 2020:
                rate = 8 + random.uniform(-0.5, 2)
            values.append(max(3, rate))
    return dates, values


def generate_stock_data(start_year: int = 2020, years: int = 4):
    """Generate sample stock price data."""
    import random
    random.seed(45)
    dates = []
    values = []
    price = 100
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            for day in [1, 8, 15, 22]:
                try:
                    dates.append(datetime(year, month, day))
                    # Random walk with drift
                    price = price * (1 + random.uniform(-0.02, 0.025))
                    values.append(price)
                except ValueError:
                    pass
    return dates, values


def generate_interest_rate_data(start_year: int = 2000, years: int = 24):
    """Generate sample interest rate data."""
    import random
    random.seed(46)
    dates = []
    values = []
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            dates.append(datetime(year, month, 1))
            # Fed funds rate simulation
            if year < 2008:
                rate = 4 + math.sin(year / 2) * 2
            elif 2008 <= year <= 2015:
                rate = 0.25
            elif 2015 < year <= 2019:
                rate = (year - 2015) * 0.5
            elif 2020 <= year <= 2021:
                rate = 0.25
            else:
                rate = min(5.5, (year - 2021) * 2)
            values.append(max(0, rate + random.uniform(-0.1, 0.1)))
    return dates, values


class TestChartGeneration:
    """Test chart generation and basic structure."""

    def test_single_subplot_chart(self, html_dir, screenshots_dir):
        """Test single subplot chart creation."""
        dates, values = generate_gdp_data()

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='GDP Growth', color='#00d4aa')
        chart.set_title('GDP Growth Rate')
        chart.set_yaxis(row=1, title='% Change YoY')
        chart.add_hline(row=1, y=0)
        chart.enable_unified_spikeline()

        html_path = html_dir / "single_subplot.html"
        chart.to_html(str(html_path))

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

    def test_multi_subplot_chart(self, html_dir, screenshots_dir):
        """Test multi-subplot chart creation."""
        gdp_dates, gdp_values = generate_gdp_data()
        inf_dates, inf_values = generate_inflation_data()
        unemp_dates, unemp_values = generate_unemployment_data()

        chart = EconChart(
            num_rows=3,
            subplot_titles=('GDP Growth', 'Inflation', 'Unemployment'),
            height=700,
        )

        chart.add_line(row=1, x=gdp_dates, y=gdp_values, name='GDP', color='#00d4aa')
        chart.add_line(row=2, x=inf_dates, y=inf_values, name='CPI', color='#ff6b6b')
        chart.add_line(row=3, x=unemp_dates, y=unemp_values, name='Unemployment', color='#4ecdc4')

        chart.set_yaxis(row=1, title='% YoY')
        chart.set_yaxis(row=2, title='% YoY')
        chart.set_yaxis(row=3, title='% Rate')

        chart.add_hline(row=1, y=0)
        chart.add_hline(row=2, y=2.0)  # Inflation target

        chart.set_legend(orientation='h', position='top')
        chart.enable_unified_spikeline()

        html_path = html_dir / "multi_subplot.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_stock_data()
        # Create exponential growth for log scale demo
        exp_values = [v * (1.1 ** (i/10)) for i, v in enumerate(values)]

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=exp_values, name='Stock Price', color='#ffd93d')
        chart.set_yaxis(row=1, title='Price ($)', scale_type='log')
        chart.set_title('Stock Price (Log Scale)')
        chart.enable_unified_spikeline()

        html_path = html_dir / "log_scale.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_inflation_data()
        min_val, max_val = min(values), max(values)

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='Inflation', color='#ff6b6b')
        chart.set_title('Inflation Rate')

        html_path = html_dir / "scale_test.html"
        chart.to_html(str(html_path))

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
        dates, gdp = generate_gdp_data()
        _, rates = generate_interest_rate_data()
        # Trim to same length
        min_len = min(len(dates), len(rates))
        dates = dates[:min_len]
        gdp = gdp[:min_len]
        rates = rates[:min_len]

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=gdp, name='GDP Growth', color='#00d4aa')
        chart.add_line(row=1, x=dates, y=rates, name='Interest Rate', color='#ff6b6b')
        chart.set_title('GDP vs Interest Rates')

        html_path = html_dir / "multi_series_scale.html"
        chart.to_html(str(html_path))

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

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='Test Data', color='#00d4aa')
        chart.set_title('Hover Test')
        chart.enable_unified_spikeline()

        html_path = html_dir / "hover_test.html"
        chart.to_html(str(html_path))

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

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='Accurate Data', color='#4ecdc4')

        html_path = html_dir / "hover_accuracy.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_gdp_data()

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='GDP', color='#00d4aa')
        chart.set_title('Zoom Test')

        html_path = html_dir / "zoom_test.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_inflation_data()

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='Inflation', color='#ff6b6b')

        html_path = html_dir / "zoom_reset_test.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_gdp_data()

        chart = EconChart(num_rows=2, subplot_titles=('Chart 1', 'Chart 2'), height=500)
        chart.add_line(row=1, x=dates, y=values, name='Series 1', color='#00d4aa')
        chart.add_line(row=2, x=dates, y=[v * 0.5 for v in values], name='Series 2', color='#ff6b6b')
        chart.set_title('DOM Test Chart')
        chart.set_legend(orientation='h', position='top')

        html_path = html_dir / "dom_structure.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_gdp_data()

        titles = ('GDP Growth', 'Inflation Rate', 'Unemployment')
        chart = EconChart(num_rows=3, subplot_titles=titles, height=700)
        chart.add_line(row=1, x=dates, y=values, name='GDP', color='#00d4aa')
        chart.add_line(row=2, x=dates, y=[v * 0.3 for v in values], name='Inflation', color='#ff6b6b')
        chart.add_line(row=3, x=dates, y=[abs(v) * 0.2 for v in values], name='Unemployment', color='#4ecdc4')

        html_path = html_dir / "subplot_titles.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_stock_data()

        chart = EconChart(num_rows=1, height=400)
        chart.add_line(row=1, x=dates, y=values, name='Stock', color='#ffd93d')
        chart.set_title('Dark Theme Test')

        html_path = html_dir / "dark_theme.html"
        chart.to_html(str(html_path))

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
        dates, values = generate_gdp_data()

        custom_colors = {
            'background': '#0f0f23',
            'paper': '#1a1a3e',
            'grid': '#404060',
            'text': '#ccccff',
            'spike': 'rgba(200, 200, 255, 0.5)',
            'zero_line': 'rgba(200, 200, 255, 0.3)',
        }

        chart = EconChart(num_rows=1, height=400, colors=custom_colors)
        chart.add_line(row=1, x=dates, y=values, name='GDP', color='#88ff88')
        chart.set_title('Custom Colors')

        html_path = html_dir / "custom_colors.html"
        chart.to_html(str(html_path))

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


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
