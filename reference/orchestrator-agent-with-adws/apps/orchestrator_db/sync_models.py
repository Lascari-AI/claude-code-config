#!/usr/bin/env python3
"""
Model Sync Script

Copies the Pydantic database models from apps/orchestrator_db/models.py
to all orchestrator apps:
  - apps/orchestrator_3_stream/backend/modules/orch_database_models.py
  - adws/adw_modules/orch_database_models.py

This ensures that the database models are centrally defined and can be
easily synchronized across the project.

Usage:
    python apps/orchestrator_db/sync_models.py
    # or
    uv run python apps/orchestrator_db/sync_models.py
"""

import shutil
from pathlib import Path


def sync_models():
    """Copy models.py to both orchestrator apps"""

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    source = project_root / "apps" / "orchestrator_db" / "models.py"

    target_file_name = "orch_database_models.py"

    target_3_stream = (
        project_root
        / "apps"
        / "orchestrator_3_stream"
        / "backend"
        / "modules"
        / target_file_name
    )

    target_adws = (
        project_root
        / "adws"
        / "adw_modules"
        / target_file_name
    )

    targets = [
        target_3_stream,
        target_adws,
    ]

    # Verify source exists
    if not source.exists():
        print(f"❌ Source file not found: {source}")
        return False

    # Copy to all targets
    all_success = True
    for target in targets:
        # Create target directory if it doesn't exist
        target.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        try:
            shutil.copy2(source, target)
            print(f"✅ Successfully copied models:")
            print(f"   From: {source.relative_to(project_root)}")
            print(f"   To:   {target.relative_to(project_root)}")

            # Show file info
            size_kb = target.stat().st_size / 1024
            print(f"   Size: {size_kb:.1f} KB")
            print()

        except Exception as e:
            print(f"❌ Failed to copy to {target.relative_to(project_root)}: {e}")
            print()
            all_success = False

    return all_success


if __name__ == "__main__":
    print("=" * 60)
    print("Database Models Sync Script")
    print("=" * 60)
    print()

    success = sync_models()

    print()
    if success:
        print("✅ Sync completed successfully!")
        print()
        print("The Pydantic models are now available in all apps:")
        print("  orchestrator_3_stream:")
        print(
            "    from modules.orch_database_models import Agent, OrchestratorAgent, ..."
        )
        print()
        print("  adws:")
        print(
            "    from adw_modules.orch_database_models import Agent, OrchestratorAgent, ..."
        )
    else:
        print("❌ Sync failed!")
        exit(1)

    print("=" * 60)
