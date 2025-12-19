---
covers: Validate manifest, documentation structure, frontmatter schema, and check for semantic drift.
concepts: [audit, validation, frontmatter, drift-detection, manifest]
---

# Docs Audit Workflow

Validate manifest, documentation structure, frontmatter schema compliance, and semantic drift. Quick mode validates manifest and structure; deep mode adds semantic checks and dependency graph analysis.

---

**Modes:**
- `quick` (default) - Manifest + structure + frontmatter validation (fast, script-driven)
- `deep` - Quick + semantic drift check (thorough, requires AI analysis)

## Quick Audit

Run the validation script to check all deterministic rules:

```bash
uv run .claude/skills/docs-framework/scripts/audit.py <docs_path>
```

Where `<docs_path>` is the path to the documentation root containing `.rwyn.yaml`:
- Repository scope: `docs/` (at repository root)
- Component scope: `<component>/docs/` (e.g., `src/auth/docs/`)

The script validates:
- **Manifest**: existence, required fields, enums, conditionals, nesting, staleness
- **Structure**: three zones, foundation files, 00-overview.md in all directories
- **Numbering**: two-digit prefixes, lowercase-hyphen format
- **Frontmatter**: covers required, concepts length, type field placement
- **Links**: broken links, generic anchor text, orphan files
- **Dependencies**: circular dependency detection in depends-on graph

**Exit codes:** 0 = pass, 1 = warnings only, 2 = critical issues

Parse the JSON output and format as the report template below.

## Deep Audit

Run quick audit first, then perform these semantic checks.

### Reference Documentation

For semantic checks, consult these standards:
- `.claude/skills/docs-framework/20-standards/50-code-linking.md` - Code reference format
- `.claude/skills/docs-framework/40-templates/10-codebase-templates/` - Required sections

### Semantic Drift Detection
Sample 2-3 L3 nodes and compare documentation claims to code reality:

1. Pick a random L3 documentation node
2. Read the code files it references
3. Compare:
   - Does the documented architecture match the code?
   - Are the stated responsibilities accurate?
   - Do code references point to the right files?
   - Have any referenced files been renamed/deleted?
   - Does documented behavior match implementation?

Example findings:
- "Doc says 'uses Redis for caching' but code uses Memcached"
- "Doc references `UserSession` class which was renamed to `AuthSession`"
- "Doc states 'all inputs validated' but validation is commented out"

### Coverage Analysis

- What percentage of source directories have corresponding docs in `10-codebase/`?
- Are there undocumented areas that should have docs?
- Is the Foundation zone complete (purpose, principles, boundaries)?

### Content Quality

- [ ] No placeholder text remains ("[To be filled]", "TBD", etc.)
- [ ] Code references use `file:line` or `file` format

### Component Isolation Check (Component Scope Only)

For `scope: component` documentation:
- [ ] No references to paths outside the component's `root` directory
- [ ] No links to parent repository docs (all links are internal)
- [ ] Foundation docs describe integration boundaries with host system
- [ ] Code references use relative paths from `root`
- [ ] Documentation is fully self-contained (portable)

## Anti-Pattern Detection

The script detects these issues automatically (marked with †). Deep mode adds semantic checks (marked with *):

| Anti-Pattern | Severity | Description |
|--------------|----------|-------------|
| Missing manifest † | Critical | No `.rwyn.yaml` file in docs folder |
| Invalid manifest † | Critical | Manifest missing required fields or has invalid values |
| Nested manifest † | Critical | Parent directory contains another `.rwyn.yaml` |
| Missing zones † | Critical | One or more of 00-foundation, 10-codebase, 99-appendix missing |
| Missing frontmatter † | Critical | File lacks YAML frontmatter |
| Empty covers † | Critical | `covers` field is empty or missing |
| Circular dependency † | Critical | Cycle detected in `depends-on` graph |
| Missing overview † | Critical | Directory without 00-overview.md |
| Broken link † | Critical | Link to non-existent file |
| Component leak * | Warning | Component docs reference paths outside `root` |
| Stale manifest † | Warning | `updated` date older than 30 days |
| Numbering format † | Warning | Files/dirs not using XX-lowercase-name pattern |
| Legacy Covers † | Warning | `## Covers` section still exists (should be in frontmatter) |
| Generic anchor † | Warning | "click here" instead of descriptive text |
| Orphan file † | Warning | File not linked from parent overview |
| Placeholder text * | Warning | Unfilled template sections |
| Stale reference * | Warning | Code file referenced doesn't exist |

## Output Format

### Script JSON Output

The script outputs JSON with this structure:

```json
{
  "timestamp": "2025-12-18T...",
  "docs_root": "docs/",
  "manifest": {"valid": true, "fields": {...}, "issues": [...]},
  "structure": {"zones_present": [...], "missing_overviews": [...], "issues": [...]},
  "frontmatter": {"files_checked": 25, "issues": [...]},
  "links": {"total": 45, "broken": [...], "generic_anchors": [...], "orphan_files": [...], "circular_deps": [...]},
  "summary": {"files_checked": 25, "critical": 2, "warnings": 5, "health_score": 85}
}
```

### Formatted Report

Format the JSON into this markdown report:

```markdown
# Docs Audit Report

**Date**: [timestamp]
**Mode**: [quick/deep]
**Path**: docs/

## Manifest

| Field | Value |
|-------|-------|
| RWYN Version | 1.0 |
| Scope | repository/component |
| Coverage | complete/partial |
| Status | stable/draft |
| Updated | YYYY-MM-DD |
| Root | [component only] |

## Summary

| Metric | Value |
|--------|-------|
| Files checked | X |
| Directories checked | Y |
| Issues found | Z |
| Critical | A |
| Warnings | B |
| Suggestions | C |

## Health Score: [X/100]

[Visual indicator: ████████░░ 80%]

---

## Critical Issues
*Must fix - blocks AI navigation*

### [Issue 1]
- **Location**: `docs/10-auth/00-overview.md`
- **Problem**: Missing "Child Nodes" section
- **Impact**: AI cannot discover L3 documentation
- **Fix**: Add Child Nodes section linking to L3 files

### [Issue 2]
...

---

## Warnings
*Should fix - degrades experience*

### [Issue 1]
- **Location**: `docs/20-api/10-endpoints.md`
- **Problem**: Code reference `src/api/routes.py` not found
- **Impact**: Broken link when navigating to code
- **Fix**: Update reference to `src/api/router.py`

---

## Suggestions
*Nice to have - improvements*

### [Suggestion 1]
- **Location**: `docs/00-overview.md`
- **Suggestion**: Add architecture diagram
- **Benefit**: Faster mental model building

---

## Semantic Drift Report (Deep Mode Only)

### Sampled: `docs/10-auth/20-sessions.md`
- ✅ Session lifecycle matches documented flow
- ✅ Redis storage confirmed in code
- ⚠️ Doc says "tokens expire after 1 hour" but code shows 24 hours

### Sampled: `docs/20-api/10-endpoints.md`
- ✅ Endpoint list matches router
- ❌ Doc references deprecated `v1/` prefix, code uses `v2/`

---

## Recommended Actions

Priority order:
1. Fix [Critical Issue 1] - [one-line description]
2. Fix [Critical Issue 2] - [one-line description]
3. Update [Warning 1] - [one-line description]
4. Run `/docs:interview-codebase src/auth/` to update stale session docs
5. Run `/docs:sync` to check full coverage alignment
```

## Output

- Structured audit report
- Issues categorized by severity
- Specific file locations and fixes
- Recommended next actions
