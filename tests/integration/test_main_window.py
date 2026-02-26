"""Integration tests for MainWindow view layer signal wiring and UI state."""

from unittest.mock import MagicMock

import pytest

from src.models.cleaning_options import CleaningOptions
from src.models.text_document import TextDocument
from src.utils.constants import APP_VERSION
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
    """Construct a MainWindow and clean up the aboutToQuit connection on teardown.

    MainWindow.__init__ connects app.aboutToQuit → window._save_settings. Without
    teardown, every test that uses this fixture adds another live connection to the
    session-scoped QApplication, preventing GC of the window objects for the whole
    test session and triggering save_settings for every window at program exit.
    """
    vm = MainViewModel(mock_file_svc, mock_text_svc)
    win = MainWindow(vm)
    yield win
    try:
        qapp.aboutToQuit.disconnect(win._save_settings)
    except RuntimeError:
        pass  # already disconnected or never connected


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
            assert (
                window.ui.findChild(QCheckBox, name) is None
            ), f"Orphan widget {name!r} should not exist"

    def test_text_label_placeholders_not_present(self, window):
        from PySide6.QtWidgets import QLabel

        for name in ("label", "label_2"):
            assert (
                window.ui.findChild(QLabel, name) is None
            ), f"Placeholder label {name!r} should not exist"


class TestMergeTab:
    def test_merge_tab_has_expected_widgets(self, window):
        from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton

        assert window.ui.findChild(QListWidget, "mergeFileList") is not None
        assert window.ui.findChild(QPushButton, "mergeButton") is not None
        assert window.ui.findChild(QPushButton, "mergeAddCurrentButton") is not None
        assert window.ui.findChild(QPushButton, "mergeAddFilesButton") is not None
        assert window.ui.findChild(QLineEdit, "mergeSeparatorEdit") is not None


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

        monkeypatch.setattr("src.views.main_window.QFile.open", lambda *_: False)
        with pytest.raises(RuntimeError, match="Cannot open UI file"):
            MainWindow(MagicMock())

    def test_raises_if_loader_returns_none(self, monkeypatch, qapp):
        from unittest.mock import MagicMock

        from src.views.main_window import MainWindow

        monkeypatch.setattr("src.views.main_window.QUiLoader.load", lambda *_: None)
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

    def test_clean_options_reflect_checkbox_states(self, window, mock_text_svc, qtbot):
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


class TestKeyboardShortcuts:
    """Verify QShortcut wiring by activating each shortcut's signal directly.

    qtbot.keyClick sends QKeyEvent, which does not trigger QShortcut (those
    listen for QShortcutEvent dispatched by Qt's shortcut system). Emitting
    activated directly tests the actual signal-to-slot connection without
    depending on OS-level key event routing.

    hasFocus() is unreliable in headless tests because it requires the window
    to hold true OS-level focus. Instead: for Ctrl+F and Ctrl+H, the observable
    side effect is the tab switching to Find/Replace — that is what we assert.
    For F3, the cursor position advancing to the second match is the assertion.
    """

    def _shortcut_for(self, window, key_string: str):
        """Return the QShortcut whose key matches key_string, or raise."""
        from PySide6.QtGui import QKeySequence, QShortcut

        target = QKeySequence(key_string)
        shortcuts = window.ui.findChildren(QShortcut)
        for sc in shortcuts:
            if sc.key() == target:
                return sc
        raise AssertionError(f"No QShortcut with key '{key_string}' found on window.ui")

    def test_ctrl_f_switches_to_find_replace_tab(self, window, qtbot):
        """Ctrl+F switches to the Find/Replace tab (tab index matches _find_replace_tab_index)."""
        from PySide6.QtWidgets import QTabWidget

        tab = window.ui.findChild(QTabWidget, "tabWidget")
        assert tab.currentIndex() == 0, "precondition: starts on Clean tab"
        sc = self._shortcut_for(window, "Ctrl+F")
        sc.activated.emit()
        qtbot.wait(10)
        assert tab.currentIndex() == window._find_replace_tab_index

    def test_ctrl_h_switches_to_find_replace_tab(self, window, qtbot):
        """Ctrl+H switches to the Find/Replace tab (tab index matches _find_replace_tab_index)."""
        from PySide6.QtWidgets import QTabWidget

        tab = window.ui.findChild(QTabWidget, "tabWidget")
        assert tab.currentIndex() == 0, "precondition: starts on Clean tab"
        sc = self._shortcut_for(window, "Ctrl+H")
        sc.activated.emit()
        qtbot.wait(10)
        assert tab.currentIndex() == window._find_replace_tab_index

    def test_f3_triggers_find_next(self, window, qtbot):
        """F3 finds the next occurrence of the current search term."""
        window._plain_text_edit.setPlainText("hello world hello")
        window._find_edit.setText("hello")
        # First find via direct call establishes an initial selection
        window._on_find_clicked()
        assert window._plain_text_edit.textCursor().selectedText() == "hello"
        pos_after_first = window._plain_text_edit.textCursor().position()
        # F3 shortcut should advance to next occurrence
        sc = self._shortcut_for(window, "F3")
        sc.activated.emit()
        qtbot.wait(10)
        assert window._plain_text_edit.textCursor().selectedText() == "hello"
        pos_after_second = window._plain_text_edit.textCursor().position()
        assert pos_after_second > pos_after_first


