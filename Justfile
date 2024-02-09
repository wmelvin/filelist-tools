@default:
  @just --list

# Run test, lint, check, pyproject-build
@build: test lint check
  pipenv run pyproject-build

# ruff format --check
@check:
  pipenv run ruff format --check

# Remove dist and egg-info
@clean:
  rm dist/*
  rmdir dist
  rm src/filelist_tools.egg-info/*
  rmdir src/filelist_tools.egg-info

# ruff format
@format:
  pipenv run ruff format

# ruff check
@lint:
  pipenv run ruff check

# pytest
@test:
  pipenv run pytest -vv
