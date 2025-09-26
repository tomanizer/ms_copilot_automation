PY := python3
VENV := venv
ACT := source $(VENV)/bin/activate

.PHONY: venv install browsers test chat ask clean

venv:
	$(PY) -m venv $(VENV)

install: venv
	$(ACT) && python -m pip install --upgrade pip && pip install -r requirements.txt

browsers:
	$(ACT) && python -m playwright install

test:
	$(ACT) && PYTHONPATH=$$(pwd) pytest -q

chat:
	$(ACT) && PYTHONPATH=$$(pwd) python -m src.cli.main chat "$(PROMPT)"

ask:
	$(ACT) && PYTHONPATH=$$(pwd) python -m src.cli.main ask-with-file "$(FILE)" "$(PROMPT)" --out "$(OUT)"

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache htmlcov .coverage
