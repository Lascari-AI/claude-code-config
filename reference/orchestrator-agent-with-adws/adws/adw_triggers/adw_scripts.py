# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ADW Runner - Triggers AI Developer Workflows in background processes.

Spawns workflow scripts using `uv run`. Workflows fetch all context from DB via adw_id.

Usage:
    from adws.adw_triggers.adw_scripts import run_adw_workflow_async
    await run_adw_workflow_async(adw_id, workflow_type, working_dir)
"""

from __future__ import annotations

import subprocess
from pathlib import Path


async def run_adw_workflow_async(
    adw_id: str,
    workflow_type: str,
) -> dict[str, str]:
    """Run an ADW workflow in a detached background process.

    Args:
        adw_id: UUID of the ADW record (workflow fetches prompt/config from DB)
        workflow_type: Workflow type (maps to adw_workflows/adw_{type}.py)

    Returns:
        Dict with status, pid, or error
    """
    # Get project root (adws/adw_triggers/adw_scripts.py -> adws -> project root)
    project_root = Path(__file__).parent.parent.parent

    # Build path to workflow file relative to project root
    workflow_path = project_root / "adws" / "adw_workflows" / f"adw_{workflow_type}.py"
    if not workflow_path.exists():
        return {"status": "error", "error": f"Workflow not found: {workflow_path}"}

    # Only adw_id needed - workflow fetches prompt, working_dir from DB
    cmd = ["uv", "run", str(workflow_path), "--adw-id", adw_id]

    try:
        # Run from project root for proper imports and .env access
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"status": "started", "pid": str(process.pid), "adw_id": adw_id}

    except FileNotFoundError:
        return {"status": "error", "error": "uv command not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
