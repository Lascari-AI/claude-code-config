# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg>=0.29.0",
#   "python-dotenv>=1.0.0",
#   "rich>=13.0",
# ]
# ///
"""
ADW Manual Trigger - Manually create and trigger an ADW for testing.

This script:
1. Creates an ADW record in the database (like start_adw tool does)
2. Triggers the workflow via adw_scripts.py
3. Allows testing the complete flow without the orchestrator

Usage:
    uv run adws/adw_triggers/adw_manual_trigger.py <adw_name> <workflow_type> <prompt> <working_dir> [model]

Example:
    uv run adws/adw_triggers/adw_manual_trigger.py "test-feature" "plan_build" "Create a hello world script" "/path/to/project" "claude-sonnet-4-5-20250929"

Arguments:
    adw_name:      Human-readable name for the ADW (e.g., "test-feature")
    workflow_type: Workflow type (maps to adw_workflows/adw_<type>.py, e.g., "plan_build")
    prompt:        The task prompt to execute
    working_dir:   Working directory for the agents
    model:         Optional model name (default: claude-sonnet-4-5-20250929)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()

console = Console()


# =============================================================================
# DATABASE OPERATIONS (inline to avoid import complexity)
# =============================================================================


async def create_adw_record(
    adw_name: str,
    workflow_type: str,
    prompt: str,
    working_dir: str,
    model: str,
    orchestrator_agent_id: str | None = None,
) -> str:
    """Create an ADW record in the database.

    Args:
        adw_name: Human-readable name
        workflow_type: Workflow type
        prompt: Task prompt
        working_dir: Working directory
        model: Model name
        orchestrator_agent_id: Optional parent orchestrator ID

    Returns:
        The created ADW ID (UUID string)
    """
    import asyncpg

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    adw_id = str(uuid.uuid4())

    # Build input_data with prompt, working_dir, and model
    input_data = {
        "prompt": prompt,
        "working_dir": working_dir,
        "model": model,
    }

    # Add review_model for review workflows
    if workflow_type in ("plan_build_review", "plan_build_review_fix"):
        input_data["review_model"] = "claude-opus-4-5-20251101"

    # Add fix_model for fix workflows
    if workflow_type == "plan_build_review_fix":
        input_data["fix_model"] = "claude-opus-4-5-20251101"

    # Determine total_steps based on workflow type
    workflow_steps = {
        "plan_build": 2,
        "plan_build_review": 3,
        "plan_build_review_fix": 4,
    }
    total_steps = workflow_steps.get(workflow_type, 2)

    conn = await asyncpg.connect(database_url)
    try:
        # If no orchestrator_agent_id provided, try to find or create one
        if orchestrator_agent_id is None:
            # Try to find an existing orchestrator agent
            row = await conn.fetchrow("SELECT id FROM orchestrator_agents LIMIT 1")
            if row:
                orchestrator_agent_id = str(row["id"])
            else:
                # Create a new orchestrator agent for manual testing
                orchestrator_agent_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO orchestrator_agents (
                        id, name, model, status, created_at, updated_at
                    ) VALUES (
                        $1, 'manual-test-orchestrator', $2, 'idle', NOW(), NOW()
                    )
                    """,
                    uuid.UUID(orchestrator_agent_id),
                    model,
                )
                console.print(
                    f"[dim]Created orchestrator agent: {orchestrator_agent_id}[/dim]"
                )

        await conn.execute(
            """
            INSERT INTO ai_developer_workflows (
                id, orchestrator_agent_id, adw_name, workflow_type,
                description, status, total_steps, input_data, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, 'pending', $6, $7, NOW(), NOW()
            )
            """,
            uuid.UUID(adw_id),
            uuid.UUID(orchestrator_agent_id) if orchestrator_agent_id else None,
            adw_name,
            workflow_type,
            f"Manual trigger: {prompt[:100]}...",
            total_steps,
            json.dumps(input_data),
        )

        # Fetch the created ADW to get full record with timestamps
        adw_row = await conn.fetchrow(
            "SELECT * FROM ai_developer_workflows WHERE id = $1",
            uuid.UUID(adw_id)
        )
    finally:
        await conn.close()

    # Broadcast ADW creation via WebSocket for real-time UI updates
    if adw_row:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from adw_modules.adw_websockets import broadcast_adw_created

            adw_data = {
                "id": str(adw_row["id"]),
                "orchestrator_agent_id": str(adw_row["orchestrator_agent_id"]) if adw_row["orchestrator_agent_id"] else None,
                "adw_name": adw_row["adw_name"],
                "workflow_type": adw_row["workflow_type"],
                "description": adw_row["description"],
                "status": adw_row["status"],
                "current_step": adw_row["current_step"],
                "completed_steps": adw_row["completed_steps"],
                "total_steps": adw_row["total_steps"],
                "input_data": adw_row["input_data"],
                "created_at": adw_row["created_at"].isoformat() if adw_row["created_at"] else None,
                "updated_at": adw_row["updated_at"].isoformat() if adw_row["updated_at"] else None,
            }
            await broadcast_adw_created(adw_data)
            console.print("[dim]Broadcasted ADW creation via WebSocket[/dim]")
        except Exception as e:
            console.print(f"[dim yellow]WebSocket broadcast failed (non-critical): {e}[/dim yellow]")

    return adw_id


