# Qt Implementation Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 10 identified issues in the TextTools Qt implementation: content sync bugs, dead code, unwired menu actions, undo history loss, orphaned UI widgets, missing UX signals, and app metadata.

**Architecture:** TextTools uses strict MVVM: View (main_window.py) wires signals only; ViewModel (main_viewmodel.py) holds state and emits signals; Services are pure Python. UI layout lives in main_window.ui (Qt Designer XML). Changes to ViewModel signatures require matching updates in View callers.

**Tech Stack:** Python 3.14, PySide6 6.8.0+, pytest + pytest-qt, UV, XML editing for `.ui` files.

---

## Context: Files touched in this plan

| File | Layer | Changes |
|------|-------|---------|
| `src/viewmodels/main_viewmodel.py` | ViewModel | Fix content sync; remove dead signals |
| `src/views/main_window.py` | View | Wire menus; fix undo; title bar; filtering |
| `src/views/ui/main_window.ui` | UI XML | Remove orphans; add shortcuts; Merge tab label |
| `src/utils/constants.py` | Utils | Fix version; add file extensions list |
| `src/main.py` | Entry | Add setApplicationVersion |
| `tests/unit/test_main_viewmodel.py` | Tests | Update for new signatures; remove dead signal tests |

---

### Task 1: Fix ViewModel content sync — pass current editor text to apply_cleaning and replace_all

**Problem:** `apply_cleaning` and `replace_all` use `self._current_document.content` (the last
file-load state). User edits typed directly into the QPlainTextEdit are ignored. Checking a
cleaning checkbox after typing overwrites the edits with cleaning applied to the stale document.

**Files:**
- Modify: `src/viewmodels/main_viewmodel.py`
- Modify: `src/views/main_window.py`
- Modify: `tests/unit/test_main_viewmodel.py`
- Modify: `tests/integration/test_application.py`

**Step 1: Write the failing test (content sync)**

In `tests/unit/test_main_viewmodel.py`, add to `TestApplyCleaning`:

```python
def test_uses_current_text_when_provided(self, vm, mock_file_svc, mock_text_svc):
    """apply_cleaning should clean the passed text, not _current_document.content."""
    vm.load_file("/tmp/test.txt")  # loads "hello world"
    opts = CleaningOptions(trim_whitespace=True)
    vm.apply_cleaning(opts, current_text="  edited text  ")
    # text service should have received the editor text, not "hello world"
    mock_text_svc.apply_options.assert_called_once_with("  edited text  ", opts)
```

Add to `TestReplaceAll`:

```python
def test_replace_all_uses_current_text_when_provided(self, vm, qtbot):
    """replace_all should operate on the passed text, not _current_document.content."""
    vm.load_file("/tmp/test.txt")  # loads "hello world"
    with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
        vm.replace_all("hello", "goodbye", current_text="hello hello")
    assert blocker.args[0] == "goodbye goodbye"
```

**Step 2: Run to confirm FAIL**

```bash
pytest tests/unit/test_main_viewmodel.py::TestApplyCleaning::test_uses_current_text_when_provided tests/unit/test_main_viewmodel.py::TestReplaceAll::test_replace_all_uses_current_text_when_provided -v
```

Expected: `TypeError: apply_cleaning() got an unexpected keyword argument 'current_text'`

**Step 3: Update apply_cleaning signature in main_viewmodel.py**

Current signature (line 102–121):
```python
@Slot(object)
def apply_cleaning(self, options: CleaningOptions) -> None:
    if self._current_document is None:
        self.status_changed.emit("No document loaded")
        return
    cleaned = self._text_service.apply_options(
        self._current_document.content, options
    )
```

New signature — add `current_text: str | None = None`:
```python
@Slot(object)
def apply_cleaning(
    self, options: CleaningOptions, current_text: str | None = None
) -> None:
    if self._current_document is None:
        self.status_changed.emit("No document loaded")
        return
    content = current_text if current_text is not None else self._current_document.content
    cleaned = self._text_service.apply_options(content, options)
```

**Step 4: Update replace_all signature in main_viewmodel.py**

Current signature (line 123–142):
```python
@Slot(str, str)
def replace_all(self, find_term: str, replace_term: str) -> None:
    if self._current_document is None or not find_term:
        return
    content = self._current_document.content
```

