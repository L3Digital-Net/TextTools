"""Integration tests for MainWindow view layer signal wiring and UI state."""

from unittest.mock import MagicMock

import pytest

from src.utils.constants import APP_VERSION

from src.models.cleaning_options import CleaningOptions
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
        window._file_name_edit.setText("/tmp/test.txt")
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert "test.txt" in window.ui.windowTitle()

    def test_title_has_no_star_immediately_after_load(self, window, qtbot):
        window._file_name_edit.setText("/tmp/test.txt")
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert "*" not in window.ui.windowTitle()

    def test_title_shows_star_after_user_edit(self, window, qtbot):
        window._file_name_edit.setText("/tmp/test.txt")
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        # Simulate a user edit by directly modifying the document
        cursor = window._plain_text_edit.textCursor()
        cursor.insertText("X")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()

    def test_title_loses_star_after_file_saved(self, window, qtbot):
        window._file_name_edit.setText("/tmp/test.txt")
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

    def test_title_keeps_star_after_cleaning(self, window, mock_text_svc, qtbot):
        """Cleaning (content_updated) must not clear the modified flag."""
        window._file_name_edit.setText("/tmp/test.txt")
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        # Simulate a user edit
        cursor = window._plain_text_edit.textCursor()
        cursor.insertText("X")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()
        # Apply cleaning — this must NOT clear the star
        opts = CleaningOptions(trim_whitespace=True)
        window._viewmodel.apply_cleaning(opts, window._plain_text_edit.toPlainText())
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle(), "Star should persist after cleaning"


class TestOrphanWidgets:
    def test_unnamed_checkboxes_not_present(self, window):
        from PySide6.QtWidgets import QCheckBox
        for name in ("checkBox_2", "checkBox_4", "checkBox_6"):
            assert window.ui.findChild(QCheckBox, name) is None, \
                f"Orphan widget {name!r} should not exist"

    def test_text_label_placeholders_not_present(self, window):
        from PySide6.QtWidgets import QLabel
        for name in ("label", "label_2"):
            assert window.ui.findChild(QLabel, name) is None, \
                f"Placeholder label {name!r} should not exist"


class TestMergeTab:
    def test_merge_tab_has_coming_soon_label(self, window):
        from PySide6.QtWidgets import QLabel
        label = window.ui.findChild(QLabel, "mergeComingSoonLabel")
        assert label is not None
        assert "coming soon" in label.text().lower()


class TestRequireHelper:
    def test_raises_for_none_widget(self):
        from src.views.main_window import _require

        with pytest.raises(RuntimeError, match="Required widget 'myWidget'"):
            _require(None, "myWidget")

    def test_returns_widget_when_present(self):
        from src.views.main_window import _require

        sentinel = object()
        assert _require(sentinel, "any") is sentinel


class TestWindowShow:
    def test_show_does_not_raise(self, window):
        # Covers MainWindow.show() — line 81
        window.show()


class TestLoadUiErrors:
    def test_raises_if_ui_file_unreadable(self, monkeypatch, qapp):
        from unittest.mock import MagicMock
        from src.views.main_window import MainWindow

        monkeypatch.setattr(
            "src.views.main_window.QFile.open", lambda *_: False
        )
        with pytest.raises(RuntimeError, match="Cannot open UI file"):
            MainWindow(MagicMock())

    def test_raises_if_loader_returns_none(self, monkeypatch, qapp):
        from unittest.mock import MagicMock
        from src.views.main_window import MainWindow

        monkeypatch.setattr(
            "src.views.main_window.QUiLoader.load", lambda *_: None
        )
        with pytest.raises(RuntimeError, match="QUiLoader failed"):
            MainWindow(MagicMock())


class TestSaveHandler:
    def test_warning_shown_when_filepath_empty(self, window, monkeypatch):
        """Empty fileNameEdit triggers QMessageBox.warning — lines 240-244."""
        warnings: list = []
        monkeypatch.setattr(
            "src.views.main_window.QMessageBox.warning",
            lambda *a: warnings.append(a),
        )
        window._file_name_edit.setText("")
        window._on_save_clicked()
        assert len(warnings) == 1

    def test_save_delegates_to_viewmodel(self, window, qtbot):
        """Non-empty filepath triggers ViewModel.save_file — line 246."""
        window._file_name_edit.setText("/tmp/out.txt")
        window._plain_text_edit.setPlainText("some content")
        with qtbot.waitSignal(window._viewmodel.file_saved, timeout=1000):
            window._on_save_clicked()


class TestCleanHandler:
    def test_checking_trim_checkbox_triggers_cleaning(
        self, window, mock_text_svc, qtbot
    ):
        """stateChanged → _on_clean_requested — lines 253-258."""
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        with qtbot.waitSignal(window._viewmodel.content_updated, timeout=1000):
            window._trim_cb.setChecked(True)

    def test_clean_options_reflect_checkbox_states(
        self, window, mock_text_svc, qtbot
    ):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._clean_cb.setChecked(False)
        window._remove_tabs_cb.setChecked(True)
        window._on_clean_requested()
        call_args = mock_text_svc.apply_options.call_args
        opts = call_args[0][1]
        assert opts.remove_tabs is True
        assert opts.clean_whitespace is False


