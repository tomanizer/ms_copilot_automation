# Contributor Guide

Thank you for your interest in improving MS365 Copilot Automation! This guide captures best practices for development.

## Workflow

1. **Fork and Clone**
   - Fork the repository and clone your fork locally.
2. **Create a Branch**
   - Use descriptive branch names (e.g., `feature/live-download` or `docs/update-readme`).
3. **Set Up the Environment**
   - Follow the [Getting Started](getting-started.md) guide to install dependencies and configure credentials.
4. **Coding Standards**
   - Use Python 3.10+ features as appropriate.
   - Aim for small, focused commits with clear messages.
   - Keep changes ASCII unless non-ASCII is already used.
5. **Static Analysis (Recommended)**
   - Run `ruff` or `flake8` if you have them configured.
   - Optional: run `mypy` for type checking; annotations are gradually being introduced.
6. **Testing**
   - Run unit tests: `PYTHONPATH=$(pwd) pytest`.
   - Opt-in live tests only when you have credentials: `M365_COPILOT_E2E=1 PYTHONPATH=$(pwd) pytest -m copilot_e2e`.
7. **Commit & Push**
   - Include a summary of the change, referencing issues when appropriate.
8. **Open a Pull Request**
   - Describe the motivation, key changes, and testing performed.

## Commit Message Style

- Use the imperative mood: `Add Playwright retry helper`, `Fix missing username check`.
- Include a brief summary (<72 characters) followed by details in the body if needed.

## Code Style

- Prefer readability over micro-optimisations.
- Add concise comments only where logic is non-obvious.
- Keep functions small; extract helpers when logic grows.

## Tests

- Contribute new tests alongside features or bug fixes.
- Use async fixtures and stubs similar to those in `tests/test_copilot_controller.py` for isolated testing.
- Keep live tests optional and resilient (skip when credentials are absent or when Copilot refuses a download).

## Documentation

- Update README and docs when CLI options, environment variables, or workflows change.
- Include examples where possible.

## Release Checklist (suggested)

- `pytest` clean
- Manual smoke test (headed auth + prompt)
- Update version metadata (if a tagging system is introduced)
- Document noteworthy changes in the changelog (future enhancement)

## Questions?

Open an issue or reach out to maintainers via the repository discussions.
