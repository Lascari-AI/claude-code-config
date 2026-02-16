#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "rich",
# ]
# ///

"""
Migration Runner for Multi-Agent Orchestration Database

Runs SQL migrations in order without dropping existing tables.
Uses idempotent operations (CREATE IF NOT EXISTS, CREATE OR REPLACE).

Usage:
    uv run apps/orchestrator_db/run_migrations.py

Features:
    - Runs migrations in dependency order (0-7)
    - Idempotent - safe to run multiple times
    - Preserves existing data
    - Rich terminal output with progress tracking
    - Loads DATABASE_URL from .env file

Requirements:
    - psql command-line tool installed
    - DATABASE_URL set in root .env file
    - NeonDB connection with SSL
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Migration files in dependency order
MIGRATIONS = [
    "0_orchestrator_agents.sql",
    "1_agents.sql",
    "2_prompts.sql",
    "3_agent_logs.sql",
    "4_system_logs.sql",
    "5_indexes.sql",
    "6_functions.sql",
    "7_triggers.sql",
    "8_orchestrator_chat.sql",
    "9_ai_developer_workflows.sql",
]

def main():
    console.print(Panel.fit(
        "[bold cyan]Multi-Agent Orchestration Database Migrations[/bold cyan]",
        border_style="cyan"
    ))

    # Load .env from project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_file = project_root / ".env"
    migrations_dir = script_dir / "migrations"

    if not env_file.exists():
        console.print(f"[red]✗ Error:[/red] .env file not found at {env_file}", style="bold")
        console.print("Create a .env file with DATABASE_URL='your-neon-connection-string'")
        sys.exit(1)

    load_dotenv(env_file)

    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        console.print("[red]✗ Error:[/red] DATABASE_URL environment variable is required", style="bold")
        console.print(f"Add DATABASE_URL to {env_file}")
        sys.exit(1)

    # Check if psql is available
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]✗ Error:[/red] psql command not found", style="bold")
        console.print("Install PostgreSQL client tools to use this script")
        sys.exit(1)

    # Verify migrations directory exists
    if not migrations_dir.exists():
        console.print(f"[red]✗ Error:[/red] Migrations directory not found at {migrations_dir}", style="bold")
        sys.exit(1)

    console.print(f"\n[dim]Using .env from:[/dim] {env_file}")
    console.print(f"[dim]Migrations directory:[/dim] {migrations_dir}")
    console.print(f"[dim]Database:[/dim] {database_url.split('@')[1].split('?')[0] if '@' in database_url else 'unknown'}\n")

    # Run migrations
    failed = []
    succeeded = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for migration_file in MIGRATIONS:
            migration_path = migrations_dir / migration_file

            if not migration_path.exists():
                console.print(f"[yellow]⚠ Warning:[/yellow] Migration file not found: {migration_file}")
                failed.append((migration_file, "File not found"))
                continue

            task = progress.add_task(f"Running {migration_file}...", total=None)

            result = subprocess.run(
                ["psql", database_url, "-f", str(migration_path)],
                capture_output=True,
                text=True
            )

            progress.remove_task(task)

            if result.returncode == 0:
                console.print(f"[green]✓[/green] {migration_file}")
                succeeded.append(migration_file)
            else:
                console.print(f"[red]✗[/red] {migration_file}")
                console.print(f"[dim]{result.stderr}[/dim]")
                failed.append((migration_file, result.stderr))

    # Summary
    console.print()
    if failed:
        console.print(Panel.fit(
            f"[red]Migration completed with errors[/red]\n"
            f"Succeeded: {len(succeeded)}/{len(MIGRATIONS)}\n"
            f"Failed: {len(failed)}/{len(MIGRATIONS)}",
            border_style="red",
            title="Migration Status"
        ))

        # Show failed migrations
        table = Table(title="Failed Migrations", border_style="red")
        table.add_column("File", style="cyan")
        table.add_column("Error", style="red")

        for migration_file, error in failed:
            table.add_row(migration_file, error[:100] + "..." if len(error) > 100 else error)

        console.print(table)
        sys.exit(1)
    else:
        console.print(Panel.fit(
            f"[green]✓ All migrations completed successfully[/green]\n"
            f"Applied: {len(succeeded)}/{len(MIGRATIONS)} migrations",
            border_style="green",
            title="Migration Status"
        ))

        # Show created tables
        table = Table(title="Database Schema", border_style="green", show_header=False)
        table.add_column("Item", style="cyan")
        table.add_column("Description", style="dim")

        table.add_row("orchestrator_agents", "Singleton orchestrator")
        table.add_row("agents", "Managed agent registry")
        table.add_row("prompts", "Prompt history")
        table.add_row("agent_logs", "Event logs")
        table.add_row("system_logs", "Application logs")
        table.add_row("orchestrator_chat", "Human-orchestrator chat history")
        table.add_row("ai_developer_workflows", "ADW execution tracking")
        table.add_row("indexes", "Performance indexes")
        table.add_row("functions", "Trigger functions")
        table.add_row("triggers", "Auto-update triggers")

        console.print(table)

        console.print("\n[dim]Note: All migrations are idempotent - safe to run multiple times[/dim]")

if __name__ == "__main__":
    main()
