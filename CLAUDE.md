# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plugin Routing — Qt Plugins (MANDATORY)

This is a PySide6/Qt project. Always invoke the appropriate plugin skill before writing code:

| Task | Invoke |
|------|--------|
| Write or add tests (pytest-qt, QTest) | `qt:qtest-patterns` skill |
| Run the test suite or check pass/fail | `qt:run` skill |
| Measure test coverage, find gaps | `qt:coverage` skill → `qt:qt-coverage-workflow` skill |
| Generate tests for uncovered lines | `qt:generate` skill (delegates to `qt:test-generator` agent) |
| Visual/GUI interaction testing | `qt:visual` skill (delegates to `qt:gui-tester` agent) |
| Any new feature or UI work | `qt:qtest-patterns` after implementation, `qt:visual` to verify |

**Rule**: Never write Qt/PySide6 tests without first consulting `qt:qtest-patterns`. Never run tests manually via raw `pytest` when `qt:run` is available — use the skill so the agent can capture results and act on failures.

## Project Overview

TextTools is a PySide6 desktop application for text processing on Linux. Its planned features are encoding conversion (to UTF-8), text formatting/cleaning, find/replace, and file management. **The MVVM framework and UI shell are in place, but all TextTools feature logic is unimplemented — the current source files are scaffolding/template code.** `DESIGN.md` is the authoritative spec for what needs to be built (UI mockups, widget objectNames, feature acceptance criteria, data flow diagrams).

**Tech stack**: Python 3.14, PySide6 6.8.0+, MVVM architecture, Qt Designer for UI.

## Commands

```bash
# Run the application (must be run from project root)
python -m src.main

# Run all tests (coverage is on by default via pyproject.toml addopts)
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

Coverage runs automatically with every `pytest` invocation — it produces terminal output and `htmlcov/` without extra flags.

## Architecture (MVVM — Strictly Enforced)

```
View (src/views/)           → Loads .ui files, connects signals, updates UI
    ↕ Qt Signals/Slots
ViewModel (src/viewmodels/) → QObject subclass, emits signals, calls services
    ↕ Method calls
Service (src/services/)     → External I/O (files, APIs), injected into ViewModels
    ↕ Method calls
Model (src/models/)         → Pure Python dataclasses, business logic, validation
```

**Dependency wiring**: `create_application()` in `src/main.py` is the sole composition root — it creates services, injects them into ViewModels, and injects ViewModels into Views. No layer constructs its own dependencies.

### Layer Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| **Model** | Pure Python, dataclasses, validation | Any Qt imports |
| **ViewModel** | QObject, Signal/Slot, calling services | Direct widget manipulation |
| **View** | Loading .ui files, findChild(), signal connections | Business logic, data validation |
| **Service** | File I/O, external APIs | Qt imports, UI concerns |

### UI: Qt Designer Only

All UI layouts live in `.ui` files under `src/views/ui/`. Views load them via `QUiLoader` and access widgets with `findChild(WidgetType, "objectName")`. The objectName strings that views must use are defined in **DESIGN.md Appendix A** — these must match exactly what is set in Qt Designer.

### ServiceProtocol Pattern

Each ViewModel defines its own `ServiceProtocol` (using `typing.Protocol`) in the same file as the ViewModel, not in a separate module. This keeps the contract local to the consumer. See `src/viewmodels/main_viewmodel.py` for the reference implementation.

## Branch Protection

- **All development happens on the `testing` branch** — never commit to `main`
- `main` is protected by pre-commit hooks; only human-authorized merges allowed
- Run `python .agents/branch_protection.py` before modifications if uncertain

## Testing Patterns

- Uses **pytest** with **pytest-qt** (provides `qtbot` fixture for signal testing)
- Session-scoped `qapp` fixture in `tests/conftest.py` creates a single QApplication
- Tests follow **Arrange-Act-Assert** pattern
- Use `qtbot.waitSignal()` for testing signal emissions
- ViewModels are tested with mock services (via pytest-mock); no Qt app needed for ViewModel-only tests

## Conventions

- **Type hints**: Required on all functions (mypy strict mode)
- **Docstrings**: Google-style on all public APIs
- **Naming**: files `snake_case.py`, classes `PascalCase`, private `_leading_underscore`
- **Signals for cross-layer communication**: Never call View methods from ViewModel directly
- **Threading**: Long operations must use `QThread`; never block the UI thread
- **Formatting**: Black (88 char lines), isort (black profile) — configured in `pyproject.toml`
