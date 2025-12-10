# Running Scripts

A Python script is a file intended for standalone execution, e.g., with `python <script>.py`. Using uv manages script dependencies automatically without manual environment management.

## Running Scripts Without Dependencies

For scripts with no external requirements, execute with `uv run`:

```python
print("Hello world")
```

```bash
$ uv run example.py
Hello world
```

Standard library modules work similarly:

```python
import os
print(os.path.expanduser("~"))
```

```bash
$ uv run example.py
/Users/astral
```

### Passing Arguments

Scripts accept command-line arguments:

```python
import sys
print(" ".join(sys.argv[1:]))
```

```bash
$ uv run example.py test
test

$ uv run example.py hello world!
hello world!
```

### Reading from stdin

Scripts can read directly from stdin:

```bash
$ echo 'print("hello world!")' | uv run -

uv run - <<EOF
print("hello world!")
EOF
```

### Project Context

If you use `uv run` in a _project_, i.e., a directory with a `pyproject.toml`, it will install the current project before running the script. Use `--no-project` to skip this behavior:

```bash
$ uv run --no-project example.py
```

## Running Scripts With Dependencies

When scripts require external packages, declare them explicitly. This supports on-demand environment creation rather than long-lived virtual environments.

### Using the --with Flag

For a script requiring the `rich` package:

```python
import time
from rich.progress import track

for i in track(range(20), description="For example:"):
    time.sleep(0.05)
```

Execute with dependencies:

```bash
$ uv run --with rich example.py
For example: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
```

Add version constraints:

```bash
$ uv run --with 'rich>12,<13' example.py
```

Multiple dependencies can be requested by repeating `--with`:

```bash
$ uv run --with 'dependency1' --with 'dependency2' example.py
```

## Creating Python Scripts

Initialize scripts with inline metadata using `uv init --script`:

```bash
$ uv init --script example.py --python 3.12
```

## Declaring Script Dependencies

Python supports inline script metadata via PEP 723. Use `uv add --script` to declare dependencies:

```bash
$ uv add --script example.py 'requests<3' 'rich'
```

This adds a `script` section at the file's top:

```python
# /// script
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

Run the script:

```bash
$ uv run example.py
[
│   ('1', 'PEP Purpose and Guidelines'),
│   ('2', 'Procedure for Adding New Modules'),
│   ...
]
```

### Python Version Requirements

uv also respects Python version requirements:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# Use some syntax added in Python 3.12
type Point = tuple[float, float]
print(Point)
```

The `dependencies` field must be provided even if empty. uv automatically finds and downloads required Python versions.

## Using Shebangs for Executable Files

Make scripts executable by adding a shebang:

```bash
#!/usr/bin/env -S uv run --script

print("Hello, world!")
```

Make executable and run:

```bash
$ chmod +x greet
$ ./greet
Hello, world!
```

With dependencies and version requirements:

```bash
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

import httpx

print(httpx.get("https://example.com"))
```

## Using Alternative Package Indexes

Specify alternative indexes when adding dependencies:

```bash
$ uv add --index "https://example.com/simple" --script example.py 'requests<3' 'rich'
```

This includes index data in inline metadata:

```python
# [[tool.uv.index]]
# url = "https://example.com/simple"
```

Refer to package index documentation for authentication requirements.

## Locking Dependencies

Scripts can be locked using the `uv.lock` file format:

```bash
$ uv lock --script example.py
```

This creates an adjacent `.lock` file (e.g., `example.py.lock`). Subsequent operations like `uv run --script`, `uv add --script`, `uv export --script`, and `uv tree --script` reuse locked dependencies.

## Improving Reproducibility

Add an `exclude-newer` field to limit distributions to those released before a specific date:

```python
# /// script
# dependencies = [
#   "requests",
# ]
# [tool.uv]
# exclude-newer = "2023-10-16T00:00:00Z"
# ///

import requests

print(requests.__version__)
```

Dates use RFC 3339 format (e.g., `2006-12-02T02:07:43Z`).

## Using Different Python Versions

Request specific Python versions per invocation:

```python
import sys

print(".".join(map(str, sys.version_info[:3])))
```

```bash
$ uv run example.py
3.12.6

$ uv run --python 3.10 example.py
3.10.15
```

## Using GUI Scripts

On Windows, `.pyw` files execute with `pythonw`:

```python
from tkinter import Tk, ttk

root = Tk()
root.title("uv")
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World").grid(column=0, row=0)
root.mainloop()
```

```bash
PS> uv run example.pyw
```

With dependencies:

```python
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout

app = QApplication(sys.argv)
widget = QWidget()
grid = QGridLayout()

text_label = QLabel()
text_label.setText("Hello World!")
grid.addWidget(text_label)

widget.setLayout(grid)
widget.setGeometry(100, 100, 200, 50)
widget.setWindowTitle("uv")
widget.show()
sys.exit(app.exec_())
```

```bash
PS> uv run --with PyQt5 example_pyqt.pyw
```

## Next Steps

Consult the command reference for `uv run` details, or learn about running and installing tools with uv.
