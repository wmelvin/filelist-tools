@default:
  @just --list

# Run test, lint, check, hatch build
@build: test lint check
  hatch build

@check:
  hatch fmt --check

# Remove dist and egg-info
@clean:
  rm dist/*
  rmdir dist
  rm src/filelist_tools.egg-info/*
  rmdir src/filelist_tools.egg-info

@format:
  hatch fmt

@lint:
  hatch fmt --linter

@test:
  hatch run test
  # hatch run pytest -vv
