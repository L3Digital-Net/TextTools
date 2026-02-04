# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PySide6 desktop application template following MVVM architecture on Linux. Built with Python 3.14, Qt Designer for UI, and pytest for testing.

## Commands

```bash
# Setup (first time)
./setup.sh                  # Installs UV, creates .venv, installs deps
source .venv/bin/activate

# Run
python src/main.py

# Test
pytest tests/                                          # All tests
pytest tests/unit/                                     # Unit tests only
pytest tests/integration/                              # Integration tests only
pytest tests/unit/test_example_model.py                # Single file
pytest tests/unit/test_example_model.py::TestExampleModel::test_validate_returns_true_for_valid_data  # Single test
pytest -k "test_pattern" tests/                        # By pattern

# Code quality
black src/ tests/           # Format
isort src/ tests/           # Sort imports
mypy src/                   # Type check (strict, Python 3.14)
```

## Architecture (MVVM — strictly enforced)

Data flows one direction: **Service → Model → ViewModel → View**

Dependencies are injected via constructors in `src/main.py`:
```
Service(created) → ViewModel(receives service) → View(receives viewmodel)
```

### Layer rules

| Layer | Location | Qt imports? | Purpose |
|-------|----------|-------------|---------|
| **Model** | `src/models/` | **NO** — pure Python | Business logic, validation, dataclasses |
| **ViewModel** | `src/viewmodels/` | QObject + Signal only | Presentation logic, state via signals |
| **View** | `src/views/` | Full PySide6 | Load `.ui` files, connect signals, minimal logic |
| **Service** | `src/services/` | No | External operations, data fetching |

### UI: Qt Designer only — never hardcode layouts in Python

All UI is defined in `.ui` files under `src/views/ui/`, loaded at runtime via `QUiLoader`. Views access widgets with `self.ui.findChild(WidgetType, "objectName")`. Opening the designer: `designer src/views/ui/main_window.ui`

### Signal/slot communication pattern

ViewModels define signals (`data_loaded`, `error_occurred`, `status_changed`). Views connect their widget signals (e.g. `button.clicked`) to ViewModel slots, and observe ViewModel signals to update the UI. No direct method calls across layers.

### Dependency injection via Protocol

Services are typed with `Protocol` from `typing`, not concrete classes. This allows mock injection in tests.

## Branch Protection

- **`testing` branch**: All development happens here
- **`main` branch**: Protected — only receives merges from `testing`
- Before modifying files, verify branch: `git branch --show-current`
- Git hooks enforce this (pre-commit blocks commits to main)

## Testing Conventions

- Framework: pytest + pytest-qt + pytest-mock
- Pattern: Arrange-Act-Assert
- Qt tests use `qtbot` fixture and `qtbot.waitSignal()` for signal assertions
- Session-scoped `qapp` fixture in `tests/conftest.py` provides QApplication
- Coverage targets: Models 95%+, ViewModels 90%+
- Coverage is configured in `pyproject.toml` (runs automatically with `pytest`)

## Configuration

All tool config lives in `pyproject.toml`:
- **pytest**: `--cov=src`, verbose, strict markers
- **mypy**: strict mode, Python 3.14, PySide6 imports ignored
- **black**: line-length 88, target py314
- **isort**: black-compatible profile
