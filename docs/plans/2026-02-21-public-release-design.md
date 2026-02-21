# TextTools Public Release Design

**Date**: 2026-02-21
**Scope**: Option B — Core features: open/edit/clean/save + find/replace
**Goal**: Replace scaffold template code with real TextTools domain, clean repo for public release

---

## 1. Repo Hygiene (Phase 0 — prerequisite)

- Delete accidental `~/` directory from repo root
- Git-untrack `.contextstream/config.json`; add `.contextstream/` to `.gitignore`
- Remove internal AI config directories: `.github/agents/`, `.github/chatmodes/`, `.github/prompts/`
- Remove template artifact docs: `docs/old/`, `docs/CUSTOMIZATION_CHECKLIST.md`
- Rewrite `AGENTS.md` for TextTools identity (remove "template for building desktop apps")
- Add `setup-branch-protection.sh` to `.gitignore`
- Fix `.ui` window title: `"MainWindow"` → `"TextTools"`

---

## 2. Models (Phase 1)

Delete `src/models/example_model.py`.
Create two new model files:

### `src/models/text_document.py`

```python
@dataclass
class TextDocument:
    filepath: str
    content: str
    encoding: str = "utf-8"
    modified: bool = False

    def validate(self) -> bool:
        return len(self.filepath) > 0
```

### `src/models/cleaning_options.py`

```python
@dataclass
class CleaningOptions:
    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False
```

---

## 3. Services (Phase 2)

Delete `src/services/example_service.py`.
Create two new service files:

### `src/services/file_service.py`

- `open_file(filepath: str) -> TextDocument` — reads file, detects encoding via chardet fallback, wraps in TextDocument
- `save_file(document: TextDocument) -> None` — atomic write (temp file + rename)
- `validate_filepath(filepath: str) -> bool` — checks path is readable/writable

### `src/services/text_processing_service.py`

- `trim_whitespace(text: str) -> str` — strip leading/trailing blank lines and line-end spaces
- `clean_whitespace(text: str) -> str` — collapse multiple spaces to single space
- `remove_tabs(text: str) -> str` — strip leading tabs/spaces from each line
- `apply_options(text: str, options: CleaningOptions) -> str` — compose enabled operations

---

## 4. ViewModel (Phase 3)

Rewrite `src/viewmodels/main_viewmodel.py`:

**Signals:**
- `document_loaded = Signal(str)` — file content ready for editor
- `encoding_detected = Signal(str)` — detected encoding name
- `file_saved = Signal(str)` — saved filepath
- `error_occurred = Signal(str)` — error message for status bar / dialog
- `status_changed = Signal(str)` — status bar text

**Slots:**
- `load_file(filepath: str)` — FileService.open_file → emit document_loaded + encoding_detected
- `save_file(filepath: str, content: str)` — build TextDocument → FileService.save_file → emit file_saved
- `apply_cleaning(options: CleaningOptions)` — TextProcessingService.apply_options → emit document_loaded
- `find_next(term: str)` — emit find_requested signal (view handles QPlainTextEdit.find())
- `replace_text(find: str, replace: str)` — emit replace_requested (view handles cursor replacement)
- `replace_all(find: str, replace: str)` — TextProcessingService replaces in current content → emit document_loaded

**ServiceProtocol** (in same file as ViewModel):
```python
class FileServiceProtocol(Protocol):
    def open_file(self, filepath: str) -> TextDocument: ...
    def save_file(self, document: TextDocument) -> None: ...

class TextServiceProtocol(Protocol):
    def apply_options(self, text: str, options: CleaningOptions) -> str: ...
```

---

## 5. View (Phase 4)

Rewrite `src/views/main_window.py` to connect actual `.ui` widget names (per DESIGN.md Appendix A):

**Widget connections:**
- `fileTreeView` (QTreeView) with `QFileSystemModel` → `viewmodel.load_file`
- `saveButton` / `actionSave` → collect `fileNameEdit.text()` + `plainTextEdit.toPlainText()` → `viewmodel.save_file`
- `plainTextEdit` populated from `document_loaded` signal
- `fileNameEdit` populated from file path on load; editable for save-as
- `getEncodingFormatLabel` populated from `encoding_detected` signal
- `trimWhiteSpaceCheckBox`, `cleanWhiteSpaceCheckBox`, `removeTabsCheckBox` → read state → `viewmodel.apply_cleaning`
- `convertEncodingButton` → stub (show "Coming soon" status)
- `findButton` → `QPlainTextEdit.find(findLineEdit.text())`
- `replaceButton` → find then cursor replace
- `replaceAllButton` → `viewmodel.replace_all`
- `actionOpen`, `actionQuit`, `actionAbout` → connected

**ViewModel signal handlers:**
- `_on_document_loaded(content)` → `plainTextEdit.setPlainText(content)`
- `_on_file_saved(path)` → status bar confirmation
- `_on_error(msg)` → `QMessageBox.critical`
- `_on_status_changed(msg)` → status bar

---

## 6. Tests (Phase 5)

### Unit Tests

| File | Coverage target |
|------|----------------|
| `tests/unit/test_text_document.py` | TextDocument validation, defaults |
| `tests/unit/test_cleaning_options.py` | CleaningOptions defaults |
| `tests/unit/test_file_service.py` | open_file, save_file with tmp files |
| `tests/unit/test_text_processing_service.py` | Each algorithm, edge cases, apply_options composition |
| `tests/unit/test_main_viewmodel.py` | All slots, signal emissions, error handling |

### Integration Tests

| File | Scenarios |
|------|-----------|
| `tests/integration/test_application.py` | Full load → clean → save workflow with real files |

### GUI Tests (qt-pilot)

| File | Scenarios |
|------|-----------|
| `tests/gui/test_main_window.py` | Launch app, load file via tree, apply cleaning, find/replace, save |

---

## 7. Code Quality + Docs (Phase 6)

- Python 3.14 type hints: `Optional[X]` → `X | None`, `List[X]` → `list[X]` throughout
- Qt6 enums: `QFile.ReadOnly` → `QFile.OpenModeFlag.ReadOnly`
- `requirements.txt`: add `chardet>=5.0.0`
- `README.md`: update to describe real working features
- `CHANGELOG.md`: create `[0.2.0]` entry with accurate changes
- `AGENTS.md`: rewrite for TextTools (not "template for desktop apps")

---

## Implementation Order

```
Phase 0: Repo hygiene (git cleanup)
Phase 1: Models (no Qt — pure Python, testable immediately)
Phase 2: Services (no Qt — file I/O and text processing)
Phase 3: ViewModel (Qt signals, tested with mock services)
Phase 4: View (wire real .ui widgets)
Phase 5: Tests (unit + integration + qt-pilot GUI)
Phase 6: Code quality + docs
```

Each phase completes with all tests passing before the next begins.
