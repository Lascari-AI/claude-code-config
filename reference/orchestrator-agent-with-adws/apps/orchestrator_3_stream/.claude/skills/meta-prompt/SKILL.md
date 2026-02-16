---
name: meta-prompt
description: Generates new Claude Code custom slash command prompts following the established template structure. Use when the user asks to create a new slash command, generate a command prompt, or build a custom command for .claude/commands/
---

# Meta-Prompt Skill

## Purpose

This skill generates well-structured **custom slash commands** for Claude Code. These commands are stored in `.claude/commands/*.md` and can be invoked with `/command-name`. This skill focuses exclusively on creating slash commands, not system or user prompts.

## What Are Custom Slash Commands?

Custom slash commands are Markdown files that:
- Live in `.claude/commands/` (project-level) or `~/.claude/commands/` (personal)
- Get invoked with `/command-name`
- Support arguments via `$1`, `$2`, `$ARGUMENTS`
- Can reference files with `@filename`
- Can execute bash with `!command` (requires `allowed-tools` frontmatter)
- Include frontmatter configuration (YAML metadata)

## Slash Command Anatomy

Every slash command has **6 core sections**:

1. **Frontmatter** (YAML configuration)
2. **Purpose** (what the command does)
3. **Variables** (dynamic and static values)
4. **Codebase Structure** (optional - relevant project structure)
5. **Instructions** (rules, constraints, best practices)
6. **Workflow** (step-by-step execution)
7. **Report** (output format specification)

---

# Section 1: Purpose

## What It Is

The Purpose section provides a **1-3 sentence overview** of what the slash command does. It should be clear, concise, and answer: "What problem does this command solve?"

## Best Practices

✅ **Do:**
- Start with an action verb (e.g., "Generate", "Analyze", "Create", "Review")
- Be specific about what the command accomplishes
- Mention the expected outcome
- Keep it under 3 sentences

❌ **Don't:**
- Write long paragraphs
- Include implementation details
- Duplicate information from frontmatter description
- Use vague language

## Examples

### Good Purpose Statements

```markdown
# Purpose

Generate a concise engineering implementation plan based on user requirements and relevant documentation, then save it to the specs directory for future reference.
```

```markdown
# Purpose

Analyze code files for common security vulnerabilities including SQL injection, XSS, insecure dependencies, and authentication issues. Provides detailed findings with remediation suggestions.
```

```markdown
# Purpose

Create and command an agent to accomplish a small task then delete the agent when the task is complete.
```

### Bad Purpose Statements

```markdown
# Purpose

This command does stuff with files. It's useful for when you need to work on things.
```
*Too vague - doesn't explain what it actually does*

```markdown
# Purpose

This command first reads all the files in the directory, then it parses them using the Read tool, after that it analyzes the content by looking for specific patterns, then it generates a report with all the findings, and finally it saves everything to a file in the output directory with proper formatting and structure.
```
*Too detailed - this belongs in Workflow section*

---

# Section 2: Variables

## What It Is

The Variables section defines **all dynamic and static values** used throughout the command. This creates a clear contract for what inputs the command expects and what constants it uses.

## Variable Types

### Dynamic Variables (Arguments)

Variables that come from user input when invoking the command:

- `$1` - First argument
- `$2` - Second argument
- `$3` - Third argument (and so on...)
- `$ARGUMENTS` - All arguments as a single string

### Static Variables (Constants)

Fixed values used within the command:

- Configuration values (e.g., `MAX_RESULTS: 50`)
- Default paths (e.g., `OUTPUT_DIR: "specs"`)
- Time intervals (e.g., `SLEEP_INTERVAL: 10 seconds`)
- Format specifications (e.g., `DATE_FORMAT: "YYYY-MM-DD"`)

## Best Practices

✅ **Do:**
- Use UPPER_CASE_SNAKE_CASE for variable names
- Provide descriptive names (not `VAR1`, `VAR2`)
- Include type hints in comments if helpful
- Group related variables together
- Put dynamic variables first, static variables second

❌ **Don't:**
- Use unclear abbreviations
- Mix naming conventions
- Forget to define variables you use in Workflow
- Define variables you never use

## Examples

### Single Dynamic Variable

