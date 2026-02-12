# Agent Instructions

This file provides instructions for AI agents working on this Python SDK repository.

## Project Overview

- **Language**: Python (3.6+, CI tests on 3.7, 3.9, 3.11)
- **Package Manager**: pip with setuptools
- **Build System**: setuptools + wheel (configured via `pyproject.toml`)
- **Testing**: unittest (standard library)
- **Linting/Formatting**: Ruff
- **Published To**: PyPI as `events-sdk-python`

### Project Structure

```
hightouch/
  htevents/
    __init__.py           # Module-level API (track, identify, group, etc.)
    client.py             # Client class — core SDK logic
    consumer.py           # Queue consumer that batches and sends events
    request.py            # HTTP request handling
    oauth_manager.py      # OAuth token management
    utils.py              # Shared utilities
    version.py            # VERSION string (must match pyproject.toml)
    test/
      __init__.py         # Test loader and TestInit tests
      client.py           # Client unit tests
      consumer.py         # Consumer unit tests
      request.py          # Request unit tests
      oauth.py            # OAuth tests
      module.py           # Module-level API tests
      utils.py            # Utility tests
      constants.py        # Shared test constants
```

### Key Dependencies

Runtime dependencies (defined in `pyproject.toml` under `[project] dependencies`):

- `requests~=2.7` — HTTP client
- `backoff~=2.1` — Retry logic with exponential backoff
- `python-dateutil~=2.2` — Date parsing
- `PyJWT>=2.0,<3.0` + `pyjwt[crypto]` — JWT signing for OAuth

Dev dependencies (defined under `[project.optional-dependencies] dev`):

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

The CI matrix tests Python 3.7, 3.9, and 3.11. If you have `pyenv` or multiple Python versions available, test across versions:

```bash
# Example with pyenv
pyenv shell 3.7
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all

pyenv shell 3.9
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all

pyenv shell 3.11
python -m pip install -e .[dev] && python -m unittest hightouch.htevents.test.all
```

At minimum, ensure tests pass on Python 3.11 (the primary CI target).

---

## CI/CD

### CI Pipeline (`.github/workflows/ci.yml`)

Triggered on pushes to `master` and pull requests (ignoring markdown file changes).

Steps:
1. **Checkout** the repository
2. **Set up Python** (matrix: 3.7, 3.9, 3.11)
3. **Install dependencies**: `pip install --upgrade pip && pip install -e .[dev]`
4. **Lint**: `ruff check hightouch/htevents/` and `ruff format --diff hightouch/htevents/`
5. **Test**: `python -m unittest hightouch.htevents.test.all`

### Release Pipeline (`.github/workflows/ci-release.yml`)

Triggered when a GitHub Release is published.

Steps:
1. Checkout, set up Python 3.11
2. Install dependencies + `build` and `twine`
3. Build: `python -m build`
4. Publish to PyPI via `pypa/gh-action-pypi-publish`

---

## Version Bumping

### Semantic Versioning

- **PATCH** (0.0.3 → 0.0.4): Bug fixes, dependency updates, no new features
- **MINOR** (0.0.3 → 0.1.0): New backwards-compatible features
- **MAJOR** (0.0.3 → 1.0.0): Breaking API changes

Dependency updates are typically **PATCH** bumps.

### Files to Update

Both of these must stay in sync:
1. `pyproject.toml` → `version = "X.Y.Z"` under `[project]`
2. `hightouch/htevents/version.py` → `VERSION = 'X.Y.Z'`

---

## Publishing to PyPI

Publishing is automated via GitHub Actions on release.

### Release Process

1. Update `VERSION` in `hightouch/htevents/version.py` and `version` in `pyproject.toml`
2. Create a git tag matching the new version, push to GitHub, and merge to `master`
3. Create a new GitHub Release using the tag: https://github.com/ht-sdks/events-sdk-python/releases/new
4. Publishing the release triggers the `ci-release` workflow
5. Confirm the release on PyPI: https://pypi.org/project/events-sdk-python/

---

## Linting and Formatting

This project uses **Ruff** (v0.1.4) for both linting and formatting, configured in `ruff.toml`.

```bash
# Check for lint errors
python -m ruff check hightouch/htevents/

# Auto-fix lint errors where possible
python -m ruff check --fix hightouch/htevents/

# Check formatting (show diff without modifying)
python -m ruff format --diff hightouch/htevents/

# Apply formatting
python -m ruff format hightouch/htevents/
```

Key Ruff settings:
- Line length: 88 (same as Black)
- Target: Python 3.11
- Quote style: single quotes
- Enabled rules: Pyflakes (`F`), pycodestyle subset (`E4`, `E7`, `E9`), isort (`I`)

---

## Docker Development

The project includes a `Dockerfile` and `Makefile` for containerized development:

```bash
# Build the Docker image
make build

# Run tests in Docker
make test

# Open a Python REPL in the container
make repl

# Open a shell in the container
make shell

# Run linting/formatting in Docker
make format
```

---

## Common Issues

### Version Mismatch

The version must be identical in two places:
- `pyproject.toml` (`version = "X.Y.Z"`)
- `hightouch/htevents/version.py` (`VERSION = 'X.Y.Z'`)

If these diverge, the published package will have inconsistent version metadata.

### PyJWT Import Errors

The SDK uses `PyJWT` with the `[crypto]` extra for OAuth. If you see import errors related to `jwt` or `cryptography`, ensure:

```bash
python -m pip install "PyJWT>=2.0,<3.0" "pyjwt[crypto]"
```

### Ruff Version Pinning

The dev dependency pins `ruff==0.1.4`. If updating Ruff, be aware that newer versions may introduce new lint rules or change formatting behavior. After updating:

1. Run `ruff check hightouch/htevents/` and fix any new violations
2. Run `ruff format --diff hightouch/htevents/` to check for formatting changes
3. Apply formatting if needed: `ruff format hightouch/htevents/`

### Test Discovery

Tests are loaded via `hightouch.htevents.test.all`, which uses `pkgutil.iter_modules` to discover all test modules in the `test/` directory. If adding new test files, they will be automatically discovered — no registration needed.

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
| Docker build | `make build` |
| Docker test | `make test` |
