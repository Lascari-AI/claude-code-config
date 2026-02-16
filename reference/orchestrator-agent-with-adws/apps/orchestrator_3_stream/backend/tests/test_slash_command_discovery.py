"""
Test slash command discovery with nested directories

Tests the discover_slash_commands() function to ensure it properly:
- Discovers commands in root .claude/commands/ directory
- Recursively discovers commands in subdirectories
- Generates proper namespaced names using colons
- Maintains backward compatibility with root-level commands
- Handles edge cases like empty directories and deep nesting
"""

import os
import sys

import pytest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.slash_command_parser import discover_slash_commands


def test_discover_root_level_commands(tmp_path):
    """Test that root-level commands are discovered with simple names"""

    # Create test directory structure
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create root level command
    root_cmd = commands_dir / "test.md"
    root_cmd.write_text("""---
description: Root level test command
argument-hint: [arg1]
model: sonnet
---
# Test Command
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify command found
    assert len(commands) == 1

    # Verify root command has simple name
    assert commands[0]["name"] == "test"
    assert commands[0]["description"] == "Root level test command"
    assert commands[0]["arguments"] == "[arg1]"
    assert commands[0]["model"] == "sonnet"


def test_discover_nested_commands(tmp_path):
    """Test that nested slash commands are discovered with namespaced names"""

    # Create test directory structure
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create root level command
    root_cmd = commands_dir / "test.md"
    root_cmd.write_text("""---
description: Root level test command
---
# Test Command
""")

    # Create nested command
    nested_dir = commands_dir / "experts" / "websocket"
    nested_dir.mkdir(parents=True)
    nested_cmd = nested_dir / "question.md"
    nested_cmd.write_text("""---
description: Nested websocket command
argument-hint: [question]
model: haiku
---
# Websocket Question
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify both commands found
    assert len(commands) == 2

    # Verify root command has simple name
    root = next((c for c in commands if c["name"] == "test"), None)
    assert root is not None
    assert root["description"] == "Root level test command"

    # Verify nested command has namespaced name
    nested = next((c for c in commands if c["name"] == "experts:websocket:question"), None)
    assert nested is not None
    assert nested["description"] == "Nested websocket command"
    assert nested["arguments"] == "[question]"
    assert nested["model"] == "haiku"


def test_discover_multiple_nesting_levels(tmp_path):
    """Test commands at different nesting levels"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Level 0 (root)
    (commands_dir / "root.md").write_text("---\ndescription: Root\n---\n# Root")

    # Level 1
    level1_dir = commands_dir / "level1"
    level1_dir.mkdir()
    (level1_dir / "cmd1.md").write_text("---\ndescription: Level 1\n---\n# L1")

    # Level 2
    level2_dir = level1_dir / "level2"
    level2_dir.mkdir()
    (level2_dir / "cmd2.md").write_text("---\ndescription: Level 2\n---\n# L2")

    # Level 3
    level3_dir = level2_dir / "level3"
    level3_dir.mkdir()
    (level3_dir / "cmd3.md").write_text("---\ndescription: Level 3\n---\n# L3")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify all commands found
    assert len(commands) == 4

    # Extract command names
    names = [c["name"] for c in commands]

    # Verify correct namespacing at each level
    assert "root" in names
    assert "level1:cmd1" in names
    assert "level1:level2:cmd2" in names
    assert "level1:level2:level3:cmd3" in names

    # Verify descriptions are preserved
    assert next(c for c in commands if c["name"] == "root")["description"] == "Root"
    assert next(c for c in commands if c["name"] == "level1:cmd1")["description"] == "Level 1"
    assert next(c for c in commands if c["name"] == "level1:level2:cmd2")["description"] == "Level 2"
    assert next(c for c in commands if c["name"] == "level1:level2:level3:cmd3")["description"] == "Level 3"


def test_empty_commands_directory(tmp_path):
    """Test with no commands"""
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    commands = discover_slash_commands(str(tmp_path))
    assert len(commands) == 0


def test_missing_commands_directory(tmp_path):
    """Test with missing .claude/commands directory"""
    commands = discover_slash_commands(str(tmp_path))
    assert len(commands) == 0


def test_commands_without_frontmatter(tmp_path):
    """Test that commands without frontmatter still get discovered"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command without frontmatter
    cmd = commands_dir / "no-frontmatter.md"
    cmd.write_text("# Just a regular markdown file\n\nWith no frontmatter")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify command found with empty metadata
    assert len(commands) == 1
    assert commands[0]["name"] == "no-frontmatter"
    assert commands[0]["description"] == ""
    assert commands[0]["arguments"] == ""
    assert commands[0]["model"] == ""


def test_nested_commands_without_frontmatter(tmp_path):
    """Test that nested commands without frontmatter get proper names"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create nested command without frontmatter
    nested_dir = commands_dir / "tools" / "build"
    nested_dir.mkdir(parents=True)
    cmd = nested_dir / "parallel.md"
    cmd.write_text("# Build in parallel")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify namespaced name is correct
    assert len(commands) == 1
    assert commands[0]["name"] == "tools:build:parallel"
    assert commands[0]["description"] == ""


def test_sorting_of_commands(tmp_path):
    """Test that commands are sorted alphabetically by name"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create commands in non-alphabetical order
    (commands_dir / "zebra.md").write_text("---\ndescription: Z\n---\n")
    (commands_dir / "alpha.md").write_text("---\ndescription: A\n---\n")
    (commands_dir / "beta.md").write_text("---\ndescription: B\n---\n")

    nested_dir = commands_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "gamma.md").write_text("---\ndescription: G\n---\n")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify sorting
    names = [c["name"] for c in commands]
    assert names == sorted(names)
    assert names == ["alpha", "beta", "nested:gamma", "zebra"]


