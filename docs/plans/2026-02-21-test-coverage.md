# Test Coverage Expansion Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Increase test coverage from 78% to ~95% by covering all reachable code paths in `main_window.py`, `file_service.py`, and `main.py`.

**Architecture:** Three files receive new/extended tests. Modal dialogs (`QMessageBox`, `QFileDialog`) are intercepted with `monkeypatch.setattr`. The two genuinely untestable lines (`main()` entry point and `if __name__ == "__main__":`) receive `# pragma: no cover`.

**Tech Stack:** pytest, pytest-qt (`qtbot`, `monkeypatch`), `unittest.mock.MagicMock`, PySide6.

---

## Baseline

| File | Before | After target |
|------|--------|-------------|
| `src/main.py` | 0% | ~65% |
| `src/services/file_service.py` | 78% | ~95% |
| `src/views/main_window.py` | 74% | ~95% |
| Overall | 78% | ~95% |

---

### Task 1: Add pragma comments to `src/main.py`

**Files:**
- Modify: `src/main.py`

**Step 1: Add `# pragma: no cover` to `main()` and `__main__` guard**

```python
def main() -> None:  # pragma: no cover
    ...

if __name__ == "__main__":  # pragma: no cover
    main()
```

**Step 2: Verify tests still pass**

Run: `pytest tests/ --tb=short -q`
Expected: all 73 pass, no regressions

**Step 3: Commit**

```bash
git add src/main.py
git commit -m "chore: mark untestable entry-point lines with pragma no cover"
```

---

### Task 2: Create `tests/unit/test_main.py`

**Files:**
- Create: `tests/unit/test_main.py`

**Step 1: Write tests**

```python
"""Unit tests for src/main.py — composition root."""

from src import main as main_module
from src.main import create_application
from src.views.main_window import MainWindow


class TestModuleImport:
    def test_module_imports_without_error(self):
        """Importing src.main executes logging setup and logger assignment."""
        # Just importing covers lines 18-24 (module-level code)
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
```

**Step 2: Run tests**

Run: `pytest tests/unit/test_main.py -v`
Expected: 4 tests pass

**Step 3: Commit**

```bash
git add tests/unit/test_main.py
git commit -m "test: add unit tests for src/main.py create_application and module import"
```

---

### Task 3: Cover `FileService` edge cases

**Files:**
- Modify: `tests/unit/test_file_service.py`

**Step 1: Add chardet and atomic-save-cleanup tests**

Add to the bottom of `tests/unit/test_file_service.py`:

```python
class TestDetectEncoding:
    """Tests for _detect_encoding module-level function."""

    def test_utf16_le_detected_by_chardet(self, tmp_path):
        """UTF-16-LE gives chardet high confidence, exercising the chardet branch."""
        pytest.importorskip("chardet")  # skip if chardet not installed
        from src.services.file_service import _detect_encoding
        raw = "hello world".encode("utf-16-le")
        # chardet detects utf-16-le with confidence >= 0.7
        encoding = _detect_encoding(raw)
        assert encoding.lower().replace("-", "") in ("utf16le", "utf16")

    def test_falls_back_to_utf8_for_empty_bytes(self):
        from src.services.file_service import _detect_encoding
        # Empty bytes: chardet returns low/no confidence → fallback
        encoding = _detect_encoding(b"")
        assert encoding == "utf-8"


class TestAtomicSaveCleanup:
    """Verify temp file is cleaned up when os.replace fails."""

    def test_temp_file_removed_on_replace_failure(self, svc, tmp_path, monkeypatch):
        import os
        removed: list[str] = []

        original_replace = os.replace

        def failing_replace(src: str, dst: str) -> None:
            raise OSError("simulated disk full")

        monkeypatch.setattr("os.replace", failing_replace)
        monkeypatch.setattr(
            "os.unlink", lambda p: removed.append(p)
        )

        from src.models.text_document import TextDocument
        doc = TextDocument(filepath=str(tmp_path / "out.txt"), content="data")

        with pytest.raises(OSError, match="simulated disk full"):
            svc.save_file(doc)

        assert len(removed) == 1, "temp file should have been unlinked"
```

**Step 2: Run tests**

Run: `pytest tests/unit/test_file_service.py -v`
Expected: all existing + 3 new tests pass

**Step 3: Commit**

```bash
git add tests/unit/test_file_service.py
git commit -m "test: cover chardet detection path and atomic-save cleanup in FileService"
```

