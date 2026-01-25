#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Auto-Format Hook for Claude Code (Formatting Only)
===================================================
Type: PostToolUse
Triggers: Edit, Write, MultiEdit

A formatting-only hook that handles code style without modifying imports:
- Python: ruff format (code formatting only)
- JavaScript/TypeScript: prettier (code formatting only)
- Go: gofmt (formatting only, NOT goimports which removes unused)
- Rust: rustfmt

NOTE: Import sorting and unused import removal are handled separately by
import-cleanup.py which runs on Stop hook. This prevents premature removal
of imports that haven't been used yet during multi-step edits.

All formatters are optional - the hook gracefully skips if a tool isn't installed.
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FormatResult:
    """Result of formatting a single file."""

    file_path: str
    language: str
    formatted: bool = False
    linted: bool = False
    imports_organized: bool = False
    used_project_config: bool = False  # True if project config was detected and used
    errors: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)


def run_command(cmd: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, "", str(e)


def tool_exists(tool: str) -> bool:
    """Check if a tool is available in PATH."""
    return shutil.which(tool) is not None


def has_ruff_config(file_path: str) -> bool:
    """Check if project has ruff configuration."""
    from pathlib import Path

    # Walk up from file to find config
    current = Path(file_path).parent
    for _ in range(10):  # Max 10 levels up
        if (current / "pyproject.toml").exists():
            # Check if it has [tool.ruff] section
            try:
                content = (current / "pyproject.toml").read_text()
                if "[tool.ruff]" in content:
                    return True
            except:
                pass
        if (current / "ruff.toml").exists() or (current / ".ruff.toml").exists():
            return True
        if current == current.parent:
            break
        current = current.parent
    return False


def format_python(file_path: str) -> FormatResult:
    """
    Format Python file using ruff format only.

    This hook ONLY handles code formatting (like black).
    Import sorting and unused import removal are handled by import-cleanup.py
    which runs on the Stop hook to avoid removing imports prematurely.

    Respects existing project configuration if found.
    """
    result = FormatResult(file_path=file_path, language="python")

    if not tool_exists("ruff"):
        result.errors.append("ruff not installed - skipping Python formatting")
        return result

    # Check for existing ruff configuration
    has_config = has_ruff_config(file_path)
    result.used_project_config = has_config

    # Run ruff format only (black-compatible formatting)
    # NOTE: ruff check --fix (linting, import sorting, unused imports) is
    # intentionally NOT run here - see import-cleanup.py for Stop hook
    success, _, stderr = run_command(["ruff", "format", file_path])

    if success:
        result.formatted = True
        result.tools_used.append("ruff format")
    else:
        result.errors.append(f"ruff format: {stderr.strip()}")

    return result


def has_eslint_config(file_path: str) -> bool:
    """Check if project has ESLint configuration."""
    from pathlib import Path

    current = Path(file_path).parent
    eslint_configs = [
        "eslint.config.js",
        "eslint.config.mjs",
        "eslint.config.cjs",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yaml",
        ".eslintrc.yml",
    ]
    for _ in range(10):
        for config in eslint_configs:
            if (current / config).exists():
                return True
        # Check package.json for eslintConfig
        pkg_json = current / "package.json"
        if pkg_json.exists():
            try:
                import json

                with open(pkg_json) as f:
                    pkg = json.load(f)
                if "eslintConfig" in pkg:
                    return True
            except:
                pass
        if current == current.parent:
            break
        current = current.parent
    return False


def has_prettier_config(file_path: str) -> bool:
    """Check if project has Prettier configuration."""
    from pathlib import Path

    current = Path(file_path).parent
    prettier_configs = [
        ".prettierrc",
        ".prettierrc.json",
        ".prettierrc.yaml",
        ".prettierrc.yml",
        ".prettierrc.js",
        ".prettierrc.cjs",
        "prettier.config.js",
        "prettier.config.cjs",
    ]
    for _ in range(10):
        for config in prettier_configs:
            if (current / config).exists():
                return True
        # Check package.json for prettier config
        pkg_json = current / "package.json"
        if pkg_json.exists():
            try:
                import json

                with open(pkg_json) as f:
                    pkg = json.load(f)
                if "prettier" in pkg:
                    return True
            except:
                pass
        if current == current.parent:
            break
        current = current.parent
    return False


def format_javascript(file_path: str) -> FormatResult:
    """
    Format JavaScript/TypeScript file using prettier only.

    NOTE: ESLint is intentionally NOT run here because it can remove unused imports.
    ESLint (including import-related rules) is handled by import-cleanup.py on Stop hook.

    Respects existing project configuration if found.
    Only runs tools if project has appropriate config.
    """
    result = FormatResult(file_path=file_path, language="javascript/typescript")

    has_prettier = has_prettier_config(file_path)
    result.used_project_config = has_prettier

    # Prettier for formatting only (only if config exists)
    # NOTE: ESLint is handled by import-cleanup.py on Stop hook
    if tool_exists("prettier") and has_prettier:
        success, _, stderr = run_command(["prettier", "--write", file_path])
        if success:
            result.formatted = True
            result.tools_used.append("prettier")
        else:
            result.errors.append(f"prettier: {stderr.strip()}")

    return result


def format_go(file_path: str) -> FormatResult:
    """
    Format Go file using gofmt only.

    NOTE: goimports (which removes unused imports) is intentionally NOT used here.
    Import organization is handled by import-cleanup.py on the Stop hook.
    """
    result = FormatResult(file_path=file_path, language="go")

    # Use gofmt for formatting only (no import manipulation)
    # goimports is handled by import-cleanup.py on Stop hook
    if tool_exists("gofmt"):
        success, _, stderr = run_command(["gofmt", "-w", file_path])
        if success:
            result.formatted = True
            result.tools_used.append("gofmt")
        else:
            result.errors.append(f"gofmt: {stderr.strip()}")
    else:
        result.errors.append("gofmt not installed")

    return result


def format_rust(file_path: str) -> FormatResult:
    """Format Rust file using rustfmt."""
    result = FormatResult(file_path=file_path, language="rust")

    if tool_exists("rustfmt"):
        success, _, stderr = run_command(["rustfmt", file_path])
        if success:
            result.formatted = True
            result.tools_used.append("rustfmt")
        else:
            result.errors.append(f"rustfmt: {stderr.strip()}")
    else:
        result.errors.append("rustfmt not installed")

    return result


def get_language_and_formatter(file_path: str) -> Optional[callable]:
    """Determine language from file extension and return appropriate formatter."""
    ext = Path(file_path).suffix.lower()

    formatters = {
        # Python
        ".py": format_python,
        ".pyi": format_python,
        # JavaScript/TypeScript
        ".js": format_javascript,
        ".jsx": format_javascript,
        ".ts": format_javascript,
        ".tsx": format_javascript,
        ".mjs": format_javascript,
        ".cjs": format_javascript,
        # Go
        ".go": format_go,
        # Rust
        ".rs": format_rust,
    }

    return formatters.get(ext)


def format_output(results: list[FormatResult]) -> str:
    """Generate concise output for the formatting results."""
    if not results:
        return ""

    lines = []

    for r in results:
        if not r.tools_used and not r.errors:
            continue  # Skip files with no action taken

        status_parts = []
        if r.formatted:
            status_parts.append("formatted")
        if r.linted:
            status_parts.append("linted")
        if r.imports_organized:
            status_parts.append("imports sorted")

        if status_parts:
            filename = Path(r.file_path).name
            tools = ", ".join(r.tools_used)
            config_indicator = " (project config)" if r.used_project_config else ""
            lines.append(
                f"  {filename}: {' + '.join(status_parts)} [{tools}]{config_indicator}"
            )

        for error in r.errors:
            lines.append(f"  {Path(r.file_path).name}: {error}")

    if lines:
        return "\n".join(lines)
    return ""


def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Only process Edit, Write, MultiEdit tools
        if tool_name not in ("Edit", "Write", "MultiEdit"):
            sys.exit(0)

        # Collect files to format
        files_to_format = []

        # Get file_path from tool_input
        file_path = tool_input.get("file_path", "")
        if file_path and Path(file_path).exists():
            files_to_format.append(file_path)

        # Also check CLAUDE_FILE_PATHS environment variable (for compatibility)
        env_files = os.environ.get("CLAUDE_FILE_PATHS", "")
        if env_files:
            for f in env_files.split():
                if f and Path(f).exists() and f not in files_to_format:
                    files_to_format.append(f)

        if not files_to_format:
            sys.exit(0)

        # Format each file
        results = []
        for file_path in files_to_format:
            formatter = get_language_and_formatter(file_path)
            if formatter:
                result = formatter(file_path)
                results.append(result)

        # Output results
        output = format_output(results)
        if output:
            print(output)

        sys.exit(0)

    except json.JSONDecodeError:
        # No valid JSON input - exit silently
        sys.exit(0)
    except Exception as e:
        # Don't block on errors
        print(f"Auto-format hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
