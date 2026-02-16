#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "rich",
#     "click",
# ]
# ///

"""
Table Drop Utility for Multi-Agent Orchestration Database

Safely drops individual database tables with explicit CLI flags.
Requires confirmation before executing destructive operations.

Usage:
    # List available tables
    uv run apps/orchestrator_db/drop_table.py --list

    # Drop a single table
    uv run apps/orchestrator_db/drop_table.py --table prompts

    # Drop multiple tables
    uv run apps/orchestrator_db/drop_table.py --table prompts --table agent_logs

    # Skip confirmation (dangerous!)
    uv run apps/orchestrator_db/drop_table.py --table prompts --yes

Features:
    - Explicit table flags (no wildcards or "drop all")
    - Confirmation prompts for safety
    - Handles CASCADE for foreign key constraints
    - Rich terminal output with color coding
    - Loads DATABASE_URL from .env file

IMPORTANT: Never use DROP TABLE in migration files!
           Use this utility instead for explicit, controlled drops.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()

# Available tables in the database
AVAILABLE_TABLES = [
    "orchestrator_agents",
    "agents",
    "prompts",
    "agent_logs",
    "system_logs",
    "orchestrator_chat",
]

# Table dependencies (for CASCADE warnings)
TABLE_DEPENDENCIES = {
    "agents": ["prompts", "agent_logs", "system_logs"],
    "orchestrator_agents": [],
    "prompts": [],
    "agent_logs": [],
    "system_logs": [],
    "orchestrator_chat": [],
}


def load_database_url() -> str:
    """Load DATABASE_URL from .env file"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        console.print(
            f"[red]✗ Error:[/red] .env file not found at {env_file}", style="bold"
        )
        console.print("Create a .env file with DATABASE_URL='your-neon-connection-string'")
        sys.exit(1)

    load_dotenv(env_file)
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        console.print(
            "[red]✗ Error:[/red] DATABASE_URL environment variable is required",
            style="bold",
        )
        console.print(f"Add DATABASE_URL to {env_file}")
        sys.exit(1)

    return database_url


def check_psql_installed():
    """Verify psql command is available"""
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(
            "[red]✗ Error:[/red] psql command not found", style="bold"
        )
        console.print("Install PostgreSQL client tools to use this script")
        sys.exit(1)


