---
covers: Map source directory structure to docs/10-codebase/ sections.
concepts: [scaffold, mapping, structure, sections]
---

# Docs Scaffold Workflow

Map your source directory structure to documentation sections. Analyzes `src/` (or equivalent) and proposes a mirrored structure in `docs/10-codebase/` with L2 section overviews.

---

## Prerequisites

- `/docs:init` has been run (docs/ exists with three-zone structure)
- User has identified their source directory

## Process

### 1. Analyze Source Structure

Run tree on the source directory (2-3 levels deep):
```bash
eza --tree --level=3 [source_path]
# or: tree -L 3 [source_path]
```

Identify major subdirectories that represent architectural domains:
- Look for: auth, api, core, data, models, services, utils, etc.
- Skip: tests, __pycache__, node_modules, build artifacts

### 2. Propose Section Mapping

Present a mapping table to the user:

```
Source Directory        →    Documentation Section
──────────────────────────────────────────────────
src/auth/               →    docs/10-codebase/10-auth/
src/api/                →    docs/10-codebase/20-api/
src/core/               →    docs/10-codebase/30-core/
src/models/             →    docs/10-codebase/40-models/
src/utils/              →    (skip - utilities rarely need architecture docs)
```

**Numbering guidelines:**
- Use 10, 20, 30... (gaps allow insertions)
- Group related sections numerically
- All sections go in `10-codebase/`

Ask the user:
- "Does this mapping look right?"
- "Any directories to skip or add?"
- "Should any sections be renamed?"

### 3. Create Section Stubs

For each confirmed mapping:

1. Create the directory: `docs/10-codebase/XX-section/`

2. Create `00-overview.md` using template from:
   `.claude/skills/docs-framework/40-templates/10-codebase-templates/30-section-overview-template.md`

3. Fill in minimal content:
   ```markdown
   # [Section Name]: Overview (L2)

   ## Covers
   [To be filled after interview]

   ## File Tree
   ```
   [source_path]/
   ├── [actual files from source]
   ```

   ## Section Scope
   [To be filled after interview]

   ## Child Nodes
   [To be added after interview]
   ```

### 4. Update L1 Codebase Overview

Edit `docs/10-codebase/00-overview.md`:
- Add each new section to the Section Index
- Use placeholder descriptions until interviews complete

```markdown
## Section Index

### [10-auth/](10-auth/00-overview.md)
Authentication and authorization. [Details pending interview]

### [20-api/](20-api/00-overview.md)
API layer and endpoints. [Details pending interview]
```

### 5. Generate Coverage Report

Output a summary:

```
Documentation Scaffold Complete
══════════════════════

Created Sections (in docs/10-codebase/):
- 10-auth/00-overview.md
- 20-api/00-overview.md
- 30-core/00-overview.md

Coverage Map:
┌─────────────────┬──────────────────────────┬────────────┐
│ Source          │ Docs                     │ Status     │
├─────────────────┼──────────────────────────┼────────────┤
│ src/auth/       │ 10-codebase/10-auth/     │ ✅ Created │
│ src/api/        │ 10-codebase/20-api/      │ ✅ Created │
│ src/core/       │ 10-codebase/30-core/     │ ✅ Created │
│ src/utils/      │ (skipped)                │ ⏭️ Skip    │
└─────────────────┴──────────────────────────┴────────────┘

Next Steps:
1. Run /docs:interview-codebase src/auth/ to start knowledge extraction
2. Repeat for each section
3. Run /docs:draft to generate full documentation
```

## Output

- Created directories and files in `10-codebase/`
- Coverage map (source → docs)
- Clear next steps with specific commands
