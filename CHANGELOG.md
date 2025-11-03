# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated `.github/prompts/documentation.prompt.md` to remove Star Trek Retro Remake project references
- Replaced project-specific documentation structure with template-appropriate structure
- Updated documentation guidelines to reflect PySide6 MVVM template repository standards
- Updated `.github/prompts/README.md` last updated date to 2025-11-03
- Improved formatting in documentation prompt file for better readability

### Documentation
- Removed references to STRR/, backup/, and scripts/ directories specific to other projects
- Added proper template documentation structure guidelines
- Enhanced documentation checklist for template repositories

---

## [0.1.0] - 2025-11-02

### Added
- Complete MVVM architecture implementation with Models, ViewModels, and Views
- Example Model (ExampleModel) with validation and business logic
- Main ViewModel (MainViewModel) with reactive data binding using Qt signals/slots
- Main Window View loading UI from Qt Designer .ui files
- Example Service for external operations and dependency injection
- Comprehensive test suite with pytest, pytest-qt, and pytest-mock
  - 9 unit tests for Models (100% coverage)
  - 10 unit tests for ViewModels (96% coverage)
  - 3 integration tests for full application workflow
- Complete project documentation:
  - GitHub Copilot instructions for AI-assisted development
  - AGENTS.md quick reference for AI agents
  - Branch protection documentation and setup scripts
  - UI design guide for Qt Designer workflow
  - CONTRIBUTING.md guidelines
  - QUICKSTART guides for both manual and UV setup
- Branch protection system to prevent accidental main branch modifications
- UV package manager support with setup scripts
- Logging configuration with file and console handlers
- Type hints throughout the codebase
- Dependency injection pattern implementation

### Changed
- Module imports updated to use proper `src.` prefix for package imports
- Test suite enhanced to handle multiple signal emissions correctly

### Fixed
- Import issues causing test failures resolved
- Test timing issue in `test_load_data_emits_status_changed_signal` fixed

### Documentation
- Comprehensive architecture documentation following SOLID principles
- MVVM pattern implementation guidelines
- Testing best practices and examples
- Qt Designer workflow documentation (NO hardcoded UI in Python)
- Branch protection quick reference guides

## Technical Details

### Architecture
- **MVVM Pattern**: Strict separation of concerns
  - Models: Pure Python, no Qt dependencies (100% coverage)
  - ViewModels: QObject-based with signals/slots (96% coverage)
  - Views: UI-only, loads .ui files from Qt Designer
- **SOLID Principles**: Applied throughout
  - Single Responsibility: Each class has one clear purpose
  - Open/Closed: Extensible through dependency injection
  - Liskov Substitution: Proper inheritance hierarchies
  - Interface Segregation: Protocol-based interfaces
  - Dependency Inversion: Services injected into ViewModels

### Testing
- **Total Tests**: 22 tests passing
- **Coverage**: 48% overall (focused on business logic)
  - Models: 100% coverage
  - ViewModels: 96% coverage
  - Services: 68% coverage
- **Test Categories**:
  - Unit tests for Models and ViewModels
  - Integration tests for complete workflows
  - Qt-specific tests using pytest-qt plugin

### Dependencies
- PySide6 >= 6.8.0 (Qt for Python)
- Python 3.14
- pytest >= 8.3.0
- pytest-qt >= 4.4.0
- pytest-mock >= 3.14.0
- pytest-cov >= 5.0.0

### Platform Support
- **Supported**: Linux only
- **Not Supported**: Windows, macOS (by design for this template)

---

## [0.1.0] - Initial Template

### Note
This is a template repository. Version numbers represent template iterations, not application versions.

[Unreleased]: https://github.com/L3DigitalNet/Template-Desktop-Application/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/L3DigitalNet/Template-Desktop-Application/releases/tag/v0.1.0
