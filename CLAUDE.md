# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TextTools is a PySide6 desktop application for text processing on Linux. It provides encoding conversion (to UTF-8), text formatting/cleaning, find/replace, and file management. The project is in early development — the MVVM framework and UI shell are in place, but feature logic is mostly unimplemented (template/example code exists as scaffolding).

**Tech stack**: Python 3.14, PySide6 6.8.0+, MVVM architecture, Qt Designer for UI.

## Commands

```bash
# Run the application
python src/main.py

# Run all tests (coverage enabled by default via pyproject.toml)
pytest tests/

# Run a single test file
pytest tests/unit/test_example_model.py

# Run a single test case
pytest tests/unit/test_example_model.py::TestExampleModel::test_validate_returns_true_for_valid_data

# Run tests matching a pattern
pytest -k "test_viewmodel" tests/

# Type checking (strict mode configured in pyproject.toml)
mypy src/

# Formatting
black src/ tests/
isort src/ tests/

# Dependency management (always use UV, not pip)
uv pip install -r requirements.txt
uv pip install <package-name>
```

## Architecture (MVVM — Strictly Enforced)

The codebase follows a strict MVVM pattern with dependency injection. Layer boundaries are non-negotiable:

```
View (src/views/)          → Loads .ui files, connects signals, updates UI
    ↕ Qt Signals/Slots
ViewModel (src/viewmodels/) → QObject subclass, emits signals, calls services
    ↕ Method calls
Service (src/services/)     → External I/O (files, APIs), injected into ViewModels
    ↕ Method calls
Model (src/models/)         → Pure Python dataclasses, business logic, validation
```

**Dependency flow**: `main.py` creates Services → injects into ViewModels → injects into Views. See `create_application()` in `src/main.py`.

### Layer Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| **Model** | Pure Python, dataclasses, validation | Any Qt imports |
| **ViewModel** | QObject, Signal/Slot, calling services | Direct widget manipulation |
| **View** | Loading .ui files, findChild(), signal connections | Business logic, data validation |
| **Service** | File I/O, external APIs | Qt imports, UI concerns |

### UI: Qt Designer Only

All UI layouts are defined in `.ui` files under `src/views/ui/` — **never hardcode layouts in Python**. Views load them via `QUiLoader` and access widgets with `findChild()` using the objectName from Qt Designer.

## Branch Protection

- **All development happens on the `testing` branch** — never commit to `main`
- `main` is protected by pre-commit hooks; only human-authorized merges allowed
- Run `python .agents/branch_protection.py` before modifications if uncertain

## Testing Patterns

- Uses **pytest** with **pytest-qt** (provides `qtbot` fixture for signal testing)
- Session-scoped `qapp` fixture in `tests/conftest.py` creates a single QApplication
- Tests follow **Arrange-Act-Assert** pattern
- Use `qtbot.waitSignal()` for testing signal emissions
- ViewModels are tested with mock services (via pytest-mock)

## Key Design Document

`DESIGN.md` contains the full application specification (~10K words) including UI mockups, widget objectNames (Appendix A), color scheme (Appendix B), feature acceptance criteria, and data flow diagrams. **Consult this before implementing any feature.**

## Conventions

- **Type hints**: Required on all functions (mypy strict mode)
- **Docstrings**: Google-style on all public APIs
- **Naming**: files `snake_case.py`, classes `PascalCase`, private `_leading_underscore`
- **Dependency injection**: Services use `typing.Protocol` for interfaces; inject via constructor
- **Signals for cross-layer communication**: Never call View methods from ViewModel directly
- **Threading**: Long operations must use `QThread`; never block the UI thread
- **Formatting**: Black (88 char lines), isort (black profile) — configured in `pyproject.toml`
