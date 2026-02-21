# TextTools Consolidation & Salvage Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strip all template/scaffolding code and replace it with real TextTools functionality as specified in DESIGN.md, following strict MVVM and TDD practices.

**Architecture:** The project was started from an MVVM desktop template. The Qt Designer UI (`main_window.ui`) is complete and matches the spec. All Python code (models, services, viewmodels, view) is still template boilerplate that references nonexistent widgets. This plan replaces every template Python file with real TextTools implementations, bottom-up (Models -> Services -> ViewModel -> View -> main.py).

**Tech Stack:** Python 3.14, PySide6 6.8+, chardet (encoding detection), pytest + pytest-qt (testing), mypy strict mode.

---

## Audit Summary: Current State

| Layer | File(s) | Status |
|-------|---------|--------|
| **UI** | `src/views/ui/main_window.ui` | **DONE** - Matches DESIGN.md spec |
| **Models** | `src/models/example_model.py` | Template - needs full replacement |
| **Services** | `src/services/example_service.py` | Template - needs full replacement |
| **ViewModels** | `src/viewmodels/main_viewmodel.py` | Template - needs full replacement |
| **Views** | `src/views/main_window.py` | Template - references wrong widgets, will crash |
| **Entry point** | `src/main.py` | Template - wrong app name, wires template classes |
| **Constants** | `src/utils/constants.py` | Template - wrong app name, wrong window size |
| **Tests** | `tests/unit/*.py`, `tests/integration/*.py` | Template - tests template code only |
| **Config** | `pyproject.toml`, `requirements.txt` | Incomplete - missing chardet, missing [project] section |
| **Docs** | `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | Template content - need TextTools rewrites |
| **Spec** | `DESIGN.md` | **DONE** - Comprehensive 1333-line specification |

**Key risk:** `main_window.py` looks for `loadButton`, `clearButton`, `listWidget`, `detailsText`, `statusLabel` — none of which exist in the .ui file. The app crashes on startup.

---

## Task 1: Fix Project Configuration & Dependencies

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`
- Modify: `src/utils/constants.py`
- Modify: `.github/workflows/ci.yml:18` (branch name)

**Step 1: Add missing dependencies to requirements.txt**

```txt
# Core
PySide6>=6.8.0
chardet>=5.2.0

# Testing
pytest>=8.3.0
pytest-qt>=4.4.0
pytest-mock>=3.14.0
pytest-cov>=5.0.0

# Development
black>=24.0.0
isort>=5.13.0
mypy>=1.8.0
```

**Step 2: Add [project] section to pyproject.toml**

Add at the top of `pyproject.toml`:

```toml
[project]
name = "texttools"
version = "0.1.0"
description = "Desktop text processing application for Linux"
requires-python = ">=3.14"
license = {text = "MIT"}
```

**Step 3: Fix constants.py**

```python
"""Application constants."""

APP_NAME = "TextTools"
APP_VERSION = "0.1.0"
APP_ORGANIZATION = "TextTools"

# Window defaults (match main_window.ui)
DEFAULT_WINDOW_WIDTH = 894
DEFAULT_WINDOW_HEIGHT = 830

# Supported file extensions for file tree filter
TEXT_FILE_EXTENSIONS = [".txt", ".md", ".log", ".csv", ".json", ".xml", ".html", ".css", ".py", ".js", ".ts", ".cfg", ".ini", ".yaml", ".yml", ".toml"]

# Encoding
DEFAULT_ENCODING = "utf-8"
```

**Step 4: Fix CI branch name**

In `.github/workflows/ci.yml`, change `develop` to `testing` in the branch triggers.

**Step 5: Install dependencies**

Run: `uv pip install chardet`

**Step 6: Commit**

```bash
git add requirements.txt pyproject.toml src/utils/constants.py .github/workflows/ci.yml
git commit -m "chore: fix project config, add chardet dependency, update constants"
```

---

## Task 2: Create TextDocument Model (TDD)

**Files:**
- Create: `src/models/text_document.py`
- Create: `tests/unit/test_text_document.py`

**Reference:** DESIGN.md Section 6.1 (lines 371-393)

**Step 1: Write the failing tests**

```python
"""Tests for TextDocument model."""
from src.models.text_document import TextDocument


class TestTextDocument:
    """Tests for the TextDocument dataclass."""

    def test_create_with_defaults(self) -> None:
        doc = TextDocument(filepath="/tmp/test.txt", content="hello")
        assert doc.filepath == "/tmp/test.txt"
        assert doc.content == "hello"
        assert doc.encoding == "utf-8"
        assert doc.modified is False

    def test_validate_returns_true_for_valid_filepath(self) -> None:
        doc = TextDocument(filepath="/tmp/test.txt", content="hello")
        assert doc.validate() is True

    def test_validate_returns_false_for_empty_filepath(self) -> None:
        doc = TextDocument(filepath="", content="hello")
        assert doc.validate() is False

    def test_modified_flag_can_be_set(self) -> None:
        doc = TextDocument(filepath="/tmp/test.txt", content="hello")
        doc.modified = True
        assert doc.modified is True

    def test_custom_encoding(self) -> None:
        doc = TextDocument(filepath="/tmp/test.txt", content="hello", encoding="iso-8859-1")
        assert doc.encoding == "iso-8859-1"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_text_document.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.models.text_document'`

**Step 3: Write minimal implementation**

```python
"""TextDocument model representing a loaded text file."""
from dataclasses import dataclass


@dataclass
class TextDocument:
    """Represents a text document with metadata.

    Attributes:
        filepath: Absolute path to the file on disk.
        content: The text content of the file.
        encoding: Detected or assigned character encoding.
        modified: Whether the content has been modified since last save.
    """

    filepath: str
    content: str
    encoding: str = "utf-8"
    modified: bool = False

    def validate(self) -> bool:
        """Validate that the document has a non-empty filepath."""
        return len(self.filepath) > 0
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_text_document.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add src/models/text_document.py tests/unit/test_text_document.py
git commit -m "feat: add TextDocument model with validation"
```

---

## Task 3: Create CleaningOptions Model (TDD)

