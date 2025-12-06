---
allowed-tools: Read, Bash(git:*), Bash(gh:*)
description: Analyze changes and create smart git commit(s)
arguments: "Additional instructions for the commit"
model: "claude-haiku-4-5"
---

additional instructions = $ARGUMENTS

type = "feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"

# Smart Git Commit

## Guardrails

- Never force push
- Never hard reset
- Never skip pre-commit hooks - if they fail, stop and report the error
- Warn when committing on `main` or `master` branch
- If no changes exist, report "no local changes" and stop

## Workflow

### 1. Context Gathering

Before analyzing changes, gather repository context:

```bash
git rev-parse --show-toplevel  # Confirm we're in a git repo
git branch --show-current      # Current branch name
git rev-parse --abbrev-ref @{upstream} 2>/dev/null  # Upstream tracking
git status -sb                 # Ahead/behind status
```

### 2. Analyze Changes

Check current git status and analyze what changed:

```bash
git status
git diff --staged
git diff
```

### 3. Present Options

Based on the changes, present options in this exact format:

```
## Summary
[Brief description of all changes detected]

## Options
1. Quick commit - Stage all and commit with a single message
2. Atomic commits - Split into [N] focused commits by logical grouping
3. Manual staging - Let me choose what to stage

## Recommendation
[Option N] because [brief reason]
```

If the changes are simple and cohesive, recommend option 1.
If the changes touch multiple unrelated areas, recommend option 2.

### 4. Generate Message(s)

For each commit:

- Use the appropriate commit type (feat/fix/docs/style/refactor/perf/test/chore)
- Follow conventional commits format: `type: description`
- For complex changes, include a body explaining what and why

**Important:** Do NOT include any AI attribution:
- No "Generated with Claude Code"
- No "Co-Authored-By: Claude"

### 5. Execute

Before committing, show the suggested message and ask for approval:
- Use it as-is
- Modify it
- Add more details to the body
- Stage different files

Once approved, create the commit.

**Pre-commit hooks:**
- If pre-commit hooks fail, STOP and report the error
- Do NOT offer to skip hooks with `-n` or `--no-verify`
- The user must fix the issues before committing

### 6. Post-commit

After successful commit(s), run:

```bash
git log -1 --oneline   # Show the commit
git status             # Confirm working tree state
```

Then present next steps in this exact format:

```
## Next Steps
1. Push to remote
2. Create a PR (using `gh pr create`)
3. Do nothing
```

If on `main`/`master` branch, warn before pushing and confirm.

## Success Criteria

- Commit(s) created with conventional format (`type: description`)
- No AI attribution in commit messages
- All pre-commit hooks passed
- Working tree in expected state (clean, or only intentionally unstaged files remain)
- Push completed if requested
