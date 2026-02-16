---
model: claude-sonnet-4-5-20250929
description: Build the codebase in parallel by delegating file creation to build-agents
argument-hint: [path-to-plan]
---

# Build in Parallel

Follow the `Workflow` to implement the `PATH_TO_PLAN` by delegating individual file creation to specialized build-agents in parallel, then `Report` the completed work.

## Variables

PATH_TO_PLAN: $ARGUMENTS

## Codebase Structure

The build-agent sub-agent is located at `.claude/agents/build-agent.md` and is specialized for writing individual files based on detailed specifications.

## Instructions

- **Never guess or assume context**: Each build-agent needs comprehensive instructions as if they are new engineers
- **Provide verbose specifications**: Include all relevant files, patterns, conventions, and examples
- **Launch agents in parallel**: Use a single message with multiple Task tool calls to maximize efficiency
- **One file per agent**: Each build-agent should focus on implementing ONE specific file
- **Include full context**: Specifications must include:
  - Exact file path
  - Complete functional requirements
  - Related files and their relationships
  - Code style and patterns to follow
  - Dependencies and imports needed
  - Example code or similar files to reference

## Workflow

### Step 1: Read and Analyze the Plan

- If no `PATH_TO_PLAN` is provided, STOP immediately and ask the user to provide it
- Read the plan at `PATH_TO_PLAN`
- Analyze the plan thoroughly to understand:
  - All files that need to be created or modified
  - Dependencies between files
  - The overall architecture and flow
  - Code style and conventions mentioned

### Step 2: Gather Context for Specifications

- Read relevant existing files in the codebase to understand:
  - Coding patterns and conventions
  - Import styles and module organization
  - Error handling approaches
  - Documentation standards
  - Similar implementations that can serve as examples
- Use Grep/Glob to find related files that provide context
- Identify which files can be built in parallel vs which have dependencies

### Step 3: Create Detailed File Specifications

For each file that needs to be created/modified, create a comprehensive specification that includes:

```markdown
# File: [absolute/path/to/file.ext]

## Purpose
[What this file does and why it exists]

## Requirements
- [Detailed requirement 1]
- [Detailed requirement 2]
- [etc.]

## Related Files
- **[file-path]**: [how it relates and what to reference]
- [etc.]

## Code Style & Patterns
- [Pattern 1 to follow]
- [Pattern 2 to follow]
- [etc.]

## Dependencies
- [Import/dependency 1]
- [Import/dependency 2]
- [etc.]

## Example Code
[Provide similar code from the codebase or pseudocode example]

## Integration Points
[How this file connects with other parts of the system]

## Verification
[How to verify this file works: tests to run, type checks, etc.]
```

### Step 4: Identify Parallel vs Sequential Work

- Group files into batches based on dependencies:
  - **Batch 1**: Files with no dependencies (can be built in parallel)
  - **Batch 2**: Files that depend on Batch 1
  - **Batch 3**: Files that depend on Batch 2
  - [etc.]

### Step 5: Launch Build Agents in Parallel

For each batch (starting with Batch 1):

- Launch multiple build-agent instances in parallel using a **single message** with multiple Task tool calls
- Each Task tool call should:
  - Use `subagent_type: "build-agent"`
  - Provide the complete specification created in Step 3
  - Include all necessary context for that specific file
- Wait for all agents in the current batch to complete before moving to the next batch

Example of launching agents in parallel:
```
In a single message, make multiple Task tool calls:
- Task(subagent_type="build-agent", prompt="[Full spec for file1]")
- Task(subagent_type="build-agent", prompt="[Full spec for file2]")
- Task(subagent_type="build-agent", prompt="[Full spec for file3]")
```

### Step 6: Monitor and Collect Results

- Review the reports from each build-agent
- Identify any issues or concerns raised
- Note any deviations from specifications
- Check verification results (tests, type checks, etc.)

### Step 7: Handle Issues

- If any agents report problems:
  - Review the issue
  - Make necessary adjustments
  - Re-launch the specific agent with updated specifications if needed

### Step 8: Final Verification

- Run any project-wide checks (e.g., full test suite, build process)
- Verify all files integrate correctly
- Check that all requirements from the plan are met

## Report

Your final report should include:

### Summary
- Brief overview of what was implemented
- Number of files created/modified
- Any significant architectural decisions made

### File-by-File Breakdown
For each file:
- **Path**: [file path]
- **Status**: ✅ Created | ⚠️ Created with issues | ❌ Failed
- **Summary**: [Brief summary from build-agent report]
- **Issues**: [Any issues or concerns]

### Verification Results
```bash
git diff --stat
```

### Overall Status
- **Total Files**: [number]
- **Successful**: [number]
- **Issues**: [number]
- **Failed**: [number]

### Recommendations
- [Any follow-up work needed]
- [Suggestions for testing]
- [Other recommendations]