**Files:**
- Create: `src/models/cleaning_options.py`
- Create: `tests/unit/test_cleaning_options.py`

**Reference:** DESIGN.md Section 6.1 (lines 387-393)

**Step 1: Write the failing tests**

```python
"""Tests for CleaningOptions model."""
from src.models.cleaning_options import CleaningOptions


class TestCleaningOptions:
    """Tests for the CleaningOptions dataclass."""

    def test_all_defaults_are_false(self) -> None:
        opts = CleaningOptions()
        assert opts.trim_whitespace is False
        assert opts.clean_whitespace is False
        assert opts.remove_tabs is False

    def test_any_enabled_returns_true_when_option_set(self) -> None:
        opts = CleaningOptions(trim_whitespace=True)
        assert opts.any_enabled() is True

    def test_any_enabled_returns_false_when_all_off(self) -> None:
        opts = CleaningOptions()
        assert opts.any_enabled() is False

    def test_multiple_options_can_be_set(self) -> None:
        opts = CleaningOptions(trim_whitespace=True, clean_whitespace=True, remove_tabs=True)
        assert opts.trim_whitespace is True
        assert opts.clean_whitespace is True
        assert opts.remove_tabs is True
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_cleaning_options.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""CleaningOptions model for text cleaning configuration."""
from dataclasses import dataclass


@dataclass
class CleaningOptions:
    """Configuration for text cleaning operations.

    Attributes:
        trim_whitespace: Remove leading/trailing whitespace from lines and document.
        clean_whitespace: Normalize multiple spaces to single space.
        remove_tabs: Remove tab characters and leading indentation.
    """

    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False

    def any_enabled(self) -> bool:
        """Check if any cleaning option is enabled."""
        return self.trim_whitespace or self.clean_whitespace or self.remove_tabs
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_cleaning_options.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/models/cleaning_options.py tests/unit/test_cleaning_options.py
git commit -m "feat: add CleaningOptions model"
```

---

## Task 4: Create TextProcessingService (TDD)

**Files:**
- Create: `src/services/text_processing_service.py`
- Create: `tests/unit/test_text_processing_service.py`

**Reference:** DESIGN.md Sections 8.2 (lines 915-934), F-002 (lines 537-573), F-003 (lines 577-609), F-004 (lines 613-638)

**Step 1: Write the failing tests**

```python
"""Tests for TextProcessingService."""
from src.services.text_processing_service import TextProcessingService
from src.models.cleaning_options import CleaningOptions


class TestTrimWhitespace:
    """Tests for trim_whitespace method."""

    def setup_method(self) -> None:
        self.service = TextProcessingService()

    def test_removes_leading_blank_lines(self) -> None:
        text = "\n\n\nhello\nworld"
        assert self.service.trim_whitespace(text) == "hello\nworld"

    def test_removes_trailing_blank_lines(self) -> None:
        text = "hello\nworld\n\n\n"
        assert self.service.trim_whitespace(text) == "hello\nworld"

    def test_strips_trailing_spaces_from_lines(self) -> None:
        text = "hello   \nworld   "
        assert self.service.trim_whitespace(text) == "hello\nworld"

    def test_preserves_internal_blank_lines(self) -> None:
        text = "hello\n\nworld"
        assert self.service.trim_whitespace(text) == "hello\n\nworld"

    def test_handles_empty_string(self) -> None:
        assert self.service.trim_whitespace("") == ""

    def test_handles_whitespace_only(self) -> None:
        assert self.service.trim_whitespace("   \n\n   ") == ""


class TestCleanWhitespace:
    """Tests for clean_whitespace method."""

    def setup_method(self) -> None:
        self.service = TextProcessingService()

    def test_reduces_multiple_spaces_to_single(self) -> None:
        assert self.service.clean_whitespace("hello    world") == "hello world"

    def test_converts_tabs_to_spaces(self) -> None:
        assert self.service.clean_whitespace("hello\tworld") == "hello world"

    def test_preserves_line_breaks(self) -> None:
        assert self.service.clean_whitespace("hello\nworld") == "hello\nworld"

    def test_handles_mixed_whitespace(self) -> None:
        assert self.service.clean_whitespace("hello \t  world") == "hello world"


class TestRemoveTabs:
    """Tests for remove_tabs method."""

    def setup_method(self) -> None:
        self.service = TextProcessingService()

    def test_removes_leading_tabs(self) -> None:
        assert self.service.remove_tabs("\thello") == "hello"

    def test_removes_leading_spaces(self) -> None:
        assert self.service.remove_tabs("    hello") == "hello"

    def test_removes_mixed_leading_whitespace(self) -> None:
        assert self.service.remove_tabs("\t  hello") == "hello"

    def test_preserves_paragraph_structure(self) -> None:
        text = "\thello\n\n\tworld"
        assert self.service.remove_tabs(text) == "hello\n\nworld"


class TestApplyCleaningOptions:
    """Tests for apply_cleaning_options method."""

    def setup_method(self) -> None:
        self.service = TextProcessingService()

    def test_no_options_returns_unchanged(self) -> None:
        opts = CleaningOptions()
        assert self.service.apply_cleaning_options("  hello  ", opts) == "  hello  "

    def test_applies_trim_only(self) -> None:
        opts = CleaningOptions(trim_whitespace=True)
        result = self.service.apply_cleaning_options("\n\nhello   \n\n", opts)
        assert result == "hello"

    def test_applies_all_options(self) -> None:
        opts = CleaningOptions(trim_whitespace=True, clean_whitespace=True, remove_tabs=True)
        result = self.service.apply_cleaning_options("\n\t hello    world  \n\n", opts)
        assert "  " not in result  # no double spaces
        assert "\t" not in result  # no tabs
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_text_processing_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""TextProcessingService for text cleaning operations."""
import re

from src.models.cleaning_options import CleaningOptions


class TextProcessingService:
    """Handles text cleaning and processing operations.

    All methods are pure functions operating on strings — no file I/O or Qt dependencies.
    """

    def trim_whitespace(self, text: str) -> str:
        """Remove leading/trailing blank lines and trailing spaces from each line.

        Algorithm from DESIGN.md F-002:
        1. Strip leading blank lines from document start
        2. Strip trailing blank lines from document end
        3. Strip trailing whitespace from each line
        """
        lines = text.splitlines()

        # Strip leading empty lines
        while lines and not lines[0].strip():
            lines.pop(0)
        # Strip trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in lines]

        return "\n".join(lines)

    def clean_whitespace(self, text: str) -> str:
        """Normalize whitespace: tabs to spaces, multiple spaces to single.

        Algorithm from DESIGN.md F-003.
        """
        text = text.replace("\t", " ")
        text = re.sub(r" {2,}", " ", text)
        return text

    def remove_tabs(self, text: str) -> str:
        """Remove tab characters and leading whitespace from lines.

        Algorithm from DESIGN.md F-004.
        """
        lines = text.splitlines()
        lines = [line.lstrip(" \t") for line in lines]
        return "\n".join(lines)

    def apply_cleaning_options(self, text: str, options: CleaningOptions) -> str:
        """Apply enabled cleaning operations in sequence.

        Order: remove_tabs -> clean_whitespace -> trim_whitespace
        (tabs first so clean_whitespace doesn't double-process)
        """
        if options.remove_tabs:
            text = self.remove_tabs(text)
        if options.clean_whitespace:
            text = self.clean_whitespace(text)
        if options.trim_whitespace:
            text = self.trim_whitespace(text)
        return text
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_text_processing_service.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/text_processing_service.py tests/unit/test_text_processing_service.py
git commit -m "feat: add TextProcessingService with trim, clean, and remove_tabs"
```

