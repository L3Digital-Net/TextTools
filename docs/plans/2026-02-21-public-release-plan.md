# TextTools Public Release Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace scaffold template code with real TextTools domain, clean repo for public release.

**Architecture:** Six-phase delivery — repo hygiene first, then models → services → viewmodel → view, each layer tested before the next is touched. View wires existing `.ui` widget objectNames (DESIGN.md Appendix A) to ViewModel signals/slots via `findChild()`. No business logic in the view layer.

**Tech Stack:** Python 3.14, PySide6 6.8.0+, MVVM, pytest + pytest-qt + pytest-mock, UV

---

## Phase 0: Repo Hygiene

### Task 0.1: Remove accidental `~/` directory

The literal `~` directory was created by a shell expansion mistake (`mkdir ~/...` run inside the project root instead of home).

**Step 1: Remove it from git tracking and disk**

```bash
git rm -r "~/"
```

Expected output: `rm '~/.claude/plans/partitioned-zooming-journal.md'`

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove accidental tilde directory from repo root"
```

---

### Task 0.2: Clean up internal files from repo

**Step 1: Remove internal AI config directories**

```bash
git rm -r .github/agents/ .github/chatmodes/ .github/prompts/ 2>/dev/null || true
git rm -r docs/old/ docs/CUSTOMIZATION_CHECKLIST.md 2>/dev/null || true
```

**Step 2: Update `.gitignore` to exclude internal tooling**

Add these lines to the end of `.gitignore`:

```gitignore
# Internal tooling
.contextstream/
setup-branch-protection.sh

# Project plans (local development notes)
# docs/plans/  ← keep commented; plans are useful in the public repo
```

**Step 3: Untrack `.contextstream/config.json`**

```bash
git rm --cached .contextstream/config.json
```

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: remove internal AI configs and add gitignore entries"
```

---

### Task 0.3: Fix window title in `.ui` file

**File:** `src/views/ui/main_window.ui`

Find the line containing `<string>MainWindow</string>` under `windowTitle` and change it to:

```xml
<property name="windowTitle">
 <string>TextTools</string>
</property>
```

**Verify:**

```bash
grep -n "windowTitle" src/views/ui/main_window.ui
```

Expected: `<string>TextTools</string>`

**Commit:**

```bash
git add src/views/ui/main_window.ui
git commit -m "fix: set window title to TextTools in .ui file"
```

---

### Task 0.4: Rewrite `AGENTS.md`

Replace the entire content of `AGENTS.md` with a TextTools-specific version that removes all "template" references.

**File:** `AGENTS.md`

```markdown
# Agent Instructions for TextTools

## Overview

TextTools is a PySide6 desktop application for text processing on Linux.
Architecture: MVVM with dependency injection, Qt Designer .ui files.

## Branch Protection

BEFORE ANY FILE MODIFICATION, RUN:

```bash
python .agents/branch_protection.py
```

- NEVER modify files on `main` branch
- ALWAYS work on `testing` branch

## Architecture

```
src/models/       — Pure Python dataclasses, no Qt imports
src/viewmodels/   — QObject, signals/slots, calls services
src/views/        — Loads .ui files, findChild(), no business logic
src/services/     — File I/O, text processing, no Qt imports
src/utils/        — Constants
src/main.py       — Composition root: wires services → viewmodels → views
```

## Widget ObjectNames

UI widget names are defined in DESIGN.md Appendix A. When modifying the .ui file,
keep objectNames in sync with `findChild()` calls in `src/views/main_window.py`.

## Testing

```bash
.venv/bin/python -m pytest tests/ -v
.venv/bin/python -m mypy src/
```

## Conventions

- Type hints required on all functions
- `str | None` not `Optional[str]`, `list[X]` not `List[X]` (Python 3.10+ syntax)
- Google-style docstrings on public APIs
- Signals for all cross-layer communication
- Long operations must use QThread — never block UI thread
```

**Commit:**

```bash
git add AGENTS.md
git commit -m "docs: rewrite AGENTS.md for TextTools identity"
```

---

## Phase 1: Models

### Task 1.1: `TextDocument` model (TDD)

**Files:**
- Create: `src/models/text_document.py`
- Create: `tests/unit/test_text_document.py`

**Step 1: Write the failing tests**

Create `tests/unit/test_text_document.py`:

```python
"""Unit tests for TextDocument model."""
import pytest
from src.models.text_document import TextDocument


class TestTextDocument:
    def test_initialization_with_required_fields(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="hello")
        assert doc.filepath == "/tmp/test.txt"
        assert doc.content == "hello"

    def test_default_encoding_is_utf8(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.encoding == "utf-8"

    def test_default_modified_is_false(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.modified is False

    def test_validate_returns_true_for_nonempty_filepath(self):
        doc = TextDocument(filepath="/tmp/test.txt", content="")
        assert doc.validate() is True

    def test_validate_returns_false_for_empty_filepath(self):
        doc = TextDocument(filepath="", content="hello")
        assert doc.validate() is False

    def test_custom_encoding_stored(self):
        doc = TextDocument(filepath="/tmp/f.txt", content="x", encoding="latin-1")
        assert doc.encoding == "latin-1"

    def test_modified_flag_settable(self):
        doc = TextDocument(filepath="/tmp/f.txt", content="x", modified=True)
        assert doc.modified is True
```

**Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/unit/test_text_document.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.models.text_document'`

**Step 3: Implement `TextDocument`**

Create `src/models/text_document.py`:

```python
"""TextDocument — core domain model for a loaded text file.

This is the primary data transfer object between FileService and MainViewModel.
If fields change, update FileService.open_file() and MainViewModel._current_document
references accordingly.
"""
from dataclasses import dataclass


@dataclass
class TextDocument:
    """A text file loaded into memory with its metadata.

    Attributes:
        filepath: Absolute or relative path to the source file.
        content: Decoded text content of the file.
        encoding: Character encoding used to decode the file.
        modified: True if content has been changed since last save.
    """

    filepath: str
    content: str
    encoding: str = "utf-8"
    modified: bool = False

    def validate(self) -> bool:
        """Return True if this document has a non-empty filepath."""
        return len(self.filepath) > 0
```

