#!/usr/bin/env python3
"""
Sync plan.md from plan.json

Automatically generates a human-readable markdown file from the structured
plan.json whenever plan.json is created or modified.

================================================================================
HOW THIS WORKS (Hook Mechanism)
================================================================================

This script is triggered by a Claude Code PostToolUse hook configured in:
    .claude/settings.json

Hook configuration:
    {
        "matcher": "Edit|Write",
        "hooks": [{
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/skills/session/plan/scripts/sync-plan-md.py"
        }]
    }

Flow:
    1. Claude uses Edit or Write tool on ANY file
    2. PostToolUse hook triggers, passing tool input via stdin as JSON:
       {
           "tool_name": "Write",
           "tool_input": {"file_path": "/path/to/file.json", ...},
           ...
       }
    3. This script checks if file_path ends with "plan.json"
       - If NO: exits immediately (exit 0), no action taken
       - If YES: reads plan.json, generates plan.md in same directory

This approach means:
    - Hook runs on ALL Edit/Write operations (lightweight check)
    - Only plan.json files trigger the actual markdown generation
    - plan.md stays in sync automatically without manual intervention

================================================================================
OUTPUT
================================================================================

Generates plan.md with:
    - Status emojis: ⬜ pending, 🔄 in_progress, ✅ complete, 🚫 blocked
    - File context tables showing before/after states
    - Testing strategy with verification steps
    - Task details with IDK actions and context references
    - Auto-generation timestamp in footer

================================================================================
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def format_status_emoji(status: str) -> str:
    """Convert status to emoji indicator."""
    return {
        "pending": "⬜",
        "in_progress": "🔄",
        "complete": "✅",
        "completed": "✅",
        "blocked": "🚫",
    }.get(status, "⬜")


def format_file_status(status: str) -> str:
    """Format file status for display."""
    return {
        "exists": "📄",
        "new": "✨",
        "modified": "📝",
        "deleted": "🗑️",
    }.get(status, "📄")


def generate_plan_md(plan: dict) -> str:
    """Generate markdown content from plan structure."""
    lines = []

    # Header
    lines.append("# Implementation Plan")
    lines.append("")
    lines.append(f"> **Session**: `{plan.get('session_id', 'Unknown')}`")
    lines.append(f"> **Status**: {plan.get('status', 'draft').title()}")
    lines.append(
        f"> **Spec**: [{plan.get('spec_reference', './spec.md')}]({plan.get('spec_reference', './spec.md')})"
    )

    if plan.get("created_at"):
        lines.append(f"> **Created**: {plan.get('created_at', '')[:10]}")
    if plan.get("updated_at"):
        lines.append(f"> **Updated**: {plan.get('updated_at', '')[:10]}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary stats
    checkpoints = plan.get("checkpoints", [])
    total_tasks = sum(
        len(task)
        for cp in checkpoints
        for task_group in cp.get("task_groups", [])
        for task in [task_group.get("tasks", [])]
    )
    completed_cps = len([cp for cp in checkpoints if cp.get("status") == "complete"])

    lines.append("## Overview")
    lines.append("")
    lines.append(f"- **Checkpoints**: {len(checkpoints)} ({completed_cps} complete)")
    lines.append(f"- **Total Tasks**: {total_tasks}")
    lines.append("")

    # Checkpoints
    for cp in checkpoints:
        cp_id = cp.get("id", "?")
        status_emoji = format_status_emoji(cp.get("status", "pending"))

        lines.append(
            f"## {status_emoji} Checkpoint {cp_id}: {cp.get('title', 'Untitled')}"
        )
        lines.append("")
        lines.append(f"**Goal**: {cp.get('goal', 'No goal specified')}")
        lines.append("")

        # Prerequisites
        prereqs = cp.get("prerequisites", [])
        if prereqs:
            lines.append(
                f"**Prerequisites**: Checkpoints {', '.join(map(str, prereqs))}"
            )
            lines.append("")

        # File Context
        file_context = cp.get("file_context", {})
        if file_context:
            lines.append("### File Context")
            lines.append("")

            beginning = file_context.get("beginning", {})
            ending = file_context.get("ending", {})

            if beginning.get("files") or ending.get("files"):
                lines.append("| State | File | Status | Description |")
                lines.append("|-------|------|--------|-------------|")

                for f in beginning.get("files", []):
                    status_icon = format_file_status(f.get("status", "exists"))
                    lines.append(
                        f"| Before | `{f.get('path', '')}` | {status_icon} {f.get('status', '')} | {f.get('description', '')} |"
                    )

                for f in ending.get("files", []):
                    status_icon = format_file_status(f.get("status", "exists"))
                    lines.append(
                        f"| After | `{f.get('path', '')}` | {status_icon} {f.get('status', '')} | {f.get('description', '')} |"
                    )

                lines.append("")

            # Tree visualization
            if ending.get("tree"):
                lines.append("**Projected Structure**:")
                lines.append("```")
                lines.append(ending.get("tree", ""))
                lines.append("```")
                lines.append("")

        # Testing Strategy
        testing = cp.get("testing_strategy", {})
        if testing:
            lines.append("### Testing Strategy")
            lines.append("")
            lines.append(f"**Approach**: {testing.get('approach', 'Not specified')}")
            lines.append("")
            steps = testing.get("verification_steps", [])
            if steps:
                lines.append("**Verification Steps**:")
                for step in steps:
                    lines.append(f"- [ ] `{step}`")
                lines.append("")

        # Task Groups and Tasks
        task_groups = cp.get("task_groups", [])
        for task_group in task_groups:
            tg_id = task_group.get("id", "?")
            tg_title = task_group.get("title", "")
            tg_objective = task_group.get("objective", "No objective")
            tg_status = format_status_emoji(task_group.get("status", "pending"))

            # Display title if available, otherwise just objective
            if tg_title:
                lines.append(f"### {tg_status} Task Group {tg_id}: {tg_title}")
                lines.append("")
                lines.append(f"**Objective**: {tg_objective}")
            else:
                lines.append(f"### {tg_status} Task Group {tg_id}: {tg_objective}")
            lines.append("")

            tasks = task_group.get("tasks", [])
            for task in tasks:
                task_id = task.get("id", "?")
                task_status = format_status_emoji(task.get("status", "pending"))

                lines.append(
                    f"#### {task_status} Task {task_id}: {task.get('title', 'Untitled')}"
                )
                lines.append("")
                lines.append(f"**File**: `{task.get('file_path', 'Unknown')}`")
                lines.append("")
                lines.append(
                    f"**Description**: {task.get('description', 'No description')}"
                )
                lines.append("")

                # Context
                context = task.get("context", {})
                read_before = context.get("read_before", [])
                if read_before:
                    lines.append("**Context to Load**:")
                    for ref in read_before:
                        line_info = (
                            f" (lines {ref.get('lines')})" if ref.get("lines") else ""
                        )
                        lines.append(
                            f"- `{ref.get('file', '')}`{line_info} - {ref.get('purpose', '')}"
                        )
                    lines.append("")

                # Dependencies
                deps = task.get("depends_on", [])
                if deps:
                    lines.append(f"**Depends On**: Tasks {', '.join(deps)}")
                    lines.append("")

                # Actions (file-scoped atomic operations)
                actions = task.get("actions", [])
                if actions:
                    lines.append("**Actions**:")
                    for action in actions:
                        action_status = format_status_emoji(
                            action.get("status", "pending")
                        )
                        action_id = action.get("id", "?")
                        action_cmd = action.get("command", "No command")
                        action_file = action.get("file", "")
                        file_info = f" (`{action_file}`)" if action_file else ""
                        lines.append(
                            f"- {action_status} **{action_id}**: {action_cmd}{file_info}"
                        )
                    lines.append("")

        lines.append("---")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(
        f"*Auto-generated from plan.json on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    )

    return "\n".join(lines)


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Get the file path from tool input
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only process plan.json files
    if not file_path.endswith("plan.json"):
        sys.exit(0)

    plan_json_path = Path(file_path)

    # Check if file exists
    if not plan_json_path.exists():
        print(f"plan.json not found: {file_path}", file=sys.stderr)
        sys.exit(0)

    # Read plan.json
    try:
        with open(plan_json_path, "r") as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing plan.json: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading plan.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate markdown
    markdown_content = generate_plan_md(plan)

    # Write plan.md in the same directory
    plan_md_path = plan_json_path.parent / "plan.md"
    try:
        with open(plan_md_path, "w") as f:
            f.write(markdown_content)
        print(f"Generated: {plan_md_path}")
    except Exception as e:
        print(f"Error writing plan.md: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