---

## Task 5: Create EncodingService (TDD)

**Files:**
- Create: `src/services/encoding_service.py`
- Create: `tests/unit/test_encoding_service.py`

**Reference:** DESIGN.md Section 8.2 (lines 897-913), F-001 (lines 508-534)

**Step 1: Write the failing tests**

```python
"""Tests for EncodingService."""
import os
import tempfile

from src.services.encoding_service import EncodingService


class TestDetectEncoding:
    """Tests for detect_encoding method."""

    def setup_method(self) -> None:
        self.service = EncodingService()

    def test_detects_utf8(self) -> None:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write("hello world".encode("utf-8"))
            filepath = f.name
        try:
            encoding = self.service.detect_encoding(filepath)
            assert encoding.lower().replace("-", "") in ("utf8", "ascii")
        finally:
            os.unlink(filepath)

    def test_detects_latin1(self) -> None:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write("caf\xe9".encode("iso-8859-1"))
            filepath = f.name
        try:
            encoding = self.service.detect_encoding(filepath)
            assert encoding.lower() in ("iso-8859-1", "windows-1252", "latin-1", "iso-8859-9", "ibm866")
        finally:
            os.unlink(filepath)

    def test_raises_for_missing_file(self) -> None:
        import pytest

        with pytest.raises(FileNotFoundError):
            self.service.detect_encoding("/nonexistent/file.txt")


class TestConvertToUtf8:
    """Tests for convert_to_utf8 method."""

    def setup_method(self) -> None:
        self.service = EncodingService()

    def test_converts_latin1_bytes_to_utf8_string(self) -> None:
        raw_bytes = "caf\xe9".encode("iso-8859-1")
        result = self.service.convert_to_utf8(raw_bytes, "iso-8859-1")
        assert result == "caf\xe9"
        assert isinstance(result, str)

    def test_utf8_passthrough(self) -> None:
        raw_bytes = "hello".encode("utf-8")
        result = self.service.convert_to_utf8(raw_bytes, "utf-8")
        assert result == "hello"


class TestIsValidEncoding:
    """Tests for is_valid_encoding method."""

    def setup_method(self) -> None:
        self.service = EncodingService()

    def test_utf8_is_valid(self) -> None:
        assert self.service.is_valid_encoding("utf-8") is True

    def test_nonsense_is_invalid(self) -> None:
        assert self.service.is_valid_encoding("not-a-real-encoding") is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_encoding_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""EncodingService for detecting and converting text encodings."""
import codecs
import logging

import chardet

logger = logging.getLogger(__name__)


class EncodingService:
    """Handles text encoding detection and conversion using chardet.

    No Qt dependencies — pure Python service.
    """

    def detect_encoding(self, filepath: str) -> str:
        """Detect the character encoding of a file.

        Args:
            filepath: Path to the file to analyze.

        Returns:
            Detected encoding name (e.g., 'utf-8', 'iso-8859-1').

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        with open(filepath, "rb") as f:
            raw_data = f.read()

        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8") or "utf-8"
        confidence = result.get("confidence", 0.0)

        logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.0%})")
        return encoding

    def convert_to_utf8(self, raw_bytes: bytes, source_encoding: str) -> str:
        """Convert raw bytes from source encoding to a UTF-8 Python string.

        Args:
            raw_bytes: The raw file bytes.
            source_encoding: The detected source encoding name.

        Returns:
            Decoded string (Python str is UTF-8 internally).
        """
        return raw_bytes.decode(source_encoding)

    def is_valid_encoding(self, encoding_name: str) -> bool:
        """Check whether an encoding name is recognized by Python."""
        try:
            codecs.lookup(encoding_name)
            return True
        except LookupError:
            return False
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_encoding_service.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/encoding_service.py tests/unit/test_encoding_service.py
git commit -m "feat: add EncodingService with chardet-based detection"
```

---

## Task 6: Create FileService (TDD)

**Files:**
- Create: `src/services/file_service.py`
- Create: `tests/unit/test_file_service.py`

**Reference:** DESIGN.md Section 8.2 (lines 876-895)

**Step 1: Write the failing tests**

