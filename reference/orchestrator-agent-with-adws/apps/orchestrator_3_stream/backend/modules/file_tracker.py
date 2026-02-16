"""
File Tracker Module

Tracks file modifications and reads during agent execution.
Maintains separate registries for modified and read files per agent.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel

# Add parent directory to path to import git_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from apps.orchestrator_db.git_utils import GitUtils


# Pydantic models for type safety
class FileChange(BaseModel):
    path: str
    absolute_path: str
    status: str  # 'created' | 'modified' | 'deleted'
    lines_added: int
    lines_removed: int
    diff: Optional[str] = None
    summary: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class FileRead(BaseModel):
    path: str
    absolute_path: str
    line_count: int
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class AgentLogMetadata(BaseModel):
    """Metadata structure stored in agent_log.payload"""
    file_changes: Optional[List[FileChange]] = None
    read_files: Optional[List[FileRead]] = None
    total_files_modified: Optional[int] = None
    total_files_read: Optional[int] = None
    generated_at: Optional[str] = None


# Tool categories
FILE_MODIFYING_TOOLS = ["Write", "Edit", "MultiEdit", "Bash"]
FILE_READING_TOOLS = ["Read"]


class FileTracker:
    """Tracks file operations for a single agent."""

    def __init__(self, agent_id: UUID, agent_name: str, working_dir: str):
        """
        Initialize file tracker for an agent.

        Args:
            agent_id: UUID of the agent
            agent_name: Name of the agent
            working_dir: Working directory for file operations
        """
        self.agent_id = str(agent_id)
        self.agent_name = agent_name
        self.working_dir = working_dir

        # Use sets to track unique file paths
        self.modified_files: Set[str] = set()
        self.read_files: Set[str] = set()

        # Store detailed info for modified files
        self._file_details: Dict[str, Dict[str, Any]] = {}

    def track_modified_file(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Record a file modification from a tool.

        Args:
            tool_name: Name of the tool (Write, Edit, etc.)
            tool_input: Tool input parameters
        """
        # Extract file_path from tool_input
        file_path = tool_input.get("file_path")

        if not file_path:
            return

        # Add to modified files set
        self.modified_files.add(file_path)

        # Store tool info for later summary generation
        if file_path not in self._file_details:
            self._file_details[file_path] = {
                "tool_name": tool_name,
                "tool_input": tool_input
            }

    def track_read_file(self, file_path: str) -> None:
        """
        Record a file read operation.

        Args:
            file_path: Path to the file that was read
        """
        if file_path:
            self.read_files.add(file_path)

    def get_modified_files(self) -> List[str]:
        """Return list of modified file paths."""
        return list(self.modified_files)

    def get_read_files(self) -> List[str]:
        """Return list of read file paths."""
        return list(self.read_files)

    async def generate_file_changes_summary(self) -> List[Dict[str, Any]]:
        """
        Generate comprehensive summary of file modifications with diffs and AI summaries.

        Returns:
            List of file change dictionaries with diffs, stats, and AI summaries
        """
        file_changes = []

        for file_path in self.modified_files:
            try:
                # Get tool info
                tool_info = self._file_details.get(file_path, {})
                tool_name = tool_info.get("tool_name", "Unknown")

                # Resolve absolute path
                abs_path = GitUtils.resolve_absolute_path(file_path, self.working_dir)

                # Get relative path for display
                try:
                    rel_path = os.path.relpath(abs_path, self.working_dir)
                except ValueError:
                    # If paths are on different drives (Windows), use filename
                    rel_path = os.path.basename(abs_path)

                # Generate diff
                diff = GitUtils.get_file_diff(file_path, self.working_dir)

                # Parse stats
                lines_added, lines_removed = GitUtils.parse_diff_stats(diff) if diff else (0, 0)

                # Determine status
                status = GitUtils.get_file_status(file_path, self.working_dir)

                # Generate AI summary
                summary = await generate_file_change_summary(file_path, diff, tool_name)

                file_change = {
                    "path": rel_path,
                    "absolute_path": abs_path,
                    "status": status,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "diff": diff,
                    "summary": summary,
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name
                }

                file_changes.append(file_change)

            except Exception as e:
                # Log error but continue processing other files
                print(f"Error generating summary for {file_path}: {e}")
                continue

        return file_changes

    def generate_read_files_summary(self) -> List[Dict[str, Any]]:
        """
        Generate summary of read files with line counts.

        Returns:
            List of read file dictionaries with line counts
        """
        read_files = []

        for file_path in self.read_files:
            try:
                # Resolve absolute path
                abs_path = GitUtils.resolve_absolute_path(file_path, self.working_dir)

                # Get relative path for display
                try:
                    rel_path = os.path.relpath(abs_path, self.working_dir)
                except ValueError:
                    rel_path = os.path.basename(abs_path)

                # Count lines
                line_count = GitUtils.count_file_lines(file_path, self.working_dir)

                file_read = {
                    "path": rel_path,
                    "absolute_path": abs_path,
                    "line_count": line_count,
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name
                }

                read_files.append(file_read)

            except Exception as e:
                print(f"Error generating read summary for {file_path}: {e}")
                continue

        return read_files


async def generate_file_change_summary(
    file_path: str,
    diff: Optional[str],
    tool_name: str
) -> str:
    """
    Generate AI summary for a file change using LLM.

    Uses existing fast_claude_query from single_agent_prompt module.

    Args:
        file_path: Path to the modified file
        diff: Git diff string
        tool_name: Tool that made the change

    Returns:
        Concise 1-2 sentence summary or fallback message
    """
    try:
        # Import here to avoid circular dependency
        from .single_agent_prompt import (
            EVENT_SUMMARIZER_SYSTEM_PROMPT,
            EVENT_SUMMARIZER_USER_PROMPT,
            fast_claude_query,
        )

        # If no diff, return simple summary
        if not diff or not diff.strip():
            return f"{tool_name} operation on {os.path.basename(file_path)}"

        # Truncate diff if too large (max 2000 chars as per plan)
        truncated_diff = diff[:2000] + "\n[...truncated]" if len(diff) > 2000 else diff

        # Build details using existing event summarizer format
        details = f"""File: {os.path.basename(file_path)}
Tool: {tool_name}
Diff (first 2000 chars):
{truncated_diff}"""

        # Use existing EVENT_SUMMARIZER_USER_PROMPT template
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type="FileChange",
            details=details
        )

        # Use existing EVENT_SUMMARIZER_SYSTEM_PROMPT
        summary = await fast_claude_query(prompt, system_prompt=EVENT_SUMMARIZER_SYSTEM_PROMPT)

        # Return summary or fallback
        if summary and summary.strip():
            return summary.strip()[:200]  # Limit to 200 chars
        else:
            # Fallback: simple heuristic-based summary
            lines = diff.split('\n')
            added_lines = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
            removed_lines = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))

            if added_lines > 0 and removed_lines == 0:
                return f"Added {added_lines} new lines to {os.path.basename(file_path)}"
            elif removed_lines > 0 and added_lines == 0:
                return f"Removed {removed_lines} lines from {os.path.basename(file_path)}"
            else:
                return f"Modified {os.path.basename(file_path)} (+{added_lines} -{removed_lines} lines)"

    except Exception as e:
        # Fallback on error
        return f"Modified {os.path.basename(file_path)}"
