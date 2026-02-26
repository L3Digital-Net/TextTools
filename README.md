# TextTools

A PySide6 desktop application for text processing on Linux. Provides encoding conversion (to UTF-8), text formatting/cleaning, find/replace, and file management through a split-panel interface.

**Status**: v0.3.0 — core features implemented and tested. Encoding conversion, find/replace, text cleaning, and file I/O are fully functional. See `DESIGN.md` for the full specification.

## Stack

- **Language**: Python 3.14
- **UI Framework**: PySide6 6.8.0+ (Qt for Python)
- **Architecture**: MVVM with dependency injection
- **Testing**: pytest + pytest-qt + pytest-mock
- **Package Manager**: UV
- **Platform**: Linux only

## Setup

**Prerequisites**: Python 3.14, Linux.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Running

```bash
python src/main.py
```

## Testing

Coverage runs automatically with every `pytest` invocation (configured in `pyproject.toml`):

```bash
# All tests (includes coverage report)
pytest tests/

# Single test file
pytest tests/unit/test_text_document.py

# Filtered by name
pytest -k "test_viewmodel" tests/
```

## Code Quality

```bash
# Type checking
mypy src/

# Formatting
black src/ tests/
isort src/ tests/
```

## UI Development

All layouts are defined in Qt Designer `.ui` files under `src/views/ui/`. Never hardcode layouts in Python — load them with `QUiLoader` and access widgets via `findChild()`.

```bash
designer src/views/ui/main_window.ui
```

## Architecture

```
src/
├── models/       # Pure Python dataclasses, validation, business logic (no Qt)
├── viewmodels/   # QObject subclasses, signals/slots, calls services
├── views/        # Loads .ui files, connects signals — no business logic
│   └── ui/       # Qt Designer .ui files
├── services/     # File I/O, external integrations — injected into ViewModels
├── utils/        # Constants, helpers
└── main.py       # Composition root — wires services → viewmodels → views
```

`main.py:create_application()` is the sole place where dependencies are composed. Layers only know about the layer directly below them.

## Branch Protection

- All development happens on the `testing` branch
- `main` is protected by pre-commit hooks — only human-authorized merges
- Run `python .agents/branch_protection.py` before modifications if uncertain

## Dependencies

**Runtime**:
```
PySide6>=6.8.0
chardet>=5.0.0   # optional: encoding detection (falls back to utf-8 without it)
```

**Development / testing**:
```
pytest>=8.3.0, pytest-qt>=4.4.0, pytest-mock>=3.14.0, pytest-cov>=5.0.0
mypy>=1.0.0, black>=24.0.0, isort>=5.13.0
```