**Step 4: Run tests to confirm pass**

```bash
.venv/bin/python -m pytest tests/unit/test_text_document.py -v
```

Expected: `7 passed`

**Step 5: Commit**

```bash
git add src/models/text_document.py tests/unit/test_text_document.py
git commit -m "feat: add TextDocument model with tests"
```

---

### Task 1.2: `CleaningOptions` model (TDD)

**Files:**
- Create: `src/models/cleaning_options.py`
- Create: `tests/unit/test_cleaning_options.py`

**Step 1: Write the failing tests**

Create `tests/unit/test_cleaning_options.py`:

```python
"""Unit tests for CleaningOptions model."""
from src.models.cleaning_options import CleaningOptions


class TestCleaningOptions:
    def test_all_options_default_to_false(self):
        opts = CleaningOptions()
        assert opts.trim_whitespace is False
        assert opts.clean_whitespace is False
        assert opts.remove_tabs is False

    def test_options_can_be_set(self):
        opts = CleaningOptions(trim_whitespace=True, remove_tabs=True)
        assert opts.trim_whitespace is True
        assert opts.clean_whitespace is False
        assert opts.remove_tabs is True

    def test_all_options_enabled(self):
        opts = CleaningOptions(
            trim_whitespace=True,
            clean_whitespace=True,
            remove_tabs=True,
        )
        assert opts.trim_whitespace is True
        assert opts.clean_whitespace is True
        assert opts.remove_tabs is True
```

**Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/unit/test_cleaning_options.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.models.cleaning_options'`

**Step 3: Implement `CleaningOptions`**

Create `src/models/cleaning_options.py`:

```python
"""CleaningOptions — configuration for text cleaning operations.

Passed from View → ViewModel → TextProcessingService. If fields change,
update MainWindow._collect_cleaning_options() and TextProcessingService.apply_options().
"""
from dataclasses import dataclass


@dataclass
class CleaningOptions:
    """Flags controlling which text cleaning operations to apply.

    Attributes:
        trim_whitespace: Strip leading/trailing blank lines; strip trailing
            spaces from each line.
        clean_whitespace: Collapse multiple consecutive spaces to one.
        remove_tabs: Strip leading tabs and spaces from the start of each line.
    """

    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_cleaning_options.py -v
```

Expected: `3 passed`

**Step 5: Commit**

```bash
git add src/models/cleaning_options.py tests/unit/test_cleaning_options.py
git commit -m "feat: add CleaningOptions model with tests"
```

---

## Phase 2: Services

### Task 2.1: `TextProcessingService` (TDD)

**Files:**
- Create: `src/services/text_processing_service.py`
- Create: `tests/unit/test_text_processing_service.py`

**Step 1: Write the failing tests**

Create `tests/unit/test_text_processing_service.py`:

```python
"""Unit tests for TextProcessingService — no Qt required."""
import pytest
from src.services.text_processing_service import TextProcessingService
from src.models.cleaning_options import CleaningOptions


@pytest.fixture
def svc():
    return TextProcessingService()


class TestTrimWhitespace:
    def test_strips_leading_blank_lines(self, svc):
        result = svc.trim_whitespace("\n\nhello")
        assert result == "hello"

    def test_strips_trailing_blank_lines(self, svc):
        result = svc.trim_whitespace("hello\n\n")
        assert result == "hello"

    def test_strips_trailing_spaces_from_each_line(self, svc):
        result = svc.trim_whitespace("hello   \nworld   ")
        assert result == "hello\nworld"

    def test_preserves_internal_blank_lines(self, svc):
        result = svc.trim_whitespace("para1\n\npara2")
        assert result == "para1\n\npara2"

    def test_empty_string_returns_empty(self, svc):
        assert svc.trim_whitespace("") == ""

    def test_only_whitespace_returns_empty(self, svc):
        assert svc.trim_whitespace("   \n  \n") == ""


class TestCleanWhitespace:
    def test_collapses_multiple_spaces(self, svc):
        result = svc.clean_whitespace("hello    world")
        assert result == "hello world"

    def test_single_space_unchanged(self, svc):
        result = svc.clean_whitespace("hello world")
        assert result == "hello world"

    def test_preserves_line_breaks(self, svc):
        result = svc.clean_whitespace("line1\nline2")
        assert result == "line1\nline2"

    def test_collapses_per_line(self, svc):
        result = svc.clean_whitespace("a  b\nc   d")
        assert result == "a b\nc d"

    def test_empty_string(self, svc):
        assert svc.clean_whitespace("") == ""


class TestRemoveTabs:
    def test_removes_leading_tab(self, svc):
        result = svc.remove_tabs("\thello")
        assert result == "hello"

    def test_removes_leading_spaces(self, svc):
        result = svc.remove_tabs("   hello")
        assert result == "hello"

    def test_removes_mixed_leading_whitespace(self, svc):
        result = svc.remove_tabs("\t  hello")
        assert result == "hello"

    def test_preserves_non_leading_whitespace(self, svc):
        result = svc.remove_tabs("hello\tworld")
        assert result == "hello\tworld"

    def test_processes_each_line(self, svc):
        result = svc.remove_tabs("\tline1\n\tline2")
        assert result == "line1\nline2"

    def test_empty_string(self, svc):
        assert svc.remove_tabs("") == ""


class TestApplyOptions:
    def test_no_options_returns_unchanged(self, svc):
        text = "  hello  \n  world  "
        result = svc.apply_options(text, CleaningOptions())
        assert result == text

    def test_trim_only(self, svc):
        result = svc.apply_options("\nhello\n", CleaningOptions(trim_whitespace=True))
        assert result == "hello"

    def test_clean_only(self, svc):
        result = svc.apply_options("a  b", CleaningOptions(clean_whitespace=True))
        assert result == "a b"

    def test_remove_tabs_only(self, svc):
        result = svc.apply_options("\thello", CleaningOptions(remove_tabs=True))
        assert result == "hello"

    def test_all_options_compose(self, svc):
        text = "\n\t  hello    world  \n\n"
        opts = CleaningOptions(
            trim_whitespace=True, clean_whitespace=True, remove_tabs=True
        )
        result = svc.apply_options(text, opts)
        assert result == "hello world"
```

**Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/unit/test_text_processing_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.services.text_processing_service'`

**Step 3: Implement `TextProcessingService`**

Create `src/services/text_processing_service.py`:

```python
"""TextProcessingService — stateless text cleaning operations.

No Qt imports. No file I/O. Each method is a pure function wrapped in a class
for dependency injection. Called by MainViewModel.apply_cleaning().
If the CleaningOptions fields change, update apply_options() below.
"""
import re
import logging
from src.models.cleaning_options import CleaningOptions


logger = logging.getLogger(__name__)


class TextProcessingService:
    """Stateless text cleaning and manipulation.

    All methods take a str and return a str; they have no side effects.
    """

    def trim_whitespace(self, text: str) -> str:
        """Strip leading/trailing blank lines; strip trailing spaces from each line."""
        lines = text.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(line.rstrip() for line in lines)

    def clean_whitespace(self, text: str) -> str:
        """Collapse two or more consecutive spaces to a single space on each line."""
        lines = text.splitlines()
        return "\n".join(re.sub(r" {2,}", " ", line) for line in lines)

    def remove_tabs(self, text: str) -> str:
        """Strip leading tabs and spaces from the start of each line."""
        lines = text.splitlines()
        return "\n".join(line.lstrip(" \t") for line in lines)

    def apply_options(self, text: str, options: CleaningOptions) -> str:
        """Apply enabled cleaning operations in a fixed order.

        Order: trim_whitespace → clean_whitespace → remove_tabs.
        This order is intentional: trimming first removes boundary noise before
        whitespace normalization runs on the meaningful content.
        """
        if options.trim_whitespace:
            text = self.trim_whitespace(text)
        if options.clean_whitespace:
            text = self.clean_whitespace(text)
        if options.remove_tabs:
            text = self.remove_tabs(text)
        return text
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_text_processing_service.py -v
```

Expected: `18 passed`

**Step 5: Commit**

```bash
git add src/services/text_processing_service.py tests/unit/test_text_processing_service.py
git commit -m "feat: add TextProcessingService with tests"
```

---

### Task 2.2: `FileService` (TDD)

**Files:**
- Create: `src/services/file_service.py`
- Create: `tests/unit/test_file_service.py`

**Step 1: Write the failing tests**

Create `tests/unit/test_file_service.py`:

```python
"""Unit tests for FileService — uses tmp_path, no Qt required."""
import pytest
from src.services.file_service import FileService
from src.models.text_document import TextDocument


@pytest.fixture
def svc():
    return FileService()


class TestOpenFile:
    def test_reads_utf8_file(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.content == "hello world"
        assert doc.filepath == str(f)

    def test_detected_encoding_stored(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("hello".encode("utf-8"))
        doc = svc.open_file(str(f))
        assert isinstance(doc.encoding, str)
        assert len(doc.encoding) > 0

    def test_modified_is_false_on_open(self, svc, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.modified is False

    def test_raises_file_not_found(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.open_file("/nonexistent/path/file.txt")

    def test_reads_multiline_content(self, svc, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("line1\nline2\nline3", encoding="utf-8")
        doc = svc.open_file(str(f))
        assert doc.content == "line1\nline2\nline3"


class TestSaveFile:
    def test_writes_content_to_disk(self, svc, tmp_path):
        filepath = str(tmp_path / "out.txt")
        doc = TextDocument(filepath=filepath, content="saved content")
        svc.save_file(doc)
        assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "saved content"

    def test_save_round_trip(self, svc, tmp_path):
        filepath = str(tmp_path / "round.txt")
        doc = TextDocument(filepath=filepath, content="round trip")
        svc.save_file(doc)
        loaded = svc.open_file(filepath)
        assert loaded.content == "round trip"

    def test_raises_value_error_for_empty_filepath(self, svc):
        doc = TextDocument(filepath="", content="data")
        with pytest.raises(ValueError):
            svc.save_file(doc)

    def test_overwrites_existing_file(self, svc, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("old content", encoding="utf-8")
        doc = TextDocument(filepath=str(f), content="new content")
        svc.save_file(doc)
        assert f.read_text(encoding="utf-8") == "new content"
```

**Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/unit/test_file_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.services.file_service'`

**Step 3: Implement `FileService`**

Create `src/services/file_service.py`:

```python
"""FileService — all file system I/O for TextTools.

No Qt imports. Wraps file operations in TextDocument objects.
Called only from MainViewModel — never directly from the View.

Atomic save: writes to a temp file in the same directory then calls os.replace()
to swap atomically. This prevents partial-write corruption if the process dies mid-save.

Encoding detection: uses chardet if available and confidence >= 0.7. Falls back
to utf-8 otherwise. Decode errors use 'replace' to avoid crashing on binary content.
"""
import logging
import os
import tempfile

from src.models.text_document import TextDocument


logger = logging.getLogger(__name__)

_ENCODING_FALLBACK = "utf-8"
_ENCODING_MIN_CONFIDENCE = 0.7


class FileService:
    """Read and write text files, wrapping results in TextDocument."""

    def open_file(self, filepath: str) -> TextDocument:
        """Read a file and return a TextDocument.

        Args:
            filepath: Path to the file to read.

        Returns:
            TextDocument with decoded content and detected encoding.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            OSError: For other I/O failures.
        """
        logger.info("Opening file: %s", filepath)
        with open(filepath, "rb") as f:
            raw = f.read()
        encoding = _detect_encoding(raw)
        content = raw.decode(encoding, errors="replace")
        return TextDocument(filepath=filepath, content=content, encoding=encoding)

    def save_file(self, document: TextDocument) -> None:
        """Write document content to disk atomically.

        Args:
            document: TextDocument with filepath and content to write.

        Raises:
            ValueError: If document.filepath is empty.
            PermissionError: If the destination is not writable.
            OSError: For other I/O failures.
        """
        if not document.validate():
            raise ValueError("Document filepath is empty")

        logger.info("Saving file: %s", document.filepath)
        dirpath = os.path.dirname(os.path.abspath(document.filepath)) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dirpath)
        try:
            with os.fdopen(fd, "w", encoding=document.encoding) as f:
                f.write(document.content)
            os.replace(tmp_path, document.filepath)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def _detect_encoding(raw: bytes) -> str:
    """Return the most likely encoding for raw bytes.

    Module-level so it can be tested without instantiating FileService.
    Falls back to utf-8 if chardet is unavailable or confidence is too low.
    """
    try:
        import chardet  # optional dependency

        result = chardet.detect(raw)
        if result["encoding"] and result["confidence"] >= _ENCODING_MIN_CONFIDENCE:
            return result["encoding"]
    except ImportError:
        logger.debug("chardet not installed; defaulting to utf-8")
    return _ENCODING_FALLBACK
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_file_service.py -v
```