```python
"""Tests for FileService."""
import os
import tempfile

import pytest

from src.services.file_service import FileService


class TestReadFile:
    """Tests for read_file method."""

    def setup_method(self) -> None:
        self.service = FileService()

    def test_reads_utf8_file(self, tmp_path: object) -> None:
        # tmp_path is a pytest fixture (pathlib.Path)
        f = tmp_path / "test.txt"  # type: ignore[operator]
        f.write_text("hello world", encoding="utf-8")  # type: ignore[union-attr]
        content = self.service.read_file(str(f))
        assert content == "hello world"

    def test_reads_file_with_encoding(self, tmp_path: object) -> None:
        f = tmp_path / "test.txt"  # type: ignore[operator]
        f.write_bytes("caf\xe9".encode("iso-8859-1"))  # type: ignore[union-attr]
        content = self.service.read_file(str(f), encoding="iso-8859-1")
        assert content == "caf\xe9"

    def test_raises_for_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            self.service.read_file("/nonexistent/file.txt")


class TestWriteFile:
    """Tests for write_file method."""

    def setup_method(self) -> None:
        self.service = FileService()

    def test_writes_file(self, tmp_path: object) -> None:
        f = tmp_path / "output.txt"  # type: ignore[operator]
        self.service.write_file(str(f), "hello world")
        assert f.read_text(encoding="utf-8") == "hello world"  # type: ignore[union-attr]

    def test_overwrites_existing_file(self, tmp_path: object) -> None:
        f = tmp_path / "output.txt"  # type: ignore[operator]
        f.write_text("old content", encoding="utf-8")  # type: ignore[union-attr]
        self.service.write_file(str(f), "new content")
        assert f.read_text(encoding="utf-8") == "new content"  # type: ignore[union-attr]


class TestReadFileRaw:
    """Tests for read_file_raw method."""

    def setup_method(self) -> None:
        self.service = FileService()

    def test_returns_bytes(self, tmp_path: object) -> None:
        f = tmp_path / "test.txt"  # type: ignore[operator]
        f.write_bytes(b"hello")  # type: ignore[union-attr]
        raw = self.service.read_file_raw(str(f))
        assert raw == b"hello"
        assert isinstance(raw, bytes)


class TestValidateFilepath:
    """Tests for validate_filepath method."""

    def setup_method(self) -> None:
        self.service = FileService()

    def test_valid_existing_file(self, tmp_path: object) -> None:
        f = tmp_path / "test.txt"  # type: ignore[operator]
        f.write_text("hi", encoding="utf-8")  # type: ignore[union-attr]
        assert self.service.validate_filepath(str(f)) is True

    def test_empty_path_is_invalid(self) -> None:
        assert self.service.validate_filepath("") is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_file_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""FileService for file I/O operations."""
import logging
import os

logger = logging.getLogger(__name__)


class FileService:
    """Handles all file system operations.

    No Qt dependencies — pure Python service.
    """

    def read_file(self, filepath: str, encoding: str = "utf-8") -> str:
        """Read file content as a decoded string.

        Args:
            filepath: Path to the file.
            encoding: Character encoding to use for decoding.

        Returns:
            File content as string.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        logger.info(f"Reading file: {filepath} (encoding: {encoding})")
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()

    def read_file_raw(self, filepath: str) -> bytes:
        """Read file content as raw bytes (for encoding detection).

        Args:
            filepath: Path to the file.

        Returns:
            Raw file bytes.
        """
        with open(filepath, "rb") as f:
            return f.read()

    def write_file(self, filepath: str, content: str, encoding: str = "utf-8") -> None:
        """Write string content to a file.

        Args:
            filepath: Destination file path.
            content: Text content to write.
            encoding: Character encoding to use.

        Raises:
            PermissionError: If the file cannot be written.
        """
        logger.info(f"Writing file: {filepath} (encoding: {encoding})")
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)

    def validate_filepath(self, filepath: str) -> bool:
        """Check if a filepath is non-empty and points to an existing file.

        Args:
            filepath: Path to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not filepath:
            return False
        return os.path.isfile(filepath)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_file_service.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/file_service.py tests/unit/test_file_service.py
git commit -m "feat: add FileService for file I/O operations"
```

---

## Task 7: Delete Template Code

**Files:**
- Delete: `src/models/example_model.py`
- Delete: `src/services/example_service.py`
- Delete: `tests/unit/test_example_model.py`

**Step 1: Delete the template files**

```bash
rm src/models/example_model.py
rm src/services/example_service.py
rm tests/unit/test_example_model.py
```

**Step 2: Run the new tests to confirm nothing is broken**

Run: `pytest tests/unit/test_text_document.py tests/unit/test_cleaning_options.py tests/unit/test_text_processing_service.py tests/unit/test_encoding_service.py tests/unit/test_file_service.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove template example_model and example_service"
```

---

## Task 8: Rewrite MainViewModel (TDD)

**Files:**
- Rewrite: `src/viewmodels/main_viewmodel.py`
- Rewrite: `tests/unit/test_main_viewmodel.py`

**Reference:** DESIGN.md Section 6.1 (lines 396-422), Section 8.5 (lines 1067-1077)

This is the largest task. The ViewModel mediates between all services and the view.

**Step 1: Write the failing tests**

