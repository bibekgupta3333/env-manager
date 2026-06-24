.PHONY: install test lint typecheck clean check shellcheck binary run-daemon

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=env_manager --cov-report=term-missing

lint:
	ruff check env_manager/ tests/

flake8:
	flake8 env_manager/ tests/

format:
	black --line-length=79 env_manager/ tests/

lint-fix:
	ruff check --fix env_manager/ tests/

shellcheck:
	shellcheck testbed/run_e2e.sh

typecheck:
	mypy env_manager/

check: lint flake8 shellcheck typecheck test
	@echo "All checks passed"

binary:
	pyinstaller env-manager.spec --clean --noconfirm
	@echo "Binary built: dist/envs-dist/envs"

run-daemon:
	uvicorn env_manager.daemon.server:app --host 0.0.0.0 --port 9876 --reload

bump-patch:
	bump-my-version bump patch

bump-minor:
	bump-my-version bump minor

bump-major:
	bump-my-version bump major

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