Expected: `9 passed`

**Step 5: Commit**

```bash
git add src/services/file_service.py tests/unit/test_file_service.py
git commit -m "feat: add FileService with atomic save and encoding detection"
```

---

## Phase 3: Remove Template Code

### Task 3.1: Delete example files and update `conftest.py`

**Step 1: Delete template files**

```bash
git rm src/models/example_model.py
git rm src/services/example_service.py
git rm tests/unit/test_example_model.py
```

**Step 2: Update `tests/conftest.py`**

Replace the entire file with:

```python
"""Pytest configuration and shared fixtures for TextTools test suite."""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication instance for the entire test session.

    Session-scoped because Qt allows only one QApplication per process.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
```

**Step 3: Run tests to confirm nothing is broken**

```bash
.venv/bin/python -m pytest tests/unit/ -v
```

Expected: all TextDocument, CleaningOptions, FileService, TextProcessingService tests pass.

**Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "chore: remove example template files, update conftest"
```

---

## Phase 4: ViewModel

### Task 4.1: Rewrite `MainViewModel` (TDD)

**Files:**
- Modify: `src/viewmodels/main_viewmodel.py`
- Modify: `tests/unit/test_main_viewmodel.py`

**Step 1: Write the failing tests**

Replace `tests/unit/test_main_viewmodel.py` with:

```python
"""Unit tests for MainViewModel.

Services are mocked so these tests run without file system access.
Uses qtbot (pytest-qt) for signal assertion.
"""
import pytest
from unittest.mock import MagicMock
from src.viewmodels.main_viewmodel import MainViewModel
from src.models.text_document import TextDocument
from src.models.cleaning_options import CleaningOptions


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
    svc.apply_options.return_value = "cleaned text"
    return svc


@pytest.fixture
def vm(mock_file_svc, mock_text_svc, qapp):
    return MainViewModel(mock_file_svc, mock_text_svc)


class TestLoadFile:
    def test_calls_file_service(self, vm, mock_file_svc):
        vm.load_file("/tmp/test.txt")
        mock_file_svc.open_file.assert_called_once_with("/tmp/test.txt")

    def test_emits_document_loaded_with_content(self, vm, qtbot):
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file("/tmp/test.txt")
        assert blocker.args[0] == "hello world"

    def test_emits_encoding_detected(self, vm, qtbot):
        with qtbot.waitSignal(vm.encoding_detected, timeout=1000) as blocker:
            vm.load_file("/tmp/test.txt")
        assert blocker.args[0] == "utf-8"

    def test_emits_error_on_file_not_found(self, vm, mock_file_svc, qtbot):
        mock_file_svc.open_file.side_effect = FileNotFoundError("not found")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.load_file("/tmp/missing.txt")
        assert "Cannot open file" in blocker.args[0]

    def test_emits_status_changed(self, vm, qtbot):
        messages = []
        vm.status_changed.connect(messages.append)
        vm.load_file("/tmp/test.txt")
        qtbot.wait(10)
        assert any("test.txt" in m for m in messages)


class TestSaveFile:
    def test_calls_file_service_save(self, vm, mock_file_svc, qtbot):
        # Load first to set current encoding
        vm.load_file("/tmp/test.txt")
        vm.save_file("/tmp/out.txt", "content to save")
        assert mock_file_svc.save_file.called

    def test_emits_file_saved_signal(self, vm, qtbot):
        with qtbot.waitSignal(vm.file_saved, timeout=1000) as blocker:
            vm.save_file("/tmp/out.txt", "content")
        assert blocker.args[0] == "/tmp/out.txt"

    def test_emits_error_on_permission_denied(self, vm, mock_file_svc, qtbot):
        mock_file_svc.save_file.side_effect = PermissionError("denied")
        with qtbot.waitSignal(vm.error_occurred, timeout=1000) as blocker:
            vm.save_file("/tmp/out.txt", "content")
        assert "Cannot save file" in blocker.args[0]


