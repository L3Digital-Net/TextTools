"""End-to-end integration tests — real services + real MainWindow.

Uses create_application() (real FileService + real TextProcessingService + real
MainWindow) to verify the full signal chain including widget state.

Complements the other test files:
  test_application.py   — real services, ViewModel only (no View)
  test_main_window.py   — real View, mocked services
  test_live_scenarios.py — real services AND real View (this file)

These tests catch mismatches between actual service output and the View's handling:
e.g. trim_whitespace producing "hello\nworld" must actually appear in the editor.
"""

import pytest

from src.main import create_application


@pytest.fixture()
def app(qapp):
    w = create_application()
    yield w
    w.ui.close()


class TestFileLoadUpdatesView:
    def test_editor_populated_after_load(self, app, tmp_path, qtbot):
        f = tmp_path / "hello.txt"
        f.write_text("hello integration", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        assert app._plain_text_edit.toPlainText() == "hello integration"

    def test_encoding_label_set_after_load(self, app, tmp_path, qtbot):
        # Non-ASCII bytes (é, ñ) are needed — pure ASCII content is detected as
        # "ascii" by chardet (technically correct, since ASCII ⊂ UTF-8).
        f = tmp_path / "enc.txt"
        f.write_text("café résumé naïve", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.encoding_detected, timeout=2000):
            app._viewmodel.load_file(str(f))
        assert app._encoding_label.text().lower() == "utf-8"

    def test_title_shows_filename_after_load(self, app, tmp_path, qtbot):
        f = tmp_path / "title_check.txt"
        f.write_text("data", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        assert "title_check.txt" in app.ui.windowTitle()

    def test_status_bar_shows_filename_after_load(self, app, tmp_path, qtbot):
        f = tmp_path / "status_bar.txt"
        f.write_text("data", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        app._viewmodel.load_file(str(f))
        qtbot.wait(20)
        assert "status_bar.txt" in app.ui.statusBar().currentMessage()


class TestSaveRoundTrip:
    def test_save_writes_editor_content_to_disk(self, app, tmp_path, qtbot):
        f = tmp_path / "out.txt"
        app._file_name_edit.setText(str(f))
        app._plain_text_edit.setPlainText("round trip content")
        with qtbot.waitSignal(app._viewmodel.file_saved, timeout=2000):
            app._on_save_clicked()
        assert f.read_text(encoding="utf-8") == "round trip content"

    def test_title_loses_star_after_save(self, app, tmp_path, qtbot):
        """The modified indicator (*) must clear once file_saved fires."""
        f = tmp_path / "save_star.txt"
        f.write_text("original", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        # Introduce a modification via the cursor API (same path as a real keystroke)
        cursor = app._plain_text_edit.textCursor()
        cursor.insertText("X")
        qtbot.wait(10)
        assert "*" in app.ui.windowTitle()
        with qtbot.waitSignal(app._viewmodel.file_saved, timeout=2000):
            app._on_save_clicked()
        assert "*" not in app.ui.windowTitle()


class TestCleaningWithRealService:
    def test_trim_removes_trailing_spaces_and_blank_lines(
        self, app, tmp_path, qtbot
    ):
        # trim_whitespace strips trailing spaces per line and removes trailing
        # blank lines, but does NOT strip leading spaces.
        f = tmp_path / "trim.txt"
        f.write_text("hello   \nworld   \n\n", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        with qtbot.waitSignal(app._viewmodel.content_updated, timeout=2000) as blocker:
            app._trim_cb.setChecked(True)
        assert blocker.args[0] == "hello\nworld"

    def test_clean_whitespace_collapses_runs(self, app, tmp_path, qtbot):
        # clean_whitespace collapses 2+ consecutive spaces to a single space.
        f = tmp_path / "clean.txt"
        f.write_text("a  b   c", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        with qtbot.waitSignal(app._viewmodel.content_updated, timeout=2000) as blocker:
            app._clean_cb.setChecked(True)
        assert blocker.args[0] == "a b c"

    def test_remove_tabs_strips_leading_indent(self, app, tmp_path, qtbot):
        f = tmp_path / "tabs.txt"
        f.write_text("\tindented\n\t\tdouble", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        with qtbot.waitSignal(app._viewmodel.content_updated, timeout=2000) as blocker:
            app._remove_tabs_cb.setChecked(True)
        assert blocker.args[0] == "indented\ndouble"


class TestFindReplaceWithRealContent:
    def test_find_selects_matching_text(self, app, tmp_path, qtbot):
        f = tmp_path / "find.txt"
        f.write_text("the quick brown fox", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        app._find_edit.setText("brown")
        app._on_find_clicked()
        assert app._plain_text_edit.textCursor().selectedText() == "brown"

    def test_find_wraps_from_end_of_document(self, app, tmp_path, qtbot):
        f = tmp_path / "wrap.txt"
        f.write_text("the quick brown fox", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        # Move cursor past the word so the first find() call misses it
        cursor = app._plain_text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        app._plain_text_edit.setTextCursor(cursor)
        app._find_edit.setText("quick")
        app._on_find_clicked()  # wraps to start, then finds
        assert app._plain_text_edit.textCursor().selectedText() == "quick"

    def test_replace_all_updates_editor_and_emits_signal(
        self, app, tmp_path, qtbot
    ):
        f = tmp_path / "rep.txt"
        f.write_text("cat cat cat", encoding="utf-8")
        app._file_name_edit.setText(str(f))
        with qtbot.waitSignal(app._viewmodel.document_loaded, timeout=2000):
            app._viewmodel.load_file(str(f))
        app._find_edit.setText("cat")
        app._replace_edit.setText("dog")
        with qtbot.waitSignal(app._viewmodel.content_updated, timeout=2000) as blocker:
            app._on_replace_all_clicked()
        assert blocker.args[0] == "dog dog dog"
        assert app._plain_text_edit.toPlainText() == "dog dog dog"
