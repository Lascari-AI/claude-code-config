#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///
"""
Copy Claude Configuration Script

Merges .claude/ directory from root into apps/orchestrator_3_stream/.claude/
This is a merge operation - it overwrites and adds files but never deletes.

Usage:
    uv run scripts/copy_claude.py
    ./scripts/copy_claude.py  (if executable)
"""

import shutil
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Whitelist: Only copy these directories from .claude/
# Paths are relative to .claude/ directory
COPY_WHITELIST = [
    "agents/",
    "commands/",
    "skills/",
]

# Blacklist: Never copy these specific files (even if whitelisted)
# Paths are relative to .claude/ directory
COPY_BLACKLIST = [
    "commands/prime.md",
]


def is_whitelisted(relative_path: Path) -> bool:
    """
    Check if a file should be copied based on whitelist and blacklist.

    Args:
        relative_path: Path relative to .claude/ directory

    Returns:
        True if file should be copied, False otherwise
    """
    path_str = str(relative_path)

    # Check blacklist first - if file is blacklisted, never copy
    if path_str in COPY_BLACKLIST:
        return False

    for whitelist_item in COPY_WHITELIST:
        # Check if path starts with whitelisted directory
        if path_str.startswith(whitelist_item.rstrip("/")):
            return True

    return False


def copy_claude_config():
    """
    Merge .claude/ from root into apps/orchestrator_3_stream/.claude/

    This performs a merge operation:
    - Only copies whitelisted directories (see COPY_WHITELIST)
    - Overwrites existing files
    - Creates missing directories
    - Never deletes files
    """
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define source and destination
    source_dir = project_root / ".claude"
    dest_dir = project_root / "apps" / "orchestrator_3_stream" / ".claude"

    # Validate source directory exists
    if not source_dir.exists():
        console.print(Panel(
            f"[red]Error: Source directory not found:[/red]\n{source_dir}",
            title="❌ Copy Failed",
            border_style="red",
            expand=False
        ))
        return False

    # Track statistics
    stats = {
        "copied": 0,
        "overwritten": 0,
        "skipped": 0,
        "dirs_created": 0,
        "errors": 0
    }

    errors = []
    skipped_files = []

    # Create destination directory if it doesn't exist
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
        stats["dirs_created"] += 1

    # Walk through source directory
    for source_path in source_dir.rglob("*"):
        # Skip directories (we only copy files)
        if source_path.is_dir():
            continue

        # Calculate relative path and destination
        relative_path = source_path.relative_to(source_dir)

        # Check whitelist
        if not is_whitelisted(relative_path):
            stats["skipped"] += 1
            skipped_files.append(str(relative_path))
            continue

        dest_path = dest_dir / relative_path

        try:
            # Create parent directory if needed
            if not dest_path.parent.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                stats["dirs_created"] += 1

            # Check if file exists (for statistics)
            file_exists = dest_path.exists()

            # Copy file (overwrites if exists)
            shutil.copy2(source_path, dest_path)

            # Update statistics
            if file_exists:
                stats["overwritten"] += 1
            else:
                stats["copied"] += 1

        except Exception as e:
            stats["errors"] += 1
            errors.append(f"{relative_path}: {str(e)}")

    # Create results table
    table = Table(
        title="Copy Statistics",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=False
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("New files copied", str(stats["copied"]))
    table.add_row("Files overwritten", str(stats["overwritten"]))
    table.add_row("Files skipped", str(stats["skipped"]), style="yellow")
    table.add_row("Directories created", str(stats["dirs_created"]))
    table.add_row("Total files processed", str(stats["copied"] + stats["overwritten"]))

    if stats["errors"] > 0:
        table.add_row("Errors", str(stats["errors"]), style="red")

    # Display results
    console.print()
    console.print(Panel(
        f"[bold cyan]Source:[/bold cyan] {source_dir}\n"
        f"[bold cyan]Destination:[/bold cyan] {dest_dir}",
        title="📁 Merge Operation",
        border_style="cyan",
        expand=False
    ))

    console.print()
    console.print(table)

    # Display skipped files if any (limit to first 10)
    if skipped_files:
        console.print()
        console.print(Panel(
            "\n".join(f"[yellow]•[/yellow] {file}" for file in skipped_files[:10]),
            title="⏭️  Skipped Files (Not Whitelisted)",
            border_style="yellow",
            expand=False
        ))
        if len(skipped_files) > 10:
            console.print(f"[dim]... and {len(skipped_files) - 10} more skipped files[/dim]")

    # Display errors if any
    if errors:
        console.print()
        console.print(Panel(
            "\n".join(f"[red]•[/red] {error}" for error in errors[:10]),
            title="⚠️  Errors Encountered",
            border_style="red",
            expand=False
        ))
        if len(errors) > 10:
            console.print(f"[dim]... and {len(errors) - 10} more errors[/dim]")

    # Success summary
    console.print()
    if stats["errors"] == 0:
        console.print(Panel(
            f"[green]✓[/green] Successfully merged [bold]{stats['copied'] + stats['overwritten']}[/bold] files",
            title="✅ Merge Complete",
            border_style="green",
            expand=False
        ))
        return True
    else:
        console.print(Panel(
            f"[yellow]⚠[/yellow] Merged with [bold]{stats['errors']}[/bold] errors",
            title="⚠️  Merge Complete (with errors)",
            border_style="yellow",
            expand=False
        ))
        return False


if __name__ == "__main__":
    try:
        success = copy_claude_config()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        exit(1)
    except Exception as e:
        console.print(Panel(
            f"[red]Unexpected error:[/red]\n{str(e)}",
            title="❌ Fatal Error",
            border_style="red",
            expand=False
        ))
        exit(1)