class TestConvertEncodingHandler:
    def test_convert_button_calls_viewmodel(self, window, qtbot):
        """Clicking the Convert button must call viewmodel.convert_to_utf8."""
        from unittest.mock import patch

        window._plain_text_edit.setPlainText("hello")
        with patch.object(window._viewmodel, "convert_to_utf8") as mock_convert:
            window._convert_button.click()
        mock_convert.assert_called_once_with("hello")


class TestStatusBarCursorPosition:
    def test_cursor_label_exists(self, window):
        """A permanent cursor label must be visible in the status bar."""
        assert hasattr(window, "_cursor_label")
        assert window._cursor_label.text() != ""

    def test_cursor_label_shows_line_and_col(self, window, qtbot):
        """Moving the cursor must update the cursor label."""
        window._plain_text_edit.setPlainText("first line\nsecond line")
        # Move cursor to start of second line (position 11)
        cursor = window._plain_text_edit.textCursor()
        cursor.setPosition(11)
        window._plain_text_edit.setTextCursor(cursor)
        qtbot.wait(10)
        label_text = window._cursor_label.text()
        assert "Ln 2" in label_text
        assert "Col 1" in label_text

    def test_cursor_label_shows_char_count(self, window, qtbot):
        """The cursor label must include the document character count."""
        window._plain_text_edit.setPlainText("hello")
        qtbot.wait(10)
        assert "5 chars" in window._cursor_label.text()

    def test_char_count_updates_on_delete_without_cursor_move(self, window, qtbot):
        """Char count must update even when content changes without cursor moving."""
        window._plain_text_edit.setPlainText("hello world")
        cursor = window._plain_text_edit.textCursor()
        cursor.setPosition(5)
        window._plain_text_edit.setTextCursor(cursor)
        # deleteChar removes the character after the cursor — cursor position unchanged
        for _ in range(3):
            cursor = window._plain_text_edit.textCursor()
            cursor.deleteChar()
        qtbot.wait(10)
        assert "8 chars" in window._cursor_label.text()


@pytest.fixture
def _real_save_svc(mock_file_svc):
    """Extends mock_file_svc with real FileService.save_file for disk-write assertions."""
    from src.services.file_service import FileService

    mock_file_svc.save_file.side_effect = FileService().save_file
    return mock_file_svc


@pytest.fixture
def window_real_save(_real_save_svc, mock_text_svc, qapp):
    vm = MainViewModel(_real_save_svc, mock_text_svc)
    return MainWindow(vm)


class TestActionSaveAsHandler:
    def test_chosen_path_is_saved(self, window_real_save, tmp_path, monkeypatch, qtbot):
        """getSaveFileName returns path → file saved to that path."""
        out = tmp_path / "renamed.txt"
        monkeypatch.setattr(
            "src.views.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: (str(out), ""),
        )
        window_real_save._plain_text_edit.setPlainText("save-as content")
        with qtbot.waitSignal(window_real_save._viewmodel.file_saved, timeout=2000):
            window_real_save._on_action_save_as()
        assert out.read_text(encoding="utf-8") == "save-as content"
        assert window_real_save._file_name_edit.text() == str(out)

    def test_cancelled_dialog_is_no_op(self, window, monkeypatch):
        """getSaveFileName returns '' → nothing saved."""
        monkeypatch.setattr(
            "src.views.main_window.QFileDialog.getSaveFileName",
            lambda *a, **kw: ("", ""),
        )
        emitted: list = []
        window._viewmodel.file_saved.connect(emitted.append)
        window._on_action_save_as()
        assert emitted == []


