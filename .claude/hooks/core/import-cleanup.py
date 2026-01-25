#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Import Cleanup Hook for Claude Code
====================================
Type: Stop
Triggers: When agent finishes (Stop event)

Handles import sorting and unused import removal AFTER the agent completes.
This prevents premature removal of imports that the agent added but hasn't
used yet during multi-step edits.

Operations:
- Python: ruff check --fix --select I,F401 (isort + unused imports)
- Go: goimports -w (formatting + import organization)
- JavaScript/TypeScript: eslint --fix (if configured with import rules)

Determines which files to process by checking git status for modified files.
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
class CleanupResult:
    """Result of cleaning up imports in a single file."""

    file_path: str
    language: str
    imports_organized: bool = False
    unused_removed: bool = False
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


def get_modified_files() -> list[str]:
    """
    Get list of modified files from git.
    Returns absolute paths of modified files.
    """
    try:
        # Get both staged and unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            # Try without HEAD (for new repos or initial commits)
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                timeout=10,
            )

        if result.returncode == 0 and result.stdout.strip():
            # Get git root directory
            root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_root = (
                root_result.stdout.strip()
                if root_result.returncode == 0
                else os.getcwd()
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    abs_path = os.path.join(git_root, line)
                    if os.path.exists(abs_path):
                        files.append(abs_path)
            return files

        # Also check for untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_root = (
                root_result.stdout.strip()
                if root_result.returncode == 0
                else os.getcwd()
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    abs_path = os.path.join(git_root, line)
                    if os.path.exists(abs_path):
                        files.append(abs_path)
            return files

    except Exception:
        pass

    return []


def has_ruff_config(file_path: str) -> bool:
    """Check if project has ruff configuration."""
    current = Path(file_path).parent
    for _ in range(10):  # Max 10 levels up
        if (current / "pyproject.toml").exists():
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


def has_eslint_config(file_path: str) -> bool:
    """Check if project has ESLint configuration."""
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
        pkg_json = current / "package.json"
        if pkg_json.exists():
            try:
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


def cleanup_python(file_path: str) -> CleanupResult:
    """
    Clean up Python imports using ruff.

    Runs:
    - I (isort): Import sorting
    - F401: Remove unused imports
    """
    result = CleanupResult(file_path=file_path, language="python")

    if not tool_exists("ruff"):
        result.errors.append("ruff not installed - skipping import cleanup")
        return result

    has_config = has_ruff_config(file_path)

    if has_config:
        # Use project's configuration
        cmd = ["ruff", "check", "--fix", file_path]
    else:
        # Use minimal defaults for import cleanup only
        cmd = [
            "ruff",
            "check",
            "--fix",
            "--select",
            "I,F401",  # Only isort and unused imports
            file_path,
        ]

    success, _, stderr = run_command(cmd)

    if success or "error" not in stderr.lower():
        result.imports_organized = True
        result.unused_removed = True
        result.tools_used.append("ruff check --fix (imports)")
    else:
        result.errors.append(f"ruff: {stderr.strip()}")

    return result


def cleanup_go(file_path: str) -> CleanupResult:
    """
    Clean up Go imports using goimports.

    goimports handles both formatting and import organization,
    including removing unused imports.
    """
    result = CleanupResult(file_path=file_path, language="go")

    if tool_exists("goimports"):
        success, _, stderr = run_command(["goimports", "-w", file_path])
        if success:
            result.imports_organized = True
            result.unused_removed = True
            result.tools_used.append("goimports")
        else:
            result.errors.append(f"goimports: {stderr.strip()}")
    else:
        result.errors.append("goimports not installed")

    return result


def cleanup_javascript(file_path: str) -> CleanupResult:
    """
    Clean up JavaScript/TypeScript imports using eslint.

    Only runs if project has eslint config (import rules are project-specific).
    """
    result = CleanupResult(file_path=file_path, language="javascript/typescript")

    if not has_eslint_config(file_path):
        # No eslint config - nothing to do
        return result

    if tool_exists("eslint"):
        success, _, stderr = run_command(["eslint", "--fix", file_path])
        if success or "error" not in stderr.lower():
            result.imports_organized = True
            result.tools_used.append("eslint --fix")
        else:
            result.errors.append(f"eslint: {stderr.strip()}")
    else:
        result.errors.append("eslint not installed but config found")

    return result


def get_cleanup_function(file_path: str) -> Optional[callable]:
    """Determine language from file extension and return appropriate cleanup function."""
    ext = Path(file_path).suffix.lower()

    cleaners = {
        # Python
        ".py": cleanup_python,
        ".pyi": cleanup_python,
        # Go
        ".go": cleanup_go,
        # JavaScript/TypeScript
        ".js": cleanup_javascript,
        ".jsx": cleanup_javascript,
        ".ts": cleanup_javascript,
        ".tsx": cleanup_javascript,
        ".mjs": cleanup_javascript,
        ".cjs": cleanup_javascript,
    }

    return cleaners.get(ext)


def format_output(results: list[CleanupResult]) -> str:
    """Generate concise output for the cleanup results."""
    if not results:
        return ""

    lines = []
    processed_count = 0

    for r in results:
        if not r.tools_used and not r.errors:
            continue

        status_parts = []
        if r.imports_organized:
            status_parts.append("imports sorted")
        if r.unused_removed:
            status_parts.append("unused removed")

        if status_parts:
            processed_count += 1
            filename = Path(r.file_path).name
            tools = ", ".join(r.tools_used)
            lines.append(f"  {filename}: {' + '.join(status_parts)} [{tools}]")

        for error in r.errors:
            lines.append(f"  {Path(r.file_path).name}: {error}")

    if lines:
        header = f"Import cleanup ({processed_count} file{'s' if processed_count != 1 else ''}):"
        return header + "\n" + "\n".join(lines)
    return ""


def main():
    try:
        # Get modified files from git
        files_to_clean = get_modified_files()

        if not files_to_clean:
            # No modified files found
            sys.exit(0)

        # Clean up imports in each file
        results = []
        for file_path in files_to_clean:
            cleaner = get_cleanup_function(file_path)
            if cleaner:
                result = cleaner(file_path)
                results.append(result)

        # Output results
        output = format_output(results)
        if output:
            print(output)

        sys.exit(0)

    except Exception as e:
        # Don't block on errors
        print(f"Import cleanup hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
