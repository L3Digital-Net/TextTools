# Template-Desktop-Application

Generic template for a desktop application using PySide6, Python, following MVVM architecture and SOLID principles.

## Overview

This is a template repository for building professional desktop applications with:

- **UI Framework**: PySide6 (Qt for Python) - Latest version compatible with Python 3.14
- **Language**: Python 3.14
- **Platform**: Linux only
- **Architecture**: MVVM (Model-View-ViewModel)
- **Design Principles**: SOLID
- **Testing**: Pytest with pytest-qt

## Project Structure

```
Template-Desktop-Application/
├── src/                          # Source code
│   ├── models/                   # Business logic and domain entities
│   ├── viewmodels/               # Presentation logic
│   ├── views/                    # PySide6 UI components
│   ├── services/                 # External integrations
│   ├── utils/                    # Helper functions
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── conftest.py               # Pytest configuration
├── .github/                      # GitHub configuration
│   ├── copilot-instructions.md   # GitHub Copilot instructions
│   └── workflows/                # CI/CD workflows
├── .agents/                      # AI agent memory and preferences
│   ├── memory.instruction.md     # Coding standards and patterns
│   └── branch_protection.py      # Branch protection checker
├── AGENTS.md                     # Quick reference for AI agents
├── BRANCH_PROTECTION.md          # Branch protection documentation
├── BRANCH_PROTECTION_QUICK.md    # Branch protection quick reference
├── create-branch-protections.prompt.md  # Branch protection setup guide
├── setup-branch-protection.sh    # Automated branch protection setup
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.14
- pip (Python package manager)
- Linux operating system

### Installation

1. Clone this repository:

   ```bash
   git clone <your-repo-url>
   cd Template-Desktop-Application
   ```

2. Run the setup script (installs UV, creates virtual environment, and installs dependencies):

   ```bash
   ./setup.sh
   ```

3. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

### UV Package Management

This project uses [UV](https://github.com/astral-sh/uv) for fast Python package management:

```bash
# Install a new package
uv pip install package-name

# Update requirements.txt
uv pip freeze > requirements.txt

# Sync dependencies
uv pip sync requirements.txt
```

### Running the Application

```bash
python src/main.py
```

## Branch Protection

This repository implements comprehensive branch protection to prevent accidental modifications to the `main` branch:

- **testing branch**: All development, commits, and changes happen here
- **main branch**: Protected - only receives tested merges from testing

### Setting Up Branch Protection

To set up branch protection on a new repository:

1. **Quick Setup**: Run `./setup-branch-protection.sh` for automated installation
2. **Manual Setup**: Follow step-by-step instructions in `create-branch-protections.prompt.md`
3. **Custom Setup**: Use the prompt file as a guide for customized implementations

The protection system includes:

- **Git Hooks**: Prevent human mistakes (pre-commit, post-checkout, post-merge)
- **AI Agent Script**: Blocks AI modifications to main (`.agents/branch_protection.py`)
- **Documentation**: Clear rules and workflows for all contributors

### Documentation

**For detailed information**, see:

- `create-branch-protections.prompt.md` - Complete setup instructions
- `BRANCH_PROTECTION.md` - Complete documentation
- `BRANCH_PROTECTION_QUICK.md` - Quick reference guide

**Quick rules:**

- ✅ Always work on `testing` branch
- ❌ Never commit directly to `main` branch
- ✅ Merge to `main` only after testing and approval
- ✅ Switch back to `testing` immediately after merging

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest tests/unit/test_example.py
```

### Editing UI Files

UI files are created and edited using Qt Designer (NOT hardcoded in Python):

```bash
# Open Qt Designer with a .ui file
designer src/views/ui/main_window.ui

# Or launch Qt Designer separately
designer
```

**Important**: All UI layouts, widgets, and properties should be designed in Qt Designer. Python code only loads the .ui file and connects signals.

## Architecture

### MVVM Pattern

This template follows the Model-View-ViewModel (MVVM) pattern:

- **Model**: Contains business logic, data structures, and domain rules (pure Python, no UI)
- **ViewModel**: Manages presentation logic, exposes data to views via Qt signals
- **View**: PySide6 widgets that load .ui files from Qt Designer and handle user interactions

### UI Design Workflow

**CRITICAL**: Never hardcode UI in Python. Always use Qt Designer:

1. **Design in Qt Designer**: Create/edit `.ui` files in `src/views/ui/`
2. **Load in Python**: Use `QUiLoader` to load .ui files at runtime
3. **Connect Signals**: Python code connects widget signals to ViewModel slots
4. **Update UI**: Modify layouts/widgets in Qt Designer, not Python code

Example View structure:

```python
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

class MyView(QMainWindow):
    def _load_ui(self):
        ui_file = QFile("src/views/ui/my_view.ui")
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
```

### SOLID Principles

All code should follow SOLID principles:

1. **Single Responsibility**: Each class has one clear purpose
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subtypes must be substitutable for base types
4. **Interface Segregation**: Small, focused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concrete implementations

## Development Guidelines

### For Developers

See [AGENTS.md](AGENTS.md) for:

- Quick reference and checklist
- Common patterns and templates
- Troubleshooting guide
- File structure and naming conventions

### For AI Assistants

This repository includes comprehensive instructions for AI coding assistants:

- **GitHub Copilot**: See `.github/copilot-instructions.md`
- **Other AI Agents**: See `.agents/memory.instruction.md` and `AGENTS.md`

These files contain detailed guidelines on:

- Architecture patterns to follow
- Code generation templates
- Testing strategies
- SOLID principle implementation
- PySide6 best practices

## Creating a New Feature

1. **Design**: Identify Model, ViewModel, and View responsibilities
2. **Test**: Write tests first (TDD approach)
3. **Implement**:
   - Create Model (pure Python, no Qt)
   - Create ViewModel (QObject with signals)
   - Create View (PySide6 widgets)
4. **Verify**: Run tests and ensure all pass

Example:

```bash
# Create model
touch src/models/my_feature.py
touch tests/unit/test_my_feature_model.py

# Create viewmodel
touch src/viewmodels/my_feature_viewmodel.py
touch tests/unit/test_my_feature_viewmodel.py

# Create view
touch src/views/my_feature_view.py
```

## Dependencies

Core dependencies:

```
PySide6>=6.5.0          # Qt for Python UI framework
pytest>=7.4.0           # Testing framework
pytest-qt>=4.2.0        # Qt testing plugin
pytest-mock>=3.11.0     # Mocking for tests
pytest-cov>=4.1.0       # Coverage reporting
```

## Contributing

When contributing to this template:

1. Follow the MVVM architecture strictly
2. Maintain SOLID principles
3. Write tests for all new code
4. Use type hints on all functions
5. Add docstrings to public APIs
6. Run tests before committing

## License

See [LICENSE](LICENSE) file for details.

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Pytest Documentation](https://docs.pytest.org/)
- [MVVM Pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
