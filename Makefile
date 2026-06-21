.PHONY: install test lint typecheck clean check

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=env_manager --cov-report=term-missing

lint:
	ruff check env_manager/ tests/

lint-fix:
	ruff check --fix env_manager/ tests/

typecheck:
	mypy env_manager/

check: lint typecheck test
	@echo "All checks passed"

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
