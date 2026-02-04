# TextTools Consolidation Plan

## Problem Summary

TextTools was forked from a "Template-Desktop-Application" repo but never transitioned from template to real app. The Qt Designer UI file is the **only** TextTools-specific code — everything else (models, services, viewmodels, views, tests, README, constants) is still generic template scaffolding. The app **crashes on startup** because the View references template widgets (`loadButton`, `listWidget`) that don't exist in the real UI file.

### Current State
- **UI file** (`src/views/ui/main_window.ui`): Real TextTools interface — complete and well-designed
- **DESIGN.md**: Comprehensive 1330-line specification — excellent blueprint
- **CLAUDE.md**: Accurate project-level instructions
- **All Python code**: Generic template code — `ExampleModel`, `ExampleService`, template `MainViewModel`/`MainWindow`
- **Tests**: Well-patterned but test template code, not TextTools
- **README/CHANGELOG/CONTRIBUTING/AGENTS.md**: Template content ("Template-Desktop-Application")
- **Dependencies**: Not installed, no virtual environment
- **Git hooks**: Not installed (branch protection inactive)
- **Orphaned `~/` directory**: Literal tilde folder in project root (accident)
- **App name**: Still says "Template Desktop Application" in `main.py` and `constants.py`

---

## Plan: Clean Slate + Core Wiring

Goal: Remove all template code, create real TextTools models/services/viewmodel/view that connect to the existing UI, fix project housekeeping, and get a **runnable app** that opens files in the text editor. This provides a solid foundation for implementing remaining features from DESIGN.md.

---

## Step 1: Project Housekeeping

**Files to modify/create/delete:**

### 1a. Remove orphaned directory
- Delete `/home/chris/projects/TextTools/~/` (literal tilde directory created by accident)

### 1b. Fix constants
- **File**: `src/utils/constants.py`
- Change `APP_NAME` to `"TextTools"`
- Change `APP_VERSION` to `"0.1.0"`
- Update window dimensions to match UI: `894x830`

### 1c. Fix main.py app metadata
- **File**: `src/main.py`
- Change `setApplicationName("Template Desktop Application")` → `"TextTools"`
- Change `setOrganizationName("YourOrganization")` → appropriate value
- Update imports to use new real services/viewmodels (done in later steps)

### 1d. Update requirements.txt
- **File**: `requirements.txt`
- Add `chardet>=5.2.0` (encoding detection, per DESIGN.md)

### 1e. Create pyproject.toml project section
- **File**: `pyproject.toml`
- Add `[project]` section with name="TextTools", version, dependencies, python-requires

### 1f. Track CLAUDE.md
- `git add CLAUDE.md`

### 1g. Update README.md
- **File**: `README.md`
- Rewrite for TextTools (not template) — project description, setup with `uv`, running instructions

### 1h. Update CHANGELOG.md
- **File**: `CHANGELOG.md`
- Clear template history, start fresh with v0.1.0

