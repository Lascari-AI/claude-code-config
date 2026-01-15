"""
Plan Structure Models (Pydantic)

Type-safe structure definitions for plan.json checkpoint-based planning.

These models define:
- Task hierarchy: Plan → Checkpoint → TaskGroup → Task → Action
- File context tracking: beginning/ending states per checkpoint
- Testing strategy per checkpoint
- IDK-formatted action specifications
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Enums / Literals
# ============================================================================

PlanStatus = Literal["draft", "in_progress", "complete"]
TaskStatus = Literal["pending", "in_progress", "complete", "blocked"]
FileStatus = Literal["exists", "new", "modified", "deleted"]


# ============================================================================
# Task-Level Models
# ============================================================================


class ContextReference(BaseModel):
    """A file reference to read before executing a task."""

    file: str = Field(..., description="Path to the file to read")
    lines: Optional[str] = Field(
        None, description="Line range, e.g., '1-50' or '10-25'"
    )
    purpose: str = Field(..., description="Why this context is needed")


class TaskContext(BaseModel):
    """Pre-loaded context for task execution without searching."""

    read_before: list[ContextReference] = Field(
        default_factory=list, description="Files to read before executing the task"
    )
    related_files: list[str] = Field(
        default_factory=list,
        description="Other files that may be affected or referenced",
    )


class Action(BaseModel):
    """File-scoped atomic operation within a task."""

    id: str = Field(..., description="Hierarchical ID, e.g., '1.1.1.1'")
    command: str = Field(..., description="IDK-formatted command")
    file: str = Field(..., description="Target file path")
    status: TaskStatus = Field(default="pending")


class Task(BaseModel):
    """A unit of work within a task group."""

    id: str = Field(..., description="Hierarchical ID, e.g., '1.1.1'")
    title: str = Field(..., description="Short one-sentence summary (max)")
    file_path: str = Field(..., description="Primary file this task operates on")
    description: str = Field(..., description="Detailed description of what to do")
    context: TaskContext = Field(default_factory=TaskContext)
    depends_on: list[str] = Field(
        default_factory=list, description="Task IDs that must complete before this task"
    )
    status: TaskStatus = Field(default="pending")
    actions: list[Action] = Field(
        default_factory=list, description="Atomic operations to perform"
    )


# ============================================================================
# TaskGroup-Level Models
# ============================================================================


class TaskGroup(BaseModel):
    """Objective-based grouping of tasks within a checkpoint."""

    id: str = Field(..., description="TaskGroup ID, e.g., '1.1'")
    title: str = Field(..., description="Short title for scanning")
    objective: str = Field(..., description="What this task group accomplishes")
    status: TaskStatus = Field(default="pending")
    tasks: list[Task] = Field(default_factory=list)


# ============================================================================
# Checkpoint-Level Models
# ============================================================================


class FileState(BaseModel):
    """State of a file at a point in time."""

    path: str = Field(..., description="File path relative to project root")
    status: FileStatus = Field(
        ..., description="File state: exists, new, modified, deleted"
    )
    description: str = Field(..., description="What this file contains/does")


class FileSnapshot(BaseModel):
    """Snapshot of file states at a checkpoint boundary."""

    files: list[FileState] = Field(default_factory=list)
    tree: Optional[str] = Field(
        None, description="ASCII tree visualization for human review"
    )


class FileContext(BaseModel):
    """Beginning and ending file states for a checkpoint."""

    beginning: FileSnapshot = Field(..., description="State at checkpoint start")
    ending: FileSnapshot = Field(..., description="Projected state after completion")


class TestingStrategy(BaseModel):
    """How to verify a checkpoint is complete and working."""

    approach: str = Field(..., description="High-level testing approach")
    verification_steps: list[str] = Field(
        default_factory=list, description="Specific commands or checks to run"
    )


class Checkpoint(BaseModel):
    """A sequential milestone containing task groups."""

    id: int = Field(..., description="Checkpoint number (1-based)")
    title: str = Field(..., description="Short descriptive title")
    goal: str = Field(..., description="What this checkpoint achieves")
    prerequisites: list[int] = Field(
        default_factory=list, description="Checkpoint IDs that must complete first"
    )
    status: TaskStatus = Field(default="pending")
    file_context: FileContext
    testing_strategy: TestingStrategy
    task_groups: list[TaskGroup] = Field(default_factory=list)


# ============================================================================
# Top-Level Plan Model
# ============================================================================


class Plan(BaseModel):
    """The complete implementation plan for a session."""

    session_id: str = Field(..., description="Parent session identifier")
    spec_reference: str = Field(
        default="./spec.md", description="Path to the finalized spec"
    )
    created_at: datetime
    updated_at: datetime
    status: PlanStatus = Field(default="draft")
    checkpoints: list[Checkpoint] = Field(default_factory=list)


# ============================================================================
# Plan State Model (for state.json)
# ============================================================================


class PlanState(BaseModel):
    """Tracks plan execution progress in state.json."""

    status: Literal["not_started", "in_progress", "complete"] = Field(
        default="not_started"
    )
    current_checkpoint: Optional[int] = Field(
        None, description="Currently executing checkpoint"
    )
    current_task_group: Optional[str] = Field(
        None, description="Currently executing task group ID"
    )
    current_task: Optional[str] = Field(None, description="Currently executing task ID")
    checkpoints_completed: list[int] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    summary: Optional[str] = Field(
        None, description="Brief progress summary for quick resume"
    )