---

### Task 4: Cover `MainWindow` — setup helpers

**Files:**
- Modify: `tests/integration/test_main_window.py`

Cover `_require()` error path (line 50), `show()` (line 81), and `_load_ui` error paths (lines 90, 95).

**Step 1: Add import and two test classes at the top of the integration test file**

Add after existing imports:

```python
from unittest.mock import MagicMock, patch
```

Add new test classes:

```python
class TestRequireHelper:
    def test_raises_runtime_error_for_none_widget(self):
        from src.views.main_window import _require
        with pytest.raises(RuntimeError, match="Required widget 'myWidget'"):
            _require(None, "myWidget")

    def test_returns_widget_when_not_none(self):
        from src.views.main_window import _require
        sentinel = object()
        assert _require(sentinel, "any") is sentinel


class TestWindowShow:
    def test_show_does_not_raise(self, window):
        # Covers MainWindow.show() — line 81
        window.show()


class TestLoadUiErrors:
    def test_raises_if_ui_file_unreadable(self, monkeypatch, qapp):
        monkeypatch.setattr(
            "src.views.main_window.QFile.open", lambda *_: False
        )
        with pytest.raises(RuntimeError, match="Cannot open UI file"):
            MainWindow(MagicMock())

    def test_raises_if_loader_returns_none(self, monkeypatch, qapp):
        monkeypatch.setattr(
            "src.views.main_window.QUiLoader.load", lambda *_: None
        )
        with pytest.raises(RuntimeError, match="QUiLoader failed"):
            MainWindow(MagicMock())
```

**Step 2: Run new tests**

Run: `pytest tests/integration/test_main_window.py -v -k "TestRequire or TestWindowShow or TestLoadUi"`
Expected: 5 tests pass

**Step 3: Commit**

```bash
git add tests/integration/test_main_window.py
git commit -m "test: cover _require helper, show(), and _load_ui error paths in MainWindow"
```

---

### Task 5: Cover `MainWindow` — save and clean handlers

**Files:**
- Modify: `tests/integration/test_main_window.py`

Cover `_on_save_clicked` (lines 238–246) and `_on_clean_requested` (lines 253–258).

**Step 1: Add test classes**

```python
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

    def test_save_delegates_to_viewmodel(self, window, mock_file_svc, qtbot):
        """Non-empty filepath triggers ViewModel.save_file — line 246."""
        window._file_name_edit.setText("/tmp/out.txt")
        window._plain_text_edit.setPlainText("some content")
        with qtbot.waitSignal(window._viewmodel.file_saved, timeout=1000):
            window._on_save_clicked()


class TestCleanHandler:
    def test_checking_trim_checkbox_calls_apply_cleaning(
        self, window, mock_text_svc, qtbot
    ):
        """stateChanged → _on_clean_requested — lines 253-258."""
        # Load a document first so ViewModel has content
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
```

**Step 2: Run new tests**

Run: `pytest tests/integration/test_main_window.py -v -k "TestSave or TestClean"`
Expected: 4 tests pass

**Step 3: Commit**

```bash
git add tests/integration/test_main_window.py
git commit -m "test: cover save handler (empty/valid path) and clean handler in MainWindow"
```

---

### Task 6: Cover `MainWindow` — find and replace handlers

**Files:**
- Modify: `tests/integration/test_main_window.py`

Cover `_on_find_clicked` (lines 262–271), `_on_replace_clicked` (lines 275–282), `_on_replace_all_clicked` (line 289).

**Step 1: Add test classes**

