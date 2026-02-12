#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Universal Hook Logger - Claude Code Hook

Logs all hook payloads to session-specific JSONL files AND optionally
to the PostgreSQL database for UI consumption.

Dual-write ensures:
1. JSONL files always written (primary backup)
2. Database written if SESSION_DB_URL is configured

Database write errors do NOT block JSONL writing.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_hook_name(input_data: dict) -> str:
    """Extract hook event name from input data."""
    return input_data.get("hook_event_name", "Unknown")


def create_log_entry(input_data: dict) -> dict:
    """Create enriched log entry with timestamp and full payload."""
    return {"timestamp": datetime.now().isoformat(), "payload": input_data}


def write_log_entry(session_id: str, hook_name: str, log_entry: dict) -> None:
    """Write log entry to appropriate JSONL file."""
    # Use CLAUDE_PROJECT_DIR if available, otherwise use cwd
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # Create directory structure relative to project root (within agents/logging/)
    log_dir = Path(project_dir) / "agents" / "logging" / "hook_logs" / session_id
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create hook-specific log file
    log_file = log_dir / f"{hook_name}.jsonl"

    # Append to JSONL file
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def write_to_database(input_data: dict) -> bool:
    """
    Write event to database if configured.

    Returns True if written successfully, False otherwise.
    Errors are logged but do not block execution.
    """
    # Check if database is configured
    db_url = os.environ.get("SESSION_DB_URL")
    if not db_url:
        # No DB configured - this is fine, just skip
        return False

    try:
        # Import the db_writer module (relative import from same directory)
        from db_writer import write_event_sync

        return write_event_sync(input_data)

    except ImportError as e:
        # db_writer not available - log and continue
        print(f"Hook logger: db_writer import failed: {e}", file=sys.stderr)
        return False

    except Exception as e:
        # Any other error - log and continue
        print(f"Hook logger DB error: {e}", file=sys.stderr)
        return False


def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)

        # Extract session ID and hook name
        session_id = input_data.get("session_id", "unknown")
        hook_name = get_hook_name(input_data)

        # Create and write log entry to JSONL (always)
        log_entry = create_log_entry(input_data)
        write_log_entry(session_id, hook_name, log_entry)

        # Write to database (if configured, non-blocking)
        # This is wrapped in try/except to ensure JSONL write success
        # even if DB write fails
        try:
            write_to_database(input_data)
        except Exception as e:
            # Log but don't fail - JSONL was already written
            print(f"Hook logger: DB write skipped: {e}", file=sys.stderr)

        # Success - exit silently
        sys.exit(0)

    except Exception as e:
        # Log error but don't block hook execution
        print(f"Hook logger error: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking error


if __name__ == "__main__":
    main()