class TestApplyCleaning:
    def test_calls_text_service_with_options(self, vm, mock_file_svc, mock_text_svc):
        vm.load_file("/tmp/test.txt")
        opts = CleaningOptions(trim_whitespace=True)
        vm.apply_cleaning(opts)
        mock_text_svc.apply_options.assert_called_once_with("hello world", opts)

    def test_emits_document_loaded_with_cleaned_text(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        opts = CleaningOptions(trim_whitespace=True)
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.apply_cleaning(opts)
        assert blocker.args[0] == "cleaned text"

    def test_no_op_when_no_document_loaded(self, vm, mock_text_svc, qtbot):
        vm.apply_cleaning(CleaningOptions(trim_whitespace=True))
        mock_text_svc.apply_options.assert_not_called()


class TestReplaceAll:
    def test_replaces_all_occurrences_in_content(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")  # content = "hello world"
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.replace_all("hello", "goodbye")
        assert blocker.args[0] == "goodbye world"

    def test_emits_status_with_count(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        messages = []
        vm.status_changed.connect(messages.append)
        vm.replace_all("hello", "goodbye")
        qtbot.wait(10)
        assert any("1 occurrence" in m for m in messages)

    def test_no_op_when_no_document(self, vm, qtbot):
        # Should not emit document_loaded when no document
        emitted = []
        vm.document_loaded.connect(emitted.append)
        vm.replace_all("x", "y")
        qtbot.wait(10)
        assert emitted == []

    def test_no_op_for_empty_find_term(self, vm, qtbot):
        vm.load_file("/tmp/test.txt")
        emitted = []
        vm.document_loaded.connect(emitted.append)
        qtbot.wait(10)
        emitted.clear()
        vm.replace_all("", "replacement")
        qtbot.wait(10)
        assert emitted == []
```

**Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/unit/test_main_viewmodel.py -v
```

Expected: Most tests fail with import errors or signature mismatches.

**Step 3: Implement the new `MainViewModel`**

Replace `src/viewmodels/main_viewmodel.py`:

```python
"""MainViewModel — presentation logic for the TextTools main window.

Mediates between MainWindow (View) and the service layer.
No direct widget manipulation — communicates exclusively via signals.

ServiceProtocols are defined here (per CLAUDE.md: protocol is local to consumer).
If signal or slot signatures change, update MainWindow._connect_signals() in lockstep.
"""
import logging
from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from src.models.cleaning_options import CleaningOptions
from src.models.text_document import TextDocument


logger = logging.getLogger(__name__)


class FileServiceProtocol(Protocol):
    """Interface required of any file service injected into MainViewModel."""

    def open_file(self, filepath: str) -> TextDocument: ...

    def save_file(self, document: TextDocument) -> None: ...


class TextServiceProtocol(Protocol):
    """Interface required of any text processing service injected into MainViewModel."""

    def apply_options(self, text: str, options: CleaningOptions) -> str: ...


class MainViewModel(QObject):
    """Presentation logic for the main window.

    Signals:
        document_loaded: Emitted with decoded file content ready for the editor.
        encoding_detected: Emitted with encoding name on file open.
        file_saved: Emitted with filepath after a successful save.
        error_occurred: Emitted with error message on any failure.
        status_changed: Emitted with status bar text.
        find_requested: Emitted with search term; view performs the find.
        replace_requested: Emitted with (find, replace); view performs the replace.
    """

    document_loaded = Signal(str)
    encoding_detected = Signal(str)
    file_saved = Signal(str)
    error_occurred = Signal(str)
    status_changed = Signal(str)
    find_requested = Signal(str)
    replace_requested = Signal(str, str)

    def __init__(
        self,
        file_service: FileServiceProtocol,
        text_service: TextServiceProtocol,
    ) -> None:
        super().__init__()
        self._file_service = file_service
        self._text_service = text_service
        self._current_document: TextDocument | None = None

    @Slot(str)
    def load_file(self, filepath: str) -> None:
        """Load a file from disk and emit its content for the editor."""
        logger.info("Loading file: %s", filepath)
        self.status_changed.emit(f"Loading {filepath}...")
        try:
            doc = self._file_service.open_file(filepath)
            self._current_document = doc
            self.document_loaded.emit(doc.content)
            self.encoding_detected.emit(doc.encoding)
            self.status_changed.emit(f"Opened: {filepath}")
        except (FileNotFoundError, PermissionError, OSError) as e:
            msg = f"Cannot open file: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.status_changed.emit("Error opening file")

    @Slot(str, str)
    def save_file(self, filepath: str, content: str) -> None:
        """Save editor content to a filepath."""
        logger.info("Saving to: %s", filepath)
        encoding = self._current_document.encoding if self._current_document else "utf-8"
        doc = TextDocument(filepath=filepath, content=content, encoding=encoding)
        try:
            self._file_service.save_file(doc)
            self._current_document = doc
            self.file_saved.emit(filepath)
            self.status_changed.emit(f"Saved: {filepath}")
        except (ValueError, PermissionError, OSError) as e:
            msg = f"Cannot save file: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.status_changed.emit("Error saving file")

    @Slot(object)
    def apply_cleaning(self, options: CleaningOptions) -> None:
        """Apply text cleaning to current document content.

        No-op when no document is loaded.
        """
        if self._current_document is None:
            self.status_changed.emit("No document loaded")
            return
        cleaned = self._text_service.apply_options(
            self._current_document.content, options
        )
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=cleaned,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.document_loaded.emit(cleaned)
        self.status_changed.emit("Text cleaned")

    @Slot(str, str)
    def replace_all(self, find_term: str, replace_term: str) -> None:
        """Replace all occurrences of find_term in current document content.

        No-op when no document is loaded or find_term is empty.
        """
        if self._current_document is None or not find_term:
            return
        content = self._current_document.content
        count = content.count(find_term)
        new_content = content.replace(find_term, replace_term)
        self._current_document = TextDocument(
            filepath=self._current_document.filepath,
            content=new_content,
            encoding=self._current_document.encoding,
            modified=True,
        )
        self.document_loaded.emit(new_content)
        noun = "occurrence" if count == 1 else "occurrences"
        self.status_changed.emit(f"Replaced {count} {noun}")

    @Slot(str)
    def request_find(self, term: str) -> None:
        """Signal the view to find the next occurrence of term."""
        self.find_requested.emit(term)

    @Slot(str, str)
    def request_replace(self, find_term: str, replace_term: str) -> None:
        """Signal the view to replace the current selection."""
        self.replace_requested.emit(find_term, replace_term)
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_main_viewmodel.py -v
```

Expected: All tests pass.

**Step 5: Run full suite to verify nothing broken**

```bash
.venv/bin/python -m pytest tests/unit/ -v
```

**Step 6: Commit**

```bash
git add src/viewmodels/main_viewmodel.py tests/unit/test_main_viewmodel.py
git commit -m "feat: rewrite MainViewModel with real TextTools domain"
```

---

## Phase 5: Wiring (View + main.py)

### Task 5.1: Update `src/main.py`

**File:** `src/main.py`

Replace entirely:

```python
"""Application entry point — composition root for TextTools.

Creates services → injects into ViewModel → injects into View.
This is the only place in the app where concrete types are instantiated.
"""
import logging
import sys

from PySide6.QtWidgets import QApplication

from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main_window import MainWindow


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def create_application() -> MainWindow:
    """Wire services → viewmodel → view and return the main window."""
    file_service = FileService()
    text_service = TextProcessingService()
    viewmodel = MainViewModel(file_service, text_service)
    return MainWindow(viewmodel)


def main() -> None:
    """Application entry point."""
    logger.info("Starting TextTools")
    app = QApplication(sys.argv)
    app.setApplicationName("TextTools")
    app.setOrganizationName("TextTools")

    window = create_application()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Note:** The `FileHandler('app.log')` is removed — logging to file in the CWD is inappropriate for end-users. Console logging is sufficient.

**Commit:**

```bash
git add src/main.py
git commit -m "feat: update main.py to wire real TextTools services"
```

---

### Task 5.2: Rewrite `src/views/main_window.py`

**File:** `src/views/main_window.py`

Replace entirely:

```python
"""Main application window — UI wiring only, no business logic.

Loads UI from src/views/ui/main_window.ui via QUiLoader. Widget objectNames
referenced here must match DESIGN.md Appendix A exactly. If the .ui file
changes objectNames, update findChild() calls below to match.

Signal flow:
  User action → View slot → ViewModel slot (via signal or direct call)
  ViewModel signal → View slot → widget update
"""
import os

from PySide6.QtCore import QDir, QFile
from PySide6.QtGui import QFileSystemModel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTreeView,
)

from src.models.cleaning_options import CleaningOptions
from src.viewmodels.main_viewmodel import MainViewModel


class MainWindow(QMainWindow):
    """Main application window.

    Responsibilities:
    - Load main_window.ui and locate all named widgets
    - Wire user actions to ViewModel slots
    - Handle ViewModel signals to update the UI
    - Implement find/replace directly on QPlainTextEdit (Qt built-in)

    Not responsible for: file I/O, text processing, encoding detection.
    """

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel
        self._load_ui()
        self._setup_file_tree()
        self._connect_signals()

    # ------------------------------------------------------------------ setup

    def _load_ui(self) -> None:
        """Load main_window.ui and resolve all widget references."""
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.setCentralWidget(self.ui)

        # Widget references — objectNames from DESIGN.md Appendix A
        self._plain_text_edit: QPlainTextEdit = self.ui.findChild(
            QPlainTextEdit, "plainTextEdit"
        )
        self._file_name_edit: QLineEdit = self.ui.findChild(QLineEdit, "fileNameEdit")
        self._save_button: QPushButton = self.ui.findChild(QPushButton, "saveButton")
        self._file_tree_view: QTreeView = self.ui.findChild(QTreeView, "fileTreeView")
        self._encoding_label: QLabel = self.ui.findChild(
            QLabel, "getEncodingFormatLabel"
        )
        self._trim_cb: QCheckBox = self.ui.findChild(
            QCheckBox, "trimWhiteSpaceCheckBox"
        )
        self._clean_cb: QCheckBox = self.ui.findChild(
            QCheckBox, "cleanWhiteSpaceCheckBox"
        )
        self._remove_tabs_cb: QCheckBox = self.ui.findChild(
            QCheckBox, "removeTabsCheckBox"
        )
        self._find_edit: QLineEdit = self.ui.findChild(QLineEdit, "findLineEdit")
        self._find_button: QPushButton = self.ui.findChild(QPushButton, "findButton")
        self._replace_edit: QLineEdit = self.ui.findChild(QLineEdit, "replaceLineEdit")
        self._replace_button: QPushButton = self.ui.findChild(
            QPushButton, "replaceButton"
        )
        self._replace_all_button: QPushButton = self.ui.findChild(
            QPushButton, "replaceAllButton"
        )
        self._convert_button: QPushButton = self.ui.findChild(
            QPushButton, "convertEncodingButton"
        )

    def _setup_file_tree(self) -> None:
        """Configure QFileSystemModel rooted at the user's home directory."""
        self._fs_model = QFileSystemModel(self)
        self._fs_model.setRootPath(QDir.homePath())
        self._file_tree_view.setModel(self._fs_model)
        self._file_tree_view.setRootIndex(
            self._fs_model.index(QDir.homePath())
        )
        # Hide size/type/date columns — name column only
        for col in range(1, self._fs_model.columnCount()):
            self._file_tree_view.hideColumn(col)

    def _connect_signals(self) -> None:
        """Wire UI events to ViewModel slots and ViewModel signals to UI handlers."""
        # File tree → load file (directories are filtered inside the slot)
        self._file_tree_view.clicked.connect(self._on_tree_item_clicked)

        # Save
        self._save_button.clicked.connect(self._on_save_clicked)

        # Cleaning: each checkbox triggers a fresh apply when a doc is loaded.
        # The checkboxes act as "apply now" toggles, not deferred configuration.
        self._trim_cb.stateChanged.connect(self._on_clean_requested)
        self._clean_cb.stateChanged.connect(self._on_clean_requested)
        self._remove_tabs_cb.stateChanged.connect(self._on_clean_requested)

        # Find / Replace
        self._find_button.clicked.connect(self._on_find_clicked)
        self._replace_button.clicked.connect(self._on_replace_clicked)
        self._replace_all_button.clicked.connect(self._on_replace_all_clicked)

        # Encoding convert is stubbed for v1
        self._convert_button.clicked.connect(
            lambda: self.statusBar().showMessage("Encoding conversion — coming soon")
        )

        # ViewModel → View
        self._viewmodel.document_loaded.connect(self._on_document_loaded)
        self._viewmodel.encoding_detected.connect(self._on_encoding_detected)
        self._viewmodel.file_saved.connect(self._on_file_saved)
        self._viewmodel.error_occurred.connect(self._on_error)
        self._viewmodel.status_changed.connect(self._on_status_changed)

    # ---------------------------------------------------------- user actions

    def _on_tree_item_clicked(self, index) -> None:  # type: ignore[override]
        """Load file on tree click; ignore directory clicks."""
        path = self._fs_model.filePath(index)
        if os.path.isfile(path):
            self._file_name_edit.setText(path)
            self._viewmodel.load_file(path)

    def _on_save_clicked(self) -> None:
        """Collect filepath and editor content, then delegate to ViewModel."""
        filepath = self._file_name_edit.text().strip()
        if not filepath:
            QMessageBox.warning(
                self, "Save", "Enter a file path in the filename field before saving."
            )
            return
        self._viewmodel.save_file(filepath, self._plain_text_edit.toPlainText())

    def _on_clean_requested(self) -> None:
        """Build CleaningOptions from checkbox states; delegate to ViewModel."""
        options = CleaningOptions(
            trim_whitespace=self._trim_cb.isChecked(),
            clean_whitespace=self._clean_cb.isChecked(),
            remove_tabs=self._remove_tabs_cb.isChecked(),
        )
        self._viewmodel.apply_cleaning(options)

    def _on_find_clicked(self) -> None:
        """Find next occurrence of the search term in the editor."""
        term = self._find_edit.text()
        if not term:
            return
        found = self._plain_text_edit.find(term)
        if not found:
            # Wrap: move cursor to start and try again
            cursor = self._plain_text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._plain_text_edit.setTextCursor(cursor)
            self._plain_text_edit.find(term)

    def _on_replace_clicked(self) -> None:
        """Replace current selection if it matches, then find next."""
        find_term = self._find_edit.text()
        replace_term = self._replace_edit.text()
        if not find_term:
            return
        cursor = self._plain_text_edit.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == find_term:
            cursor.insertText(replace_term)
        self._on_find_clicked()

    def _on_replace_all_clicked(self) -> None:
        """Delegate replace-all to ViewModel (operates on stored content)."""
        self._viewmodel.replace_all(
            self._find_edit.text(), self._replace_edit.text()
        )

    # ------------------------------------------ ViewModel signal handlers

    def _on_document_loaded(self, content: str) -> None:
        self._plain_text_edit.setPlainText(content)

    def _on_encoding_detected(self, encoding: str) -> None:
        self._encoding_label.setText(encoding)

    def _on_file_saved(self, filepath: str) -> None:
        self.statusBar().showMessage(f"Saved: {filepath}")

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message, QMessageBox.StandardButton.Ok)

    def _on_status_changed(self, message: str) -> None:
        self.statusBar().showMessage(message)
```

**Step 2: Run tests to confirm nothing is broken**

```bash
.venv/bin/python -m pytest tests/unit/ -v
```

Expected: All unit tests still pass (view is not covered by unit tests — that's normal).

**Step 3: Smoke-test the app visually**

```bash
.venv/bin/python src/main.py
```

Expected: App launches with "TextTools" title bar, file tree showing home directory, all tabs visible.

**Step 4: Commit**

```bash
git add src/views/main_window.py
git commit -m "feat: rewrite MainWindow to wire real .ui widgets"
```

---

## Phase 6: Integration Tests

### Task 6.1: Rewrite integration tests

**File:** `tests/integration/test_application.py`

Replace entirely:

```python
"""Integration tests — real services, real models, mocked Qt.

These tests verify the full stack (FileService → ViewModel → signal) without
launching a real window. The view layer is excluded here; that's covered by
qt-pilot GUI tests.
"""
import pytest
from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.viewmodels.main_viewmodel import MainViewModel
from src.models.cleaning_options import CleaningOptions


@pytest.fixture
def file_svc():
    return FileService()


@pytest.fixture
def text_svc():
    return TextProcessingService()


@pytest.fixture
def vm(file_svc, text_svc, qapp):
    return MainViewModel(file_svc, text_svc)


class TestLoadSaveWorkflow:
    def test_load_real_file(self, vm, tmp_path, qtbot):
        f = tmp_path / "sample.txt"
        f.write_text("hello integration", encoding="utf-8")

        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file(str(f))

        assert blocker.args[0] == "hello integration"

    def test_save_then_reload(self, vm, tmp_path, qtbot):
        filepath = str(tmp_path / "out.txt")

        with qtbot.waitSignal(vm.file_saved, timeout=1000):
            vm.save_file(filepath, "saved content")

        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.load_file(filepath)

        assert blocker.args[0] == "saved content"


class TestCleaningWorkflow:
    def test_load_then_clean_then_save(self, vm, tmp_path, qtbot):
        f = tmp_path / "dirty.txt"
        f.write_text("\n  hello    world  \n\n", encoding="utf-8")

        # Load
        with qtbot.waitSignal(vm.document_loaded):
            vm.load_file(str(f))

        # Clean all options
        opts = CleaningOptions(
            trim_whitespace=True, clean_whitespace=True, remove_tabs=False
        )
        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.apply_cleaning(opts)

        cleaned = blocker.args[0]
        assert cleaned == "hello world"

        # Save cleaned result
        save_path = str(tmp_path / "clean.txt")
        with qtbot.waitSignal(vm.file_saved, timeout=1000):
            vm.save_file(save_path, cleaned)

        assert (tmp_path / "clean.txt").read_text(encoding="utf-8") == "hello world"


class TestReplaceAllWorkflow:
    def test_replace_all_end_to_end(self, vm, tmp_path, qtbot):
        f = tmp_path / "replace.txt"
        f.write_text("foo bar foo baz foo", encoding="utf-8")

        with qtbot.waitSignal(vm.document_loaded):
            vm.load_file(str(f))

        with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
            vm.replace_all("foo", "qux")

        assert blocker.args[0] == "qux bar qux baz qux"
```

**Step 2: Run**

```bash
.venv/bin/python -m pytest tests/integration/ -v
```

Expected: All integration tests pass.

**Step 3: Commit**

```bash
git add tests/integration/test_application.py
git commit -m "test: rewrite integration tests for real TextTools domain"
```

---

## Phase 7: GUI Tests (qt-pilot)

### Task 7.1: qt-pilot smoke test

This is an **interactive step** — Claude uses the qt-pilot MCP tools to drive the live application.

**Step 1: Launch the app**

Use `mcp__qt-pilot__launch_app` with:
- `module = "src.main"`
- `working_dir = "/home/chris/projects/TextTools"`
- `python_paths = ["/home/chris/projects/TextTools"]`

**Step 2: Capture initial screenshot**

Use `mcp__qt-pilot__capture_screenshot` and verify:
- Window title is "TextTools"
- File tree is visible in the left panel
- Three tabs visible (Clean, Merge, Find/Replace)
- Editor area is on the right

**Step 3: Create a test file and load it**

The test file will be created outside the app. Then use `mcp__qt-pilot__find_widgets` to confirm `plainTextEdit` is present, and verify the file tree shows the home directory.

**Step 4: Test find/replace tab**

- Click the Find/Replace tab
- Use `mcp__qt-pilot__click_widget` on `findLineEdit`
- Use `mcp__qt-pilot__type_text` to enter a search term
- Click `findButton`
- Capture screenshot to verify behavior

**Step 5: Test save with empty filepath**

- Click `saveButton` without entering a filepath
- Verify a warning dialog appears (screenshot)

**Step 6: Close app**

Use `mcp__qt-pilot__close_app`.

---

## Phase 8: Code Quality + Docs

### Task 8.1: Fix Python 3.14 type hints

In all source files, update:
- `Optional[X]` → `X | None` (also remove `Optional` imports from `typing`)
- `List[X]` → `list[X]` (also remove `List` imports)
- `from typing import List, Optional` → remove or keep only what's still needed (`Protocol`)

Files to check:
- `src/models/text_document.py` — already clean
- `src/models/cleaning_options.py` — already clean
- `src/services/file_service.py` — already clean
- `src/services/text_processing_service.py` — already clean
- `src/viewmodels/main_viewmodel.py` — already clean
- `src/views/main_window.py` — already clean

Run mypy to confirm:

```bash
.venv/bin/python -m mypy src/
```

Expected: `Success: no issues found`

**Commit:**

```bash
git add -A
git commit -m "chore: verify mypy clean, Python 3.14 type hints throughout"
```

---

### Task 8.2: Update `requirements.txt`

Add `chardet`:

```
# TextTools dependencies
PySide6>=6.8.0
chardet>=5.0.0
pytest>=8.3.0
pytest-qt>=4.4.0
pytest-mock>=3.14.0
pytest-cov>=5.0.0
```

Install and verify:

```bash
uv pip install chardet
.venv/bin/python -m pytest tests/ -v
```

**Commit:**

```bash
git add requirements.txt
git commit -m "deps: add chardet for encoding detection"
```

---

### Task 8.3: Update `README.md`

Replace the "Status" line and test command reference:

- Remove: `**Status**: Core MVVM framework is in place. Feature logic is under active development — see DESIGN.md for the full specification.`
- Replace with: `**Status**: Core features working — open/edit text files, apply whitespace cleaning, find/replace, save.`
- Update the single test file example to reference `test_text_document.py` (not the deleted `test_example_model.py`)

**Commit:**

```bash
git add README.md
git commit -m "docs: update README to reflect real TextTools feature state"
```

---

### Task 8.4: Update `CHANGELOG.md`

Add a `[0.2.0]` release entry above `[0.1.0]`:

```markdown
## [0.2.0] - 2026-02-21

### Added
- `TextDocument` model: filepath, content, encoding, modified flag
- `CleaningOptions` model: trim_whitespace, clean_whitespace, remove_tabs
- `FileService`: open/save text files with atomic write and chardet encoding detection
- `TextProcessingService`: trim, clean, remove-tabs operations and apply_options composition
- `MainViewModel`: real load_file, save_file, apply_cleaning, replace_all slots
- Main window wired to actual .ui widgets: file tree, editor, cleaning checkboxes, find/replace, save

### Changed
- Replaced `ExampleModel` / `ExampleService` scaffold with real TextTools domain classes
- `MainWindow` now connects file tree (QFileSystemModel), editor, and all tabs to ViewModel
- Removed console `app.log` file handler — logging goes to stdout only
- Window title corrected to "TextTools"

### Removed
- `ExampleModel`, `ExampleService`, `example_model.py`, `example_service.py`
- Internal AI agent configs from `.github/agents/`, `.github/chatmodes/`, `.github/prompts/`
- Template artifact docs: `docs/old/`, `docs/CUSTOMIZATION_CHECKLIST.md`
```

**Commit:**

```bash
git add CHANGELOG.md
git commit -m "docs: add 0.2.0 CHANGELOG entry for public release"
```

---

### Task 8.5: Final test run and coverage check

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected:
- All tests pass
- Coverage ≥ 80% for models and services (view/main.py remain low — acceptable)

```bash
.venv/bin/python -m mypy src/
```

Expected: `Success: no issues found`

**Final commit:**

```bash
git add -A
git commit -m "chore: final quality pass for public release v0.2.0"
```

---

## Coverage Targets

| File | Target |
|------|--------|
| `src/models/text_document.py` | 100% |
| `src/models/cleaning_options.py` | 100% |
| `src/services/text_processing_service.py` | 100% |
| `src/services/file_service.py` | 90%+ |
| `src/viewmodels/main_viewmodel.py` | 90%+ |
| `src/views/main_window.py` | via qt-pilot only |
| `src/main.py` | via qt-pilot only |

---

## Quick Reference: Key Widget ObjectNames

| Widget | objectName | Type |
|--------|-----------|------|
| File tree | `fileTreeView` | QTreeView |
| Editor | `plainTextEdit` | QPlainTextEdit |
| Filename field | `fileNameEdit` | QLineEdit |
| Save button | `saveButton` | QPushButton |
| Encoding label | `getEncodingFormatLabel` | QLabel |
| Convert button | `convertEncodingButton` | QPushButton |
| Trim checkbox | `trimWhiteSpaceCheckBox` | QCheckBox |
| Clean checkbox | `cleanWhiteSpaceCheckBox` | QCheckBox |
| Remove tabs checkbox | `removeTabsCheckBox` | QCheckBox |
| Find input | `findLineEdit` | QLineEdit |
| Find button | `findButton` | QPushButton |
| Replace input | `replaceLineEdit` | QLineEdit |
| Replace button | `replaceButton` | QPushButton |
| Replace all button | `replaceAllButton` | QPushButton |
