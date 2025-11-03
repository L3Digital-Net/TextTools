---
description: "Create or update project documentation including docstrings, README, and code comments for PySide6 MVVM applications"
mode: "agent"
---

# Create or Update Project Documentation

Handle all documentation tasks for the PySide6 MVVM template project.

## Basic Process Flow

1. Analyze the current code in the file or project
2. Update docstrings and inline comments to reflect current implementation
3. Ensure documentation follows repository guidelines
4. Update README.md and other markdown files as needed
5. Verify documentation reflects MVVM architecture

## General Guidelines

- **MANDATORY**: Do not change any code logic or implementation
- **MANDATORY**: Only create or update documentation elements
- **MANDATORY**: Follow MVVM architectural documentation standards
- **Python 3.10+ REQUIRED**: Document PySide6 compatibility requirements

## Docstring Standards

### Format

Use Google or NumPy docstring style as specified in [copilot-instructions.md](../copilot-instructions.md).

### Requirements

- **ALL** public classes, methods, and functions must have docstrings
- Use type hints instead of documenting types in docstrings
- Keep descriptions concise and clear
- Document parameters, returns, and raises
- Include usage examples for complex APIs

### Example

```python
def process_data(items: list[str], validate: bool = True) -> dict[str, int]:
    """Process a list of items and return frequency counts.

    Args:
        items: List of strings to process.
        validate: Whether to validate items before processing.

    Returns:
        Dictionary mapping items to their frequency counts.

    Raises:
        ValueError: If validate is True and invalid items found.

    Example:
        >>> process_data(['a', 'b', 'a'])
        {'a': 2, 'b': 1}
    """
```

## Inline Documentation

- Use inline comments for complex logic blocks
- Explain MVVM-specific patterns and choices
- Document Qt-specific behaviors
- Clarify signal/slot connections
- Note threading considerations

## MVVM Documentation Requirements

### Model Layer

- Document business logic and validation rules
- Explain domain-specific concepts
- Note any assumptions or constraints
- No Qt-related documentation needed

### ViewModel Layer

- Document signals and their purposes
- Explain state management approach
- Note threading considerations
- Document dependencies and injection

### View Layer

- Document UI structure and organization
- Explain custom widgets or behaviors
- Note Qt Designer usage if applicable
- Document signal/slot connections

## Project Documentation Files

### README.md

- Project overview and purpose
- Quick start guide
- Installation instructions
- MVVM architecture explanation
- Development workflow
- Testing approach

### AGENTS.md

- Quick reference for AI agents
- Common patterns and templates
- Troubleshooting guide
- Development checklist

### CONTRIBUTING.md

- How to contribute
- Code style guidelines
- MVVM principles to follow
- Testing requirements
- Pull request process

## Code Comments Best Practices

- **DO**: Explain why, not what
- **DO**: Document non-obvious design decisions
- **DO**: Explain MVVM layer boundaries
- **DO**: Note Qt-specific behaviors
- **DON'T**: State the obvious
- **DON'T**: Leave TODO comments without issues
- **DON'T**: Include commented-out code

## Documentation Checklist

- [ ] All public APIs have docstrings
- [ ] Type hints are present and accurate
- [ ] Complex logic has inline comments
- [ ] MVVM architecture is documented
- [ ] README is up to date
- [ ] Examples are working and clear
- [ ] Sphinx/pdoc compatible format (if applicable)

## Template Documentation Structure

### Core Documentation Files

- **README.md**: Main project documentation with setup, usage, and architecture overview
- **QUICKSTART.md**: Quick start guide for getting up and running
- **CONTRIBUTING.md**: Guidelines for contributing to the project
- **CHANGELOG.md**: Version history and changes (maintained in root directory)
- **LICENSE**: Project license information

### GitHub Documentation

- **.github/copilot-instructions.md**: Comprehensive GitHub Copilot instructions
- **.github/prompts/**: Collection of specialized prompts for development tasks

### Agent Documentation

- **AGENTS.md**: Quick reference guide for AI agents
- **.agents/memory.instruction.md**: AI agent memory and preferences

### Branch Protection Documentation

- **BRANCH_PROTECTION.md**: Complete branch protection system documentation
- **BRANCH_PROTECTION_QUICK.md**: Quick reference for branch protection
- **create-branch-protections.prompt.md**: Setup instructions for repositories

### UI Design Documentation

- **UI_DESIGN_GUIDE.md**: Guide for creating UI with Qt Designer
- **QUICKSTART_UI_UV.md**: Quick start for UI development with UV

### Component Documentation (Optional)

For specific modules that need detailed documentation, create markdown files in the project root or a `docs/` directory:

- **ARCHITECTURE.md**: Detailed architecture document covering MVVM implementation
- **DESIGN.md**: Design decisions and patterns used in the application
- **API.md**: API documentation for public interfaces

### Testing Documentation

- **tests/README.md** (optional): Testing strategy and guidelines
- Test documentation should be minimal, as tests themselves serve as documentation
- Use descriptive test names that explain expected behavior
