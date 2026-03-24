PYTHON ?= python3

.PHONY: help install install-dev lint typecheck test format build clean docs docs-serve

help:
	@echo "Targets:"
	@echo "  install      Install package"
	@echo "  install-dev  Install package with dev dependencies"
	@echo "  lint         Run ruff checks"
	@echo "  format       Run ruff format"
	@echo "  typecheck    Run mypy"
	@echo "  test         Run pytest"
	@echo "  build        Build wheel/sdist"
	@echo "  docs         Build MkDocs docs"
	@echo "  docs-serve   Serve docs locally"
	@echo "  clean        Remove build artifacts"

install:
	$(PYTHON) -m pip install .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy proofagent

test:
	$(PYTHON) -m pytest -q

build:
	$(PYTHON) -m pip install build
	$(PYTHON) -m build

docs:
	$(PYTHON) -m mkdocs build

docs-serve:
	$(PYTHON) -m mkdocs serve

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info site
