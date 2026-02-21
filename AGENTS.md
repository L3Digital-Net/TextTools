# Agent Instructions for TextTools

TextTools is a PySide6 desktop application for text processing on Linux. Features: open files,
edit text, apply cleaning operations (trim whitespace, clean whitespace, remove tabs), find/replace,
and save with encoding detection. MVVM architecture with Qt Designer `.ui` files.

## ⚠️ Branch Protection

**BEFORE ANY FILE MODIFICATION, RUN:**

```bash
python .agents/branch_protection.py
```

- ❌ NEVER modify files on `main` branch
- ✅ ALWAYS work on `testing` branch
- ✅ Only assist with merges when human explicitly authorizes

## Commands

```bash
pytest tests/                   # run tests + coverage (configured in pyproject.toml)
mypy src/                       # type check (strict mode)
black src/ tests/               # format
isort src/ tests/               # import order
uv pip install -r requirements.txt  # install deps
```

## Architecture

```
View (src/views/)           → Loads .ui files, connects signals, updates UI
    ↕ Qt Signals/Slots
ViewModel (src/viewmodels/) → QObject subclass, emits signals, calls services
    ↕ Method calls
Service (src/services/)     → File I/O, text processing — no Qt imports
    ↕ Method calls
Model (src/models/)         → Pure Python dataclasses, validation — no Qt imports
```

**Composition root**: `create_application()` in `src/main.py` — the only place that
constructs services, injects them into ViewModels, and injects ViewModels into Views.

### Layer Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| `models/` | Pure Python, dataclasses, validation | Any Qt import |
| `viewmodels/` | QObject, Signal/Slot, calling services | Direct widget access |
| `views/` | Load .ui files, findChild(), signal connections | Business logic |
| `services/` | File I/O, text processing | Qt imports |

### Key Domain Files

| File | Purpose |
|------|---------|
| `src/models/text_document.py` | `TextDocument` dataclass (filepath, content, encoding, modified) |
| `src/models/cleaning_options.py` | `CleaningOptions` dataclass (trim/clean/remove_tabs flags) |
| `src/services/file_service.py` | `open_file`, `save_file` (atomic write via mkstemp+os.replace) |
| `src/services/text_processing_service.py` | `trim_whitespace`, `clean_whitespace`, `remove_tabs`, `apply_options` |
| `src/viewmodels/main_viewmodel.py` | All signals/slots; defines `FileServiceProtocol` + `TextServiceProtocol` |
| `src/views/main_window.py` | Loads `main_window.ui`, wires all widgets |
| `src/views/ui/main_window.ui` | Qt Designer layout — widget objectNames defined here |

### Widget objectNames (from DESIGN.md Appendix A)

View connects to widgets by these names via `findChild()`:
`plainTextEdit`, `fileNameEdit`, `saveButton`, `fileTreeView`, `getEncodingFormatLabel`,
`trimWhiteSpaceCheckBox`, `cleanWhiteSpaceCheckBox`, `removeTabsCheckBox`,
`findLineEdit`, `findButton`, `replaceLineEdit`, `replaceButton`, `replaceAllButton`,
`convertEncodingButton`, `actionOpen`, `actionSave`, `actionQuit`, `actionAbout`

### ServiceProtocol Pattern

Each ViewModel defines its own `ServiceProtocol` (using `typing.Protocol`) **in the same file as
the ViewModel** — not in a separate module. See `src/viewmodels/main_viewmodel.py`.

## Testing

- **pytest-qt**: provides `qtbot` fixture; use `qtbot.waitSignal()` for signal assertions
- **pytest-mock**: use `mocker.Mock()` for service mocks in ViewModel tests
- **Session-scoped `qapp`** fixture in `tests/conftest.py`
- Markers: `pytest -m unit`, `-m integration`, `-m gui`

```python
def test_slot_emits_signal(qtbot, mocker):
    mock_service = mocker.Mock(spec=FileServiceProtocol)
    vm = MainViewModel(mock_service, mocker.Mock())
    with qtbot.waitSignal(vm.document_loaded, timeout=1000) as blocker:
        vm.load_file("/path/to/file.txt")
    assert blocker.args[0] == expected_content
```

## Conventions

- **Type hints**: required on all functions — mypy strict mode enforced
- **Modern syntax**: `str | None` not `Optional[str]`, `list[X]` not `List[X]`
- **Qt6 enums**: `QFile.OpenModeFlag.ReadOnly` not deprecated `QFile.ReadOnly`
- **Docstrings**: Google-style on all public APIs
- **Signals for cross-layer communication**: never call View methods from ViewModel
- **Long operations**: must use `QThread`, never block the UI thread