```markdown
## Variables

FILE_PATH: $1
```

### Multiple Dynamic Variables

```markdown
## Variables

USER_PROMPT: $1
DOCUMENTATION_URLS: $2
OUTPUT_FORMAT: $3
```

### With Static Variables

```markdown
## Variables

PROBLEM_DESCRIPTION: $1
SLEEP_INTERVAL: 10 seconds
MAX_RETRIES: 3
OUTPUT_DIR: "specs"
```

### Complex Example

```markdown
## Variables

# Dynamic variables (from user input)
REPOSITORY_URL: $1
BRANCH_NAME: $2
COMMIT_MESSAGE: $3

# Static configuration
MAX_FILE_SIZE: 1000000  # 1MB in bytes
ALLOWED_EXTENSIONS: [".py", ".js", ".ts", ".go"]
DEFAULT_BRANCH: "main"
TIMEOUT_SECONDS: 300
```

### No Arguments Example

```markdown
## Variables

None (uses current working directory)

# Static configuration
OUTPUT_FILE: "codebase-analysis.md"
MAX_DEPTH: 3
```

---

# Section 3: Codebase Structure

## What It Is

The Codebase Structure section describes **relevant project organization** that helps Claude understand where to find or place files. This section is **OPTIONAL** - only include it when the command needs to work with specific directory structures.

## When to Include This Section

✅ **Include when:**
- Command creates new files in specific directories
- Command expects certain project structure
- Command navigates between multiple directories
- Understanding project layout is critical for the task

❌ **Skip when:**
- Command works on single files
- Structure doesn't matter for the task
- Command is project-agnostic
- Current working directory is sufficient

## Best Practices

✅ **Do:**
- Show only relevant parts of the structure
- Use ASCII tree format for clarity
- Explain the purpose of each directory
- Keep it concise (under 20 lines usually)

❌ **Don't:**
- Show the entire project structure
- Include irrelevant directories
- Duplicate information from documentation
- Make it too detailed

## Examples

### Simple Structure

```markdown
## Codebase Structure

```
project/
├── specs/          # Implementation plans and specifications
├── src/            # Source code
└── tests/          # Test files
```
```

### Detailed Structure with Annotations

```markdown
## Codebase Structure

```
apps/orchestrator_3_stream/
├── backend/
│   ├── main.py                   # FastAPI server entry point
│   ├── modules/
│   │   ├── database.py           # Database operations
│   │   ├── agent_manager.py      # Agent lifecycle management
│   │   └── websocket_manager.py  # Real-time event broadcasting
│   └── prompts/                  # Agent system prompts
└── frontend/
    └── src/
        ├── components/           # Vue components
        └── stores/               # Pinia state management
```
```

### Multi-App Structure

```markdown
## Codebase Structure

```
apps/
├── orchestrator_db/      # Central database schema
│   ├── models.py         # Pydantic models (source of truth)
│   └── migrations/       # SQL migration files
├── orchestrator_1_term/  # CLI orchestrator
└── orchestrator_3_stream/# Web UI orchestrator
```
```

### When to Skip

```markdown
## Codebase Structure

(This section intentionally omitted - command works on any file structure)
```

Or simply don't include the section at all.

---

# Section 4: Instructions

## What It Is

The Instructions section provides **detailed rules, constraints, and guidelines** that Claude must follow when executing the command. This is where you define the "guardrails" for the task.

## What to Include

### 1. Success Criteria
How to know when the task is complete

### 2. Constraints
What NOT to do, limitations, boundaries

### 3. Quality Standards
Code quality, formatting, best practices

### 4. Edge Cases
Special scenarios to handle

### 5. Tool Usage
Which tools to use and how

### 6. Error Handling
How to handle failures

## Best Practices