class TestConfigPersistence:
    @pytest.fixture(autouse=True)
    def isolated_settings(self, tmp_path, monkeypatch):
        """Redirect QSettings to a temp ini file — never touches real user prefs.

        Patches src.views.main_window.QSettings so _save_settings and
        _load_settings both hit the temp file. Stores the path on self so test
        bodies can construct a matching QSettings instance to read/clear it.
        """
        from PySide6.QtCore import QSettings

        tmp_ini = str(tmp_path / "test_settings.ini")
        monkeypatch.setattr(
            "src.views.main_window.QSettings",
            lambda *_: QSettings(tmp_ini, QSettings.Format.IniFormat),
        )
        # Expose path so test bodies read/clear the SAME file the window uses
        self._tmp_ini = tmp_ini

    def test_save_settings_writes_geometry(self, window, qtbot):
        """_save_settings must write window/geometry to QSettings."""
        from PySide6.QtCore import QSettings

        # Clear geometry in the same temp file the window will write to
        s = QSettings(self._tmp_ini, QSettings.Format.IniFormat)
        s.remove("window/geometry")
        window.ui.show()
        window._save_settings()
        s2 = QSettings(self._tmp_ini, QSettings.Format.IniFormat)
        assert s2.value("window/geometry") is not None

    def test_load_settings_does_not_raise_when_empty(self, window):
        """_load_settings must not raise when no settings have been saved."""
        from PySide6.QtCore import QSettings

        QSettings(self._tmp_ini, QSettings.Format.IniFormat).clear()
        window._load_settings()  # must not raise

    def test_save_and_restore_geometry(self, window, qtbot):
        """Geometry saved by _save_settings is restored by _load_settings."""
        window.ui.show()
        window.ui.resize(700, 600)
        qtbot.wait(10)
        window._save_settings()
        window.ui.resize(300, 300)
        qtbot.wait(10)
        window._load_settings()
        qtbot.wait(10)
        size = window.ui.size()
        assert size.width() == 700
        assert size.height() == 600


class TestMergeWorkflow:
    """Integration tests for the merge tab — real files, real ViewModel signals."""

    def test_add_current_and_merge(
        self, window, mock_file_svc, mock_text_svc, tmp_path, qtbot
    ):
        """Load a file, add it to the merge list, merge it, verify editor content."""
        from PySide6.QtWidgets import QListWidget

        file1 = tmp_path / "a.txt"
        file1.write_text("aaa")
        file2 = tmp_path / "b.txt"
        file2.write_text("bbb")

        # Configure mocks for two separate load calls
        docs = [
            TextDocument(filepath=str(file1), content="aaa", encoding="utf-8"),
            TextDocument(filepath=str(file2), content="bbb", encoding="utf-8"),
        ]
        mock_file_svc.open_file.side_effect = docs
        mock_text_svc.merge_documents.return_value = "aaa\nbbb"

        # Load first file and add to merge list
        window._viewmodel.load_file(str(file1))
        window._viewmodel.add_current_to_merge()

        # Reload mock for second file
        mock_file_svc.open_file.side_effect = [
            TextDocument(filepath=str(file2), content="bbb", encoding="utf-8"),
        ]
        window._viewmodel.load_file(str(file2))
        window._viewmodel.add_current_to_merge()

        # Reset side_effect for execute_merge (re-opens both files)
        mock_file_svc.open_file.side_effect = [
            TextDocument(filepath=str(file1), content="aaa", encoding="utf-8"),
            TextDocument(filepath=str(file2), content="bbb", encoding="utf-8"),
        ]

        with qtbot.waitSignal(window._viewmodel.document_loaded, timeout=1000):
            window._viewmodel.execute_merge()

        assert window._plain_text_edit.toPlainText() == "aaa\nbbb"

    def test_merge_tab_list_refreshes_on_add(
        self, window, mock_file_svc, tmp_path, qtbot
    ):
        """Adding a file to merge list refreshes the QListWidget display."""
        from PySide6.QtWidgets import QListWidget

        doc = TextDocument(filepath="/tmp/hello.txt", content="hi", encoding="utf-8")
        mock_file_svc.open_file.return_value = doc
        window._viewmodel.load_file("/tmp/hello.txt")

        list_widget = window.ui.findChild(QListWidget, "mergeFileList")
        assert list_widget is not None
        assert list_widget.count() == 0

        with qtbot.waitSignal(window._viewmodel.merge_list_changed, timeout=1000):
            window._viewmodel.add_current_to_merge()

        assert list_widget.count() == 1
        assert list_widget.item(0).text() == "hello.txt"

    def test_merge_empty_list_shows_error(self, window, monkeypatch, qtbot):
        """Clicking Merge with no files emits error_occurred and shows an error dialog.

        Must monkeypatch QMessageBox.critical: the signal is connected to _on_error
        which calls QMessageBox.critical() (a blocking modal). The modal creates a
        nested event loop that blocks waitSignal's slot from ever firing in offscreen
        mode — the dialog is never dismissed so the test hangs without this patch.
        """
        monkeypatch.setattr(
            "src.views.main_window.QMessageBox.critical",
            lambda *a, **kw: None,
        )
        with qtbot.waitSignal(
            window._viewmodel.error_occurred, timeout=1000
        ) as blocker:
            window._viewmodel.execute_merge()
        assert "No files in merge list" in blocker.args[0]


