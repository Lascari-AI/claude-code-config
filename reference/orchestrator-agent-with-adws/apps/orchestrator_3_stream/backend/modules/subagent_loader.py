"""
Subagent Template Loader

Discovers, parses, and caches subagent template files from .claude/agents/ directory.
Templates are markdown files with YAML frontmatter that define specialized agent configurations.
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from .logger import OrchestratorLogger
from .subagent_models import SubagentFrontmatter, SubagentTemplate


def parse_subagent_file(file_path: Path, logger: OrchestratorLogger) -> Optional[SubagentTemplate]:
    """
    Parse a subagent template file with YAML frontmatter.

    Args:
        file_path: Path to the .md template file
        logger: Logger instance for debug/error messages

    Returns:
        SubagentTemplate if parsing succeeds, None otherwise

    Template format:
        ---
        name: template-name
        description: Template description
        tools: [Read, Write, Edit]
        model: sonnet
        color: blue
        ---

        # System Prompt

        Agent instructions here...
    """
    logger.debug(f"Reading template file: {file_path}")

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read template file {file_path}: {e}")
        return None

    # Split frontmatter and body
    if not content.startswith('---'):
        logger.error(f"Template {file_path.name} missing frontmatter delimiter (should start with '---')")
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        logger.error(f"Template {file_path.name} has incomplete frontmatter (needs two '---' delimiters)")
        return None

    frontmatter_text = parts[1].strip()
    prompt_body = parts[2].strip()

    # Parse YAML frontmatter
    try:
        frontmatter_data = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter_data, dict):
            logger.error(f"Invalid YAML frontmatter in {file_path.name}: expected dictionary, got {type(frontmatter_data)}")
            return None
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML frontmatter in {file_path.name}: {e}")
        return None

    # Parse tools field if it's a string (comma-separated)
    if 'tools' in frontmatter_data and isinstance(frontmatter_data['tools'], str):
        # Split by comma and strip whitespace
        tools_str = frontmatter_data['tools']
        frontmatter_data['tools'] = [t.strip() for t in tools_str.split(',') if t.strip()]

    # Validate with Pydantic
    try:
        frontmatter = SubagentFrontmatter(**frontmatter_data)
    except ValidationError as e:
        logger.error(f"Template validation failed for {file_path.name}: {e}")
        return None

    # Create template instance
    try:
        template = SubagentTemplate(
            frontmatter=frontmatter,
            prompt_body=prompt_body,
            file_path=file_path
        )
        return template
    except ValidationError as e:
        logger.error(f"Template validation failed for {file_path.name}: {e}")
        return None


class SubagentRegistry:
    """
    Registry for discovering and caching subagent templates.

    Scans .claude/agents/ directory for template files, parses them,
    and provides lookup by name.
    """

    def __init__(self, working_dir: str | Path, logger: OrchestratorLogger):
        """
        Initialize the subagent registry.

        Args:
            working_dir: Orchestrator working directory
            logger: Logger instance
        """
        self.working_dir = Path(working_dir)
        self.logger = logger
        self.templates_dir = self.working_dir / ".claude" / "agents"
        self._templates: Dict[str, SubagentTemplate] = {}

        self.logger.info(f"Initializing SubagentRegistry with working_dir: {self.working_dir}")
        self.logger.info(f"Templates directory: {self.templates_dir}")

        # Discover templates immediately
        self._templates = self.discover_templates()

    def discover_templates(self) -> Dict[str, SubagentTemplate]:
        """
        Discover and parse all template files in .claude/agents/.

        Returns:
            Dictionary mapping template name to SubagentTemplate

        Logs:
            - Warnings if directory doesn't exist or no templates found
            - Info for each successfully loaded template
            - Summary of discovery results
        """
        templates: Dict[str, SubagentTemplate] = {}

        # Check if directory exists
        if not self.templates_dir.exists():
            self.logger.warning(f"⚠️  Subagent templates directory not found: {self.templates_dir}")
            self.logger.warning("💡 Create .claude/agents/ directory and add *.md template files to enable specialized agents")
            self.logger.info(f"Run: mkdir -p {self.templates_dir}")
            return templates

        self.logger.info(f"Scanning for templates in {self.templates_dir}")

        # Find all .md files
        template_files = list(self.templates_dir.glob("*.md"))

        if not template_files:
            self.logger.warning(f"⚠️  No .md files found in {self.templates_dir}")
            return templates

        # Parse each template file
        valid_count = 0
        for file_path in template_files:
            self.logger.debug(f"Parsing template file: {file_path.name}")

            template = parse_subagent_file(file_path, self.logger)

            if template:
                templates[template.frontmatter.name] = template
                valid_count += 1
                tool_count = len(template.frontmatter.tools)
                model = template.frontmatter.model or "default"
                self.logger.info(f"✓ Loaded template: {template.frontmatter.name} (tools: {tool_count}, model: {model})")
            else:
                self.logger.warning(f"✗ Skipping invalid template {file_path.name}")

        # Summary
        if templates:
            names = ', '.join(sorted(templates.keys()))
            self.logger.info(f"✅ Discovered {len(templates)} subagent template(s): {names}")
        else:
            if template_files:
                self.logger.error(f"❌ Found {len(template_files)} files but no valid templates")
            self.logger.warning(f"⚠️  No valid templates found in {self.templates_dir}")

        return templates

    def get_template(self, name: str) -> Optional[SubagentTemplate]:
        """
        Retrieve a template by name.

        Args:
            name: Template name to look up

        Returns:
            SubagentTemplate if found, None otherwise
        """
        template = self._templates.get(name)
        if not template:
            self.logger.debug(f"Template '{name}' not found in registry")
        return template

    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available templates with names and descriptions.

        Returns:
            List of dicts with 'name' and 'description' keys
        """
        return [
            {"name": t.frontmatter.name, "description": t.frontmatter.description}
            for t in self._templates.values()
        ]

    def get_available_names(self) -> List[str]:
        """
        Get sorted list of available template names.

        Returns:
            Sorted list of template names
        """
        return sorted(self._templates.keys())

    def has_templates(self) -> bool:
        """Check if any templates are available."""
        return len(self._templates) > 0
