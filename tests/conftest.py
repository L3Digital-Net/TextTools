"""Pytest configuration and shared fixtures.

This file contains fixtures that are available to all test files.
"""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests.

    This fixture is session-scoped, meaning one QApplication
    is created for all tests and reused.

    Yields:
        QApplication instance.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def example_model_data():
    """Provide example model data for tests.

    Returns:
        Dictionary with sample model data.
    """
    return {
        "id": 1,
        "name": "Test Item",
        "value": 100.0,
        "description": "Test description"
    }