# =============================================================================
# WORKFLOW TRIGGER
# =============================================================================


async def trigger_workflow(
    adw_id: str,
    workflow_type: str,
) -> dict[str, str]:
    """Trigger the workflow using adw_scripts.py.

    Args:
        adw_id: The ADW ID
        workflow_type: Workflow type (e.g., "plan_build")

    Returns:
        Result dict with status, pid, or error
    """
    # Import the runner
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from adw_triggers.adw_scripts import run_adw_workflow_async

    return await run_adw_workflow_async(
        adw_id=adw_id,
        workflow_type=workflow_type,
    )


# =============================================================================
# MAIN
# =============================================================================


async def main_async(args: argparse.Namespace) -> int:
    """Main async function.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    adw_name = args.adw_name
    workflow_type = args.workflow_type
    prompt = args.prompt
    working_dir = args.working_dir
    model = args.model

    # Validate working_dir
    if not Path(working_dir).exists():
        console.print(f"[red]Working directory does not exist: {working_dir}[/red]")
        return 1

    # Convert to absolute path
    working_dir = str(Path(working_dir).resolve())

    console.print(
        Panel(
            f"[bold cyan]ADW Manual Trigger[/bold cyan]\n\n"
            f"[bold]Name:[/bold] {adw_name}\n"
            f"[bold]Type:[/bold] {workflow_type}\n"
            f"[bold]Prompt:[/bold] {prompt[:100]}...\n"
            f"[bold]Working Dir:[/bold] {working_dir}\n"
            f"[bold]Model:[/bold] {model}",
            title="Configuration",
            width=console.width,
        )
    )

    # Create ADW record
    console.print("\n[cyan]Creating ADW record...[/cyan]")
    try:
        adw_id = await create_adw_record(
            adw_name=adw_name,
            workflow_type=workflow_type,
            prompt=prompt,
            working_dir=working_dir,
            model=model,
        )
        console.print(f"[green]Created ADW: {adw_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to create ADW record: {e}[/red]")
        return 1

    # Trigger workflow
    console.print("\n[cyan]Triggering workflow...[/cyan]")
    try:
        result = await trigger_workflow(
            adw_id=adw_id,
            workflow_type=workflow_type,
        )

        if result.get("status") == "started":
            console.print(
                Panel(
                    f"[bold green]Workflow Started Successfully![/bold green]\n\n"
                    f"[bold]ADW ID:[/bold] {adw_id}\n"
                    f"[bold]PID:[/bold] {result.get('pid')}\n\n"
                    f"[dim]The workflow is running in the background.\n"
                    f"Check the database for status updates:\n"
                    f"  SELECT * FROM ai_developer_workflows WHERE id = '{adw_id}';\n"
                    f"  SELECT * FROM agent_logs WHERE adw_id = '{adw_id}' ORDER BY timestamp;[/dim]",
                    title="Success",
                    width=console.width,
                )
            )
            return 0
        else:
            console.print(f"[red]Failed to start workflow: {result.get('error')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Failed to trigger workflow: {e}[/red]")
        return 1


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="ADW Manual Trigger - Create and trigger an ADW for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Simple test
    uv run adws/adw_triggers/adw_manual_trigger.py \\
        "test-hello" "plan_build" "Create a hello world Python script" "."

    # Full example with model
    uv run adws/adw_triggers/adw_manual_trigger.py \\
        "feature-auth" "plan_build" \\
        "Implement user authentication with JWT tokens" \\
        "/path/to/project" \\
        "claude-opus-4-5-20251101"
        """,
    )

    parser.add_argument(
        "adw_name",
        help="Human-readable name for the ADW (e.g., 'test-feature')",
    )
    parser.add_argument(
        "workflow_type",
        help="Workflow type (maps to adw_workflows/adw_<type>.py, e.g., 'plan_build')",
    )
    parser.add_argument(
        "prompt",
        help="The task prompt to execute",
    )
    parser.add_argument(
        "working_dir",
        help="Working directory for the agents",
    )
    parser.add_argument(
        "model",
        nargs="?",
        default="claude-sonnet-4-5-20250929",
        help="Model name (default: claude-sonnet-4-5-20250929)",
    )

    args = parser.parse_args()

    # Run async main
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
