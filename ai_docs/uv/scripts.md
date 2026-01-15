# Running Scripts

## Overview

UV enables execution of Python scripts with automatic dependency management. Scripts run in on-demand environments rather than requiring manual virtual environment setup.

## Key Concepts

### Basic Script Execution

Scripts without dependencies execute simply:

```bash
uv run example.py
```

The tool automatically manages virtual environments for you.

### Dependency Management

Two primary approaches exist:

1. **Command-line declaration**: `uv run --with rich example.py`
2. **Inline metadata** in script files using PEP 723 format

## Core Features

### Simple Scripts

Scripts using only standard library modules require no additional setup. Arguments pass directly:

```bash
uv run example.py test
```

### Scripts with Dependencies

Use the `--with` flag for single dependencies or repeat it for multiple packages. Version constraints work:

```bash
uv run --with 'rich>12,<13' example.py
```

### Inline Script Metadata

Initialize with:

```bash
uv init --script example.py --python 3.12
```

Add dependencies using:

```bash
uv add --script example.py 'requests<3' 'rich'
```

This creates a `# /// script` section declaring requirements directly in the file.

Example script with inline metadata:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# ///

import requests
from rich.pretty import pprint

resp = requests.get("https://peps.python.org/api/peps.json")
data = resp.json()
pprint([(k, v["title"]) for k, v in data.items()][:10])
```

### Shebang Execution

Scripts can become executable with:

```python
#!/usr/bin/env -S uv run --script
```

Make executable and run directly without the `uv run` prefix:

```bash
chmod +x example.py
./example.py
```

### Python Version Management

Request specific versions:

```bash
uv run --python 3.10 example.py
```

Specify in metadata:

```python
# /// script
# requires-python = ">=3.12"
# ///
```

### Locking & Reproducibility

- Lock dependencies: `uv lock --script example.py`
- Creates adjacent `.lock` files
- Add `exclude-newer` timestamps in metadata for reproducible future runs

Example with locked dependencies:

```bash
uv lock --script example.py
# Creates example.py.lock
```

For reproducible builds, add to metadata:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich"]
# exclude-newer = "2024-03-25T00:00:00Z"
# ///
```

### GUI Scripts

Windows `.pyw` files automatically use `pythonw`. Works with GUI libraries like PyQt5 and tkinter.

### Alternative Package Indexes

Use custom package indexes:

```bash
uv add --index "https://example.com/simple" --script example.py
```

## Important Notes

- When using inline script metadata, project dependencies are automatically ignored—the `--no-project` flag becomes unnecessary
- Use `--no-project` when *not* using inline metadata to skip project installation
- UV automatically manages virtual environments in the background
- Scripts with inline metadata are self-contained and portable

## Common Patterns

### Quick Script with External Dependency

```bash
uv run --with rich script.py
```

### Production Script with Locked Dependencies

```bash
# Initialize script
uv init --script script.py --python 3.12

# Add dependencies
uv add --script script.py requests rich

# Lock dependencies
uv lock --script script.py

# Run locked script
uv run script.py
```

### Executable Script

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///

import requests

def main():
    print("Hello from UV!")

if __name__ == "__main__":
    main()
```

---

**Source**: https://docs.astral.sh/uv/guides/scripts/
