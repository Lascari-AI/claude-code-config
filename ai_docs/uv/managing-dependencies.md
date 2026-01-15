# Working on Projects with uv

## Overview

uv provides comprehensive support for managing Python projects with dependencies defined in a `pyproject.toml` file.

## Creating a New Project

Initialize a project using:

```bash
$ uv init hello-world
$ cd hello-world
```

Or create in the current directory:

```bash
$ mkdir hello-world
$ cd hello-world
$ uv init
```

This generates:
- `.gitignore`
- `.python-version`
- `README.md`
- `main.py` (a simple "Hello world" program)
- `pyproject.toml`

Test it with: `$ uv run main.py`

## Project Structure

A complete project includes:

```
.
├── .venv/
├── .python-version
├── README.md
├── main.py
├── pyproject.toml
└── uv.lock
```

### Key Files

**pyproject.toml**: Contains project metadata and dependencies
```toml
[project]
name = "hello-world"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
dependencies = []
```

**.python-version**: Specifies the default Python version for the project's virtual environment

**.venv**: The isolated virtual environment containing project dependencies

**uv.lock**: A human-readable, cross-platform lockfile with exact resolved dependency versions. Should be committed to version control for reproducible installations across machines.

## Managing Dependencies

Add dependencies with:
```bash
$ uv add requests
$ uv add 'requests==2.31.0'
$ uv add git+https://github.com/psf/requests
```

Import from existing files:
```bash
$ uv add -r requirements.txt -c constraints.txt
```

Remove packages:
```bash
$ uv remove requests
```

Upgrade packages:
```bash
$ uv lock --upgrade-package requests
```

## Viewing Versions

```bash
$ uv version
hello-world 0.7.0

$ uv version --short
0.7.0

$ uv version --output-format json
{
    "package_name": "hello-world",
    "version": "0.7.0",
    "commit_info": null
}
```

## Running Commands

Use `uv run` to execute scripts or commands in the project environment:

```bash
$ uv add flask
$ uv run -- flask run -p 3000
$ uv run example.py
```

Alternatively, manually sync and activate the environment:

**macOS/Linux**:
```bash
$ uv sync
$ source .venv/bin/activate
$ flask run -p 3000
```

**Windows**:
```powershell
PS> uv sync
PS> .venv\Scripts\activate
PS> flask run -p 3000
```

## Building Distributions

Generate source and wheel distributions:

```bash
$ uv build
$ ls dist/
hello-world-0.1.0-py3-none-any.whl
hello-world-0.1.0.tar.gz
```

## Additional Resources

For more information, consult the projects concept page and command reference documentation.
