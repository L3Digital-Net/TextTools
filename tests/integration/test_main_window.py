"""Integration tests for MainWindow view layer signal wiring and UI state."""

import pytest
from unittest.mock import MagicMock

from src.models.text_document import TextDocument
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main_window import MainWindow


@pytest.fixture
def mock_file_svc():
    svc = MagicMock()
    svc.open_file.return_value = TextDocument(
        filepath="/tmp/test.txt", content="hello world", encoding="utf-8"
    )
    return svc


@pytest.fixture
def mock_text_svc():
    svc = MagicMock()
    svc.apply_options.return_value = "cleaned"
    return svc


@pytest.fixture
def window(mock_file_svc, mock_text_svc, qapp):
    vm = MainViewModel(mock_file_svc, mock_text_svc)
    return MainWindow(vm)


class TestWindowTitle:
    def test_title_default_with_no_document(self, window):
        assert window.ui.windowTitle() == "TextTools"

    def test_title_shows_filename_after_load(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert "test.txt" in window.ui.windowTitle()

    def test_title_has_no_star_immediately_after_load(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert "*" not in window.ui.windowTitle()

    def test_title_shows_star_after_user_edit(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        # Simulate a user edit by directly modifying the document
        cursor = window._plain_text_edit.textCursor()
        cursor.insertText("X")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()

    def test_title_loses_star_after_file_saved(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        cursor = window._plain_text_edit.textCursor()
        cursor.insertText("X")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()
        # Trigger the file_saved signal directly
        window._viewmodel.file_saved.emit("/tmp/test.txt")
        qtbot.wait(10)
        assert "*" not in window.ui.windowTitle()