New:
```python
@Slot(str, str)
def replace_all(
    self, find_term: str, replace_term: str, current_text: str | None = None
) -> None:
    if self._current_document is None or not find_term:
        return
    content = current_text if current_text is not None else self._current_document.content
```

**Step 5: Update View callers in main_window.py**

In `_on_clean_requested` (currently line 203–210), pass the editor text:
```python
def _on_clean_requested(self) -> None:
    options = CleaningOptions(
        trim_whitespace=self._trim_cb.isChecked(),
        clean_whitespace=self._clean_cb.isChecked(),
        remove_tabs=self._remove_tabs_cb.isChecked(),
    )
    self._viewmodel.apply_cleaning(options, self._plain_text_edit.toPlainText())
```

In `_on_replace_all_clicked` (currently line 236–238):
```python
def _on_replace_all_clicked(self) -> None:
    self._viewmodel.replace_all(
        self._find_edit.text(),
        self._replace_edit.text(),
        self._plain_text_edit.toPlainText(),
    )
```

**Step 6: Run tests to confirm PASS**

```bash
pytest tests/unit/test_main_viewmodel.py tests/integration/test_application.py -v
```

Expected: All pass (existing tests unaffected — `current_text=None` preserves old behaviour).

**Step 7: Commit**

```bash
git add src/viewmodels/main_viewmodel.py src/views/main_window.py tests/unit/test_main_viewmodel.py
git commit -m "fix: pass editor content to apply_cleaning and replace_all"
```

---

### Task 2: Remove dead ViewModel signals and slots

**Problem:** `find_requested`, `replace_requested`, `request_find`, `request_replace` exist in
MainViewModel but are never connected to anything. Find/replace is handled directly by the View
on QPlainTextEdit. These suggest an abandoned design and mislead future readers.

**Files:**
- Modify: `src/viewmodels/main_viewmodel.py`
- Modify: `tests/unit/test_main_viewmodel.py`

**Step 1: Verify no tests cover the dead code**

```bash
grep -n "find_requested\|replace_requested\|request_find\|request_replace" tests/
```

Expected: no matches (these symbols are only in the ViewModel itself).

**Step 2: Remove the dead signals and slots from main_viewmodel.py**

Remove these four lines in the `Signal` declarations section:
```python
find_requested = Signal(str)       # DELETE
replace_requested = Signal(str, str)  # DELETE
```

Remove these two methods entirely (currently lines 144–152):
```python
@Slot(str)
def request_find(self, term: str) -> None:
    """Signal the view to find the next occurrence of term."""
    self.find_requested.emit(term)

@Slot(str, str)
def request_replace(self, find_term: str, replace_term: str) -> None:
    """Signal the view to replace the current selection."""
    self.replace_requested.emit(find_term, replace_term)
```

**Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass (nothing tests these dead symbols).

**Step 4: Commit**

```bash
git add src/viewmodels/main_viewmodel.py
git commit -m "refactor: remove dead find_requested/replace_requested signals and slots"
```

---

### Task 3: Wire menu actions and add keyboard shortcuts

**Problem:** The `.ui` file defines `actionQuit`, `actionSave`, `actionOpen`, `actionSave_as`,
`actionAbout` — none are wired in Python. Pressing Ctrl+Q does nothing; there is no keyboard
path to quit the application cleanly. `actionOpen` should open a file dialog.

**Files:**
- Modify: `src/views/ui/main_window.ui`
- Modify: `src/views/main_window.py`

**Step 1: Add keyboard shortcuts to the .ui file XML**

In `main_window.ui`, find each `<action>` block and add a `<property name="shortcut">` child.
Edit these four action blocks (search for their `name=` attribute):

```xml
<action name="actionQuit">
 <property name="text"><string>Quit</string></property>
 <property name="shortcut"><string>Ctrl+Q</string></property>
</action>
<action name="actionSave">
 <property name="text"><string>Save</string></property>
 <property name="shortcut"><string>Ctrl+S</string></property>
</action>
<action name="actionOpen">
 <property name="text"><string>Open</string></property>
 <property name="shortcut"><string>Ctrl+O</string></property>
</action>
<action name="actionSave_as">
 <property name="text"><string>Save as...</string></property>
 <property name="shortcut"><string>Ctrl+Shift+S</string></property>
</action>
```