### 1i. Clean up template doc references
- **Files to review**: `CONTRIBUTING.md`, `AGENTS.md`, `.agents/PROTECTION_VERIFICATION.md`
- Fix path references from `Template-Desktop-Application` → `TextTools`
- Remove references to non-existent files (`setup.sh`, branch protection docs that don't exist)

---

## Step 2: Create Real Models

Replace template `ExampleModel` with TextTools domain models per DESIGN.md Section 6.1.

### 2a. Create `src/models/text_document.py`
```python
@dataclass
class TextDocument:
    """Represents a loaded text file."""
    file_path: str | None = None
    content: str = ""
    encoding: str = "utf-8"
    is_modified: bool = False
    file_name: str = ""
```
- Pure Python dataclass, no Qt imports
- Tracks file path, content, detected encoding, modified state

### 2b. Create `src/models/cleaning_options.py`
```python
@dataclass
class CleaningOptions:
    """User-selected text cleaning operations."""
    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False
```
- Maps to the 3 checkboxes in the Clean tab UI

### 2c. Delete `src/models/example_model.py`
- Remove template model entirely

### 2d. Update `src/models/__init__.py`
- Export new models

---

## Step 3: Create Real Services

Replace template `ExampleService` with TextTools services per DESIGN.md Section 8.2.

### 3a. Create `src/services/file_service.py`
```python
class FileService:
    """Handles file I/O operations."""
    def read_file(self, file_path: str) -> TextDocument: ...
    def write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> bool: ...
```
- Reads files with encoding detection (using chardet)
- Writes files with specified encoding
- No Qt imports

### 3b. Create `src/services/encoding_service.py`
```python
class EncodingService:
    """Handles encoding detection and conversion."""
    def detect_encoding(self, file_path: str) -> str: ...
    def convert_to_utf8(self, content: bytes, source_encoding: str) -> str: ...
```
- Uses chardet for detection
- Handles conversion to UTF-8

### 3c. Create `src/services/text_processing_service.py`
```python
class TextProcessingService:
    """Handles text cleaning operations."""
    def trim_whitespace(self, text: str) -> str: ...
    def clean_whitespace(self, text: str) -> str: ...
    def remove_tabs(self, text: str) -> str: ...
    def apply_cleaning(self, text: str, options: CleaningOptions) -> str: ...
```
- Pure text transformations
- Each method corresponds to a UI checkbox

### 3d. Delete `src/services/example_service.py`
- Remove template service entirely

### 3e. Update `src/services/__init__.py`
- Export new services

---

## Step 4: Rewrite ViewModel

Replace template `MainViewModel` with one that connects to real services and the actual UI widgets.

### 4a. Rewrite `src/viewmodels/main_viewmodel.py`
- **Signals needed** (per DESIGN.md):
  - `document_loaded(str, str)` — content, encoding
  - `file_saved(str)` — file path
  - `encoding_detected(str)` — encoding name
  - `error_occurred(str)` — error message
  - `status_changed(str)` — status bar text
- **Slots needed**:
  - `load_file(file_path: str)` — read file via FileService, emit document_loaded
  - `save_file(file_path: str, content: str)` — write via FileService, emit file_saved
  - `detect_encoding(file_path: str)` — detect via EncodingService, emit encoding_detected
  - `convert_encoding()` — convert loaded doc to UTF-8
  - `clean_text(content: str, options: CleaningOptions)` — apply cleaning via TextProcessingService
  - `find_text(content: str, search: str, start_pos: int)` — find in text
  - `replace_text(content: str, search: str, replace: str, pos: int)` — replace at position
  - `replace_all(content: str, search: str, replace: str)` — replace all
- **Constructor**: Accept `FileService`, `EncodingService`, `TextProcessingService` via DI
- Define service protocols for testability

---

## Step 5: Rewrite View

Replace template `MainWindow` with one that connects to the real UI widgets from `main_window.ui`.

### 5a. Rewrite `src/views/main_window.py`
- **Widget references** (from UI file — these are the actual objectNames):
  - `plainTextEdit` — main text editor (QPlainTextEdit)
  - `fileNameEdit` — filename display (QLineEdit)
  - `saveButton` — save button (QPushButton)
  - `fileTreeView` — file browser (QTreeView)
  - `convertEncodingButton` — encoding convert button
  - `getEncodingFormatLabel` — shows detected encoding
  - `currentFormatLabel` — "Current format:" label
  - `trimWhiteSpaceCheckBox`, `cleanWhiteSpaceCheckBox`, `removeTabsCheckBox` — cleaning checkboxes
  - `findLineEdit`, `findButton` — find widgets
  - `replaceLineEdit`, `replaceButton`, `replaceAllButton` — replace widgets
  - `tabWidget` — tool tabs (Clean/Merge/Find/Replace)
  - Menu actions: `actionOpen`, `actionSave`, `actionSave_as`, `actionQuit`, `actionAbout`
- **Signal connections**:
  - `saveButton.clicked` → viewmodel save
  - `actionOpen.triggered` → file dialog → viewmodel load
  - `convertEncodingButton.clicked` → viewmodel detect + convert
  - `findButton.clicked` → viewmodel find
  - `replaceButton.clicked` → viewmodel replace
  - `replaceAllButton.clicked` → viewmodel replace_all
  - `fileTreeView` selection → viewmodel load_file
- **Setup `QFileSystemModel`** for `fileTreeView` (show home directory or configurable root)
- Set `tabWidget` currentIndex to 0 (Clean tab)

---

## Step 6: Update main.py Entry Point

### 6a. Rewrite `src/main.py`
- Create real services: `FileService()`, `EncodingService()`, `TextProcessingService()`
- Create `MainViewModel(file_service, encoding_service, text_processing_service)`
- Create `MainWindow(viewmodel)`
- Update app metadata

---

## Step 7: Rewrite Tests

Replace template tests with TextTools-specific tests.

### 7a. Update `tests/conftest.py`
- Keep `qapp` fixture (it's correct)
- Remove `example_model_data` fixture
- Add fixtures for TextDocument, CleaningOptions, temp file creation

### 7b. Create `tests/unit/test_text_document.py`
- Test TextDocument dataclass creation, defaults, field assignment

### 7c. Create `tests/unit/test_cleaning_options.py`
- Test CleaningOptions defaults, flag combinations

### 7d. Create `tests/unit/test_file_service.py`
- Test read_file with real temp files (various encodings)
- Test write_file
- Test error handling (file not found, permission denied)

### 7e. Create `tests/unit/test_encoding_service.py`
- Test detect_encoding with known encodings
- Test convert_to_utf8

### 7f. Create `tests/unit/test_text_processing_service.py`
- Test trim_whitespace (leading/trailing blank lines, line edge spaces)
- Test clean_whitespace (multiple spaces → single)
- Test remove_tabs (tabs and leading spaces)
- Test apply_cleaning with various option combinations

### 7g. Rewrite `tests/unit/test_main_viewmodel.py`
- Test with mock services
- Test signal emissions for load/save/clean/find/replace
- Test error handling paths

### 7h. Rewrite `tests/integration/test_application.py`
- Test full stack: load file → display in editor → clean → save
- Use real temp files

### 7i. Delete `tests/unit/test_example_model.py`
- Remove template test file

---

## Step 8: Final Cleanup

### 8a. Remove references to template files
- Ensure no imports of `ExampleModel` or `ExampleService` remain anywhere
- Search for "Template Desktop Application" and replace all occurrences
- Search for "Template-Desktop-Application" in docs and fix

### 8b. Clean up UI file placeholder widgets
- In `main_window.ui`: rename `checkBox_2`, `checkBox_4`, `checkBox_6` to meaningful names or mark as placeholders
- Set `tabWidget` currentIndex to 0

### 8c. Run full verification
- `uv pip install -r requirements.txt`
- `python src/main.py` — app should launch without crash
- `pytest tests/` — all tests should pass
- `mypy src/` — no type errors
- `black --check src/ tests/` — formatting OK

---

## File Change Summary

| Action | File | What |
|--------|------|------|
| Delete | `~/` (orphaned dir) | Remove accidental tilde directory |
| Delete | `src/models/example_model.py` | Remove template model |
| Delete | `src/services/example_service.py` | Remove template service |
| Delete | `tests/unit/test_example_model.py` | Remove template test |
| Create | `src/models/text_document.py` | TextDocument dataclass |
| Create | `src/models/cleaning_options.py` | CleaningOptions dataclass |
| Create | `src/services/file_service.py` | File I/O service |
| Create | `src/services/encoding_service.py` | Encoding detection/conversion |
| Create | `src/services/text_processing_service.py` | Text cleaning operations |
| Create | `tests/unit/test_text_document.py` | Model tests |
| Create | `tests/unit/test_cleaning_options.py` | Model tests |
| Create | `tests/unit/test_file_service.py` | Service tests |
| Create | `tests/unit/test_encoding_service.py` | Service tests |
| Create | `tests/unit/test_text_processing_service.py` | Service tests |
| Rewrite | `src/viewmodels/main_viewmodel.py` | Real ViewModel with TextTools signals/slots |
| Rewrite | `src/views/main_window.py` | Connect to actual UI widgets |
| Rewrite | `src/main.py` | Real DI setup with TextTools services |
| Rewrite | `src/utils/constants.py` | TextTools name, version, dimensions |
| Rewrite | `tests/unit/test_main_viewmodel.py` | TextTools ViewModel tests |
| Rewrite | `tests/integration/test_application.py` | End-to-end TextTools tests |
| Rewrite | `tests/conftest.py` | TextTools fixtures |
| Rewrite | `README.md` | TextTools project description |
| Update | `CHANGELOG.md` | Fresh start at v0.1.0 |
| Update | `requirements.txt` | Add chardet dependency |
| Update | `pyproject.toml` | Add project metadata |
| Update | `src/models/__init__.py` | Export new models |
| Update | `src/services/__init__.py` | Export new services |
| Update | `CONTRIBUTING.md` | Fix template references |
| Update | `AGENTS.md` | Fix template references |
| Update | `.agents/PROTECTION_VERIFICATION.md` | Fix path references |

---

## Verification Plan

After all changes:

1. **Install dependencies**: `uv venv && source .venv/bin/activate && uv pip install -r requirements.txt`
2. **Launch app**: `python src/main.py` — should open TextTools window without crash
3. **Verify UI**: File tree visible, tabs work, text editor accepts input
4. **Run tests**: `pytest tests/ -v` — all tests pass
5. **Type check**: `mypy src/` — no errors
6. **Format check**: `black --check src/ tests/ && isort --check src/ tests/`
7. **Smoke test**: Open a file via File > Open, edit text, save — should work end-to-end

---

## Out of Scope (Follow-up Sessions)

These features are documented in DESIGN.md but deferred to future work:
- Merge tab functionality (F-011)
- Advanced find options (regex, case sensitivity toggle)
- Encoding conversion with preview
- File tree context menu
- Status bar encoding/line count display
- Color scheme (DESIGN.md Appendix B)
- Git hooks / branch protection setup
- CI/CD workflow updates