class TestPreferencesIntegration:
    """Integration tests for _apply_preferences() and the preferences dialog action."""

    @pytest.fixture(autouse=True)
    def isolated_settings(self, tmp_path, monkeypatch):
        """Redirect QSettings in main_window (used by _apply_preferences) to tmp ini.

        Also patches preferences_dialog.QSettings so any dialog construction
        in the same test body hits the same file.
        """
        from PySide6.QtCore import QSettings

        tmp_ini = str(tmp_path / "prefs_integration.ini")
        factory = lambda *_: QSettings(tmp_ini, QSettings.Format.IniFormat)
        monkeypatch.setattr("src.views.main_window.QSettings", factory)
        monkeypatch.setattr("src.views.preferences_dialog.QSettings", factory)
        self._tmp_ini = tmp_ini

    def test_font_size_applied_to_editor(self, window):
        """_apply_preferences sets QPlainTextEdit font size from QSettings."""
        from PySide6.QtCore import QSettings

        from src.views.preferences_dialog import KEY_FONT_SIZE

        QSettings(self._tmp_ini, QSettings.Format.IniFormat).setValue(KEY_FONT_SIZE, 20)
        window._apply_preferences()
        assert window._plain_text_edit.font().pointSize() == 20

    def test_word_wrap_enabled(self, window):
        """_apply_preferences enables WidgetWidth wrap when KEY_WORD_WRAP is True."""
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QPlainTextEdit

        from src.views.preferences_dialog import KEY_WORD_WRAP

        QSettings(self._tmp_ini, QSettings.Format.IniFormat).setValue(
            KEY_WORD_WRAP, True
        )
        window._apply_preferences()
        assert (
            window._plain_text_edit.lineWrapMode()
            == QPlainTextEdit.LineWrapMode.WidgetWidth
        )

    def test_word_wrap_disabled_by_default(self, window):
        """_apply_preferences sets NoWrap when KEY_WORD_WRAP is absent (default False)."""
        from PySide6.QtWidgets import QPlainTextEdit

        window._apply_preferences()  # no settings written — default False applies
        assert (
            window._plain_text_edit.lineWrapMode() == QPlainTextEdit.LineWrapMode.NoWrap
        )

    def test_dark_theme_changes_palette(self, window, qapp):
        """_apply_preferences sets a dark Window colour when theme='dark'."""
        from PySide6.QtCore import QSettings

        from src.views.preferences_dialog import KEY_THEME

        QSettings(self._tmp_ini, QSettings.Format.IniFormat).setValue(KEY_THEME, "dark")
        window._apply_preferences()
        # Dark palette: Window role should be a dark grey (R < 100).
        window_colour = qapp.palette().color(qapp.palette().ColorRole.Window)
        assert window_colour.red() < 100

    def test_preferences_persisted_across_sessions(self, mock_file_svc, mock_text_svc):
        """Font size written to settings is applied when a new MainWindow starts."""
        from PySide6.QtCore import QSettings

        from src.viewmodels.main_viewmodel import MainViewModel
        from src.views.main_window import MainWindow
        from src.views.preferences_dialog import KEY_FONT_SIZE

        QSettings(self._tmp_ini, QSettings.Format.IniFormat).setValue(KEY_FONT_SIZE, 22)
        vm = MainViewModel(mock_file_svc, mock_text_svc)
        new_window = MainWindow(vm)
        assert new_window._plain_text_edit.font().pointSize() == 22

    def test_open_preferences_dialog(self, window, monkeypatch):
        """_on_action_preferences constructs and execs a PreferencesDialog."""
        from unittest.mock import MagicMock

        mock_dlg = MagicMock()
        monkeypatch.setattr(
            "src.views.main_window.PreferencesDialog", lambda *_: mock_dlg
        )
        window._on_action_preferences()
        mock_dlg.exec.assert_called_once()
