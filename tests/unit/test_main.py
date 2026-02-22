"""Unit tests for src/main.py — composition root."""

import pytest

import src.main as main_module
from src.main import create_application
from src.views.main_window import MainWindow


@pytest.fixture()
def window(qapp):
    w = create_application()
    yield w
    w.ui.close()


class TestModuleImport:
    def test_module_has_logger(self):
        assert main_module.logger is not None


class TestCreateApplication:
    def test_returns_main_window(self, window):
        assert isinstance(window, MainWindow)

    def test_window_has_viewmodel(self, window):
        assert window._viewmodel is not None
