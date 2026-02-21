# Contributing to TextTools

## Setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Branch Workflow

All development happens on the `testing` branch. `main` is protected and only receives human-authorized merges from `testing`.

```bash
git checkout testing
```

## Development Cycle

1. Write tests first (TDD)
2. Implement in the correct MVVM layer
3. Run full test suite before committing

```bash
pytest tests/          # runs tests + coverage automatically
mypy src/              # type check
black src/ tests/      # format
isort src/ tests/      # import order
```

## Architecture Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| `models/` | Pure Python, dataclasses, validation | Any Qt import |
| `viewmodels/` | QObject, Signal/Slot, call services | Direct widget access |
| `views/` | Load .ui files, findChild(), signal connections | Business logic |
| `services/` | File I/O, external APIs | Qt imports |

New dependencies between layers must flow downward only. Never skip layers.

Each ViewModel defines its own `ServiceProtocol` (using `typing.Protocol`) in the same file as the ViewModel itself.

## UI

Design in Qt Designer, save to `src/views/ui/`. Never hardcode layouts in Python. Widget `objectName` values in `.ui` files must match what `findChild()` calls in the corresponding view. See `DESIGN.md` Appendix A for the canonical objectName list.

## Code Standards

- Type hints required on all functions (`mypy` strict mode enforced)
- Google-style docstrings on all public APIs
- Signals for all cross-layer communication — no direct method calls from ViewModel into View
- Long operations must run in `QThread` — never block the UI thread

## Commit Format

```
feat: add encoding conversion model
fix: signal not emitted on empty result
test: add edge cases for find/replace viewmodel
docs: update widget objectNames in DESIGN.md
```

## Checklist Before Committing

- [ ] Branch is `testing`, not `main`
- [ ] `pytest tests/` passes
- [ ] `mypy src/` passes with 0 errors
- [ ] MVVM layer boundaries respected
- [ ] No Qt imports in models or services