def test_special_characters_in_arguments(tmp_path):
    """Test that special characters in argument-hint are preserved"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command with special characters in argument-hint
    cmd = commands_dir / "tag.md"
    cmd.write_text("""---
description: Manage tags
argument-hint: add [tagId] | remove [tagId] | list
---
# Tag Management
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify special characters are preserved
    assert len(commands) == 1
    assert commands[0]["arguments"] == "add [tagId] | remove [tagId] | list"


def test_all_frontmatter_fields(tmp_path):
    """Test that all frontmatter fields are properly extracted"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command with all fields (using proper YAML list syntax)
    cmd = commands_dir / "full.md"
    cmd.write_text("""---
description: Full featured command
argument-hint: [input] [output]
model: opus
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
---
# Full Command
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify all fields
    assert len(commands) == 1
    assert commands[0]["name"] == "full"
    assert commands[0]["description"] == "Full featured command"
    assert commands[0]["arguments"] == "[input] [output]"
    assert commands[0]["model"] == "opus"
    assert commands[0]["allowed_tools"] == ["Read", "Write", "Bash"]
    assert commands[0]["disable_model_invocation"] is True


def test_command_name_collision_avoidance(tmp_path):
    """Test that nested structure avoids collisions"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create root-level plan command
    (commands_dir / "plan.md").write_text("---\ndescription: Root plan\n---\n")

    # Create nested plan command in subdirectory
    plan_dir = commands_dir / "plan"
    plan_dir.mkdir()
    (plan_dir / "default.md").write_text("---\ndescription: Nested plan\n---\n")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify both commands exist with different names
    assert len(commands) == 2

    names = [c["name"] for c in commands]
    assert "plan" in names
    assert "plan:default" in names

    # Verify they are distinct
    root_plan = next(c for c in commands if c["name"] == "plan")
    nested_plan = next(c for c in commands if c["name"] == "plan:default")

    assert root_plan["description"] == "Root plan"
    assert nested_plan["description"] == "Nested plan"


def test_deeply_nested_command(tmp_path):
    """Test command with very deep nesting"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create deeply nested command
    deep_dir = commands_dir / "a" / "b" / "c" / "d" / "e"
    deep_dir.mkdir(parents=True)
    (deep_dir / "deep.md").write_text("---\ndescription: Very deep\n---\n")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify deep nesting
    assert len(commands) == 1
    assert commands[0]["name"] == "a:b:c:d:e:deep"
    assert commands[0]["description"] == "Very deep"


def test_multiple_commands_in_same_nested_directory(tmp_path):
    """Test multiple commands in the same nested directory"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create multiple commands in same nested directory
    experts_dir = commands_dir / "experts" / "websocket"
    experts_dir.mkdir(parents=True)

    (experts_dir / "question.md").write_text("---\ndescription: Ask questions\n---\n")
    (experts_dir / "analyze.md").write_text("---\ndescription: Analyze code\n---\n")
    (experts_dir / "debug.md").write_text("---\ndescription: Debug issues\n---\n")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify all commands found with same namespace prefix
    assert len(commands) == 3

    names = [c["name"] for c in commands]
    assert "experts:websocket:analyze" in names
    assert "experts:websocket:debug" in names
    assert "experts:websocket:question" in names


def test_mixed_root_and_nested_commands(tmp_path):
    """Test mix of root and nested commands together"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Root commands
    (commands_dir / "build.md").write_text("---\ndescription: Build project\n---\n")
    (commands_dir / "test.md").write_text("---\ndescription: Run tests\n---\n")

    # Nested commands in different directories
    tools_dir = commands_dir / "tools"
    tools_dir.mkdir()
    (tools_dir / "format.md").write_text("---\ndescription: Format code\n---\n")

    experts_dir = commands_dir / "experts" / "api"
    experts_dir.mkdir(parents=True)
    (experts_dir / "analyze.md").write_text("---\ndescription: Analyze API\n---\n")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify all commands found
    assert len(commands) == 4

    names = [c["name"] for c in commands]
    assert "build" in names
    assert "test" in names
    assert "tools:format" in names
    assert "experts:api:analyze" in names


def test_comma_separated_allowed_tools(tmp_path):
    """Test that comma-separated allowed-tools are parsed correctly"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command with comma-separated allowed-tools
    cmd = commands_dir / "comma.md"
    cmd.write_text("""---
description: Command with comma-separated tools
allowed-tools: Bash, Read, Write, Edit
argument-hint: [input]
---
# Comma Test
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify allowed_tools parsed as list
    assert len(commands) == 1
    assert commands[0]["name"] == "comma"
    assert commands[0]["allowed_tools"] == ["Bash", "Read", "Write", "Edit"]
    assert commands[0]["description"] == "Command with comma-separated tools"


def test_yaml_list_allowed_tools(tmp_path):
    """Test that YAML list format for allowed-tools works"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command with YAML list allowed-tools
    cmd = commands_dir / "yamllist.md"
    cmd.write_text("""---
description: Command with YAML list tools
allowed-tools:
  - Bash
  - Read
  - Write
---
# YAML List Test
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify allowed_tools parsed as list
    assert len(commands) == 1
    assert commands[0]["name"] == "yamllist"
    assert commands[0]["allowed_tools"] == ["Bash", "Read", "Write"]
    assert commands[0]["description"] == "Command with YAML list tools"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
