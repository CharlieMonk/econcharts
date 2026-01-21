"""Pytest configuration and fixtures for econ-charts tests."""

import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_output_dir():
    """Create and return test output directory."""
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture(scope="session")
def screenshots_dir(test_output_dir):
    """Create and return screenshots directory."""
    screenshots = test_output_dir / "screenshots"
    screenshots.mkdir(exist_ok=True)
    return screenshots


@pytest.fixture(scope="session")
def html_dir(test_output_dir):
    """Create and return HTML output directory."""
    html_out = test_output_dir / "html"
    html_out.mkdir(exist_ok=True)
    return html_out
