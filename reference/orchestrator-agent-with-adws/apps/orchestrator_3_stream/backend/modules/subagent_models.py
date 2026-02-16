"""
Subagent Template Models

Pydantic models for parsing and validating subagent template files.
Templates are markdown files with YAML frontmatter that define specialized agent configurations.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SubagentFrontmatter(BaseModel):
    """
    Frontmatter metadata for a subagent template.

    This contains the configuration extracted from the YAML frontmatter section
    of a .claude/agents/*.md template file.

    Attributes:
        name: Unique identifier for the template
        description: Human-readable description of the agent's purpose
        tools: Optional list/string of allowed Claude SDK tools (defaults to all tools if not specified)
        model: Optional model override (sonnet, haiku, opus)
        color: Optional color for UI theming
    """
    name: str = Field(..., description="Unique template identifier")
    description: str = Field(..., description="Template description for orchestrator")
    tools: Optional[List[str]] = Field(None, description="List of allowed tool names (optional, defaults to all tools)")
    model: Optional[str] = Field(None, description="Model override (sonnet, haiku, opus)")
    color: Optional[str] = Field(None, description="UI theme color")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name is non-empty and kebab-case."""
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is non-empty."""
        if not v or not v.strip():
            raise ValueError("Template description cannot be empty")
        return v.strip()


class SubagentTemplate(BaseModel):
    """
    Complete subagent template with frontmatter and prompt body.

    Represents a fully parsed template file ready for use in agent creation.

    Attributes:
        frontmatter: Parsed YAML frontmatter configuration
        prompt_body: System prompt text (everything after frontmatter)
        file_path: Path to the source template file
    """
    frontmatter: SubagentFrontmatter = Field(..., description="Template configuration")
    prompt_body: str = Field(..., description="Agent system prompt text")
    file_path: Path = Field(..., description="Source template file path")

    @field_validator('prompt_body')
    @classmethod
    def validate_prompt_body(cls, v: str) -> str:
        """Validate prompt body is non-empty."""
        if not v or not v.strip():
            raise ValueError("Template prompt body cannot be empty")
        return v.strip()

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True  # Allow Path type