```python
"""Tests for MainViewModel."""
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import SignalInstance

from src.models.cleaning_options import CleaningOptions
from src.viewmodels.main_viewmodel import MainViewModel


@pytest.fixture
def mock_file_service() -> MagicMock:
    service = MagicMock()
    service.read_file.return_value = "file content"
    service.read_file_raw.return_value = b"file content"
    service.validate_filepath.return_value = True
    return service


@pytest.fixture
def mock_encoding_service() -> MagicMock:
    service = MagicMock()
    service.detect_encoding.return_value = "utf-8"
    service.convert_to_utf8.return_value = "file content"
    service.is_valid_encoding.return_value = True
    return service


@pytest.fixture
def mock_text_processing_service() -> MagicMock:
    service = MagicMock()
    service.apply_cleaning_options.return_value = "cleaned content"
    return service


@pytest.fixture
def viewmodel(
    mock_file_service: MagicMock,
    mock_encoding_service: MagicMock,
    mock_text_processing_service: MagicMock,
) -> MainViewModel:
    return MainViewModel(
        file_service=mock_file_service,
        encoding_service=mock_encoding_service,
        text_processing_service=mock_text_processing_service,
    )


class TestLoadFile:
    """Tests for load_file method."""

    def test_emits_document_loaded_on_success(self, viewmodel: MainViewModel, qtbot: object) -> None:
        with qtbot.waitSignal(viewmodel.document_loaded):  # type: ignore[union-attr]
            viewmodel.load_file("/tmp/test.txt")

    def test_emits_encoding_detected_on_success(self, viewmodel: MainViewModel, qtbot: object) -> None:
        with qtbot.waitSignal(viewmodel.encoding_detected):  # type: ignore[union-attr]
            viewmodel.load_file("/tmp/test.txt")

    def test_emits_error_on_missing_file(
        self, viewmodel: MainViewModel, mock_file_service: MagicMock, qtbot: object
    ) -> None:
        mock_file_service.read_file_raw.side_effect = FileNotFoundError("not found")
        with qtbot.waitSignal(viewmodel.error_occurred):  # type: ignore[union-attr]
            viewmodel.load_file("/nonexistent.txt")


class TestSaveFile:
    """Tests for save_file method."""

    def test_emits_file_saved_on_success(self, viewmodel: MainViewModel, qtbot: object) -> None:
        viewmodel.load_file("/tmp/test.txt")  # load first to set current doc
        with qtbot.waitSignal(viewmodel.file_saved):  # type: ignore[union-attr]
            viewmodel.save_file("/tmp/test.txt", "new content")

    def test_emits_error_on_write_failure(
        self, viewmodel: MainViewModel, mock_file_service: MagicMock, qtbot: object
    ) -> None:
        mock_file_service.write_file.side_effect = PermissionError("denied")
        with qtbot.waitSignal(viewmodel.error_occurred):  # type: ignore[union-attr]
            viewmodel.save_file("/tmp/test.txt", "content")


class TestCleanText:
    """Tests for clean_text method."""

    def test_calls_service_with_options(
        self, viewmodel: MainViewModel, mock_text_processing_service: MagicMock
    ) -> None:
        opts = CleaningOptions(trim_whitespace=True)
        viewmodel.clean_text("  hello  ", opts)
        mock_text_processing_service.apply_cleaning_options.assert_called_once_with("  hello  ", opts)

    def test_emits_text_cleaned_signal(self, viewmodel: MainViewModel, qtbot: object) -> None:
        opts = CleaningOptions(trim_whitespace=True)
        with qtbot.waitSignal(viewmodel.text_cleaned):  # type: ignore[union-attr]
            viewmodel.clean_text("  hello  ", opts)


class TestFindText:
    """Tests for find/replace methods."""

    def test_find_text_emits_signal(self, viewmodel: MainViewModel, qtbot: object) -> None:
        with qtbot.waitSignal(viewmodel.text_found):  # type: ignore[union-attr]
            viewmodel.find_text("hello world here hello", "hello", 0)

    def test_find_text_returns_position(self, viewmodel: MainViewModel) -> None:
        pos = viewmodel.find_text("hello world", "world", 0)
        assert pos == 6

    def test_find_text_returns_neg1_when_not_found(self, viewmodel: MainViewModel) -> None:
        pos = viewmodel.find_text("hello world", "xyz", 0)
        assert pos == -1

    def test_replace_all_returns_count(self, viewmodel: MainViewModel) -> None:
        result, count = viewmodel.replace_all("hello hello hello", "hello", "hi")
        assert result == "hi hi hi"
        assert count == 3
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_main_viewmodel.py -v`
Expected: FAIL (old template imports will fail after Task 7 deletes template code)

**Step 3: Write the implementation**

```python
"""MainViewModel — presentation logic for the TextTools main window."""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from src.models.cleaning_options import CleaningOptions
from src.models.text_document import TextDocument

logger = logging.getLogger(__name__)


class MainViewModel(QObject):
    """Main window presentation logic.

    Mediates between the View (main_window.py) and the Service layer.
    All communication with the View is via Qt Signals.

    Signals:
        document_loaded: Emitted with file content after a file is loaded.
        encoding_detected: Emitted with the encoding name after detection.
        file_saved: Emitted with the filepath after a successful save.
        text_cleaned: Emitted with cleaned text after a cleaning operation.
        text_found: Emitted with (position, length) when find locates a match.
        error_occurred: Emitted with an error message string.
    """

    document_loaded = Signal(str)
    encoding_detected = Signal(str)
    file_saved = Signal(str)
    text_cleaned = Signal(str)
    text_found = Signal(int, int)  # position, length
    error_occurred = Signal(str)

    def __init__(
        self,
        file_service: object,
        encoding_service: object,
        text_processing_service: object,
    ) -> None:
        super().__init__()
        self._file_service = file_service
        self._encoding_service = encoding_service
        self._text_processing_service = text_processing_service
        self._current_document: Optional[TextDocument] = None

    @Slot(str)
    def load_file(self, filepath: str) -> None:
        """Load a file: read raw bytes, detect encoding, decode, emit signals."""
        try:
            raw_bytes = self._file_service.read_file_raw(filepath)
            encoding = self._encoding_service.detect_encoding(filepath)
            content = self._encoding_service.convert_to_utf8(raw_bytes, encoding)

            self._current_document = TextDocument(
                filepath=filepath, content=content, encoding=encoding
            )

            self.encoding_detected.emit(encoding)
            self.document_loaded.emit(content)
            logger.info(f"Loaded: {filepath} ({encoding})")
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            self.error_occurred.emit(str(e))

    @Slot(str, str)
    def save_file(self, filepath: str, content: str) -> None:
        """Save content to a file path."""
        try:
            self._file_service.write_file(filepath, content)

            if self._current_document:
                self._current_document.filepath = filepath
                self._current_document.content = content
                self._current_document.modified = False

            self.file_saved.emit(filepath)
            logger.info(f"Saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            self.error_occurred.emit(str(e))

    def clean_text(self, text: str, options: CleaningOptions) -> str:
        """Apply cleaning options to text and emit the result."""
        cleaned = self._text_processing_service.apply_cleaning_options(text, options)
        self.text_cleaned.emit(cleaned)
        return cleaned

    def find_text(self, text: str, search_term: str, start_pos: int) -> int:
        """Find the next occurrence of search_term in text from start_pos.

        Returns:
            Position of the match, or -1 if not found.
        """
        pos = text.find(search_term, start_pos)
        if pos >= 0:
            self.text_found.emit(pos, len(search_term))
        return pos

    def replace_all(self, text: str, find: str, replace: str) -> tuple[str, int]:
        """Replace all occurrences of find with replace.

        Returns:
            Tuple of (new_text, replacement_count).
        """
        count = text.count(find)
        new_text = text.replace(find, replace)
        return new_text, count

    @property
    def current_document(self) -> Optional[TextDocument]:
        """The currently loaded document, if any."""
        return self._current_document
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_main_viewmodel.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/viewmodels/main_viewmodel.py tests/unit/test_main_viewmodel.py
git commit -m "feat: rewrite MainViewModel for TextTools with file/encoding/cleaning/find"
```

