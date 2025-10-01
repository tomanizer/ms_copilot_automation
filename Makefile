PY := python3
VENV := venv
ACT := source $(VENV)/bin/activate

.PHONY: venv install install-dev browsers test test-cov test-e2e lint format type-check check chat ask clean

venv:
	$(PY) -m venv $(VENV)

install: venv
	$(ACT) && python -m pip install --upgrade pip && pip install -r requirements.txt && pip install -e .

install-dev: install
	$(ACT) && pip install -e ".[dev]"

browsers:
	$(ACT) && python -m playwright install chromium

test:
	$(ACT) && PYTHONPATH=$$(pwd) pytest -q

test-cov:
	$(ACT) && PYTHONPATH=$$(pwd) pytest -v --cov=src --cov-report=html --cov-report=term-missing

test-e2e:
	$(ACT) && M365_COPILOT_E2E=1 PYTHONPATH=$$(pwd) pytest -m copilot_e2e -v

lint:
	$(ACT) && ruff check src tests

lint-fix:
	$(ACT) && ruff check --fix src tests

format:
	$(ACT) && ruff format src tests

format-check:
	$(ACT) && ruff format --check src tests

type-check:
	$(ACT) && mypy src --ignore-missing-imports

check: lint format-check type-check test
	@echo "All checks passed!"

chat:
	$(ACT) && ms-copilot chat "$(PROMPT)"

ask:
	$(ACT) && ms-copilot ask-with-file "$(FILE)" "$(PROMPT)" --out "$(OUT)"

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache htmlcov .coverage coverage.xml .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