`actionAbout` and `actionPreferences` intentionally have no shortcuts.

**Step 2: Add QAction and QFileDialog imports to main_window.py**

At the top of `src/views/main_window.py`, add to the `PySide6.QtGui` import (new import line):
```python
from PySide6.QtGui import QAction
```

Add to the `PySide6.QtWidgets` imports:
```python
QFileDialog,
```

Also add `QApplication` if not already present:
```python
from PySide6.QtWidgets import QApplication, ...
```

**Step 3: Add action widget lookups in _load_ui**

At the end of `_load_ui()`, after all the existing `_require()` calls, add:
```python
self._action_quit = _require(
    self.ui.findChild(QAction, "actionQuit"), "actionQuit"
)
self._action_save = _require(
    self.ui.findChild(QAction, "actionSave"), "actionSave"
)
self._action_open = _require(
    self.ui.findChild(QAction, "actionOpen"), "actionOpen"
)
self._action_save_as = _require(
    self.ui.findChild(QAction, "actionSave_as"), "actionSave_as"
)
self._action_about = _require(
    self.ui.findChild(QAction, "actionAbout"), "actionAbout"
)
```

**Step 4: Wire menu actions in _connect_signals**

Add to `_connect_signals()`:
```python
# Menu actions
self._action_quit.triggered.connect(QApplication.quit)
self._action_save.triggered.connect(self._on_save_clicked)
self._action_open.triggered.connect(self._on_action_open)
self._action_save_as.triggered.connect(
    lambda: self.ui.statusBar().showMessage("Save As — coming soon")
)
self._action_about.triggered.connect(self._on_action_about)
```

**Step 5: Add the two new action handler methods**

Add after `_on_replace_all_clicked`:
```python
def _on_action_open(self) -> None:
    """Open a file dialog and load the selected file."""
    path, _ = QFileDialog.getOpenFileName(
        self.ui,
        "Open File",
        QDir.homePath(),
        "Text Files (*.txt *.md *.csv *.log *.json *.yaml *.yml *.xml *.py *.sh *.conf *.ini *.toml);;All Files (*)",
    )
    if path:
        self._file_name_edit.setText(path)
        self._viewmodel.load_file(path)

def _on_action_about(self) -> None:
    """Show an About dialog."""
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.about(
        self.ui,
        "About TextTools",
        "TextTools v0.2.0\n\nText processing utility: encoding detection, "
        "whitespace cleaning, find/replace, and file management.\n\n"
        "Built with Python 3.14 and PySide6.",
    )
```

**Step 6: Run the test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass. (Menu wiring is tested at the application level; unit tests are unaffected.)

**Step 7: Commit**

```bash
git add src/views/ui/main_window.ui src/views/main_window.py
git commit -m "feat: wire menu actions and add keyboard shortcuts (Ctrl+S/O/Q)"
```

---

### Task 4: Fix undo history loss and add modified-state window title

**Problem 1:** `_on_document_loaded` calls `setPlainText()` which wipes Qt's undo stack. After
cleaning or replace-all, the user cannot undo back to the pre-operation state.

**Problem 2:** No visual indicator when the document has unsaved edits.

**Fix:** Replace `setPlainText` with a `QTextCursor`-based full-document replacement (single
undo operation, preserves history). Use `QTextDocument.isModified()` / `setModified(False)` to
drive a `*` indicator in the window title.

**Files:**
- Modify: `src/views/main_window.py`

