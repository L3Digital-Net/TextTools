"""Unit tests for src/main.py — composition root."""

import src.main as main_module
from src.main import create_application
from src.views.main_window import MainWindow


class TestModuleImport:
    def test_module_has_logger(self):
        # Importing src.main executes lines 18-24 (logging setup at module level)
        assert main_module.logger is not None

    def test_logger_name(self):
        assert main_module.logger.name == "src.main"


class TestCreateApplication:
    def test_returns_main_window(self, qapp):
        window = create_application()
        assert isinstance(window, MainWindow)

    def test_window_has_viewmodel(self, qapp):
        window = create_application()
        assert window._viewmodel is not None
