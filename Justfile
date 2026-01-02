@default:
  @just --list

# Run test, lint, check, hatch build
@build: test lint check
  uv build

@check:
  uv run ruff format --check

# Remove dist and egg-info
@clean:
  -rm dist/*
  -rm src/filelist_tools.egg-info/*

@format:
  uv run ruff format

@lint:
  uv run ruff check

@test:
  uv run pytest -vv

# Run test matrix using tox
@tox:
  uv run tox

# Redirect 'ty check' to temp.txt
@ty:
  uv run ty check > temp.txt