def list_tables():
    """Display available tables"""
    console.print(
        Panel.fit(
            "[bold cyan]Available Database Tables[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(title="Tables", border_style="cyan")
    table.add_column("Table Name", style="cyan", no_wrap=True)
    table.add_column("Dependent Tables (will CASCADE)", style="yellow")

    for table_name in AVAILABLE_TABLES:
        dependencies = TABLE_DEPENDENCIES.get(table_name, [])
        dep_str = ", ".join(dependencies) if dependencies else "None"
        table.add_row(table_name, dep_str)

    console.print(table)
    console.print(
        "\n[dim]Use: --table <table_name> to drop a specific table[/dim]"
    )


def drop_tables(tables: List[str], database_url: str, skip_confirmation: bool = False):
    """Drop specified tables from database"""
    # Validate table names
    invalid_tables = [t for t in tables if t not in AVAILABLE_TABLES]
    if invalid_tables:
        console.print(
            f"[red]✗ Error:[/red] Invalid table names: {', '.join(invalid_tables)}",
            style="bold",
        )
        console.print(f"\n[dim]Available tables:[/dim] {', '.join(AVAILABLE_TABLES)}")
        sys.exit(1)

    # Show warning panel
    console.print(
        Panel.fit(
            "[bold red]⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️[/bold red]\n\n"
            f"[yellow]You are about to DROP {len(tables)} table(s):[/yellow]\n"
            + "\n".join(f"  • {t}" for t in tables)
            + "\n\n[red]This will DELETE ALL DATA in these tables![/red]",
            border_style="red",
            title="Confirmation Required",
        )
    )

    # Check for cascading dependencies
    cascading_tables = set()
    for table in tables:
        deps = TABLE_DEPENDENCIES.get(table, [])
        cascading_tables.update(deps)

    if cascading_tables:
        console.print(
            Panel.fit(
                "[yellow]The following tables will also be affected (CASCADE):[/yellow]\n"
                + "\n".join(f"  • {t}" for t in sorted(cascading_tables)),
                border_style="yellow",
                title="Cascade Warning",
            )
        )

    # Confirmation prompt
    if not skip_confirmation:
        confirmed = Confirm.ask(
            "\n[bold red]Are you absolutely sure you want to proceed?[/bold red]",
            default=False,
        )
        if not confirmed:
            console.print("\n[yellow]✗ Operation cancelled[/yellow]")
            sys.exit(0)

    # Drop tables
    console.print("\n[cyan]Dropping tables...[/cyan]\n")
    failed = []
    succeeded = []

    for table_name in tables:
        # Generate DROP TABLE SQL
        drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"

        # Execute via psql
        result = subprocess.run(
            ["psql", database_url, "-c", drop_sql],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print(f"[green]✓[/green] Dropped: {table_name}")
            succeeded.append(table_name)
        else:
            console.print(f"[red]✗[/red] Failed: {table_name}")
            console.print(f"[dim]{result.stderr}[/dim]")
            failed.append((table_name, result.stderr))

    # Summary
    console.print()
    if failed:
        console.print(
            Panel.fit(
                f"[red]Operation completed with errors[/red]\n"
                f"Dropped: {len(succeeded)}/{len(tables)}\n"
                f"Failed: {len(failed)}/{len(tables)}",
                border_style="red",
                title="Drop Status",
            )
        )

        # Show failed tables
        error_table = Table(title="Failed Drops", border_style="red")
        error_table.add_column("Table", style="cyan")
        error_table.add_column("Error", style="red")

        for table_name, error in failed:
            error_table.add_row(
                table_name, error[:100] + "..." if len(error) > 100 else error
            )

        console.print(error_table)
        sys.exit(1)
    else:
        console.print(
            Panel.fit(
                f"[green]✓ Successfully dropped {len(succeeded)} table(s)[/green]\n\n"
                "[dim]Recreate tables by running:[/dim]\n"
                "[cyan]uv run apps/orchestrator_db/run_migrations.py[/cyan]",
                border_style="green",
                title="Drop Status",
            )
        )


@click.command()
@click.option(
    "--table",
    "-t",
    multiple=True,
    help="Table name to drop (can be specified multiple times)",
)
@click.option(
    "--list",
    "-l",
    "show_list",
    is_flag=True,
    help="List available tables and their dependencies",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt (DANGEROUS!)",
)
def main(table: tuple, show_list: bool, yes: bool):
    """
    Drop database tables with explicit table flags.

    IMPORTANT: This is a destructive operation. Always backup your data first!

    Examples:

        # List available tables
        uv run apps/orchestrator_db/drop_table.py --list

        # Drop a single table
        uv run apps/orchestrator_db/drop_table.py --table prompts

        # Drop multiple tables
        uv run apps/orchestrator_db/drop_table.py --table prompts --table agent_logs
    """
    console.print(
        Panel.fit(
            "[bold cyan]Database Table Drop Utility[/bold cyan]",
            border_style="cyan",
        )
    )

    # List tables mode
    if show_list:
        list_tables()
        sys.exit(0)

    # Validate we have tables to drop
    if not table:
        console.print(
            "[yellow]⚠ No tables specified[/yellow]\n",
            style="bold",
        )
        console.print("Use [cyan]--table <table_name>[/cyan] to specify tables to drop")
        console.print("Use [cyan]--list[/cyan] to see available tables\n")
        sys.exit(1)

    # Load environment
    check_psql_installed()
    database_url = load_database_url()

    # Drop tables
    tables_to_drop = list(table)
    drop_tables(tables_to_drop, database_url, skip_confirmation=yes)


if __name__ == "__main__":
    main()
