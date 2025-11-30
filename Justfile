@default:
  @just --list

# Run test (matrix), lint, check, hatch build
@build: testmx lint check
  hatch build

@check:
  hatch fmt --check

# Remove dist and egg-info
@clean:
  -rm dist/*
  -rm src/filelist_tools.egg-info/*

@format:
  hatch fmt

@lint:
  hatch fmt --linter

@test:
  hatch run test

# Run test matrix
@testmx:
  hatch run test:test

# Run types:check (mypy)
@types:
  hatch run types:check