---

## Task 9: Rewrite MainWindow View

**Files:**
- Rewrite: `src/views/main_window.py`

**Reference:** DESIGN.md Section 6.1 (lines 424-448), Appendix A (lines 1175-1252)

This task replaces the template view code with proper widget connections to `main_window.ui`.

**Step 1: Write the implementation**

Note: View layer code is harder to TDD directly since it involves Qt widget interactions. We test it via integration tests in a later task.

```python
"""MainWindow — View layer for TextTools.

Loads the UI from Qt Designer and connects widgets to the MainViewModel via signals.
No business logic lives here — only UI wiring and display updates.
"""
import os
import logging

from PySide6.QtCore import QFile, QModelIndex
from PySide6.QtGui import QTextCursor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTreeView,
)

from PySide6.QtWidgets import QFileSystemModel

from src.models.cleaning_options import CleaningOptions
from src.viewmodels.main_viewmodel import MainViewModel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window.

    Loads main_window.ui via QUiLoader and wires all widgets
    to the MainViewModel using Qt signal/slot connections.
    """

    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel
        self._load_ui()
        self._setup_file_tree()
        self._connect_signals()

    def _load_ui(self) -> None:
        """Load the .ui file and grab widget references by objectName."""
        ui_file_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QFile.ReadOnly):  # type: ignore[arg-type]
            raise RuntimeError(f"Cannot open UI file: {ui_file_path}")

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.setCentralWidget(self.ui)

        # Right panel — editor
        self._plain_text_edit: QPlainTextEdit = self.ui.findChild(QPlainTextEdit, "plainTextEdit")  # type: ignore[assignment]
        self._file_name_edit: QLineEdit = self.ui.findChild(QLineEdit, "fileNameEdit")  # type: ignore[assignment]
        self._save_button: QPushButton = self.ui.findChild(QPushButton, "saveButton")  # type: ignore[assignment]

        # Clean tab — encoding
        self._encoding_label: QLabel = self.ui.findChild(QLabel, "getEncodingFormatLabel")  # type: ignore[assignment]
        self._convert_button: QPushButton = self.ui.findChild(QPushButton, "convertEncodingButton")  # type: ignore[assignment]

        # Clean tab — formatting checkboxes
        self._trim_checkbox: QCheckBox = self.ui.findChild(QCheckBox, "trimWhiteSpaceCheckBox")  # type: ignore[assignment]
        self._clean_checkbox: QCheckBox = self.ui.findChild(QCheckBox, "cleanWhiteSpaceCheckBox")  # type: ignore[assignment]
        self._remove_tabs_checkbox: QCheckBox = self.ui.findChild(QCheckBox, "removeTabsCheckBox")  # type: ignore[assignment]

        # Find/Replace tab
        self._find_line_edit: QLineEdit = self.ui.findChild(QLineEdit, "findLineEdit")  # type: ignore[assignment]
        self._find_button: QPushButton = self.ui.findChild(QPushButton, "findButton")  # type: ignore[assignment]
        self._replace_line_edit: QLineEdit = self.ui.findChild(QLineEdit, "replaceLineEdit")  # type: ignore[assignment]
        self._replace_button: QPushButton = self.ui.findChild(QPushButton, "replaceButton")  # type: ignore[assignment]
        self._replace_all_button: QPushButton = self.ui.findChild(QPushButton, "replaceAllButton")  # type: ignore[assignment]

        # File tree
        self._file_tree_view: QTreeView = self.ui.findChild(QTreeView, "fileTreeView")  # type: ignore[assignment]

    def _setup_file_tree(self) -> None:
        """Configure the file tree view with a QFileSystemModel."""
        self._fs_model = QFileSystemModel()
        home_dir = os.path.expanduser("~")
        self._fs_model.setRootPath(home_dir)
        self._file_tree_view.setModel(self._fs_model)
        self._file_tree_view.setRootIndex(self._fs_model.index(home_dir))
        # Hide size, type, date columns — show only name
        for col in range(1, self._fs_model.columnCount()):
            self._file_tree_view.setColumnHidden(col, True)

    def _connect_signals(self) -> None:
        """Wire all widget signals to ViewModel methods and vice versa."""
        # --- View -> ViewModel ---
        self._save_button.clicked.connect(self._on_save_clicked)
        self._convert_button.clicked.connect(self._on_convert_clicked)
        self._find_button.clicked.connect(self._on_find_clicked)
        self._replace_button.clicked.connect(self._on_replace_clicked)
        self._replace_all_button.clicked.connect(self._on_replace_all_clicked)
        self._file_tree_view.clicked.connect(self._on_tree_item_clicked)

        # Checkboxes trigger cleaning immediately when toggled
        self._trim_checkbox.stateChanged.connect(self._on_clean_option_changed)
        self._clean_checkbox.stateChanged.connect(self._on_clean_option_changed)
        self._remove_tabs_checkbox.stateChanged.connect(self._on_clean_option_changed)

        # --- ViewModel -> View ---
        self._viewmodel.document_loaded.connect(self._on_document_loaded)
        self._viewmodel.encoding_detected.connect(self._on_encoding_detected)
        self._viewmodel.file_saved.connect(self._on_file_saved)
        self._viewmodel.text_cleaned.connect(self._on_text_cleaned)
        self._viewmodel.error_occurred.connect(self._on_error)

    # ── Slot handlers: View -> ViewModel ──────────────────────────

    def _on_tree_item_clicked(self, index: QModelIndex) -> None:
        filepath = self._fs_model.filePath(index)
        if os.path.isfile(filepath):
            self._viewmodel.load_file(filepath)

    def _on_save_clicked(self) -> None:
        filepath = self._file_name_edit.text()
        content = self._plain_text_edit.toPlainText()
        if filepath:
            self._viewmodel.save_file(filepath, content)

    def _on_convert_clicked(self) -> None:
        """Re-load current file as UTF-8 conversion."""
        doc = self._viewmodel.current_document
        if doc:
            self._viewmodel.load_file(doc.filepath)

    def _on_clean_option_changed(self) -> None:
        """Apply currently-checked cleaning options to editor content."""
        options = CleaningOptions(
            trim_whitespace=self._trim_checkbox.isChecked(),
            clean_whitespace=self._clean_checkbox.isChecked(),
            remove_tabs=self._remove_tabs_checkbox.isChecked(),
        )
        if options.any_enabled():
            text = self._plain_text_edit.toPlainText()
            self._viewmodel.clean_text(text, options)

    def _on_find_clicked(self) -> None:
        search_term = self._find_line_edit.text()
        if not search_term:
            return
        text = self._plain_text_edit.toPlainText()
        cursor = self._plain_text_edit.textCursor()
        start = cursor.position()
        pos = self._viewmodel.find_text(text, search_term, start)
        if pos >= 0:
            cursor = self._plain_text_edit.textCursor()
            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_term))
            self._plain_text_edit.setTextCursor(cursor)
        elif start > 0:
            # Wrap around from beginning
            pos = self._viewmodel.find_text(text, search_term, 0)
            if pos >= 0:
                cursor = self._plain_text_edit.textCursor()
                cursor.setPosition(pos)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_term))
                self._plain_text_edit.setTextCursor(cursor)

    def _on_replace_clicked(self) -> None:
        cursor = self._plain_text_edit.textCursor()
        if cursor.hasSelection():
            replacement = self._replace_line_edit.text()
            cursor.insertText(replacement)
            self._plain_text_edit.setTextCursor(cursor)
        # Find next after replace
        self._on_find_clicked()

    def _on_replace_all_clicked(self) -> None:
        find_term = self._find_line_edit.text()
        replace_term = self._replace_line_edit.text()
        if not find_term:
            return
        text = self._plain_text_edit.toPlainText()
        new_text, count = self._viewmodel.replace_all(text, find_term, replace_term)
        self._plain_text_edit.setPlainText(new_text)
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")

    # ── Slot handlers: ViewModel -> View ──────────────────────────

    def _on_document_loaded(self, content: str) -> None:
        self._plain_text_edit.setPlainText(content)
        doc = self._viewmodel.current_document
        if doc:
            self._file_name_edit.setText(doc.filepath)

    def _on_encoding_detected(self, encoding: str) -> None:
        self._encoding_label.setText(encoding)

    def _on_file_saved(self, filepath: str) -> None:
        logger.info(f"File saved: {filepath}")

    def _on_text_cleaned(self, cleaned_text: str) -> None:
        self._plain_text_edit.setPlainText(cleaned_text)

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
```

