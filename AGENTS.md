# Agent Instructions

This file provides instructions for AI agents working on this Python SDK repository.

## Project Overview

- **Language**: Python (3.6+, CI tests on 3.9, 3.11, 3.13)
- **Package Manager**: pip with setuptools
- **Build System**: setuptools + wheel (configured via `pyproject.toml`)
- **Testing**: unittest (standard library)
- **Linting/Formatting**: Ruff (configured in `ruff.toml`)
- **Published To**: PyPI as `events-sdk-python`

### Dependencies

Runtime dependencies are defined in `pyproject.toml` under `[project] dependencies`:

- `requests~=2.7` — HTTP client
- `backoff~=2.1` — Retry logic with exponential backoff
- `python-dateutil~=2.2` — Date parsing
- `PyJWT>=2.0,<3.0` + `pyjwt[crypto]` — JWT signing for OAuth

Dev dependencies are defined under `[project.optional-dependencies] dev`:

- `mock==2.0.0` — Test mocking
- `ruff==0.1.4` — Linting and formatting

---

## Updating Dependencies

### 1. Pre-flight Checks

```bash
# Check Python version
python --version

# Ensure you're at the repository root
pwd  # Should be: /path/to/events-sdk-python

# Verify the project installs cleanly
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

### 2. Establish Test Baseline

```bash
# Run the linter
python -m ruff check hightouch/htevents/
python -m ruff format --diff hightouch/htevents/

# Run all unit tests
python -m unittest hightouch.htevents.test.all
```

Record the number of passing tests and confirm zero lint errors before making any changes. This ensures you can verify nothing broke after upgrading.

### 3. Check for Security Advisories

```bash
# Install pip-audit if not already available
python -m pip install pip-audit

# Audit installed packages
python -m pip_audit
```

Review any vulnerabilities and update affected packages.

### 4. Check Outdated Packages

```bash
python -m pip list --outdated
```

This shows installed packages with newer versions available, including:
- **Current**: Installed version
- **Latest**: Newest available version
- **Type**: Whether it's a wheel or sdist

### 5. Upgrade Dependencies

#### Option A: Safe Updates (within semver range)

```bash
# Update all packages to latest within their current constraints
python -m pip install --upgrade -e .[dev]
```

#### Option B: Major Version Updates

For major version bumps, edit `pyproject.toml` directly:

1. Update version constraints under `[project] dependencies` or `[project.optional-dependencies]`
2. Reinstall:

```bash
python -m pip install --upgrade -e .[dev]
```

#### Option C: Interactive Audit with pip-tools (recommended for pinning)

```bash
# Install pip-tools (one-time)
python -m pip install pip-tools

# Compile a fully resolved requirements file from pyproject.toml
pip-compile pyproject.toml

# Upgrade all dependencies to latest compatible versions
pip-compile --upgrade pyproject.toml

# Install from the resolved file
pip-sync requirements.txt
```

### 6. Rebuild and Test

```bash
# Run the linter
python -m ruff check hightouch/htevents/
python -m ruff format --diff hightouch/htevents/

# Run all unit tests
python -m unittest hightouch.htevents.test.all

# Verify the package builds correctly
python -m pip install build
python -m build
```

Compare test results to baseline. Fix any failures before proceeding.

### 7. Verify CI Would Pass

The CI matrix tests Python 3.9, 3.11, and 3.13. If you have `pyenv` or multiple Python versions available, test across versions:

```bash
# Example with pyenv
pyenv shell 3.9
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all

pyenv shell 3.11
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all

pyenv shell 3.13
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all
```

At minimum, ensure tests pass on Python 3.13 (the latest CI target).

---

## Common Issues When Updating Dependencies

### PyJWT Import Errors

The SDK uses `PyJWT` with the `[crypto]` extra for OAuth. If you see import errors related to `jwt` or `cryptography` after upgrading, ensure:

```bash
python -m pip install "PyJWT>=2.0,<3.0" "pyjwt[crypto]"
```

### Ruff Version Pinning

The dev dependency pins `ruff==0.1.4`. If updating Ruff, be aware that newer versions may introduce new lint rules or change formatting behavior. After updating:

1. Run `ruff check hightouch/htevents/` and fix any new violations
2. Run `ruff format --diff hightouch/htevents/` to check for formatting changes
3. Apply formatting if needed: `ruff format hightouch/htevents/`

### Version Files

When bumping the package version as part of a dependency update, both of these must stay in sync:
- `pyproject.toml` → `version = "X.Y.Z"` under `[project]`
- `hightouch/htevents/version.py` → `VERSION = 'X.Y.Z'`

---

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `python -m pip install -e .[dev]` |
| Run linter | `python -m ruff check hightouch/htevents/` |
| Check formatting | `python -m ruff format --diff hightouch/htevents/` |
| Apply formatting | `python -m ruff format hightouch/htevents/` |
| Run all tests | `python -m unittest hightouch.htevents.test.all` |
| Build package | `python -m build` |
| Check outdated deps | `python -m pip list --outdated` |
| Security audit | `python -m pip_audit` |
