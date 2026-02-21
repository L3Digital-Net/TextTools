# Changelog

All notable changes to TextTools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Renamed project from Template-Desktop-Application to TextTools
- Updated `APP_NAME` constant and `QApplication` name to "TextTools"
- Removed ContextStream MCP references from `AGENTS.md`
- Updated `README.md`, `CONTRIBUTING.md`, and `CLAUDE.md` to reflect TextTools identity and actual codebase state
- Added `.mcp.json*` and `.codex/` to `.gitignore`

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
