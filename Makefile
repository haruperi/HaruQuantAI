.PHONY: install install-dev format lint typecheck test coverage clean quality

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

install-dev: install
	pip install -e ".[dev]"
	pre-commit install
	pre-commit install --hook-type pre-push

format:
	black .
	isort .

lint:
	flake8 .

typecheck:
	mypy api tools scripts

test:
	pytest

coverage:
	pytest --cov=tools --cov=api --cov=scripts --cov-report=term-missing --cov-fail-under=80

quality: format lint typecheck coverage

clean:
	rm -rf .pytest_cache .mypy_cache htmlcov coverage.xml .coverage build dist *.egg-info
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
