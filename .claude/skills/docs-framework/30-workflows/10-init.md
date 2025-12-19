---
covers: One-time initialization of docs/ with manifest and three-zone structure.
concepts: [init, initialization, setup, three-zones, manifest, scope]
---

# Docs Init Workflow

One-time initialization of `docs/` in your project. Creates the manifest (`.rwyn.yaml`), determines scope (repository or component), and sets up the three-zone structure (Foundation/Codebase/Appendix) with template files.

---

## Prerequisites Check

First, verify the Documentation framework is installed:

1. **Check `.claude/skills/docs-framework/` exists** (framework documentation)
   - If missing: "Copy `.claude/skills/docs-framework/` from the Documentation repository first"

2. **Check `.claude/commands/docs/` exists** (commands)
   - If missing: "Copy `.claude/commands/docs/` from the Documentation repository"

If any prerequisites are missing, stop and instruct the user to copy the missing components.

## Initialization Steps

If all prerequisites pass:

### 1. Show Project Structure
Run: `eza --tree --level=2` (or `tree -L 2` if eza unavailable)
- Exclude: node_modules, .git, build artifacts, __pycache__, etc.

### 2. Check for Existing Documentation

**Check for nested documentation (blocked):**
- Search parent directories for `.rwyn.yaml`: `find .. -name ".rwyn.yaml" -type f 2>/dev/null | head -1`
- If found: "Documentation already exists at [path]. Nested documentation is not supported. Either use the existing documentation or extract this component to its own repository."
- Stop if parent manifest found.

**Check for existing docs in current location:**
- Does `docs/` already exist?
  - If yes with `.rwyn.yaml`: Report what exists, suggest `/docs:audit` to validate
  - If yes without manifest: "Found docs/ without manifest. Run this init to add manifest, or manually create .rwyn.yaml"
  - If no: Proceed with creation

### 3. Determine Scope

Ask the user to select the documentation scope:

```
Documentation Scope
═══════════════════

Choose the scope for this documentation:

[1] repository - Full codebase documentation
    Creates: docs/.rwyn.yaml + three-zone structure at current location
    Use for: Main project documentation, documenting entire codebase

[2] component - Self-contained module documentation
    Creates: docs/.rwyn.yaml + three-zone structure at current location
    Use for: Portable packages, libraries, modules within larger codebases
    Note: Documentation travels with the component when moved

Select [1/2]:
```

Store the selection for manifest creation.

### 4. Component-Specific Questions

If scope is `component`:

Ask: "What is the root directory of this component's code relative to the docs folder?"
- Common patterns: `src/`, `lib/`, `.` (if docs is alongside code), `../src/`
- This becomes the `root` field in the manifest

### 5. Create Manifest

Create `docs/.rwyn.yaml` with the appropriate content:

**For repository scope:**
```yaml
rwyn: 1.0
scope: repository
coverage: partial
status: draft
updated: [today's date YYYY-MM-DD]
```

**For component scope:**
```yaml
rwyn: 1.0
scope: component
coverage: partial
status: draft
updated: [today's date YYYY-MM-DD]
root: [user-provided root path]
```

### 6. Create Three-Zone Structure

Create these files using the templates:

**Foundation Zone:**
| File | Template Source |
|------|-----------------|
| `docs/00-foundation/00-overview.md` | `.claude/skills/docs-framework/40-templates/00-foundation-templates/10-foundation-overview-template.md` |
| `docs/00-foundation/10-purpose.md` | `.claude/skills/docs-framework/40-templates/00-foundation-templates/20-purpose-template.md` |
| `docs/00-foundation/20-principles.md` | `.claude/skills/docs-framework/40-templates/00-foundation-templates/30-principles-template.md` |
| `docs/00-foundation/30-boundaries.md` | `.claude/skills/docs-framework/40-templates/00-foundation-templates/40-boundaries-template.md` |

**Codebase Zone:**
| File | Template Source |
|------|-----------------|
| `docs/10-codebase/00-overview.md` | `.claude/skills/docs-framework/40-templates/10-codebase-templates/20-codebase-overview-template.md` |

**Appendix Zone:**
| File | Template Source |
|------|-----------------|
| `docs/99-appendix/00-overview.md` | `.claude/skills/docs-framework/40-templates/10-codebase-templates/30-section-overview-template.md` |

**Drafts Directory:**
| File | Purpose |
|------|---------|
| `docs/.drafts/.gitkeep` | Working directory for interviews |

### 7. Ask Source Directory

Ask the user: "What is your main source code directory?"
- For repository scope: Common patterns like `src/`, `app/`, `lib/`, or project root
- For component scope: Confirm the `root` path or refine it
- Store this answer for `/docs:scaffold`

### 8. Suggest Next Steps

**For repository scope:**
```
Documentation initialized successfully.

Created:
- docs/.rwyn.yaml (manifest: scope=repository, coverage=partial)
- docs/00-foundation/ (Intent zone - fill in purpose, principles, boundaries)
- docs/10-codebase/00-overview.md (L1 - describe your architecture)
- docs/99-appendix/00-overview.md (Operations zone)
- docs/.drafts/ (working directory for interviews)

Next steps:
1. Fill in docs/00-foundation/ - purpose, principles, boundaries
2. Edit docs/10-codebase/00-overview.md to describe your architecture
3. Run /docs:scaffold to map your source structure to documentation sections
4. Once documentation is complete, update manifest: coverage → complete, status → stable
```

**For component scope:**
```
Component documentation initialized successfully.

Created:
- docs/.rwyn.yaml (manifest: scope=component, root=[path])
- docs/00-foundation/ (Intent zone - why this component exists)
- docs/10-codebase/00-overview.md (L1 - component architecture)
- docs/99-appendix/00-overview.md (Operations zone)
- docs/.drafts/ (working directory for interviews)

This documentation is self-contained and will travel with the component.

Next steps:
1. Fill in docs/00-foundation/ - component purpose, principles, boundaries
2. Edit docs/10-codebase/00-overview.md to describe component architecture
3. Run /docs:scaffold [root] to map component structure to doc sections
4. Once documentation is complete, update manifest: coverage → complete, status → stable
```

## Output Summary

Provide:
- Manifest details (scope, coverage, status)
- List of created files by zone
- Project structure visualization
- Clear next steps (Foundation first, then Codebase)
