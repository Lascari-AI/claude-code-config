#!/usr/bin/env python3
"""
Initialize a new agent session directory.

Creates the session directory structure and initializes state.json from template.
Saves tokens by handling directory creation in a single script call.

Usage:
    python init-session.py --topic TOPIC [--description DESC] [--session-id ID]

Examples:
    # Auto-generate session ID from topic:
    python init-session.py --topic "Feature Name Implementation"
    # Output: 2026-01-14_feature-name-implementation_a1b2c3

    # Use custom session ID:
    python init-session.py --topic "Feature Name" --session-id "custom-session-id"
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Path to state.json template (relative to this script)
TEMPLATE_PATH = Path(__file__).parent.parent / "spec" / "templates" / "state.json"

# Session base directory (relative to project root)
SESSIONS_DIR = "agents/sessions"


def generate_session_id(topic: str) -> str:
    """Generate session ID from topic: YYYY-MM-DD_topic-slug_random6."""
    import random
    import re
    import string

    date_str = datetime.now().strftime("%Y-%m-%d")

    # Convert topic to slug: lowercase, replace spaces/special chars with hyphens
    slug = topic.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    # Truncate to reasonable length
    slug = slug[:40]

    # Generate 6-char random suffix
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    return f"{date_str}_{slug}_{random_suffix}"


def get_project_root() -> Path:
    """Find project root by looking for .claude directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".claude").is_dir():
            return parent
    raise RuntimeError("Could not find project root (.claude directory)")


def load_template() -> dict:
    """Load the state.json template."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    with open(TEMPLATE_PATH, "r") as f:
        return json.load(f)


def create_directories(session_path: Path) -> list[str]:
    """Create session directory structure. Returns list of created dirs."""
    dirs = ["research", "context", "debug"]
    created = []

    for d in dirs:
        dir_path = session_path / d
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path.relative_to(session_path)))

    return created


def init_state_json(
    session_path: Path, session_id: str, topic: str, description: str | None = None
) -> dict:
    """Initialize state.json from template with provided values."""
    template = load_template()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Substitute template placeholders
    state = json.loads(
        json.dumps(template)
        .replace("{{SESSION_ID}}", session_id)
        .replace("{{CREATED_AT}}", now)
        .replace("{{UPDATED_AT}}", now)
        .replace("{{TOPIC}}", topic)
        .replace("{{DESCRIPTION}}", description or "")
    )

    # Remove the example key_decisions entry
    state["key_decisions"] = []

    # Write state.json
    state_path = session_path / "state.json"
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    return state


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new agent session directory"
    )
    parser.add_argument("--topic", required=True, help="Session topic/title")
    parser.add_argument(
        "--description", default=None, help="Optional session description"
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Custom session ID. If not provided, auto-generates from topic.",
    )

    args = parser.parse_args()

    try:
        # Generate session ID if not provided
        session_id = args.session_id or generate_session_id(args.topic)

        project_root = get_project_root()
        session_path = project_root / SESSIONS_DIR / session_id

        # Check if session already exists
        if session_path.exists():
            print(f"Error: Session already exists: {session_path}", file=sys.stderr)
            sys.exit(1)

        # Create session directory
        session_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        created_dirs = create_directories(session_path)

        # Initialize state.json
        init_state_json(session_path, session_id, args.topic, args.description)

        # Output minimal confirmation for agent consumption
        print(
            json.dumps(
                {
                    "status": "success",
                    "session_id": session_id,
                    "session_path": str(session_path),
                    "created": {"directories": created_dirs, "files": ["state.json"]},
                }
            )
        )

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