**Step 2: Verify it loads without crashing**

Run: `python src/main.py` (after Task 10 rewires main.py)

**Step 3: Commit**

```bash
git add src/views/main_window.py
git commit -m "feat: rewrite MainWindow view to connect to actual UI widgets"
```

---

## Task 10: Rewire main.py Entry Point

**Files:**
- Rewrite: `src/main.py`

**Step 1: Rewrite the entry point**

```python
"""TextTools application entry point."""
import sys
import logging

from PySide6.QtWidgets import QApplication

from src.services.encoding_service import EncodingService
from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.utils.constants import APP_NAME, APP_ORGANIZATION
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("texttools.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def create_application() -> MainWindow:
    """Create and configure the application via dependency injection.

    Services (bottom) -> ViewModel (middle) -> View (top).
    """
    file_service = FileService()
    encoding_service = EncodingService()
    text_processing_service = TextProcessingService()

    main_viewmodel = MainViewModel(
        file_service=file_service,
        encoding_service=encoding_service,
        text_processing_service=text_processing_service,
    )

    main_window = MainWindow(main_viewmodel)
    return main_window


def main() -> None:
    """Application entry point."""
    logger.info("Starting TextTools")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)

    main_window = create_application()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 2: Run the application to verify it starts without crashing**

Run: `python src/main.py`
Expected: Window opens with file tree, tabs, text editor — no crash.

**Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: rewire main.py to use real TextTools services"
```

---

## Task 11: Write Integration Tests

**Files:**
- Rewrite: `tests/integration/test_application.py`

**Step 1: Write integration tests for key workflows**

