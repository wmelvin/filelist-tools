@default:
  @just --list

# Run test, lint, check, pyproject-build
@build: test lint check
  pipenv run pyproject-build

# ruff format --check
@check:
  pipenv run ruff format --check

# ruff format
@format:
  pipenv run ruff format

# ruff check
@lint:
  pipenv run ruff check

# pytest
@test:
  pipenv run pytest
