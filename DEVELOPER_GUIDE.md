# Developer Quick Reference

## 🚀 Getting Started

```bash
# Clone and setup
git clone <repo>
cd ms_copilot_automation

# Create virtual environment and install
make install-dev

# Install Playwright browsers
make browsers

# Set up pre-commit hooks (recommended)
pip install pre-commit
pre-commit install
```

---

## 🧪 Testing

```bash
# Run quick tests
make test

# Run with coverage report
make test-cov

# Run E2E tests (requires credentials)
make test-e2e

# Run specific test file
pytest tests/test_chat.py -v

# View coverage in browser
open htmlcov/index.html
```

---

## 🔍 Code Quality

```bash
# Run all quality checks (lint + format + type-check + test)
make check

# Lint code
make lint              # Check only
make lint-fix          # Auto-fix issues

# Format code
make format            # Format in place
make format-check      # Check only (CI mode)

# Type check
make type-check
```

---

## 🛠️ Development Workflow

### Before Committing
```bash
# Option 1: Use pre-commit (automatic)
git commit -m "Your message"  # Pre-commit runs automatically

# Option 2: Manual check
make check
git add .
git commit -m "Your message"
```

### Fixing Issues
```bash
# Auto-fix most linting issues
make lint-fix

# Format all code
make format

# If type errors, check the output
make type-check
```

---

## 📝 Code Style Guidelines

### Imports
- Standard library first
- Third-party packages second
- Local imports last
- Alphabetically sorted within each group

### Type Hints
- Use type hints for function parameters and return values
- Use `Optional[T]` or `T | None` for nullable types
- Use `Path` instead of `str` for file paths

### Docstrings
Use restructured text format:
```python
def my_function(param1: str, param2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    :param param1: Description of param1
    :type param1: str
    :param param2: Description of param2
    :type param2: int
    :returns: Description of return value
    :rtype: bool
    :raises ValueError: When something goes wrong
    """
```

### Logging
- Always use logging, never print
- Use appropriate levels: DEBUG, INFO, WARNING, ERROR
- Include context in log messages

```python
logger.info("Processing file", extra={"file": file_path, "size": size})
logger.error("Failed to process: %s", error, exc_info=True)
```

---

## 🐛 Debugging

### Run with Debug Logging
```bash
ms-copilot --log-level DEBUG chat "test"
```

### Run Headed (See Browser)
```bash
ms-copilot --headed chat "test"
```

### Playwright Debug Mode
```bash
PWDEBUG=1 ms-copilot chat "test"
```

### Run Single Test with Output
```bash
pytest tests/test_chat.py::test_normalise_response_decodes_entities_and_drops_citations -v -s
```

---

## 📦 Dependencies

### Adding New Dependencies

1. Add to `pyproject.toml`:
```toml
dependencies = [
    "new-package>=1.0.0",
]
```

2. Update `requirements.txt`:
```bash
echo "new-package>=1.0.0" >> requirements.txt
```

3. Install:
```bash
pip install -e .
```

### Adding Dev Dependencies

1. Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "existing-packages...",
    "new-dev-tool>=1.0.0",
]
```

2. Install:
```bash
pip install -e ".[dev]"
```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configuration |
| `pytest.ini` | Pytest and coverage configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `.github/workflows/test.yml` | CI/CD pipeline |
| `Makefile` | Common development commands |
| `.env` | Local environment variables (not in git) |

---

## 📊 Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| `copilot_controller.py` | 79% | 85% |
| `logger.py` | 94% | 95% |
| `files.py` | 57% | 70% |
| `config.py` | 52% | 70% |
| `chat.py` | 35% | 60% |
| `cli/main.py` | 34% | 50% |
| `ui.py` | 22% | 60% |
| `m365_auth.py` | 13% | 40% |

**Overall Target**: 60% (currently 44%)

---

## 🚨 Common Issues

### Tests Failing After Changes
```bash
# Update mocks if you added new methods to Page/Context
# Check tests/test_copilot_controller.py DummyPage class
```

### Import Errors
```bash
# Reinstall in editable mode
pip install -e .
```

### Coverage Too Low
```bash
# Lower threshold temporarily in pytest.ini
# Or add more tests
```

### Linting Errors
```bash
# Auto-fix most issues
make lint-fix

# For unfixable issues, add to pyproject.toml ignore list
```

### Type Check Failures
```bash
# Add type hints or
# Add to pyproject.toml overrides for third-party libs
```

---

## 🌐 CI/CD Pipeline

### What Runs on Push/PR
1. **Lint Check** - Ruff linting
2. **Format Check** - Code formatting
3. **Type Check** - MyPy type checking
4. **Tests** - Full test suite on Python 3.10, 3.11, 3.12
5. **Coverage** - Reports uploaded to Codecov

### Viewing Results
- Check the "Actions" tab on GitHub
- Failed checks will block merging (if configured)
- Coverage reports available on Codecov

---

## 🎯 Best Practices

1. **Write tests first** (TDD approach)
2. **Keep functions small** (single responsibility)
3. **Use type hints** everywhere
4. **Log, don't print**
5. **Handle errors explicitly**
6. **Document complex logic**
7. **Run `make check` before pushing**
8. **Keep commits focused and atomic**
9. **Write meaningful commit messages**
10. **Update tests when changing behavior**

---

## 📚 Useful Commands Cheat Sheet

```bash
# Development
make install-dev      # Install with dev tools
make test-cov        # Test with coverage
make check           # All quality checks
make lint-fix        # Fix lint issues
make format          # Format code

# Running the CLI
ms-copilot --help
ms-copilot auth --manual
ms-copilot chat "Hello"
ms-copilot ask-with-file doc.pdf "Summarize"

# Debugging
ms-copilot --headed --log-level DEBUG chat "test"
PWDEBUG=1 ms-copilot chat "test"

# Git
git add .
make check           # Before committing!
git commit -m "message"
git push
```

---

## 💡 Tips

- Use VS Code with Python extension for best experience
- Install Ruff extension for real-time linting
- Install Mypy extension for type checking
- Use GitHub Copilot or similar for test generation
- Keep the `htmlcov/` folder open to track coverage
- Run `make check` in a separate terminal while coding

---

## 🆘 Getting Help

1. Check existing tests for examples
2. Read docstrings in source code
3. Check `IMPROVEMENTS.md` for recent changes
4. Run with `--log-level DEBUG` for verbose output
5. Use Playwright inspector: `PWDEBUG=1`

---

Last updated: October 1, 2025

