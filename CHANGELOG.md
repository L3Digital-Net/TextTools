# Changelog

All notable changes to TextTools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.3.0] — 2026-02-21

### Added
- Default tab is now Clean (was Find/Replace)
- Keyboard shortcuts: Ctrl+F (find), Ctrl+H (replace), F3 (find next)
- Encoding conversion button (F-001): re-saves file as UTF-8
- Cursor position and character count in status bar
- Save As (was stubbed)
- Window geometry and splitter positions persist across sessions (QSettings)

### Fixed
- Encoding label now shows "utf-8" for ASCII files (ASCII is a subset of UTF-8)

---

## [0.2.0] - 2026-02-21

### Added
- `TextDocument` dataclass — core domain model for loaded files (`filepath`, `content`, `encoding`, `modified`)
- `CleaningOptions` dataclass — configuration for text cleaning passes
- `TextProcessingService` — stateless text cleaning: `trim_whitespace`, `clean_whitespace`, `remove_tabs`, `apply_options`
- `FileService` — atomic file save (`tempfile.mkstemp` + `os.replace`), encoding detection via `chardet` with 0.7 confidence threshold
- `MainViewModel` — full signal/slot implementation: `document_loaded`, `encoding_detected`, `file_saved`, `error_occurred`, `status_changed`; slots for `load_file`, `save_file`, `apply_cleaning`, `replace_all`
- `MainWindow` — wires QFileSystemModel file tree, all checkbox/button signals, find/replace with wrap-around cursor, ViewModel signal handlers
- `chardet>=5.0.0` runtime dependency for encoding detection
- `mypy`, `black`, `isort` dev dependencies in `requirements.txt`
- 60 unit and integration tests (100% coverage on models and TextProcessingService; 98% on ViewModel)
- `AGENTS.md` rewritten with TextTools-specific architecture reference and widget objectName table

### Changed
- Renamed project from Template-Desktop-Application to TextTools
- `main.py` composition root now wires `FileService` + `TextProcessingService` → `MainViewModel` → `MainWindow`; logging to stdout only
- `MainWindow` changed from `QMainWindow` subclass to a plain Python controller — `self.ui` is the loaded `.ui` QMainWindow, preventing nested-QMainWindow sizing bugs
- All template/scaffold files removed (`ExampleModel`, `ExampleService`, `example_model.py` tests)
- CI workflow updated: `develop` → `testing` branch, action versions pinned to v4/v5, `pip` → `uv`
- `.ui` window title changed from `"MainWindow"` to `"TextTools"`
- `pyproject.toml` mypy config: added `explicit_package_bases = true`

### Fixed
- `QFileSystemModel` import moved from `PySide6.QtGui` to `PySide6.QtWidgets` (correct for PySide6 6.10.x)
- Black/isort formatting applied to all source files

---

## [0.1.0] - 2025-11-02

### Added
- MVVM architecture scaffold: `ExampleModel`, `MainViewModel`, `ExampleService`, `MainWindow`
- Qt Designer `.ui` file loading via `QUiLoader` with `findChild()` widget access pattern
- Dependency injection wired in `main.py:create_application()`
- Test suite: 9 unit tests for Model (100% coverage), 10 unit tests for ViewModel (96% coverage), 3 integration tests
- `ServiceProtocol` pattern using `typing.Protocol` for mockable service interfaces
- Branch protection system: pre-commit hook blocks commits to `main`, `.agents/branch_protection.py` for AI agent checks
- Coverage auto-configured in `pyproject.toml` (`addopts`); no extra flags needed when running `pytest`
- Logging to both file (`app.log`) and console

### Dependencies
- PySide6 >= 6.8.0
- pytest >= 8.3.0, pytest-qt >= 4.4.0, pytest-mock >= 3.14.0, pytest-cov >= 5.0.0
- Python 3.14, Linux only
