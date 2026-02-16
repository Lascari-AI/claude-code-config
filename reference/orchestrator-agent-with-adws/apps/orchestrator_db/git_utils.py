"""
Git Utilities Module

Provides utilities for:
- Generating unified diffs for modified files
- Parsing diff statistics (lines added/removed)
- Determining file status (created/modified/deleted)
- Resolving absolute file paths
- Counting file lines
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class GitUtils:
    """Utilities for git operations and file analysis."""

    @staticmethod
    def is_git_repository(working_dir: str) -> bool:
        """
        Check if directory is inside a git repository.

        Searches the directory and all parent directories for a .git folder.

        Args:
            working_dir: Directory to check

        Returns:
            True if directory is inside a git repository, False otherwise
        """
        current = Path(working_dir).resolve()

        # Walk up the directory tree looking for .git
        while current != current.parent:
            if (current / '.git').exists():
                return True
            current = current.parent

        return False

    @staticmethod
    def get_file_diff(file_path: str, working_dir: str) -> Optional[str]:
        """
        Generate unified diff for a file.

        Args:
            file_path: Relative or absolute path to the file
            working_dir: Working directory (git repository root)

        Returns:
            Unified diff string or None if error

        Raises:
            ValueError: If working_dir is not a git repository
        """
        # Validate git repository
        if not GitUtils.is_git_repository(working_dir):
            raise ValueError(f"Directory is not a git repository: {working_dir}")

        try:
            # Resolve to absolute path first
            abs_path = GitUtils.resolve_absolute_path(file_path, working_dir)

            # Convert back to relative for git
            # Resolve both paths to handle symlinks (e.g., /var -> /private/var on macOS)
            abs_path_resolved = str(Path(abs_path).resolve())
            working_dir_resolved = str(Path(working_dir).resolve())
            rel_path = os.path.relpath(abs_path_resolved, working_dir_resolved)

            # Try to get diff from git
            result = subprocess.run(
                ["git", "diff", "HEAD", "--", rel_path],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # If no diff, file might be newly created (unstaged)
                if not result.stdout.strip():
                    # Try diff for untracked files
                    result = subprocess.run(
                        ["git", "diff", "--no-index", "/dev/null", rel_path],
                        cwd=working_dir,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode in [0, 1]:  # 1 is normal for diff with changes
                        return result.stdout
                return result.stdout

            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            # Git command failed, return None
            return None

    @staticmethod
    def parse_diff_stats(diff: str) -> Tuple[int, int]:
        """
        Extract lines added/removed from unified diff.

        Args:
            diff: Unified diff string

        Returns:
            Tuple of (lines_added, lines_removed)
        """
        if not diff:
            return (0, 0)

        lines_added = 0
        lines_removed = 0

        for line in diff.split('\n'):
            # Count lines starting with + (but not +++)
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            # Count lines starting with - (but not ---)
            elif line.startswith('-') and not line.startswith('---'):
                lines_removed += 1

        return (lines_added, lines_removed)

    @staticmethod
    def get_file_status(file_path: str, working_dir: str) -> str:
        """
        Determine file status: created, modified, or deleted.

        Uses git status --porcelain to check working tree state (not HEAD).
        This works correctly even when agents never commit files.

        Logic:
        - Checks if file exists in working directory (if not -> deleted)
        - Uses git status --porcelain to get actual working tree status
        - ?? = untracked file (created)
        - A  = added to index (created)
        - M  = modified (modified)
        - D  = deleted (deleted)

        Args:
            file_path: Relative or absolute path to the file
            working_dir: Working directory

        Returns:
            'created', 'modified', or 'deleted'

        Raises:
            ValueError: If working_dir is not a git repository
        """
        # Validate git repository
        if not GitUtils.is_git_repository(working_dir):
            raise ValueError(f"Directory is not a git repository: {working_dir}")

        try:
            abs_path = GitUtils.resolve_absolute_path(file_path, working_dir)

            # Check if file exists in working directory
            if not os.path.exists(abs_path):
                return 'deleted'

            # Convert to relative for git
            # Resolve both paths to handle symlinks (e.g., /var -> /private/var on macOS)
            abs_path_resolved = str(Path(abs_path).resolve())
            working_dir_resolved = str(Path(working_dir).resolve())
            rel_path = os.path.relpath(abs_path_resolved, working_dir_resolved)

            # Use git status --porcelain to get actual working tree status
            # Format: XY PATH (X=staged status, Y=unstaged status)
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", rel_path],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                # Git command failed - default to modified
                return 'modified'

            status_line = result.stdout.strip()

            # No output = file is unchanged/committed (but we're tracking it, so 'modified')
            if not status_line:
                return 'modified'

            # Parse status codes (first 2 characters)
            # XY format: X=index status, Y=worktree status
            status_code = status_line[:2] if len(status_line) >= 2 else '  '

            # Untracked files (newly created, not in git yet)
            if status_code == '??':
                return 'created'

            # Added to index (staged as new) - treat as created
            if status_code[0] == 'A' or status_code[1] == 'A':
                return 'created'

            # Deleted
            if 'D' in status_code:
                return 'deleted'

            # Modified (M in either position), Renamed (R), Copied (C), etc.
            if 'M' in status_code or 'R' in status_code or 'C' in status_code:
                return 'modified'

            # Default to modified for any other tracked file status
            return 'modified'

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            # Default to modified if we can't determine status
            return 'modified'

    @staticmethod
    def resolve_absolute_path(file_path: str, working_dir: str) -> str:
        """
        Convert relative path to absolute path.

        Args:
            file_path: Relative or absolute file path
            working_dir: Working directory to resolve relative paths

        Returns:
            Absolute file path
        """
        path = Path(file_path)

        if path.is_absolute():
            return str(path)

        # Resolve relative to working_dir
        absolute = Path(working_dir) / path
        return str(absolute.resolve())

    @staticmethod
    def count_file_lines(file_path: str, working_dir: str) -> int:
        """
        Count total lines in a file.

        Args:
            file_path: Relative or absolute path to file
            working_dir: Working directory

        Returns:
            Number of lines in file (0 if error)
        """
        try:
            abs_path = GitUtils.resolve_absolute_path(file_path, working_dir)

            # Check if file exists
            if not os.path.exists(abs_path):
                return 0

            # For performance, use wc -l on Unix-like systems
            try:
                result = subprocess.run(
                    ["wc", "-l", abs_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # wc -l output format: "  123 /path/to/file"
                    line_count = int(result.stdout.strip().split()[0])
                    return line_count
            except (FileNotFoundError, ValueError, IndexError):
                # wc not available or parsing failed, fall back to Python
                pass

            # Fallback: read file and count lines
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)

        except Exception as e:
            # Return 0 on any error
            return 0
