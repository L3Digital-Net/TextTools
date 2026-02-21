# TextTools - Application Design Document

## Document Information

**Document Version**: 1.0
**Date**: November 5, 2025
**Application Name**: TextTools
**Framework**: PySide6 (Qt for Python)
**Architecture**: MVVM (Model-View-ViewModel)
**Platform**: Linux

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Application Overview](#application-overview)
3. [User Interface Architecture](#user-interface-architecture)
4. [Functional Modules](#functional-modules)
5. [UI Component Specifications](#ui-component-specifications)
6. [Data Flow and Architecture](#data-flow-and-architecture)
7. [Feature Specifications](#feature-specifications)
8. [Technical Implementation Details](#technical-implementation-details)
9. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

TextTools is a desktop text processing application designed for Linux systems. The application provides text cleaning, file merging, and find/replace functionality through an intuitive split-panel interface. Built using PySide6 with strict MVVM architecture, the application emphasizes maintainability, testability, and extensibility.

### Key Features

- **Text Encoding Conversion**: UTF-8 encoding conversion with format detection
- **Text Formatting**: Whitespace cleaning, tab removal, and text normalization
- **File Management**: File tree browser with multi-file selection
- **Find/Replace**: Advanced text search and replacement
- **File Merging**: Multi-file merge capabilities (planned)
- **Real-time Preview**: Live text editing with immediate feedback

---

## 2. Application Overview

### 2.1 Purpose

TextTools is designed to solve common text processing challenges faced by users working with multiple text files, particularly when dealing with:

- Mixed text encodings requiring standardization
- Inconsistent whitespace and formatting
- Need to search/replace across large documents
- File merging and consolidation tasks

### 2.2 Target Users

- **Content Writers**: Authors working with multiple text documents
- **Developers**: Engineers processing log files or code snippets
- **Data Processors**: Analysts cleaning text data
- **Editors**: Content managers standardizing text formats

### 2.3 Design Philosophy

The application follows these core principles:

1. **Separation of Concerns**: MVVM architecture ensures UI, logic, and data remain independent
2. **UI from Designer**: All layouts created in Qt Designer (.ui files), never hardcoded
3. **Testability**: Every component can be unit tested independently
4. **Extensibility**: New features can be added without modifying existing code
5. **SOLID Principles**: Each class has a single responsibility and clear interfaces

---

## 3. User Interface Architecture

### 3.1 Main Window Layout

```text
┌─────────────────────────────────────────────────────────────────┐
│ File    Edit    Help                                   [Menu Bar]│
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┬──────────────────────────────────┐    │
│  │  LEFT PANEL          │  RIGHT PANEL                     │    │
│  │                      │                                  │    │
│  │  ┌────────────────┐  │  ┌────────────────────────────┐ │    │
│  │  │ Tab Widget     │  │  │ File Name: [_____] [Save]  │ │    │
│  │  │ Clean | Merge  │  │  ├────────────────────────────┤ │    │
│  │  │   Find/Replace │  │  │                            │ │    │
│  │  │                │  │  │   Text Editor              │ │    │
│  │  │ [Tab Contents] │  │  │   (PlainTextEdit)          │ │    │
│  │  │                │  │  │                            │ │    │
│  │  └────────────────┘  │  │                            │ │    │
│  │  ───────────────────  │  │                            │ │    │
│  │  ┌────────────────┐  │  └────────────────────────────┘ │    │
│  │  │ File Tree View │  │                                  │    │
│  │  │ (Resizable)    │  │                                  │    │
│  │  └────────────────┘  │                                  │    │
│  └──────────────────────┴──────────────────────────────────┘    │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Status Bar                                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Window Specifications

- **Default Size**: 894x830 pixels
- **Resizable**: Yes (both horizontal and vertical)
- **Minimum Size**: None specified (to be determined)
- **Layout**: Horizontal splitter dividing left panel (tools) and right panel (editor)

### 3.3 Panel Organization

#### Left Panel (Tool Panel)

- **Top Section**: Tabbed interface for different tools
  - Clean tab (text formatting options)
  - Merge tab (file merging - under development)
  - Find/Replace tab (search functionality)
- **Bottom Section**: File tree view (collapsible/resizable)
- **Splitter**: Vertical splitter allows resizing between tabs and file tree

#### Right Panel (Editor Panel)

- **Top Section**: File name display and Save button
- **Main Section**: Large text editor (QPlainTextEdit)
- **Purpose**: Primary workspace for viewing and editing text

---

## 4. Functional Modules

### 4.1 Module Overview

| Module | Status | Description |
|--------|--------|-------------|
| Text Cleaning | Active | Encoding conversion, whitespace formatting |
| File Browser | Active | File tree navigation and selection |
| Find/Replace | Active | Text search and replacement functionality |
| File Merge | Planned | Multi-file consolidation (UI prepared) |
| Text Editor | Active | Main editing workspace with save functionality |

### 4.2 Module Dependencies

```text
┌──────────────────────────────────────────┐
│         Main Window (View)               │
│  ┌────────────────────────────────────┐  │
│  │  MainViewModel (Presentation)      │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │    Services Layer            │  │  │
│  │  │  - FileService               │  │  │
│  │  │  - TextProcessingService     │  │  │
│  │  │  - EncodingService           │  │  │
│  │  └──────────────────────────────┘  │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │    Models Layer              │  │  │
│  │  │  - TextDocument              │  │  │
│  │  │  - FileItem                  │  │  │
│  │  │  - CleaningOptions           │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 5. UI Component Specifications

### 5.1 Menu Bar

#### File Menu

- **Open** (`actionOpen`): Open file(s) for editing
- **Save** (`actionSave`): Save current document
- **Save As...** (`actionSave_as`): Save document with new name
- **Preferences** (`actionPreferences`): Application settings
- **Quit** (`actionQuit`): Exit application

#### Edit Menu

- Currently empty (placeholder for future editing operations)

#### Help Menu

- **About** (`actionAbout`): Display application information

### 5.2 Clean Tab Components

#### Encoding Conversion Section

```text
┌──────────────────────────────────────────┐
│  Convert Encoding to UTF-8 (Header)      │
├──────────────────────────────────────────┤
│  Current format: [GET ENCODING] [Convert]│
└──────────────────────────────────────────┘
```

**Components**:

- `encodingConvertHeaderLabel`: Bold header text
- `convertEncodingContainer`: Container widget
- `currentFormatLabel`: Static label "Current format:"
- `getEncodingFormatLabel`: Dynamic label showing detected encoding
- `convertEncodingButton`: Action button to perform conversion

**Functionality**:

- Detects current file encoding automatically
- Displays detected encoding in real-time
- One-click conversion to UTF-8
- Updates editor content after conversion

#### Formatting Options Section

```text
┌──────────────────────────────────────────┐
│      Formatting Options (Header)         │
├──────────────────────────────────────────┤
│  ☐ Trim whitespace      ☐ [Placeholder]  │
│  ☐ Clean whitespace     ☐ [Placeholder]  │
│  ☐ Remove tabs          ☐ [Placeholder]  │
└──────────────────────────────────────────┘
```

**Components**:

- `formattingOptionsHeaderLabel`: Bold header text
- `formatOptionsContainer`: Grid layout container
- `trimWhiteSpaceCheckBox`: Remove leading/trailing spaces
- `cleanWhiteSpaceCheckBox`: Normalize multiple spaces
- `removeTabsCheckBox`: Remove tab characters
- `checkBox_2`, `checkBox_4`, `checkBox_6`: Placeholder checkboxes (to be implemented)

**Layout**: Grid layout (3 rows x 3 columns) with 6px left margin

**Tooltips**:

- **Trim whitespace**: "Remove extra linebreaks at beginning and end of document. Remove spaces and tabs at the beginning and ends of paragraphs."
- **Clean whitespace**: "Removes extra whitespace between words, i.e. convert two spaces to one space"
- **Remove tabs**: "Remove tabs and spaces at the beginning of paragraphs"

### 5.3 Merge Tab Components

**Status**: UI prepared, functionality not implemented

```text
┌──────────────────────────────────────────┐
│         (Empty - To Be Designed)         │
│                                          │
│  [Future merge configuration UI]        │
└──────────────────────────────────────────┘
```

**Components**:

- `mergeScrollArea`: Scroll container
- `mergeScrollContents`: Content widget
- `mergeTabScrollLayout`: Grid layout (empty)

**Planned Features**:

- File selection for merging
- Merge order configuration
- Delimiter options
- Preview merged result

### 5.4 Find/Replace Tab Components

```text
┌──────────────────────────────────────────┐
│  Find:                                   │
│  [___________________] [Find Next]       │
│                                          │
│  Replace with:                           │
│  [___________________] [Replace]         │
│                                          │
│         [Replace All]                    │
└──────────────────────────────────────────┘
```

**Components**:

- `findLabel`: Label "Find:"
- `findLineEdit`: Text input for search term
- `findButton`: "Find Next" button
- `replaceLabel`: Label "Replace with:"
- `replaceLineEdit`: Text input for replacement term
- `replaceButton`: "Replace" button
- `replaceAllButton`: "Replace All" button (centered)

**Layout**: Vertical layout with 6px padding

**Functionality**:

- Sequential find next operation
- Single replacement at cursor
- Global replace all occurrences
- Case-sensitive search (default)

### 5.5 File Tree View

```text
┌──────────────────────────────────────┐
│  📁 Documents/                       │
│    📁 Project/                       │
│      📄 file1.txt                    │
│      📄 file2.txt                    │
│    📄 notes.txt                      │
└──────────────────────────────────────┘
```

**Component**: `fileTreeView` (QTreeView)

**Features**:

- Hierarchical file system display
- File and folder icons
- Single/multiple selection
- Expandable/collapsible folders
- Styled panel frame

**Behavior**:

- Click file to load into editor
- Navigate using keyboard arrows
- Context menu (to be implemented)

### 5.6 Text Editor Panel

```text
┌──────────────────────────────────────────┐
│ [filename.txt_______________] [Save]    │
├──────────────────────────────────────────┤
│                                          │
│  Text content appears here...            │
│                                          │
│  Multiple lines of text                  │
│  can be edited freely                    │
│                                          │
│                                          │
└──────────────────────────────────────────┘
```

**Components**:

- `fileNameEdit`: Editable filename field
- `saveButton`: Save button with icon (DocumentSave theme)
- `plainTextEdit`: Main text editing area

**Layout**:

- Compact 2px top margin
- 3px spacing between elements
- Full expansion of text editor

**Features**:

- Plain text editing (no rich text)
- Line wrapping (to be configured)
- Syntax highlighting (future enhancement)
- Undo/redo support (built-in Qt feature)

---

## 6. Data Flow and Architecture

### 6.1 MVVM Implementation

#### Model Layer (src/models/)

```python
# example_model.py
@dataclass
class TextDocument:
    """Represents a text document with metadata."""
    filepath: str
    content: str
    encoding: str = "utf-8"
    modified: bool = False

    def validate(self) -> bool:
        """Validate document data."""
        return len(self.filepath) > 0

@dataclass
class CleaningOptions:
    """Text cleaning configuration."""
    trim_whitespace: bool = False
    clean_whitespace: bool = False
    remove_tabs: bool = False
```

#### ViewModel Layer (src/viewmodels/)

```python
# main_viewmodel.py
class MainViewModel(QObject):
    """Main window presentation logic."""

    # Signals
    document_loaded = Signal(str)  # content
    encoding_detected = Signal(str)  # encoding name
    file_saved = Signal(str)  # filepath
    error_occurred = Signal(str)  # error message

    def __init__(self, text_service: TextServiceProtocol):
        super().__init__()
        self._text_service = text_service
        self._current_document: Optional[TextDocument] = None

    @Slot(str)
    def load_file(self, filepath: str) -> None:
        """Load file and detect encoding."""
        # Business logic here

    @Slot(CleaningOptions)
    def clean_text(self, options: CleaningOptions) -> None:
        """Apply text cleaning operations."""
        # Business logic here
```

#### View Layer (src/views/)

```python
# main_window.py
class MainWindow(QMainWindow):
    """Main window UI - loads from .ui file."""

    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        self._viewmodel = viewmodel
        self._load_ui()  # Load from Qt Designer
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect UI signals to ViewModel."""
        # File tree selection -> load file
        self.fileTreeView.clicked.connect(
            lambda: self._viewmodel.load_file(selected_path)
        )

        # ViewModel signals -> UI updates
        self._viewmodel.document_loaded.connect(
            self._on_document_loaded
        )
```

### 6.2 Signal Flow Diagram

```text
User Action → View (UI Event)
    ↓
View → ViewModel (Signal/Slot)
    ↓
ViewModel → Service (Method Call)
    ↓
Service → Model (Data Operation)
    ↓
Model → Service (Result)
    ↓
Service → ViewModel (Return Value)
    ↓
ViewModel → View (Signal Emission)
    ↓
View → UI Update (Slot Handler)
```

### 6.3 File Operation Flow

```text
┌──────────────────────────────────────────────┐
│  1. User clicks file in tree view           │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  2. View emits file selected signal          │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  3. ViewModel calls FileService.read_file()  │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  4. EncodingService detects encoding         │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  5. TextDocument model created               │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  6. ViewModel emits document_loaded signal   │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  7. View updates editor and encoding label   │
└──────────────────────────────────────────────┘
```

---

## 7. Feature Specifications

### 7.1 Text Cleaning Features

#### F-001: Encoding Detection and Conversion

**Priority**: High
**Status**: Planned

**Description**: Automatically detect file encoding and convert to UTF-8.

**User Story**: As a user working with files from various sources, I need to standardize all encodings to UTF-8 so that special characters display correctly.

**Acceptance Criteria**:

- [ ] System automatically detects file encoding on load
- [ ] Detection result displayed in UI (getEncodingFormatLabel)
- [ ] Convert button converts file to UTF-8
- [ ] Editor content updates after conversion
- [ ] User notified of successful conversion
- [ ] Errors handled gracefully (unsupported encodings)

**Technical Requirements**:

- Use `chardet` library for detection
- Support common encodings: UTF-8, UTF-16, ISO-8859-1, Windows-1252, etc.
- Handle BOM (Byte Order Mark) correctly
- Preserve line endings (LF, CRLF, CR)

**Dependencies**: EncodingService, FileService

---

#### F-002: Trim Whitespace

**Priority**: High
**Status**: Planned

**Description**: Remove extra whitespace at document boundaries and paragraph edges.

**User Story**: As a content editor, I need to remove unnecessary whitespace from documents so that formatting is consistent and professional.

**Acceptance Criteria**:

- [ ] Removes leading blank lines from document start
- [ ] Removes trailing blank lines from document end
- [ ] Removes leading spaces/tabs from each line
- [ ] Removes trailing spaces/tabs from each line
- [ ] Preserves intentional paragraph breaks
- [ ] Updates editor with cleaned content

**Algorithm**:

```python
def trim_whitespace(text: str) -> str:
    lines = text.splitlines()

    # Strip leading/trailing empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    # Strip each line
    lines = [line.rstrip() for line in lines]

    return '\n'.join(lines)
```

**Dependencies**: TextProcessingService

---

#### F-003: Clean Whitespace

**Priority**: Medium
**Status**: Planned

**Description**: Normalize whitespace within lines by reducing multiple spaces to single spaces.

**User Story**: As a user cleaning pasted content, I need to remove extra spaces between words so that text appears professionally formatted.

**Acceptance Criteria**:

- [ ] Converts multiple consecutive spaces to single space
- [ ] Preserves single spaces between words
- [ ] Handles tab characters (converts to spaces)
- [ ] Preserves line breaks
- [ ] Works on entire document

**Algorithm**:

```python
import re

def clean_whitespace(text: str) -> str:
    # Replace tabs with spaces
    text = text.replace('\t', ' ')

    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)

    return text
```

**Dependencies**: TextProcessingService

---

#### F-004: Remove Tabs

**Priority**: Medium
**Status**: Planned

**Description**: Remove tab characters and leading spaces from paragraph starts.

**User Story**: As a writer working with copied content, I need to remove indentation so that paragraphs align properly.

**Acceptance Criteria**:

- [ ] Removes all tab characters from document
- [ ] Removes leading spaces from lines
- [ ] Preserves paragraph structure
- [ ] Option to convert tabs to spaces (configurable)

**Algorithm**:

```python
def remove_tabs(text: str) -> str:
    lines = text.splitlines()
    lines = [line.lstrip(' \t') for line in lines]
    return '\n'.join(lines)
```

**Dependencies**: TextProcessingService

---

### 7.2 Find/Replace Features

#### F-005: Find Text

**Priority**: High
**Status**: Planned

**Description**: Search for text in the current document with sequential navigation.

**User Story**: As a user editing large documents, I need to find specific text quickly so that I can locate and review content efficiently.

**Acceptance Criteria**:

- [ ] Enter search term in findLineEdit
- [ ] Click "Find Next" to locate next occurrence
- [ ] Editor scrolls to and highlights found text
- [ ] Wrap around to document start when reaching end
- [ ] Display message when no matches found
- [ ] Case-sensitive search (default)

**Technical Requirements**:

- Use QPlainTextEdit.find() method
- Store search state (current position)
- Highlight matched text with selection
- Show status in status bar

**Dependencies**: None (Qt built-in functionality)

---

#### F-006: Replace Text

**Priority**: High
**Status**: Planned

**Description**: Replace found text with new text, one occurrence at a time.

**User Story**: As a user correcting repeated mistakes, I need to replace specific text so that I can update content systematically.

**Acceptance Criteria**:

- [ ] Enter search term and replacement text
- [ ] "Replace" button replaces current selection only
- [ ] Automatically finds next occurrence after replace
- [ ] Works in conjunction with Find feature
- [ ] Maintains undo history

**Technical Requirements**:

- Verify text is found before replacing
- Use QTextCursor for replacement
- Emit signal to update ViewModel state

**Dependencies**: F-005 (Find Text)

---

#### F-007: Replace All

**Priority**: Medium
**Status**: Planned

**Description**: Replace all occurrences of text in document at once.

**User Story**: As a user with bulk corrections, I need to replace all instances of text so that I can save time on repetitive edits.

**Acceptance Criteria**:

- [ ] Replaces all matches in single operation
- [ ] Shows count of replacements made
- [ ] Confirmation dialog before executing
- [ ] Can be undone with single Ctrl+Z
- [ ] Fast performance on large documents

**Algorithm**:

```python
def replace_all(text: str, find: str, replace: str) -> tuple[str, int]:
    count = text.count(find)
    new_text = text.replace(find, replace)
    return new_text, count
```

**Dependencies**: F-005, F-006

---

### 7.3 File Management Features

#### F-008: File Tree Navigation

**Priority**: High
**Status**: Planned

**Description**: Browse and select files from file system tree.

**User Story**: As a user managing multiple files, I need to navigate my file system so that I can quickly access and edit different files.

**Acceptance Criteria**:

- [ ] Display file system starting from user's home or Documents
- [ ] Show folders and text files only
- [ ] Click file to load into editor
- [ ] Double-click folder to expand/collapse
- [ ] Keyboard navigation support (arrows, Enter)
- [ ] Icons for folders and files

**Technical Requirements**:

- Use QFileSystemModel for tree data
- Filter for text file extensions (.txt, .md, .log, etc.)
- Handle large directory structures efficiently
- Lazy loading of folder contents

**Dependencies**: FileService

---

#### F-009: Save File

**Priority**: Critical
**Status**: Planned

**Description**: Save current document to disk with specified filename.

**User Story**: As a user editing documents, I need to save my changes so that my work is preserved.

**Acceptance Criteria**:

- [ ] Filename editable in fileNameEdit
- [ ] Click Save button to write to disk
- [ ] Keyboard shortcut: Ctrl+S
- [ ] Success confirmation in status bar
- [ ] Error handling for write failures
- [ ] Preserve original encoding or use UTF-8
- [ ] Update document modified state

**Technical Requirements**:

- Validate filename before saving
- Create parent directories if needed
- Handle file permissions issues
- Atomic write operation (temp file + rename)

**Dependencies**: FileService

---

#### F-010: Open File

**Priority**: Critical
**Status**: Planned

**Description**: Open existing file via menu or tree selection.

**User Story**: As a user, I need to open text files so that I can view and edit their content.

**Acceptance Criteria**:

- [ ] File → Open menu shows file dialog
- [ ] Select file from file tree
- [ ] Load file content into editor
- [ ] Display filename in fileNameEdit
- [ ] Detect and display encoding
- [ ] Handle large files (>10MB) with progress indicator

**Technical Requirements**:

- Support multiple file selection in dialog
- Validate file is readable text
- Load in background thread for large files
- Emit progress signals during load

**Dependencies**: FileService, EncodingService

---

### 7.4 Future Features (Merge Tab)

#### F-011: File Merge

**Priority**: Low
**Status**: Not Started

**Description**: Combine multiple text files into single document.

**User Story**: As a user working with related files, I need to merge them into one document so that I can work with consolidated content.

**Planned Acceptance Criteria**:

- [ ] Select multiple files from tree
- [ ] Configure merge order (drag and drop)
- [ ] Specify delimiter between files
- [ ] Option to include filenames as headers
- [ ] Preview merge result before committing
- [ ] Save merged document

**Dependencies**: FileService, TextProcessingService

---

## 8. Technical Implementation Details

### 8.1 Project Structure

```text
src/
├── main.py                      # Application entry point
├── models/
│   ├── __init__.py
│   ├── text_document.py         # TextDocument model
│   ├── cleaning_options.py      # CleaningOptions model
│   └── file_item.py             # FileItem model (tree view)
├── viewmodels/
│   ├── __init__.py
│   └── main_viewmodel.py        # MainViewModel
├── views/
│   ├── __init__.py
│   ├── main_window.py           # MainWindow (loads .ui)
│   └── ui/
│       └── main_window.ui       # Qt Designer UI file
├── services/
│   ├── __init__.py
│   ├── file_service.py          # File I/O operations
│   ├── encoding_service.py      # Encoding detection/conversion
│   └── text_processing_service.py  # Text cleaning operations
└── utils/
    ├── __init__.py
    └── constants.py             # Application constants
```

### 8.2 Service Layer Specifications

#### FileService

**Responsibility**: All file system operations

```python
class FileService:
    """Handles file I/O operations."""

    def read_file(self, filepath: str, encoding: str = 'utf-8') -> str:
        """Read file content with specified encoding."""

    def write_file(self, filepath: str, content: str, encoding: str = 'utf-8') -> None:
        """Write content to file."""

    def get_file_tree(self, root_path: str) -> list[FileItem]:
        """Get directory tree structure."""

    def validate_filepath(self, filepath: str) -> bool:
        """Check if filepath is valid and writable."""
```

#### EncodingService

**Responsibility**: Encoding detection and conversion

```python
class EncodingService:
    """Handles text encoding operations."""

    def detect_encoding(self, filepath: str) -> str:
        """Detect file encoding using chardet."""

    def convert_to_utf8(self, content: str, source_encoding: str) -> str:
        """Convert text from source encoding to UTF-8."""

    def is_valid_encoding(self, encoding_name: str) -> bool:
        """Verify encoding name is supported."""
```

#### TextProcessingService

**Responsibility**: Text manipulation operations

```python
class TextProcessingService:
    """Handles text cleaning and processing."""

    def trim_whitespace(self, text: str) -> str:
        """Remove leading/trailing whitespace."""

    def clean_whitespace(self, text: str) -> str:
        """Normalize whitespace between words."""

    def remove_tabs(self, text: str) -> str:
        """Remove tab characters."""

    def apply_cleaning_options(self, text: str, options: CleaningOptions) -> str:
        """Apply multiple cleaning operations."""
```

### 8.3 Testing Strategy

#### Unit Tests

**Location**: `tests/unit/`

**Coverage Requirements**: Minimum 80% code coverage

**Key Test Areas**:

```python
# test_text_processing_service.py
class TestTextProcessingService:
    def test_trim_whitespace_removes_leading_spaces(self):
        service = TextProcessingService()
        result = service.trim_whitespace("  hello")
        assert result == "hello"

    def test_clean_whitespace_reduces_multiple_spaces(self):
        service = TextProcessingService()
        result = service.clean_whitespace("hello    world")
        assert result == "hello world"

# test_main_viewmodel.py
class TestMainViewModel:
    def test_load_file_emits_document_loaded_signal(self, qtbot, mock_file_service):
        vm = MainViewModel(mock_file_service)
        with qtbot.waitSignal(vm.document_loaded):
            vm.load_file("test.txt")
```

#### Integration Tests

**Location**: `tests/integration/`

**Key Scenarios**:

- End-to-end file loading and saving
- Text cleaning operations on real files
- UI interaction workflows

```python
# test_application.py
def test_load_and_clean_workflow(qapp, tmpdir):
    # Create test file
    test_file = tmpdir.join("test.txt")
    test_file.write("  hello    world  ")

    # Create application
    app = create_application()

    # Load file
    app.load_file(str(test_file))

    # Apply cleaning
    app.apply_cleaning(CleaningOptions(trim_whitespace=True))

    # Verify result
    assert app.get_content() == "hello    world"
```

### 8.4 Configuration Management

**Configuration File**: `config.json` (to be created)

```json
{
  "ui": {
    "window_size": [894, 830],
    "splitter_position": [600, 294],
    "default_encoding": "utf-8",
    "theme": "system"
  },
  "editor": {
    "font_family": "Monospace",
    "font_size": 11,
    "line_wrap": true,
    "show_line_numbers": false
  },
  "cleaning": {
    "trim_whitespace": false,
    "clean_whitespace": false,
    "remove_tabs": false
  },
  "file_browser": {
    "start_directory": "~",
    "show_hidden_files": false,
    "file_extensions": [".txt", ".md", ".log", ".csv"]
  }
}
```

### 8.5 Error Handling

**Error Categories**:

1. **File I/O Errors**
   - File not found
   - Permission denied
   - Disk full
   - Invalid path

2. **Encoding Errors**
   - Unsupported encoding
   - Corrupt file data
   - Invalid characters

3. **UI Errors**
   - Failed to load .ui file
   - Widget not found
   - Signal connection failure

**Error Handling Pattern**:

```python
# In Service Layer
class FileService:
    def read_file(self, filepath: str) -> str:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"Cannot find file: {filepath}")
        except PermissionError:
            logger.error(f"Permission denied: {filepath}")
            raise PermissionError(f"No permission to read: {filepath}")
        except Exception as e:
            logger.error(f"Unexpected error reading file: {e}")
            raise RuntimeError(f"Failed to read file: {str(e)}")

# In ViewModel Layer
class MainViewModel(QObject):
    error_occurred = Signal(str)

    def load_file(self, filepath: str):
        try:
            content = self._file_service.read_file(filepath)
            self.document_loaded.emit(content)
        except (FileNotFoundError, PermissionError, RuntimeError) as e:
            self.error_occurred.emit(str(e))

# In View Layer
class MainWindow(QMainWindow):
    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
```

---

## 9. Future Enhancements

### 9.1 Short-term Enhancements (Next Release)

1. **Complete Placeholder Checkboxes**
   - Implement functionality for `checkBox_2`, `checkBox_4`, `checkBox_6`
   - Add meaningful labels and tooltips
   - Examples: Remove duplicate lines, fix line endings, smart quotes

2. **Keyboard Shortcuts**
   - Ctrl+O: Open file
   - Ctrl+S: Save file
   - Ctrl+Shift+S: Save As
   - Ctrl+F: Focus find field
   - F3: Find next
   - Ctrl+H: Focus replace field
   - Ctrl+Q: Quit

3. **Status Bar Information**
   - Display file path
   - Show encoding
   - Line/column numbers
   - Character count
   - Selection info

4. **Recent Files**
   - File → Recent Files submenu
   - Store last 10 opened files
   - Quick access to frequently used files

### 9.2 Medium-term Enhancements

1. **Advanced Find/Replace**
   - Regular expression support
   - Case-insensitive option
   - Whole word matching
   - Find in multiple files

2. **File Merge Implementation**
   - Complete UI design in Qt Designer
   - Drag-and-drop file ordering
   - Custom delimiters
   - Merge preview pane

3. **Syntax Highlighting**
   - Detect file type (Python, Markdown, etc.)
   - Apply appropriate highlighting
   - Configurable color schemes

4. **Undo/Redo with History**
   - Enhanced undo stack
   - Visual history viewer
   - Branch to previous state

5. **Dark Mode**
   - System theme detection
   - Manual theme toggle
   - Custom color schemes

### 9.3 Long-term Vision

1. **Plugin System**
   - Extensible architecture
   - Custom text processing plugins
   - Community-contributed tools

2. **Batch Processing**
   - Apply operations to multiple files
   - Save/load processing profiles
   - Command-line interface

3. **Cloud Integration**
   - Save to cloud storage
   - Sync settings across devices
   - Collaborative editing

4. **AI-Powered Features**
   - Smart text suggestions
   - Grammar checking
   - Content summarization
   - Translation support

5. **Diff/Merge Tool**
   - Compare two text files
   - Visual diff highlighting
   - Three-way merge for conflicts

---

## Appendix A: Widget Object Names Reference

### Main Window

- `MainWindow`: QMainWindow (root)
- `centralwidget`: QWidget
- `menubar`: QMenuBar
- `statusbar`: QStatusBar

### Splitters

- `mainSplitter`: QSplitter (horizontal, divides left/right panels)
- `leftPanelSplitter`: QSplitter (vertical, divides tabs/tree)

### Panels

- `leftPanelContainerWidget`: QWidget (left panel container)
- `rightPanelContainerWidget`: QWidget (right panel container)

### Clean Tab

- `tabWidget`: QTabWidget
- `cleanTab`: QWidget (Clean tab)
- `cleanScrollArea`: QScrollArea
- `cleanScrollContents`: QWidget
- `encodingConvertHeaderLabel`: QLabel
- `convertEncodingContainer`: QWidget
- `currentFormatLabel`: QLabel
- `getEncodingFormatLabel`: QLabel
- `convertEncodingButton`: QPushButton
- `formattingOptionsHeaderLabel`: QLabel
- `formatOptionsContainer`: QWidget
- `trimWhiteSpaceCheckBox`: QCheckBox
- `cleanWhiteSpaceCheckBox`: QCheckBox
- `removeTabsCheckBox`: QCheckBox
- `checkBox_2`, `checkBox_4`, `checkBox_6`: QCheckBox (placeholders)

### Merge Tab

- `mergeTab`: QWidget
- `mergeScrollArea`: QScrollArea
- `mergeScrollContents`: QWidget
- `mergeTabScrollLayout`: QGridLayout

### Find/Replace Tab

- `findTab`: QWidget
- `findScrollArea`: QScrollArea
- `findScrollContents`: QWidget
- `findLabel`: QLabel
- `findWidget`: QWidget
- `findLineEdit`: QLineEdit
- `findButton`: QPushButton
- `replaceLabel`: QLabel
- `replaceWidget`: QWidget
- `replaceLineEdit`: QLineEdit
- `replaceButton`: QPushButton
- `replaceAllButton`: QPushButton

### File Tree

- `fileTreeView`: QTreeView

### Text Editor

- `fileNameEdit`: QLineEdit
- `saveButton`: QPushButton
- `plainTextEdit`: QPlainTextEdit

### Menu Actions

- `actionOpen`: QAction
- `actionSave`: QAction
- `actionSave_as`: QAction
- `actionPreferences`: QAction
- `actionQuit`: QAction
- `actionAbout`: QAction

---

## Appendix B: Color Scheme and Styling

**Note**: Current UI uses default Qt styling. Custom styling to be implemented using QSS (Qt Style Sheets).

**Planned Color Palette**:

```css
/* Primary colors */
--primary: #3498db;
--primary-dark: #2980b9;
--primary-light: #5dade2;

/* Background */
--bg-main: #ffffff;
--bg-secondary: #f8f9fa;
--bg-dark: #343a40;

/* Text */
--text-primary: #212529;
--text-secondary: #6c757d;
--text-inverse: #ffffff;

/* Borders */
--border-color: #dee2e6;
--border-focus: #3498db;

/* Status */
--success: #28a745;
--warning: #ffc107;
--error: #dc3545;
--info: #17a2b8;
```

---

## Appendix C: Performance Considerations

### Large File Handling

**File Size Thresholds**:

- **< 1MB**: Load immediately into memory
- **1-10MB**: Show progress indicator, load in background thread
- **10-50MB**: Warn user, offer to proceed
- **> 50MB**: Recommend using specialized tools

**Optimization Techniques**:

1. Lazy loading for file tree (load folders on demand)
2. Chunked reading for large files
3. Virtual text editor for documents > 10MB
4. Asynchronous save operations
5. Debounced auto-save (save after 2s of no typing)

### Memory Management

**Current Concerns**:

- Entire file loaded into memory (QPlainTextEdit)
- Undo stack can grow large for long editing sessions

**Planned Improvements**:

- Implement maximum undo stack size
- Clear undo history when opening new file
- Use QTextStream for incremental file reading
- Profile memory usage with large files

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-05 | System Analysis | Initial document creation based on main_window.ui |

---

**End of Document**
