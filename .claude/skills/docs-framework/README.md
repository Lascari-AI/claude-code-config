# Read-What-You-Need (RWYN)

**Structured Documentation for Efficient AI Collaboration**

RWYN is a documentation framework that helps AI agents navigate your codebase efficiently by creating a shared understanding structure.

It organizes knowledge hierarchically, letting agents load only what they need for each specific task.

## The Problem We're Solving

Every time you start an AI agent, it has zero context about your codebase—your architecture, design patterns, or existing solutions.

Without this context, even capable AI will duplicate existing code, break patterns, and work against your design.

RWYN addresses this by providing a structured way to document your mental model so AI agents can:
- Find the right existing code instead of recreating it
- Respect your architectural patterns
- Make changes that align with your design decisions
- Navigate efficiently to just the information needed for each task

## How It Works

RWYN uses two complementary organization schemes:

**Three Zones** (by purpose):
```
docs/
├── .rwyn.yaml         # Manifest (scope, coverage, version)
├── 00-foundation/     # Why we build (purpose, principles, boundaries)
├── 10-codebase/       # How it works (mirrors code structure)
└── 99-appendix/       # Operations (setup, deployment)
```

**Six Layers** (by depth, within Codebase):
```
L1: Codebase Overview  (docs/10-codebase/00-overview.md)
L2: Section Overviews  (High-level domains)
L3: Atomic Concepts    (Specific patterns/rules)
L4: File Headers       (File responsibilities)
L5: Function Docstrings(Function contracts)
L6: Implementation     (The code itself)
```

**Two Scopes** (what you're documenting):
| Scope | Use Case | `docs/` Location |
|-------|----------|------------------|
| **Repository** | Documenting the entire codebase | Repository root |
| **Component** | Documenting a self-contained module within a larger codebase | Component directory |

Agents read Foundation first to understand intent, then traverse Codebase for implementation details.

> **Start Here**: Read [Why This Framework](.claude/skills/docs-framework/00-reference/10-philosophy.md) for a deeper explanation of the principles.

## For AI Agents

If you are an AI agent, your entry point is **[.claude/skills/docs-framework/SKILL.md](.claude/skills/docs-framework/SKILL.md)**.
Start there to understand how to read and write documentation in this project.

## Key Benefits

- **Minimal context loading**:
  - Load only the documentation needed for your specific task
- **Clear separation of concerns**:
  - Foundation explains Why, Codebase explains How, code shows What
- **Works for both humans and AI**:
  - Same structure supports manual exploration and automated navigation
- **Preserves architectural integrity**:
  - AI understands your design decisions and respects them

When you use this framework in your project:
- `.claude/skills/docs-framework/` contains the framework (skill, workflows, templates)
- `.claude/commands/docs/` contains the slash commands (`/docs:init`, `/docs:audit`, etc.)
- `docs/` is where YOUR project documentation goes:
  - `docs/.rwyn.yaml` - Manifest defining scope and coverage
  - `docs/00-foundation/` - Purpose, principles, boundaries
  - `docs/10-codebase/` - Architecture and code documentation
  - `docs/99-appendix/` - Setup and operational guides