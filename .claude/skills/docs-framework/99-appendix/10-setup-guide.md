---
covers: How to add the documentation framework to your project using drag-and-drop.
concepts: [setup, installation, drag-and-drop, initialization]
---

# Setup Guide

Simple drag-and-drop installation — copy the framework to your project, run `/docs:init`, and start documenting. No scripts, no symlinks.

---

## Prerequisites

- A project you want to document
- Claude Code (for agents, skills, and commands)

## Installation: Drag and Drop

This framework uses a simple copy-and-paste workflow. No install scripts. No symlinks.

### Step 1: Copy the Framework

Copy these folders from the docs-framework repository to your project:

| Source | Destination | Purpose |
|--------|-------------|---------|
| `.claude/skills/docs-framework/` | `.claude/skills/docs-framework/` | documentation framework (skill, templates, workflows) |
| `.claude/commands/docs/` | `.claude/commands/docs/` | docs commands |

That's it. You're done with installation.

### Step 2: Initialize Your Documentation

In Claude Code, run:

```
/docs:init
```

The init command will ask you to choose a **scope**:

| Scope | Use When | Creates |
|-------|----------|---------|
| **repository** | Documenting the entire codebase | `docs/` at repository root |
| **component** | Documenting a self-contained module within a larger codebase | `docs/` in current directory |

This creates your `docs/` directory with the manifest and three-zone structure:

```
docs/
├── .rwyn.yaml               # Manifest (scope, coverage, version)
├── 00-foundation/           # Intent zone
│   ├── 00-overview.md
│   ├── 10-purpose.md
│   ├── 20-principles.md
│   └── 30-boundaries.md
├── 10-codebase/             # Structure zone
│   └── 00-overview.md       # L1 codebase overview
└── 99-appendix/             # Operational zone
    └── 00-overview.md
```

### The Manifest (`.rwyn.yaml`)

The manifest is created during init and tracks:

```yaml
rwyn: 1.0              # Framework version
scope: repository      # or 'component'
coverage: partial      # or 'complete'
status: draft          # or 'stable' (optional)
updated: 2025-01-15    # Last update date
```

For component scope, it also includes a `root` field pointing to the code directory.

### Step 3: Fill In Foundation

Start with the Foundation zone—this primes all future documentation.

**Option A: Interview-driven** (recommended)
Run `/docs:interview-foundation` to have an interactive conversation that extracts your purpose, principles, and boundaries, then run `/docs:draft foundation` to generate the docs.

**Option B: Manual**
Edit these files directly using the templates in `.claude/skills/docs-framework/40-templates/00-foundation-templates/`:
1. **Purpose** (`00-foundation/10-purpose.md`): Why does this system exist? Who does it serve?
2. **Principles** (`00-foundation/20-principles.md`): What heuristics guide decisions?
3. **Boundaries** (`00-foundation/30-boundaries.md`): What will this system NOT do?

### Step 4: Write Your L1 Codebase Overview

Edit `docs/10-codebase/00-overview.md` to describe your system architecture:
- System metaphor / mental model
- High-level architecture
- Section index (as you add sections)

## Directory Structure After Setup

```
your-project/
├── docs/                # YOUR project documentation
│   ├── 00-foundation/       # Intent zone (purpose, principles, boundaries)
│   ├── 10-codebase/         # Structure zone (mirrors your code)
│   └── 99-appendix/         # Operational zone (setup, deployment)
└── .claude/
    ├── skills/docs-framework/         # documentation framework (skill, templates, workflows)
    └── commands/docs/       # docs commands
```

## One Framework, One Output

| Directory | Contains | Managed By |
|-----------|----------|------------|
| `.claude/skills/docs-framework/` | documentation framework (skill, templates, workflows, rules) | docs-framework project |
| `docs/` | YOUR project documentation | You |

**Important:** Don't edit files in `.claude/skills/docs-framework/`—those are framework files. All your project documentation goes in `docs/`.

## Adding Sections to Codebase

For each major domain in your codebase, create a section inside `10-codebase/`:

```
docs/
├── 00-foundation/
│   └── ...
├── 10-codebase/
│   ├── 00-overview.md
│   ├── 10-authentication/
│   │   ├── 00-overview.md
│   │   └── 10-session-management.md
│   ├── 20-api/
│   │   └── 00-overview.md
│   └── 30-data/
│       └── 00-overview.md
└── 99-appendix/
    └── 00-overview.md
```

## Updating the Framework

To update the framework, copy the new `.claude/skills/docs-framework/` and `.claude/commands/docs/` folders over the old ones.

## Available Commands

### Setup & Structure
- **`/docs:init`** - Initialize `docs/` with three-zone structure
- **`/docs:scaffold`** - Generate section structure from source code

### Knowledge Extraction
- **`/docs:interview-foundation`** - Extract project purpose, principles, and boundaries through Socratic dialogue
- **`/docs:interview-codebase <path>`** - Extract understanding of a specific code area through interactive conversation

### Documentation Generation
- **`/docs:draft <section>`** - Generate documentation from interview notes

### Code Annotation
- **`/docs:annotate <path>`** - Add L4 file headers and L5 function docstrings to source code

### Maintenance
- **`/docs:audit`** - Check your documentation for structural issues and semantic drift
- **`/docs:sync`** - Compare code structure to documentation and identify gaps

## Troubleshooting

### Skills/commands not appearing in Claude Code

Ensure `.claude/` is at your project root and contains the `docs-framework/` and `docs/` folders. Restart Claude Code if needed.

### "docs/ already exists"

The `/docs:init` command validates existing structure rather than overwriting. Run `/docs:audit` to check the health of existing documentation.

### "Nested documentation is not supported"

You cannot create component documentation inside a directory that already has a parent `.rwyn.yaml`. Either:
1. Use the existing documentation structure
2. Extract the component to its own repository