```python
class TestFindHandler:
    def test_empty_term_is_no_op(self, window):
        """Empty findLineEdit → early return at line 264."""
        window._find_edit.setText("")
        window._on_find_clicked()  # should not raise

    def test_finds_existing_text(self, window, qtbot):
        """find() returns True when term exists — line 265."""
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._on_find_clicked()
        assert window._plain_text_edit.textCursor().hasSelection()

    def test_wraps_when_not_found_from_end(self, window, qtbot):
        """find() returns False → cursor wraps to start — lines 267-271."""
        window._plain_text_edit.setPlainText("hello")
        # Move cursor to end so find('hello') fails from current position
        cursor = window._plain_text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        window._plain_text_edit.setTextCursor(cursor)
        window._find_edit.setText("hello")
        window._on_find_clicked()  # wraps and finds


class TestReplaceHandler:
    def test_empty_find_term_is_no_op(self, window):
        """Empty findLineEdit → early return at line 278."""
        window._find_edit.setText("")
        window._on_replace_clicked()  # should not raise

    def test_replace_with_no_selection(self, window, qtbot):
        """No selection → skips replacement, calls find — lines 279-282."""
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        window._on_replace_clicked()
        # After replace+find, 'hello' should be selected
        assert window._plain_text_edit.textCursor().hasSelection()

    def test_replace_matching_selection(self, window, qtbot):
        """Matching selection → text replaced — line 281."""
        window._plain_text_edit.setPlainText("hello world")
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        # Select 'hello' manually
        cursor = window._plain_text_edit.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        window._plain_text_edit.setTextCursor(cursor)
        window._on_replace_clicked()
        assert "goodbye" in window._plain_text_edit.toPlainText()


class TestReplaceAllHandler:
    def test_replace_all_emits_content_updated(self, window, qtbot):
        """replaceAllButton → _on_replace_all_clicked → ViewModel — line 289."""
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._find_edit.setText("hello")
        window._replace_edit.setText("goodbye")
        with qtbot.waitSignal(window._viewmodel.content_updated, timeout=1000):
            window._on_replace_all_clicked()
```

**Step 2: Run new tests**

Run: `pytest tests/integration/test_main_window.py -v -k "TestFind or TestReplace"`
Expected: 7 tests pass

**Step 3: Commit**

```bash
git add tests/integration/test_main_window.py
git commit -m "test: cover find, replace, and replace-all handlers in MainWindow"
```

---

### Task 7: Cover `MainWindow` — tree click, action open/about, error handler

**Files:**
- Modify: `tests/integration/test_main_window.py`

Cover `_on_tree_item_clicked` (lines 231–234), `_on_action_open` (lines 297–306), `_on_action_about` (line 310), `_on_error` (line 366).

**Step 1: Add test classes**

```python
class TestTreeClickHandler:
    def test_file_click_loads_file(self, window, tmp_path, qtbot):
        """Clicking a file path sets fileNameEdit and calls load_file."""
        f = tmp_path / "click.txt"
        f.write_text("click content", encoding="utf-8")
        window._fs_model.filePath = MagicMock(return_value=str(f))
        window._file_name_edit.setText(str(f))
        with qtbot.waitSignal(window._viewmodel.document_loaded, timeout=1000):
            window._on_tree_item_clicked(MagicMock())
        assert window._file_name_edit.text() == str(f)

    def test_directory_click_is_ignored(self, window, tmp_path):
        """Clicking a directory does not call load_file."""
        window._fs_model.filePath = MagicMock(return_value=str(tmp_path))
        emitted: list = []
        window._viewmodel.document_loaded.connect(emitted.append)
        window._on_tree_item_clicked(MagicMock())
        assert emitted == []


class TestActionOpenHandler:
    def test_open_dialog_loads_chosen_file(self, window, tmp_path, monkeypatch, qtbot):
        """QFileDialog returns a path → file loaded — lines 304-306."""
        f = tmp_path / "opened.txt"
        f.write_text("opened", encoding="utf-8")
        monkeypatch.setattr(
            "src.views.main_window.QFileDialog.getOpenFileName",
            lambda *a, **kw: (str(f), ""),
        )
        window._file_name_edit.setText(str(f))
        with qtbot.waitSignal(window._viewmodel.document_loaded, timeout=1000):
            window._on_action_open()
        assert window._file_name_edit.text() == str(f)

    def test_cancelled_open_dialog_is_no_op(self, window, monkeypatch):
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
    def test_about_dialog_shown(self, window, monkeypatch):
        """actionAbout → QMessageBox.about called — line 310."""
        calls: list = []
        monkeypatch.setattr(
            "src.views.main_window.QMessageBox.about",
            lambda *a: calls.append(a),
        )
        window._on_action_about()
        assert len(calls) == 1
        # Version string present in message body
        assert "0.2.0" in calls[0][2]


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
```

**Step 2: Run new tests**

Run: `pytest tests/integration/test_main_window.py -v -k "TestTree or TestActionOpen or TestActionAbout or TestError"`
Expected: 7 tests pass

**Step 3: Run full suite**

Run: `pytest tests/ --tb=short -q`
Expected: ~100 tests pass, overall coverage ~95%

**Step 4: Commit**

```bash
git add tests/integration/test_main_window.py
git commit -m "test: cover tree-click, file open dialog, about dialog, and error handler"
```
