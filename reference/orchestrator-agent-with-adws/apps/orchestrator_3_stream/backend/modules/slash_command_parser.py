"""
Slash Command Frontmatter Parser

Parses YAML frontmatter from slash command .md files with special handling
for the argument-hint field, which should always be treated as a plain string.

Reference: https://docs.anthropic.com/en/docs/claude-code/slash-commands
"""

import re
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class SlashCommandFrontmatter(BaseModel):
    """
    Pydantic model for slash command frontmatter.

    All fields are optional per the Claude Code specification.
    """

    allowed_tools: Optional[List[str]] = Field(
        default=None,
        alias="allowed-tools",
        description="Tools the command can use. Inherits from conversation if not specified.",
    )

    argument_hint: Optional[str] = Field(
        default=None,
        alias="argument-hint",
        description="Arguments expected for slash command. Example: 'add [tagId] | remove [tagId] | list'",
    )

    description: Optional[str] = Field(
        default=None, description="Brief description. Uses first line if not specified."
    )

    model: Optional[str] = Field(
        default=None,
        description="Specific model string. Inherits from conversation if not specified.",
    )

    disable_model_invocation: Optional[bool] = Field(
        default=False,
        alias="disable-model-invocation",
        description="Prevent SlashCommand tool from calling this command.",
    )

    class Config:
        populate_by_name = True  # Allow both 'argument_hint' and 'argument-hint'

    @field_validator('allowed_tools', mode='before')
    @classmethod
    def parse_allowed_tools(cls, v):
        """
        Parse allowed_tools field to handle both formats:
        - YAML list: ['Read', 'Write', 'Bash']
        - Comma-separated string: 'Read, Write, Bash'

        Always returns a list of strings.
        """
        if v is None:
            return None
        if isinstance(v, list):
            # Already a list, return as-is
            return v
        if isinstance(v, str):
            # Split comma-separated string and strip whitespace
            return [tool.strip() for tool in v.split(',') if tool.strip()]
        return v

    @field_validator('argument_hint', mode='before')
    @classmethod
    def parse_argument_hint(cls, v):
        """
        Parse argument_hint field to ensure it's always a string.

        YAML sometimes parses [arg] as a list, but we want it as a string.
        """
        if v is None:
            return None
        if isinstance(v, list):
            # Convert list back to string representation
            # This handles the case where YAML parsed [arg] as a list
            return str(v[0]) if len(v) == 1 else str(v)
        return v


def parse_slash_command_frontmatter(
    frontmatter_text: str,
) -> Optional[SlashCommandFrontmatter]:
    """
    Parse slash command YAML frontmatter with special handling for argument-hint.

    The argument-hint field can contain square brackets like [tagId] which are NOT
    YAML list syntax - they're just documentation notation. This parser ensures
    argument-hint is always treated as a plain string.

    Args:
        frontmatter_text: Raw YAML frontmatter text (without --- delimiters)

    Returns:
        SlashCommandFrontmatter model or None if parsing fails

    Example:
        >>> frontmatter = '''
        ... description: Add or remove tags
        ... argument-hint: add [tagId] | remove [tagId] | list
        ... model: sonnet
        ... '''
        >>> result = parse_slash_command_frontmatter(frontmatter)
        >>> result.argument_hint
        'add [tagId] | remove [tagId] | list'
    """
    if not frontmatter_text or not frontmatter_text.strip():
        return None

    # Pre-process the frontmatter to auto-quote argument-hint values
    processed_text = _preprocess_argument_hint(frontmatter_text)

    # Parse with YAML
    try:
        data = yaml.safe_load(processed_text)
        if data is None:
            return None

        # Convert to Pydantic model
        return SlashCommandFrontmatter(**data)

    except (yaml.YAMLError, ValueError) as e:
        # If parsing fails, return None (caller should handle)
        return None