✅ **Do:**
- Use bullet points for clarity
- Be specific and actionable
- Include examples when helpful
- Define both positive (do this) and negative (don't do this) instructions
- Order from most to least important

❌ **Don't:**
- Write vague guidelines
- Repeat information from other sections
- Include workflow steps (those go in Workflow section)
- Make it too long (keep under 15 bullets typically)

## Examples

### Simple Instructions

```markdown
## Instructions

- Focus on security-critical issues only
- Identify specific line numbers for each issue
- Categorize by severity: Critical, High, Medium, Low
- Provide remediation suggestions with code examples
- Do NOT modify code, only analyze and report
```

### Complex Instructions

```markdown
## Instructions

- You can know a task is completed when you see an `agent_logs` from `check_agent_status` that has a `response` event_category followed by a `hook` with a `Stop` event_type
- Run this workflow for BOTH agents in sequence - complete the scout phase entirely before starting the build phase
- The scout agent provides READ-ONLY analysis - the build agent performs actual implementation
- Do NOT delete agents after completion - leave them for inspection and debugging
- Pass the scout's findings to the build agent as context for implementation
- If interrupted with an additional task, return to your sleep + check loop after completing the interruption
```

### Tool-Specific Instructions

```markdown
## Instructions

- Use git commands ONLY - no file modifications
- All bash commands must use the Bash tool with git prefix
- Show maximum 20 commits to avoid overwhelming output
- Include commit hash, author, date, and message in output
- Do NOT run git commands that modify history (rebase, reset, etc.)
- Handle missing files gracefully - report if file not found in git
```

### Quality-Focused Instructions

```markdown
## Instructions

- Generate production-quality code with proper error handling
- Include comprehensive type annotations/hints
- Add detailed documentation (comments, docstrings)
- Follow existing code style and conventions in the project
- Ensure all imports and dependencies are correctly declared
- Do NOT use placeholder code or TODOs
- Verify implementation with type checks and linters
```

---

# Section 5: Workflow

## What It Is

The Workflow section provides **step-by-step numbered actions** that Claude must execute to accomplish the command's goal. This is the "recipe" for task completion.

## Structure

Each workflow should:
1. Be numbered sequentially (1, 2, 3...)
2. Have clear, actionable steps
3. Include tool usage where needed
4. Flow logically from start to finish
5. End with reference to Report section

## Best Practices

✅ **Do:**
- Number every step
- Use action verbs (Read, Analyze, Create, Run, etc.)
- Include code blocks for commands
- Specify which tools to use
- Break complex steps into sub-bullets
- Reference variables by name (e.g., `FILE_PATH`, `USER_PROMPT`)
- End with: "Now follow the `Report` section to report the completed work"

❌ **Don't:**
- Use vague language ("do stuff", "check things")
- Skip important steps
- Assume Claude knows what to do
- Forget to specify tools
- Make steps too long or complex

## Examples

### Simple Linear Workflow

```markdown
## Workflow

1. Read the file at FILE_PATH using the Read tool
2. Analyze for security vulnerabilities:
   - SQL injection risks
   - Cross-site scripting (XSS)
   - Insecure authentication
   - Hardcoded secrets
   - Dependency vulnerabilities
3. Categorize findings by severity
4. Generate remediation suggestions
5. Now follow the `Report` section to report the completed work
```

### Multi-Phase Workflow

```markdown
## Workflow

### Phase 1: Scout (Analysis)

1. **(Create Scout)** Run `create_agent` to create a scout agent using the `scout-report-suggest-fast` subagent_template based on PROBLEM_DESCRIPTION
   - Name the agent something descriptive like "scout-{problem-keyword}"
2. **(Command Scout)** Run `command_agent` to command the scout agent to investigate PROBLEM_DESCRIPTION
   - Instruct the agent to provide a detailed scout report with findings
3. **(Check Scout)** The scout agent will work in the background:
   - Use `Bash(sleep ${SLEEP_INTERVAL})`
   - Every SLEEP_INTERVAL seconds run `check_agent_status`
   - Continue until you see a `response` event_category followed by a `hook` with a `Stop` event_type
4. **(Report Scout)** Retrieve and analyze the scout's findings
   - Extract key information: affected files, root causes, suggested resolutions

### Phase 2: Build (Implementation)

5. **(Create Build Agent)** Run `create_agent` to create a build agent using the `build-agent` subagent_template
6. **(Command Build Agent)** Run `command_agent` with the scout's findings
7. **(Check Build Agent)** Monitor the build agent with sleep + check loop
8. **(Report Build)** Report the implementation results
9. Now follow the `Report` section to report the completed work
```

### Conditional Workflow

```markdown
## Workflow

1. Use Glob to find all Python files in the current directory: `**/*.py`
2. For each file found:
   - Read the file using the Read tool
   - Check for `TODO` or `FIXME` comments
   - If found, record the file path and line number
3. If no TODOs found in any files:
   - Report "No TODOs found in codebase"
   - Skip to Report section
4. If TODOs found:
   - Categorize by type (TODO, FIXME, HACK, etc.)
   - Group by file
   - Count total occurrences
5. Now follow the `Report` section to report the completed work
```

### Workflow with External Data

```markdown
## Workflow

1. Parse the USER_PROMPT to understand requirements
2. For each URL in DOCUMENTATION_URLS:
   - Use WebFetch to retrieve documentation
   - Extract relevant sections for implementation
   - Note any code examples or patterns
3. Use Glob to find similar implementations in codebase: `**/*{keyword}*`
4. Read 2-3 example files to understand existing patterns
5. Create implementation plan with these sections:
   - **Overview**: Brief summary of what needs to be built
   - **Requirements**: Parsed user requirements
   - **Technical Approach**: Architecture decisions
   - **Implementation Steps**: Numbered actions
   - **Files to Modify**: List of files and changes
   - **Testing Strategy**: Verification approach
6. Generate descriptive filename from USER_PROMPT
7. Save plan to `specs/[filename].md` using Write tool
8. Now follow the `Report` section to report the completed work
```

---

# Section 6: Report

## What It Is

The Report section defines **the exact output format** that Claude should present to the user after completing the workflow. This ensures consistent, well-structured results.

## Purpose

The Report section:
- Provides a template for final output
- Ensures consistency across multiple runs
- Makes results easy to scan and understand
- Specifies what information to include
- Defines the markdown structure

## Best Practices

✅ **Do:**
- Use markdown formatting examples
- Show exact structure with placeholders (e.g., `[filename]`, `[count]`)
- Include section headers
- Specify lists, tables, code blocks
- Show what data goes where
- Use clear placeholder names

❌ **Don't:**
- Leave format ambiguous
- Use generic "report the results"
- Forget to specify formatting
- Make it too rigid (allow some flexibility)

## Examples

### Simple Summary Report

```markdown
## Report

Present findings in this format:

## Security Review: [filename]

**Total issues found**: [count]
**Severity breakdown**: Critical: [count], High: [count], Medium: [count], Low: [count]

**Files analyzed**: [count]
**Scan duration**: [time]
```

### Detailed Report with Sections

```markdown
## Report

Present findings in this format:

## Security Review: [filename]

### Summary
- Total issues found: [count]
- Critical: [count]
- High: [count]
- Medium: [count]
- Low: [count]

### Findings

#### [Severity] - [Issue Type]
**Location**: Line [number]
**Code**:
\`\`\`[language]
[vulnerable code]
\`\`\`

**Issue**: [Description of the vulnerability]

**Remediation**:
\`\`\`[language]
[fixed code]
\`\`\`

**Explanation**: [Why this fix works]

[Repeat for each finding]
```

### Table-Based Report

```markdown
## Report

Present the history in this format:

## Git History: [filename]

| Commit | Author | Date   | Message   |
| ------ | ------ | ------ | --------- |
| [hash] | [name] | [date] | [message] |
| [hash] | [name] | [date] | [message] |

**Total commits shown**: [count] (limited to last 20)
**File path**: `[FILE_PATH]`
```

### Multi-Section Report

```markdown
## Report

Present the analysis in this format:

## Codebase Structure Analysis

### Project Overview
**Name**: [project name from config]
**Type**: [web app, CLI tool, library, etc.]
**Primary Language**: [language]
**Framework**: [framework if identified]

### Directory Structure
\`\`\`
[root]/
├── [dir1]/ - [purpose]
├── [dir2]/ - [purpose]
├── [dir3]/ - [purpose]
└── [dir4]/ - [purpose]
\`\`\`

### Key Files
- `[file1]` - [purpose]
- `[file2]` - [purpose]
- `[file3]` - [purpose]

### Technologies Detected
- [technology 1]
- [technology 2]
- [technology 3]

### Entry Points
- [main entry point file and location]

### Notable Patterns
- [observation 1]
- [observation 2]
```

### Progress Report (Multi-Phase Workflow)

```markdown
## Report

Communicate to the user where you are at each step of the workflow:

1. **Scout Phase Starting**: "Creating scout agent to analyze {PROBLEM_DESCRIPTION}..."
2. **Scout Working**: "Scout agent is analyzing the codebase... (checking every {SLEEP_INTERVAL} seconds)"
3. **Scout Complete**: "Scout analysis complete. Key findings: [summary of scout's report]"
4. **Build Phase Starting**: "Creating build agent to implement the solution..."
5. **Build Working**: "Build agent is implementing changes... (checking every {SLEEP_INTERVAL} seconds)"
6. **Build Complete**: "Implementation complete. Changes made: [summary of build agent's work]"
7. **Final Summary**: "Scout-and-build workflow complete. Scout agent '{SCOUT_AGENT_NAME}' and build agent '{BUILD_AGENT_NAME}' are both available for inspection."
```

---

# Creating a Slash Command: Step-by-Step

## 1. Read the Template

```markdown
Read PROMPT_TEMPLATE.md (in this skill directory) to understand the latest structure
```

## 2. Gather Requirements

Ask the user:
- What should the command do?
- What arguments does it need?
- Should it modify files or just report?
- What tools should it use?
- What format should the output be?

## 3. Design the Structure

Create frontmatter with:
- `model: claude-sonnet-4-5-20250929` (always)
- `description:` (concise /help menu text)
- `argument-hint:` (if takes arguments)
- `allowed-tools:` (if restricting tools)

## 4. Write Each Section

Follow the detailed guidelines above for:
1. Purpose (1-3 sentences)
2. Variables (dynamic + static)
3. Codebase Structure (if needed)
4. Instructions (rules and constraints)
5. Workflow (numbered steps)
6. Report (output format)

## 5. Save the File

```markdown
Save to .claude/commands/[command-name].md
Use lowercase with hyphens for multi-word names
```

## 6. Test the Command

```markdown
Invoke with: /[command-name] [arguments]
Verify it behaves as expected
Iterate based on results
```

---

# Quick Reference

## Frontmatter Template

```yaml
---
model: claude-sonnet-4-5-20250929
description: [Brief description for /help menu]
argument-hint: [arg1] [arg2] (optional)
allowed-tools: [Only if restricting] (optional)
---
```

## Section Order

1. **Frontmatter** (YAML)
2. **Purpose** (what it does)
3. **Variables** (inputs and constants)
4. **Codebase Structure** (optional)
5. **Instructions** (rules and constraints)
6. **Workflow** (numbered steps)
7. **Report** (output format)

## Key Principles

✅ **Always:**
- Include `model: claude-sonnet-4-5-20250929`
- Write clear, actionable workflow steps
- Define exact report format
- Use descriptive variable names
- Number workflow steps

❌ **Never:**
- Use `disable-model-invocation` (allow agents to trigger commands)
- Make assumptions about what's "obvious"
- Skip the Report section
- Forget to test the command

---

# Summary

This meta-prompt skill helps you create production-quality custom slash commands for Claude Code by:

1. **Following established patterns** from `app_docs/PROMPT_TEMPLATE.md`
2. **Structuring prompts** with 6 core sections
3. **Providing clear guidance** through detailed Instructions
4. **Creating actionable workflows** with numbered steps
5. **Defining exact output** via Report templates
6. **Focusing exclusively** on slash commands (not system/user prompts)

Remember: Slash commands are stored in `.claude/commands/*.md` and invoked with `/command-name`. They support arguments, file references, bash execution, and can be project-wide or personal.

---

## Reference Materials

This skill includes local reference materials:

- **PROMPT_TEMPLATE.md** - Complete template structure for slash commands (read this first!)
- **examples/** - Real-world slash command examples from this project:
  - `orch_one_shot_agent.md` - Simple agent lifecycle workflow
  - `orch_scout_and_build.md` - Multi-phase workflow with sequential agents
  - `plan.md` - Complex document generation with detailed formatting
  - `question.md` - Read-only analysis with tool restrictions
  - `README.md` - Guide to understanding and using the examples

Always reference these local files when creating new slash commands to ensure consistency with project patterns.
