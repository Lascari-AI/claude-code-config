---
name: docs-framework
description: Documentation framework for maintaining structured, navigable documentation for the codebase. Use when reading docs/ to understand the codebase, or when writing/maintaining documentation.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(eza:*), Bash(tree:*), Bash(mkdir:*), Bash(find:*)
---

# Purpose

Maintain structured, layered documentation that is easy to navigate and update.
Follow the `Instructions`, execute the `Workflow`, based on the `Cookbook`.

## Variables

DOCS_ROOT: docs/
SKILL_ROOT: .claude/skills/docs-framework/

## Manifest Resolution

Before any workflow, locate the documentation root:

1. Search for `.rwyn.yaml` starting from current directory, then parents up to git root
2. If found: DOCS_ROOT = directory containing the manifest's parent `docs/` folder
3. If not found: DOCS_ROOT = `./docs/` (default at repository root)
4. Read manifest for `scope` (repository or component) and `coverage` (complete or partial)
5. For component scope: CODE_ROOT = manifest's `root` field

Discovery command: `find . -name ".rwyn.yaml" -type f`

## Instructions

- Based on your intent (navigate, produce, or maintain), follow the `Cookbook` to load the appropriate workflow.
- All documentation output goes to `docs/`
- Use slash commands for common operations (see Commands section)

## Workflow

1. Determine your intent (navigate, produce, maintain)
2. Follow the `Cookbook` to load the appropriate entry point
3. Execute the workflow steps from the loaded cookbook file

## Cookbook

### Navigate

- IF: You need to research, understand the codebase, or find where something is handled
- THEN: Read and execute: `10-cookbook/10-navigate.md`
- EXAMPLES:
  - "How does authentication work?"
  - "Where is error handling implemented?"
  - "What components use the API client?"

### Produce

- IF: You need to create new documentation for a feature, component, or significant addition
- THEN: Read and execute: `10-cookbook/20-produce.md`
- EXAMPLES:
  - "Document the new payment module"
  - "Create docs for the authentication system"
  - "Add documentation for the API endpoints"

### Maintain

- IF: You need to fix, update, refactor, or check alignment of existing documentation
- THEN: Read and execute: `10-cookbook/30-maintain.md`
- EXAMPLES:
  - "Update docs after refactoring auth"
  - "Check if docs are in sync with code"
  - "Fix outdated documentation"

---

## Architecture

### Documentation Output (`docs/`)

```
docs/
├── .rwyn.yaml         # Manifest (scope, coverage, version)
├── 00-foundation/     # Why we build (purpose, principles, boundaries)
├── 10-codebase/       # What we built (mirrors source structure)
└── 99-appendix/       # How to operate (setup, tooling)
```

### This Skill

```
.claude/skills/docs-framework/
├── 00-reference/      # Philosophy and background
├── 10-cookbook/       # Intent-based entry points
├── 20-standards/      # Structure rules and schemas
├── 30-workflows/      # Granular execution steps
├── 40-templates/      # Document templates
└── 99-appendix/       # Setup and configuration
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `/docs:init` | Initialize `docs/` structure with manifest |
| `/docs:scaffold <path>` | Map code structure to doc sections |
| `/docs:interview-foundation` | Extract purpose and principles |
| `/docs:interview-codebase <path>` | Extract code knowledge |
| `/docs:write <path> [notes]` | Write/update docs from notes |
| `/docs:annotate <path>` | Add headers/docstrings to code |
| `/docs:audit [quick|deep]` | Validate structure, manifest, and health |

---

## Reference

| Topic | Location |
|-------|----------|
| Philosophy | `00-reference/10-philosophy.md` |
| Architecture | `00-reference/20-architecture.md` |
| Standards | `20-standards/` |
| Templates | `40-templates/` |
| Setup | `99-appendix/10-setup-guide.md` |
