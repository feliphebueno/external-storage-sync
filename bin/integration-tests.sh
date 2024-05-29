#!/bin/sh
set -e

# Check for formatting/linting issues
ruff format --check .

# Check for PEP8 compliance
ruff check app/

# Run coverage
pytest -n 2 --cov=app --cov-branch --cov-fail-under=90 --cov-report xml --cov-report term-missing:skip-covered
