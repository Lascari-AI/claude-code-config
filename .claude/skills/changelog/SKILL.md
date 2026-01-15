---
name: changelog
description: Generate user-facing changelogs from git history. Transforms technical commits into clear, customer-friendly release notes. Use after PRs merge, before releases, or when documenting updates.
---

# Changelog Generation

Transform technical git commits into polished, user-friendly changelog entries.

## Purpose

A changelog communicates **value to users**, not implementation details to developers.
The goal is clarity: what's new, what's fixed, what users need to know.

## When to Use

- After PRs merge (update CHANGELOG.md incrementally)
- Preparing a release version
- Creating weekly/monthly update summaries
- Documenting changes for users/customers
- Generating release notes for distribution

## Change Categories

Organize changes into user-meaningful categories:

| Category | Icon | Use When |
|----------|------|----------|
| **Features** | `## Features` | New capabilities users can now do |
| **Improvements** | `## Improvements` | Enhancements to existing functionality |
| **Fixes** | `## Fixes` | Bugs that have been resolved |
| **Breaking Changes** | `## Breaking Changes` | Changes requiring user action |
| **Security** | `## Security` | Security-related updates |
| **Deprecations** | `## Deprecations` | Features being phased out |

## Commit-to-Changelog Translation

### Filter: What to Include

**Include** - User-facing impact:
- `feat:` commits → Features or Improvements
- `fix:` commits → Fixes
- `perf:` commits → Improvements (if user-noticeable)
- Security patches → Security
- Breaking changes → Breaking Changes

**Exclude** - Internal/development:
- `refactor:` (no user impact)
- `test:` (internal quality)
- `chore:` (maintenance)
- `style:` (formatting)
- `docs:` (unless user-facing docs)
- `ci:` (pipeline changes)

### Transform: Technical to User-Friendly

| Technical Commit | User-Friendly Entry |
|------------------|---------------------|
| `feat: add JWT auth middleware` | **Authentication**: Added secure login with session tokens |
| `fix: resolve race condition in checkout` | Fixed an issue where orders could fail during high traffic |
| `perf: optimize database queries` | Improved page load speed across the application |
| `feat: implement dark mode toggle` | **Dark Mode**: Switch between light and dark themes in Settings |

### Principles

1. **Lead with benefit** - "Faster exports" not "Optimized export algorithm"
2. **Use user language** - "Download" not "HTTP GET request"
3. **Be specific when helpful** - "Fixed login on Safari" not "Fixed browser bug"
4. **Group related changes** - Multiple commits for one feature = one entry
5. **Omit obvious context** - "in the app" is implied

## Changelog Format

```markdown
# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Features

- **Feature Name**: Description of what users can now do

### Improvements

- Enhancement description (brief, benefit-focused)

### Fixes

- Fixed issue where [user-facing symptom]

---

## [1.2.0] - 2025-01-15

### Features

- **Team Workspaces**: Create separate workspaces for different projects
- **Keyboard Shortcuts**: Press ? to see all available shortcuts

### Improvements

- Files now sync 2x faster across devices
- Search includes file contents, not just titles

### Fixes

- Fixed large image upload failures
- Resolved timezone issues in scheduled posts
```

## Version Sections

| Section | Use When |
|---------|----------|
| `[Unreleased]` | Changes since last release (accumulating) |
| `[X.Y.Z] - YYYY-MM-DD` | Released version with date |

**Semantic Versioning Hint**:
- `MAJOR.x.x` - Breaking changes
- `x.MINOR.x` - New features (backward compatible)
- `x.x.PATCH` - Bug fixes

## Integration Points

### With Agent Session

At session end (after build), optionally update changelog:
- Analyze commits from the session
- Determine if changes are user-facing
- Update `[Unreleased]` section if applicable

### With Release Workflow

Before release:
1. Move `[Unreleased]` entries to new version section
2. Add release date
3. Create fresh `[Unreleased]` section

## Commands

| Command | Description |
|---------|-------------|
| `/changelog:update [range]` | Update CHANGELOG.md from commits |

Range options:
- Empty: Since last changelog entry or tag
- PR number: Changes from a specific PR
- `v1.2.0..HEAD`: Since a specific tag
- `7d` or `2w`: Time-based (days/weeks)

## References

- [Keep a Changelog](https://keepachangelog.com/) - Format inspiration
- Git skill conventions for commit parsing
