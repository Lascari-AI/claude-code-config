# Managing Dependencies in UV Projects

## Overview

The documentation explains how to handle project dependencies using UV's dependency management system integrated with `pyproject.toml`.

## Adding Dependencies

UV provides the `uv add` command to include packages in your project. According to the guide, you can "add dependencies to your `pyproject.toml`" using this straightforward approach.

### Basic Usage
```
$ uv add requests
```

### Advanced Options

The system supports multiple installation scenarios:

- **Version constraints**: `uv add 'requests==2.31.0'`
- **Git-based dependencies**: `uv add git+https://github.com/psf/requests`
- **Bulk imports**: `uv add -r requirements.txt -c constraints.txt`

## Removing Dependencies

The `uv remove` command eliminates packages from your project configuration:
```
$ uv remove requests
```

## Upgrading Packages

To update a specific dependency while preserving other locked versions, use:
```
$ uv lock --upgrade-package requests
```

This approach "attempt[s] to update the specified package to the latest compatible version, while keeping the rest of the lockfile intact."

## Key Concept

The `pyproject.toml` file serves as the specification layer, while `uv.lock` maintains exact resolved versions for reproducibility across environments. Manual edits to the lockfile are discouraged—UV manages it automatically.