```python
"""Integration tests for TextTools application."""
import os

import pytest

from src.services.encoding_service import EncodingService
from src.services.file_service import FileService
from src.services.text_processing_service import TextProcessingService
from src.models.cleaning_options import CleaningOptions
from src.viewmodels.main_viewmodel import MainViewModel


class TestFileLoadAndSaveWorkflow:
    """Test loading a file, modifying it, and saving."""

    def test_load_and_save_round_trip(self, tmp_path: object, qtbot: object) -> None:
        """Load a file, verify content, save to new location."""
        # Arrange
        src_file = tmp_path / "source.txt"  # type: ignore[operator]
        src_file.write_text("hello world", encoding="utf-8")  # type: ignore[union-attr]
        dest_file = tmp_path / "dest.txt"  # type: ignore[operator]

        file_svc = FileService()
        enc_svc = EncodingService()
        text_svc = TextProcessingService()
        vm = MainViewModel(file_svc, enc_svc, text_svc)

        # Act — load
        with qtbot.waitSignal(vm.document_loaded):  # type: ignore[union-attr]
            vm.load_file(str(src_file))

        assert vm.current_document is not None
        assert vm.current_document.content == "hello world"

        # Act — save
        with qtbot.waitSignal(vm.file_saved):  # type: ignore[union-attr]
            vm.save_file(str(dest_file), "hello world")

        # Assert
        assert dest_file.read_text(encoding="utf-8") == "hello world"  # type: ignore[union-attr]


class TestCleaningWorkflow:
    """Test text cleaning through the ViewModel."""

    def test_clean_text_with_all_options(self, qtbot: object) -> None:
        file_svc = FileService()
        enc_svc = EncodingService()
        text_svc = TextProcessingService()
        vm = MainViewModel(file_svc, enc_svc, text_svc)

        dirty_text = "\n\n\t hello    world  \n\n"
        options = CleaningOptions(trim_whitespace=True, clean_whitespace=True, remove_tabs=True)

        with qtbot.waitSignal(vm.text_cleaned):  # type: ignore[union-attr]
            result = vm.clean_text(dirty_text, options)

        assert "\t" not in result
        assert "  " not in result


class TestFindReplaceWorkflow:
    """Test find and replace operations."""

    def test_find_and_replace_all(self) -> None:
        file_svc = FileService()
        enc_svc = EncodingService()
        text_svc = TextProcessingService()
        vm = MainViewModel(file_svc, enc_svc, text_svc)

        text = "the cat sat on the mat"
        new_text, count = vm.replace_all(text, "the", "a")
        assert new_text == "a cat sat on a mat"
        assert count == 2
```

**Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All unit and integration tests PASS

**Step 3: Commit**

```bash
git add tests/integration/test_application.py
git commit -m "feat: rewrite integration tests for TextTools workflows"
```

---

## Task 12: Clean Up Template Documentation

**Files:**
- Rewrite: `README.md` (replace template content with TextTools description)
- Rewrite: `CHANGELOG.md` (start fresh from v0.1.0)
- Delete or update: `docs/CUSTOMIZATION_CHECKLIST.md` (template artifact)
- Delete or update: `docs/QUICKSTART.md` (template artifact)
- Delete or update: `docs/QUICKSTART_UI_UV.md` (template artifact)

**Step 1: Rewrite README.md**

Replace the entire README with a TextTools-specific version including:
- Project name and description
- Screenshot placeholder
- Installation instructions (uv + chardet)
- Usage instructions
- Architecture overview (MVVM)
- Development setup (pytest, mypy, black, isort)
- License

**Step 2: Reset CHANGELOG.md**

```markdown
# Changelog

## [0.1.0] - 2026-02-04

### Added
- Project structure with MVVM architecture
- Qt Designer UI (main_window.ui) with Clean, Merge, Find/Replace tabs
- TextDocument and CleaningOptions models
- FileService, EncodingService, TextProcessingService
- MainViewModel with file load/save, text cleaning, find/replace
- MainWindow view wired to all UI widgets
- Comprehensive test suite (unit + integration)
- DESIGN.md specification document
```

**Step 3: Remove template docs from docs/**

```bash
rm docs/CUSTOMIZATION_CHECKLIST.md
rm -rf docs/old/
```

Keep `docs/UI_DESIGN_GUIDE.md` if it's TextTools-specific; delete if template.

**Step 4: Commit**

```bash
git add -A
git commit -m "docs: replace template documentation with TextTools content"
```

---

## Task 13: Run Full Verification

**Step 1: Run all tests with coverage**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests pass, coverage ≥ 80% on new code.

**Step 2: Run type checker**

Run: `mypy src/`
Expected: No errors (or only PySide6-related ignores).

**Step 3: Run formatters**

```bash
black src/ tests/ --check
isort src/ tests/ --check
```

**Step 4: Launch the application**

Run: `python src/main.py`
Expected: Window opens. File tree shows home directory. Clicking a text file loads it into the editor. Save button works. Find/replace works. Cleaning checkboxes work.

**Step 5: Fix any issues found, then final commit**

```bash
git add -A
git commit -m "chore: final verification pass — all tests, types, and formatting clean"
```

---

## Summary of Files Changed

### Created (new)
| File | Purpose |
|------|---------|
| `src/models/text_document.py` | TextDocument dataclass |
| `src/models/cleaning_options.py` | CleaningOptions dataclass |
| `src/services/file_service.py` | File read/write operations |
| `src/services/encoding_service.py` | chardet-based encoding detection |
| `src/services/text_processing_service.py` | Text cleaning algorithms |
| `tests/unit/test_text_document.py` | Model tests |
| `tests/unit/test_cleaning_options.py` | Model tests |
| `tests/unit/test_file_service.py` | Service tests |
| `tests/unit/test_encoding_service.py` | Service tests |
| `tests/unit/test_text_processing_service.py` | Service tests |

### Rewritten (replaced template content)
| File | What changed |
|------|-------------|
| `src/main.py` | Wires real services instead of ExampleService |
| `src/viewmodels/main_viewmodel.py` | TextTools ViewModel with file/encoding/cleaning/find |
| `src/views/main_window.py` | Connects to actual .ui widgets |
| `src/utils/constants.py` | Correct app name, window size, file extensions |
| `tests/unit/test_main_viewmodel.py` | Tests real ViewModel |
| `tests/integration/test_application.py` | Tests real workflows |
| `README.md` | TextTools description |
| `CHANGELOG.md` | Fresh changelog |

### Deleted (template artifacts)
| File | Reason |
|------|--------|
| `src/models/example_model.py` | Template scaffolding |
| `src/services/example_service.py` | Template scaffolding |
| `tests/unit/test_example_model.py` | Tests template code |
| `docs/CUSTOMIZATION_CHECKLIST.md` | Template doc |
| `docs/old/` | Template docs |

### Modified (config fixes)
| File | What changed |
|------|-------------|
| `requirements.txt` | Added chardet, black, isort, mypy |
| `pyproject.toml` | Added [project] section |
| `.github/workflows/ci.yml` | Fixed branch name |