**Step 1: No new unit tests needed for undo history** (QPlainTextEdit undo is a Qt internal;
it's not easily testable via pytest-qt). We do add a test for the title bar signal.

Add to `tests/integration/test_application.py` (or create
`tests/integration/test_main_window.py`):

```python
# tests/integration/test_main_window.py
"""Integration tests that exercise MainWindow signal wiring with a real QApplication."""
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
    def test_title_unchanged_with_no_document(self, window):
        assert window.ui.windowTitle() == "TextTools"

    def test_title_shows_filename_after_load(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert "test.txt" in window.ui.windowTitle()

    def test_title_shows_star_after_edit(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        # Simulate user typing
        window._plain_text_edit.document().setPlainText("edited")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()

    def test_title_loses_star_after_save(self, window, qtbot):
        window._viewmodel.load_file("/tmp/test.txt")
        qtbot.wait(10)
        window._plain_text_edit.document().setPlainText("edited")
        qtbot.wait(10)
        assert "*" in window.ui.windowTitle()
        # Emit file_saved signal directly
        window._viewmodel.file_saved.emit("/tmp/test.txt")
        qtbot.wait(10)
        assert "*" not in window.ui.windowTitle()
```

**Step 2: Run tests to confirm FAIL**

```bash
pytest tests/integration/test_main_window.py -v
```

Expected: `FAIL` — title stays "TextTools" (no filename/star logic exists yet).

**Step 3: Implement _set_editor_text, _update_title, and contentsChanged wiring in main_window.py**

In `__init__`, add `self._filepath: str = ""` before `self._load_ui()`.

In `_connect_signals()`, add:
```python
# Title bar: update on every document content change
self._plain_text_edit.document().contentsChanged.connect(self._update_title)
```

Update `_on_document_loaded`:
```python
def _on_document_loaded(self, content: str) -> None:
    self._set_editor_text(content)
    self._plain_text_edit.document().setModified(False)
    self._filepath = self._file_name_edit.text()
    self._update_title()
```

Update `_on_file_saved`:
```python
def _on_file_saved(self, filepath: str) -> None:
    self._filepath = filepath
    self._plain_text_edit.document().setModified(False)
    self.ui.statusBar().showMessage(f"Saved: {filepath}")
    self._update_title()
```

Add the two new helpers after all existing methods:
```python
def _set_editor_text(self, content: str) -> None:
    """Replace editor content as a single undoable operation."""
    cursor = self._plain_text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    cursor.insertText(content)

def _update_title(self) -> None:
    """Reflect current filepath and modified state in the window title."""
    name = os.path.basename(self._filepath) if self._filepath else ""
    modified = self._plain_text_edit.document().isModified()
    suffix = " *" if modified else ""
    self.ui.setWindowTitle(f"TextTools — {name}{suffix}" if name else "TextTools")
```

**Step 4: Run tests to confirm PASS**

```bash
pytest tests/integration/test_main_window.py tests/ -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
git add src/views/main_window.py tests/integration/test_main_window.py
git commit -m "fix: preserve undo history and add modified indicator in window title"
```

---

### Task 5: Remove orphaned placeholder widgets from .ui; add Merge tab placeholder

**Problem:** Three unnamed checkboxes (`checkBox_2`, `checkBox_4`, `checkBox_6`) and two
`"TextLabel"` labels (`label`, `label_2`) render in the UI but are never connected to anything.
The Merge tab shows an empty panel.

**Files:**
- Modify: `src/views/ui/main_window.ui`

**Step 1: Write a test confirming orphan widgets cannot be found**

Add to `tests/integration/test_main_window.py` (reuse the `window` fixture):
```python
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
```

**Step 2: Run to confirm FAIL**

```bash
pytest tests/integration/test_main_window.py::TestOrphanWidgets tests/integration/test_main_window.py::TestMergeTab -v
```

Expected: `FAIL` — orphan widgets exist; coming-soon label doesn't.

**Step 3: Edit main_window.ui to remove orphan widgets**

In the XML, find and delete these complete `<item>` blocks inside `formatOptionsContainerLayout`:
- The item containing `<widget class="QCheckBox" name="checkBox_2">`
- The item containing `<widget class="QCheckBox" name="checkBox_4">`
- The item containing `<widget class="QCheckBox" name="checkBox_6">`

Find and delete the complete `<item>` block containing:
```xml
<widget class="QWidget" name="widget_4" native="true">
```
(This is the widget holding `label` and `label_2`.)

**Step 4: Add "Coming soon" label to mergeTabScrollLayout**

In the XML, find `<layout class="QGridLayout" name="mergeTabScrollLayout"/>` (self-closing
tag) and replace it with:
```xml
<layout class="QGridLayout" name="mergeTabScrollLayout">
 <item row="0" column="0" alignment="Qt::AlignmentFlag::AlignCenter">
  <widget class="QLabel" name="mergeComingSoonLabel">
   <property name="text"><string>Merge — coming soon</string></property>
  </widget>
 </item>
</layout>
```

**Step 5: Run tests to confirm PASS**

```bash
pytest tests/integration/test_main_window.py -v
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add src/views/ui/main_window.ui tests/integration/test_main_window.py
git commit -m "fix: remove orphan placeholder widgets; add Merge tab coming-soon label"
```

---

### Task 6: Add file type filtering + fix app version metadata

**Problem 1:** The `QFileSystemModel` tree shows all files including binaries. For a text
editor, showing only text-adjacent extensions is more useful.

**Problem 2:** `src/utils/constants.py` declares `APP_VERSION = "1.0.0"` (wrong; current
version is 0.2.0). `src/main.py` never calls `setApplicationVersion()`.

**Files:**
- Modify: `src/utils/constants.py`
- Modify: `src/views/main_window.py`
- Modify: `src/main.py`

**Step 1: Fix constants.py**

Replace the current content of `src/utils/constants.py`:
```python
"""Utility constants for TextTools."""

APP_NAME = "TextTools"
APP_VERSION = "0.2.0"

DEFAULT_WINDOW_WIDTH = 894
DEFAULT_WINDOW_HEIGHT = 830

# File extensions shown in the QFileSystemModel tree.
# Covers common text, config, markup, and script formats.
TEXT_FILE_EXTENSIONS = [
    "*.txt", "*.md", "*.rst", "*.csv", "*.log",
    "*.json", "*.yaml", "*.yml", "*.toml", "*.xml", "*.html", "*.htm",
    "*.css", "*.js", "*.ts", "*.py", "*.sh", "*.bash",
    "*.conf", "*.cfg", "*.ini", "*.env",
]
```

**Step 2: Import TEXT_FILE_EXTENSIONS in main_window.py and apply filters**

Add import at the top of `src/views/main_window.py`:
```python
from src.utils.constants import TEXT_FILE_EXTENSIONS
```

Update `_setup_file_tree()`:
```python
def _setup_file_tree(self) -> None:
    """Configure QFileSystemModel rooted at the user's home directory."""
    self._fs_model = QFileSystemModel(self.ui)
    self._fs_model.setRootPath(QDir.homePath())
    self._fs_model.setNameFilters(TEXT_FILE_EXTENSIONS)
    self._fs_model.setNameFilterDisables(False)  # hide non-matches (not just grey them)
    self._file_tree_view.setModel(self._fs_model)
    self._file_tree_view.setRootIndex(self._fs_model.index(QDir.homePath()))
    for col in range(1, self._fs_model.columnCount()):
        self._file_tree_view.hideColumn(col)
```

**Step 3: Add setApplicationVersion in main.py**

Update `main()` in `src/main.py`:
```python
from src.utils.constants import APP_NAME, APP_VERSION

def main() -> None:
    logger.info("Starting TextTools")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    ...
```

**Step 4: Write a test for APP_VERSION consistency**

Add to `tests/unit/test_main_viewmodel.py` or create `tests/unit/test_constants.py`:
```python
# tests/unit/test_constants.py
from src.utils.constants import APP_VERSION, TEXT_FILE_EXTENSIONS


def test_app_version_is_semver():
    parts = APP_VERSION.split(".")
    assert len(parts) == 3, "APP_VERSION must be X.Y.Z"
    assert all(p.isdigit() for p in parts)


def test_text_file_extensions_are_glob_patterns():
    assert all(ext.startswith("*.") for ext in TEXT_FILE_EXTENSIONS)
    assert len(TEXT_FILE_EXTENSIONS) >= 10  # reasonable minimum
```

**Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (60 existing + new tests).

**Step 6: Commit**

```bash
git add src/utils/constants.py src/views/main_window.py src/main.py tests/unit/test_constants.py
git commit -m "fix: add file type filtering, correct APP_VERSION to 0.2.0, setApplicationVersion"
```

---

## Final verification

```bash
# Full test suite
pytest tests/ -v

# Type checking
mypy src/

# Formatting
black src/ tests/
isort src/ tests/
```

All should pass cleanly.
