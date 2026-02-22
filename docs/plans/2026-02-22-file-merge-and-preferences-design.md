# TextTools — File Merge & Preferences Design

**Date**: 2026-02-22
**Scope**: Two new features — File Merge tab and Preferences dialog
**Goal**: Implement the two remaining "coming soon" features in TextTools v0.4.0

---

## 1. File Merge Feature

### 1.1 Summary

Replace the "Merge — coming soon" label in the Merge tab with a full multi-file merge UI.
Users build a list of files, configure a separator, and click Merge to load the result into the
right-panel editor for review/save via the normal Save/Save As flow.

### 1.2 Merge Tab UI Layout

Replace the `mergeComingSoonLabel` inside `mergeScrollContents` with this layout:

```
┌──────────────────────────────────────────────┐
│  Files to Merge:                             │
│  ┌────────────────────────────────────┐ [↑] │
│  │ file1.txt                          │ [↓] │
│  │ notes.txt                          │     │
│  │ log.txt                            │ [-] │
│  └────────────────────────────────────┘     │
│                                              │
│  [Add Current File]  [Add Files...]          │
│                                              │
│  Separator between files:                    │
│  [__\n__________________________]            │
│                                              │
│           [  Merge Files  ]                  │
└──────────────────────────────────────────────┘
```

**Widget objectNames** (to be added to DESIGN.md Appendix A):

| Widget | Type | objectName |
|--------|------|------------|
| File list | QListWidget | `mergeFileList` |
| Move up | QPushButton | `mergeMoveUpButton` |
| Move down | QPushButton | `mergeMoveDownButton` |
| Remove selected | QPushButton | `mergeRemoveButton` |
| Add current file | QPushButton | `mergeAddCurrentButton` |
| Add via dialog | QPushButton | `mergeAddFilesButton` |
| Separator input | QLineEdit | `mergeSeparatorEdit` |
| Merge action | QPushButton | `mergeButton` |

**`mergeFileList` config**: `DragDropMode.InternalMove`, `DefaultDropAction.MoveAction`.
Rows display filename only; full path stored in `Qt.ItemDataRole.UserRole`.

### 1.3 MVVM Architecture

#### Service layer

Add one method to `TextProcessingService` (no new files):

```python
def merge_documents(self, docs: list[TextDocument], separator: str) -> str:
    return separator.join(doc.content for doc in docs)
```

#### ViewModel (`MainViewModel`)

New internal state:
- `_merge_filepaths: list[str]`  (ordered list of absolute paths)
- `_merge_separator: str = "\n"`  (default: single blank line between files)

New signal:
- `merge_list_changed = Signal(list)`  — carries `list[str]` of display names (filename only)

New slots:

| Slot | Signature | Behaviour |
|------|-----------|-----------|
| `add_current_to_merge` | `()` | Appends `_current_document.filepath`; error if no file loaded |
| `add_files_to_merge` | `(filepaths: list[str])` | Batch append; silently drops duplicates |
| `remove_from_merge` | `(index: int)` | Removes by index |
| `move_merge_item` | `(from_idx: int, to_idx: int)` | Reorders list |
| `set_merge_separator` | `(sep: str)` | Updates separator string |
| `execute_merge` | `()` | Reads all files via FileService, merges via TextProcessingService, emits `document_loaded` |

#### View (`MainWindow`)

- `_setup_merge_tab()` — wire all merge widgets to ViewModel slots
- `_on_merge_list_changed(names: list[str])` — refresh `mergeFileList`
- `_on_merge_add_files_clicked()` — open `QFileDialog.getOpenFileNames()` → `viewmodel.add_files_to_merge`
- Connect `mergeFileList.model().rowsMoved` → `viewmodel.move_merge_item` for drag-drop sync

### 1.4 Data Flow

**Happy path:**
```
1. User clicks file in tree → viewmodel.load_file() → document_loaded
2. User switches to Merge tab
3. User clicks "Add Current File" → viewmodel.add_current_to_merge()
   → merge_list_changed → view refreshes mergeFileList
4. Repeat steps 1–3 for each file
5. User edits separator field → viewmodel.set_merge_separator(text)
6. User clicks "Merge Files" → viewmodel.execute_merge()
   → FileService.open_file() for each path
   → TextProcessingService.merge_documents(docs, separator)
   → document_loaded → right-panel editor populated
   → status_changed: "Merged N files"
```

**Error handling:**

| Scenario | Response |
|----------|----------|
| "Add Current" with no file loaded | `error_occurred.emit("No file loaded — open a file first")` |
| Merge list empty on "Merge Files" | `error_occurred.emit("No files in merge list")` |
| File deleted between add and merge | `error_occurred.emit(f"Cannot read {name}: {e}")` — merge aborted |
| Duplicate file added | Silently ignored |

### 1.5 Tests

**Unit — additions to existing test files:**

`tests/unit/test_text_processing_service.py`:
- `test_merge_two_docs`
- `test_merge_custom_separator`
- `test_merge_single_doc`
- `test_merge_empty_list`

`tests/unit/test_main_viewmodel.py`:
- `test_add_current_to_merge`
- `test_add_current_no_file_emits_error`
- `test_add_files_to_merge`
- `test_remove_from_merge`
- `test_move_merge_item`
- `test_execute_merge_emits_document_loaded`
- `test_execute_merge_empty_list_emits_error`
- `test_duplicate_ignored`

**Integration — new class in `tests/integration/test_main_window.py`:**