class TestFindHandler:
    def test_empty_term_is_no_op(self, window):
        """Empty findLineEdit → early return at line 264."""
        window._find_edit.setText("")
        window._on_find_clicked()  # should not raise or select anything
        assert not window._plain_text_edit.textCursor().hasSelection()

    def test_finds_existing_text(self, window, qtbot):
        """find() succeeds — line 265 (found=True branch)."""
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._on_find_clicked()
        assert window._plain_text_edit.textCursor().hasSelection()

    def test_wraps_when_not_found_from_end(self, window):
        """find() returns False → cursor wraps to start — lines 267-271."""
        window._plain_text_edit.setPlainText("hello")
        # Move cursor to end so the first find('hello') misses
        cursor = window._plain_text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        window._plain_text_edit.setTextCursor(cursor)
        window._find_edit.setText("hello")
        window._on_find_clicked()  # wraps and finds from start
        assert window._plain_text_edit.textCursor().hasSelection()


class TestReplaceHandler:
    def test_empty_find_term_is_no_op(self, window):
        """Empty findLineEdit → early return at line 278."""
        window._find_edit.setText("")
        window._on_replace_clicked()  # should not raise

    def test_replace_with_no_selection_calls_find(self, window):
        """No selection → skips replacement, falls through to find — lines 279-282."""
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        window._on_replace_clicked()
        # find() advances cursor to 'hello' after replace falls through
        assert window._plain_text_edit.textCursor().hasSelection()

    def test_replace_matching_selection_inserts_replacement(self, window):
        """Matching selection → text replaced — line 281."""
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        # Manually select 'hello'
        cursor = window._plain_text_edit.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        window._plain_text_edit.setTextCursor(cursor)
        window._on_replace_clicked()
        assert "goodbye" in window._plain_text_edit.toPlainText()


class TestReplaceAllHandler:
    def test_replace_all_emits_content_updated(self, window, qtbot):
        """_on_replace_all_clicked delegates to ViewModel — line 289."""
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        with qtbot.waitSignal(window._viewmodel.content_updated, timeout=1000):
            window._on_replace_all_clicked()


class TestTreeClickHandler:
    def test_file_click_loads_file(self, window, tmp_path, qtbot):
        """Clicking a file path sets fileNameEdit and calls load_file — lines 233-234."""
        f = tmp_path / "click.txt"
        f.write_text("click content", encoding="utf-8")
        window._fs_model.filePath = MagicMock(return_value=str(f))
        with qtbot.waitSignal(window._viewmodel.document_loaded, timeout=1000):
            window._on_tree_item_clicked(MagicMock())
        assert window._file_name_edit.text() == str(f)  # confirms line 233 ran

    def test_directory_click_is_ignored(self, window, tmp_path):
        """Clicking a directory does not call load_file — line 232 branch."""
        window._fs_model.filePath = MagicMock(return_value=str(tmp_path))
        emitted: list = []
        window._viewmodel.document_loaded.connect(emitted.append)
        window._on_tree_item_clicked(MagicMock())
        assert emitted == []


class TestActionOpenHandler:
    def test_chosen_file_is_loaded(self, window, tmp_path, monkeypatch, qtbot):
        """QFileDialog returns path → file loaded — lines 304-306."""
        f = tmp_path / "opened.txt"
        f.write_text("opened", encoding="utf-8")
        monkeypatch.setattr(
            "src.views.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: (str(f), ""),
        )
        with qtbot.waitSignal(window._viewmodel.document_loaded, timeout=1000):
            window._on_action_open()
        assert window._file_name_edit.text() == str(f)  # confirms line 305 ran

    def test_cancelled_dialog_is_no_op(self, window, monkeypatch):
        """QFileDialog returns '' → nothing happens — lines 303-304 branch."""
        monkeypatch.setattr(
            "src.views.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: ("", ""),
        )
        emitted: list = []
        window._viewmodel.document_loaded.connect(emitted.append)
        window._on_action_open()
        assert emitted == []


class TestActionAboutHandler:
    def test_about_dialog_is_shown(self, window, monkeypatch):
        """actionAbout → QMessageBox.about called — line 310."""
        calls: list = []
        monkeypatch.setattr(
            "src.views.main_window.QMessageBox.about",
            lambda *a: calls.append(a),
        )
        window._on_action_about()
        assert len(calls) == 1
        assert APP_VERSION in calls[0][2]


class TestErrorHandler:
    def test_error_signal_shows_critical_dialog(self, window, monkeypatch, qtbot):
        """error_occurred signal → QMessageBox.critical — line 366."""
        calls: list = []
        monkeypatch.setattr(
            "src.views.main_window.QMessageBox.critical",
            lambda *a, **kw: calls.append(a),
        )
        window._viewmodel.error_occurred.emit("something went wrong")
        qtbot.wait(10)
        assert len(calls) == 1
        assert "something went wrong" in calls[0][2]


class TestDefaultTab:
    def test_opens_on_clean_tab(self, window):
        """Tab widget must default to index 0 (Clean tab), not 2 (Find/Replace)."""
        from PySide6.QtWidgets import QTabWidget
        tab = window.ui.findChild(QTabWidget, "tabWidget")
        assert tab is not None
        assert tab.currentIndex() == 0
