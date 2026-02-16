# Custom Slash Command Template

This template is for creating **custom slash commands** stored in `.claude/commands/*.md` and invoked with `/command-name`.

## Structure Overview

Every custom slash command consists of:
1. **Frontmatter** (YAML configuration)
2. **Purpose** (what the command does)
3. **Variables** (dynamic and static values)
4. **Codebase Structure** (optional - only if relevant)
5. **Instructions** (rules, constraints, guidelines)
6. **Workflow** (step-by-step execution)
7. **Report** (output format specification)

---

## Section Breakdown

**Purpose**: 1-3 sentence description of what the command does and why it exists.

**Variables**: Dynamic variables from command arguments (`$1`, `$2`, `$ARGUMENTS`) and static configuration values.

**Codebase Structure**: (Optional) Relevant project organization - only include when the command needs to work with specific directory structures.

**Instructions**: Detailed bullet-point rules and constraints that Claude must follow when executing the command.

**Workflow**: Step-by-step numbered actions needed to complete the task. Always ends with "Now follow the `Report` section to report the completed work".

**Report**: Exact output format specification with markdown structure, placeholders, and what information to include.

---

## Frontmatter Configuration

Frontmatter is YAML metadata at the top of your command file that controls Claude's behavior. Place it between `---` markers before your command content.

### Required Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `model` | Claude model version | `claude-sonnet-4-5-20250929` |
| `description` | Brief command description for `/help` menu | `Review code for best practices` |

### Optional Fields

| Field | Purpose | When to Use |
|-------|---------|-------------|
| `argument-hint` | Shows expected arguments in autocomplete | For commands with parameters: `[pr-number] [priority]` |
| `allowed-tools` | Restricts which tools can be used | When limiting tool access: `Bash(git:*)` for git-only |

### Important Notes

- **Always include** `model: claude-sonnet-4-5-20250929` for consistency and optimal performance
- **Always include** a clear `description` field for the `/help` menu
- **Only include** `allowed-tools` when you need to restrict tool access
- **DO NOT use** `disable-model-invocation` - we want agents to be able to trigger commands

### Example Frontmatter Configurations

**Basic slash command (most common):**
```yaml
---
model: claude-sonnet-4-5-20250929
description: Review code for best practices
---
```

**Command with arguments:**
```yaml
---
model: claude-sonnet-4-5-20250929
description: Creates implementation plan from user requirements and documentation
argument-hint: [user-prompt] [doc-urls]
---
```

**Command with restricted tools:**
```yaml
---
model: claude-sonnet-4-5-20250929
description: Show git commit history for a specific file
argument-hint: [file-path]
allowed-tools: Bash(git:*)
---
```

---

## Complete Template

Use this template when creating new slash commands. Replace all `[placeholders]` with actual content:

```markdown
---
model: claude-sonnet-4-5-20250929
description: [Brief description for /help menu]
argument-hint: [arg1] [arg2] (only if command takes arguments)
allowed-tools: [Only specify if restricting tools]
---

# Purpose

[1-3 sentence description of what this command does and the problem it solves]

## Variables

[Define dynamic and static variables]

```example
DYNAMIC_VARIABLE_NAME: $1
DYNAMIC_VARIABLE_NAME_2: $2
STATIC_VARIABLE_NAME: "static value"
```

## Codebase Structure

[Optional - Only include if command needs to work with specific directory structures]

```
project/
├── relevant-dir/    # Brief description
└── another-dir/     # Brief description
```

## Instructions

[Detailed bullet-point rules and constraints]

- [Specific rule or requirement]
- [What to do]
- [What NOT to do]
- [Edge cases to handle]
- [Tool usage guidelines]

## Workflow

[Step-by-step numbered actions]

1. [First action with details and which tools to use]
2. [Second action with specifics]
   - [Sub-step if needed]
   - [Sub-step if needed]
3. [Continue until complete]
4. Now follow the `Report` section to report the completed work

## Report

[Exact output format specification]

Present [findings/results/completion] in this format:

## [Report Title]

**[Key Metric 1]**: [value]
**[Key Metric 2]**: [value]

### [Section Name]
- [Detail 1]
- [Detail 2]

[Include code blocks, tables, lists as needed to show exact structure]
```

---

## Quick Reference

### File Naming
- Save to `.claude/commands/[command-name].md`
- Use lowercase with hyphens for multi-word names
- Example: `.claude/commands/review-pr.md` for `/review-pr`

### Variable Syntax
- `$1`, `$2`, `$3` - Individual positional arguments
- `$ARGUMENTS` - All arguments as a single string
- `STATIC_VAR: "value"` - Constants used in the command

### Workflow Best Practices
- Number every step clearly (1, 2, 3...)
- Use action verbs (Read, Analyze, Create, Run, etc.)
- Specify which tools to use
- Break complex steps into sub-bullets
- Always end with reference to Report section

### Report Format
- Show exact structure with placeholders
- Use markdown formatting (headers, lists, code blocks, tables)
- Make it clear what data goes where
- Provide examples when helpful

---

## Example Commands

See the `examples/` directory for complete working examples:

- **orch_one_shot_agent.md** - Simple workflow with agent lifecycle management
- **orch_scout_and_build.md** - Multi-phase workflow with two sequential agents
- **plan.md** - Complex command with detailed output format specification
- **question.md** - Simple read-only command with tool restrictions

---

## Testing Your Command

After creating your slash command:

1. **Test invocation**: `/[command-name] [test-arguments]`
2. **Verify behavior**: Ensure it follows the workflow correctly
3. **Check output**: Confirm report format matches specification
4. **Iterate**: Refine based on results

---

Remember: Custom slash commands are powerful tools for creating consistent, repeatable workflows. Take time to design clear workflows and well-structured reports for the best results.