def _preprocess_argument_hint(frontmatter_text: str) -> str:
    """
    Pre-process frontmatter to ensure argument-hint values are quoted.

    This allows argument-hint to contain square brackets and other special
    characters without YAML interpreting them as syntax.

    Args:
        frontmatter_text: Raw YAML frontmatter text

    Returns:
        Processed YAML with argument-hint values properly quoted

    Example:
        >>> text = "argument-hint: add [tagId] | remove [tagId]"
        >>> _preprocess_argument_hint(text)
        'argument-hint: "add [tagId] | remove [tagId]"'
    """
    lines = frontmatter_text.split("\n")
    processed_lines = []

    for line in lines:
        # Match lines like: "argument-hint: <value>"
        # Capture the key and value separately
        match = re.match(r"^(\s*argument-hint\s*:\s*)(.+?)(\s*)$", line)

        if match:
            indent = match.group(1)  # "argument-hint: "
            value = match.group(2)  # The actual value
            trailing = match.group(3)  # Trailing whitespace

            # Check if value is already quoted
            if value.startswith('"') and value.endswith('"'):
                # Already quoted, keep as-is
                processed_lines.append(line)
            elif value.startswith("'") and value.endswith("'"):
                # Already quoted with single quotes, keep as-is
                processed_lines.append(line)
            else:
                # Not quoted - check if it needs quoting
                # Quote if it contains special YAML characters: [ ] { } : | > etc.
                needs_quoting = any(
                    char in value for char in ["[", "]", "{", "}", ":", "|", ">", "#"]
                )

                if needs_quoting:
                    # Escape any existing quotes in the value
                    escaped_value = value.replace('"', '\\"')
                    # Add quotes around the value
                    processed_lines.append(f'{indent}"{escaped_value}"{trailing}')
                else:
                    # No special characters, keep as-is
                    processed_lines.append(line)
        else:
            # Not an argument-hint line, keep as-is
            processed_lines.append(line)

    return "\n".join(processed_lines)


def parse_slash_command_file(file_content: str) -> Optional[SlashCommandFrontmatter]:
    """
    Parse a complete slash command .md file and extract frontmatter.

    Args:
        file_content: Full content of the .md file

    Returns:
        SlashCommandFrontmatter model or None if no valid frontmatter found

    Example:
        >>> content = '''---
        ... description: My command
        ... argument-hint: [arg1] [arg2]
        ... ---
        ...
        ... # Command content here
        ... '''
        >>> result = parse_slash_command_file(content)
        >>> result.argument_hint
        '[arg1] [arg2]'
    """
    if not file_content.startswith("---"):
        return None

    # Split by --- to extract frontmatter
    parts = file_content.split("---", 2)

    if len(parts) < 3:
        return None

    frontmatter_text = parts[1]

    return parse_slash_command_frontmatter(frontmatter_text)


def discover_slash_commands(working_dir: str) -> List[dict]:
    """
    Discover slash commands from .claude/commands/ directory.

    Searches recursively for all .md files in subdirectories and creates
    namespaced command names based on directory structure.

    Uses the proper slash command parser to extract frontmatter metadata
    including name, description, arguments, and model.

    Args:
        working_dir: Working directory containing .claude/commands/

    Returns:
        List of dicts with name, description, arguments, model

    Examples:
        Root-level command:
        .claude/commands/plan.md → "plan"

        Nested command:
        .claude/commands/experts/websocket/question.md → "experts:websocket:question"

        >>> commands = discover_slash_commands("/path/to/project")
        >>> commands[0]
        {
            "name": "my-command",
            "description": "Does something cool",
            "arguments": "[arg1] [arg2]",
            "model": "sonnet"
        }
    """
    import logging
    from pathlib import Path

    logger = logging.getLogger(__name__)
    commands = []
    commands_dir = Path(working_dir) / ".claude" / "commands"

    if not commands_dir.exists():
        return commands

    # Find all .md files recursively in subdirectories
    for file_path in commands_dir.glob("**/*.md"):
        try:
            content = file_path.read_text()
            frontmatter = parse_slash_command_file(content)

            # Build namespaced command name based on directory structure
            # Calculate relative path from commands_dir
            relative_path = file_path.relative_to(commands_dir)

            # Get parent directory (if nested)
            if relative_path.parent != Path('.'):
                # Convert path separators to colons
                # Handle both Unix (/) and Windows (\) path separators
                namespace = str(relative_path.parent).replace('/', ':').replace('\\', ':')
                command_name = f"{namespace}:{file_path.stem}"
            else:
                # Root level command - use simple name
                command_name = file_path.stem

            if frontmatter:
                commands.append(
                    {
                        "name": command_name,
                        "description": frontmatter.description or "",
                        "arguments": frontmatter.argument_hint or "",
                        "model": frontmatter.model or "",
                        "allowed_tools": frontmatter.allowed_tools or [],
                        "disable_model_invocation": frontmatter.disable_model_invocation
                        or False,
                    }
                )
            else:
                commands.append(
                    {
                        "name": command_name,
                        "description": "",
                        "arguments": "",
                        "model": "",
                        "allowed_tools": [],
                        "disable_model_invocation": False,
                    }
                )
        except Exception as e:
            logger.error(
                f"Failed to parse slash command file {file_path.name}: {e}",
                exc_info=True
            )
            raise

    # Sort by name
    commands.sort(key=lambda x: x["name"])

    return commands