```python
class TestMergeWorkflow:
    def test_add_current_and_merge(self, window, tmp_path, qtbot): ...
    def test_merge_tab_list_refreshes_on_add(self, ...): ...
    def test_merge_empty_list_shows_error(self, ...): ...
```

---

## 2. Preferences Dialog

### 2.1 Summary

Replace the `Edit → Preferences` "coming soon" stub with a modal `QDialog` that reads/writes
QSettings. Changes are applied live via a `preferences_changed` signal connected to
`MainWindow._apply_preferences()`.

### 2.2 UI Layout

New file: `src/views/ui/preferences_dialog.ui`

```
┌─────────────────────────────────────────┐
│  Preferences                            │
├─────────────────────────────────────────┤
│  Editor                                 │
│  ─────────────────────────────────────  │
│  Font:      [Monospace    ▼] [12 ▲▼]   │
│  Word wrap: [ ] Wrap long lines         │
│  Line numbers: [x] Show line numbers    │
│                                         │
│  Appearance                             │
│  ─────────────────────────────────────  │
│  Theme:     ( ) Light  (•) Dark         │
│                                         │
│  Files                                  │
│  ─────────────────────────────────────  │
│  Default directory: [/home/user  ] [..] │
│                                         │
│  ────────────────────────────────────── │
│             [Cancel]  [Apply]  [OK]     │
└─────────────────────────────────────────┘
```

**Widget objectNames:**

| Widget | Type | objectName |
|--------|------|------------|
| Font family | QFontComboBox | `fontFamilyComboBox` |
| Font size | QSpinBox | `fontSizeSpinBox` |
| Word wrap | QCheckBox | `wordWrapCheckBox` |
| Line numbers | QCheckBox | `lineNumbersCheckBox` |
| Theme light | QRadioButton | `themeLightRadio` |
| Theme dark | QRadioButton | `themeDarkRadio` |
| Default dir | QLineEdit | `defaultDirectoryEdit` |
| Browse | QPushButton | `browseDirectoryButton` |
| OK | QPushButton | `okButton` |
| Apply | QPushButton | `applyButton` |
| Cancel | QPushButton | `cancelButton` |

### 2.3 Architecture

**`PreferencesDialog`** — new file `src/views/preferences_dialog.py`:
- Loads `preferences_dialog.ui` via `QUiLoader`
- `__init__`: reads QSettings, populates widgets
- `_on_apply_clicked()`: writes QSettings, emits `preferences_changed`
- `_on_ok_clicked()`: apply then `accept()`
- `preferences_changed = Signal()` — MainWindow connects to `_apply_preferences()`

**Deliberate MVVM exception**: Preferences dialogs have no domain logic and no service calls.
`PreferencesDialog` uses QSettings directly, matching the precedent in
`MainWindow._save_settings()` / `_load_settings()`.

**QSettings keys:**
```
TextTools/editor/font_family         str,  default "Monospace"
TextTools/editor/font_size           int,  default 12
TextTools/editor/word_wrap           bool, default False
TextTools/editor/line_numbers        bool, default True
TextTools/appearance/theme           str,  "light" | "dark", default "light"
TextTools/files/default_directory    str,  default QDir.homePath()
```

**`MainWindow` changes:**
- `actionPreferences` → `PreferencesDialog(parent=self).exec()`
- `PreferencesDialog.preferences_changed` → `self._apply_preferences()`
- `_apply_preferences()` called once on startup (after `_load_settings()`)

**`MainWindow._apply_preferences()`** reads QSettings and applies live:
- Font → `plainTextEdit.setFont()`
- Word wrap → `plainTextEdit.setLineWrapMode()`
- Theme → `QApplication.setPalette()` (dark via `QApplication.style().standardPalette()` override)
- Default dir → `_fs_model.setRootPath()` + `_file_tree_view.setRootIndex()`
- Line numbers → stored for future `LineNumberArea` widget (not yet implemented — see Known Limits)

### 2.4 Known Limits

**Line number area** (deferred): Showing line numbers in `QPlainTextEdit` requires a custom
`LineNumberEditor` subclass that paints a `LineNumberArea` widget into the editor's left viewport
margin. This is the Qt Code Editor pattern. The Preferences checkbox stores the setting, but
`_apply_preferences()` will log a warning that line numbers are not yet rendered. The
`LineNumberEditor` implementation is a separate follow-on task.

### 2.5 Tests

**Unit — new file `tests/unit/test_preferences_dialog.py`:**
- `test_dialog_reads_qsettings_on_open`
- `test_apply_writes_qsettings`
- `test_cancel_does_not_write_qsettings`
- `test_preferences_changed_signal_emitted_on_apply`

**Integration — new class in `tests/integration/test_main_window.py`:**
- `test_open_preferences_dialog`
- `test_font_size_applied_to_editor`
- `test_word_wrap_applied_to_editor`
- `test_theme_applied_to_palette`
- `test_preferences_persisted_across_sessions`

---

## 3. Implementation Order

```
Phase 1 — File Merge
  1a. Add TextProcessingService.merge_documents() + unit tests
  1b. Add MainViewModel merge state + slots + signals + unit tests
  1c. Update main_window.ui — replace coming-soon label with merge widgets
  1d. Wire merge tab in MainWindow + integration tests

Phase 2 — Preferences Dialog
  2a. Create preferences_dialog.ui in Qt Designer
  2b. Implement PreferencesDialog class + unit tests
  2c. Wire actionPreferences in MainWindow + _apply_preferences() + integration tests
  2d. Call _apply_preferences() on startup
```

Each phase completes with all tests passing before the next begins.
