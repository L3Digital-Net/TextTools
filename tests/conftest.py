"""Pytest configuration and shared fixtures for TextTools test suite."""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication instance for the entire test session.

    Session-scoped because Qt allows only one QApplication per process.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
