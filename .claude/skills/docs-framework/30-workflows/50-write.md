---
covers: Write or update L2/L3 documentation for a source path using provided context notes.
concepts: [write, draft, update, L2, L3, generation, notes]
---

# Docs Write Workflow

Write or update documentation for a source path. Uses provided context notes (interview notes, implementation notes, or any description of what was built/changed) combined with source code analysis and existing documentation to generate L2/L3 documentation.

---

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `source_path` | Argument 1 | Yes |
| `notes_file` | Argument 2 | Yes (for initial docs), Optional (for minor updates) |

**Notes file** can be:
- Interview notes from `/docs:interview-codebase`
- Implementation notes after building a feature
- A spec document you implemented against
- Any markdown describing what was built/changed

---

## Process

### 1. Validate Inputs

```
If source_path not provided:
  → Ask: "Which source path should I document?"

If notes_file not provided AND no existing docs:
  → Ask: "Please provide a notes file with context about what to document"

If notes_file not provided AND existing docs exist:
  → Proceed with code analysis only (minor update mode)
```

### 2. Gather Context

Read these sources:

| Source | Location | Purpose |
|--------|----------|---------|
| Notes file | `[notes_file]` argument | What was built/changed (primary insight source) |
| Source code | `[source_path]/` | Current implementation |
| Existing docs | `docs/10-codebase/[section]/` | What's already documented |
| L1 overview | `docs/10-codebase/00-overview.md` | Parent context |

### 3. Analyze & Generate Change Plan

Compare sources to identify what needs to be created or updated:

```
Documentation Write Plan for [source_path]
══════════════════════════════════════════

Context Sources:
- Notes file: ✅ [notes_file] (loaded)
- Source files: ✅ [N] files in [source_path]/
- Existing docs: ✅ [N] files in docs/10-codebase/[section]/
           OR: ❌ No existing docs (will create new section)

Planned Changes:
┌─────────────────────────┬────────┬─────────────────────────────┐
│ File                    │ Action │ Reason                      │
├─────────────────────────┼────────┼─────────────────────────────┤
│ 00-overview.md          │ CREATE │ New section                 │
│ 10-[concept].md         │ CREATE │ From notes                  │
│ 20-[concept].md         │ UPDATE │ New functionality added     │
└─────────────────────────┴────────┴─────────────────────────────┘

Proceed? (y/n)
```

**Guidelines for identifying changes:**
- New section with no existing docs → CREATE L2 overview + L3 nodes
- Existing section + notes about new functionality → CREATE new L3 nodes, UPDATE L2 overview
- Existing section + notes about changes → UPDATE affected L3 nodes and L2 overview
- File tree changes → UPDATE L2 overview file tree section

### 4. Load Templates

Read the appropriate templates:

| Template | Location | Used For |
|----------|----------|----------|
| Section overview | `40-templates/10-codebase-templates/30-section-overview-template.md` | L2 docs |
| Doc node | `40-templates/10-codebase-templates/40-doc-node-template.md` | L3 docs |

### 5. Write L2 Overview

Create or update `docs/10-codebase/[section]/00-overview.md`:

```markdown
---
covers: [What this section encompasses - from notes]
concepts: [key, concepts, from, notes]
code-ref: [source_path]
---

# [Section Name]: Overview (L2)

[Brief description of what this section covers]

## File Tree

```
[source_path]/
├── [actual file structure]
├── [from the source directory]
└── [keep it accurate]
```

## Section Scope

### What This Section Owns
[From notes: responsibilities and boundaries]

### What This Section Does NOT Own
[From notes: explicit boundaries, what belongs elsewhere]

## Architecture
[From notes: key patterns, data flow, design decisions]

## Child Nodes

### [10-concept-name.md](10-concept-name.md)
[Description of what this node covers]

### [20-concept-name.md](20-concept-name.md)
[Description of what this node covers]
```

**If updating existing L2:**
- Preserve existing content not contradicted by notes
- Update file tree to match current source structure
- Add new child node links
- Update architecture section if notes indicate changes

### 6. Propose L3 Nodes

Present proposed nodes to user:

```
Based on the notes, I'll create/update these L3 documentation nodes:

┌────┬─────────────────────────┬────────┬────────────────────────────┐
│ #  │ File                    │ Action │ Covers                     │
├────┼─────────────────────────┼────────┼────────────────────────────┤
│ 1  │ 10-session-lifecycle.md │ CREATE │ Session creation, storage  │
│ 2  │ 20-token-handling.md    │ UPDATE │ Added refresh flow         │
│ 3  │ 30-mfa.md               │ CREATE │ New MFA functionality      │
└────┴─────────────────────────┴────────┴────────────────────────────┘

Approve this structure? (Or suggest changes)
```

**Guidelines for L3 nodes:**
- One concept per file (atomic)
- Don't create a doc for every source file
- Group related functionality into concepts
- Use 10, 20, 30 numbering (gaps for future additions)

### 7. Write L3 Nodes

For each approved node, create or update the file:

```markdown
---
covers: [Specific scope - from notes]
concepts: [relevant, concepts]
code-ref: [specific files this covers]
---

# [Concept Name]

## Context
[Why this exists, background from notes]

## Architecture

### [Subheading based on content]
[Explanation of how it works at a conceptual level]
[Focus on the "Why" - decisions, trade-offs, patterns]

### [Another subheading if needed]
[More architectural explanation]

## Key Rules
- [Rule or invariant from notes]
- [Another important constraint]
- [Gotcha or edge case to know about]

## Code References

| File | Purpose |
|------|---------|
| `[path/to/file.ext]` | [What this file does] |
| `[path/to/other.ext]` | [What this file does] |

## Related
- [Link to related L3 node if applicable](./XX-related.md)
- [Link to another section if cross-cutting](../YY-section/00-overview.md)
```

**If updating existing L3:**
- Preserve existing content not contradicted by notes
- Add new sections for new functionality
- Update code references if files changed
- Mark removed functionality as deprecated or delete if appropriate

### 8. Update L1 Overview

Ensure `docs/10-codebase/00-overview.md` links to the new/updated section:

- Add section to child nodes list if new
- Update description if section scope changed

### 9. Validate Links

After writing all files:

1. **Check internal doc links** - All `[text](path)` links resolve
2. **Check code references** - Referenced files exist in source
3. **Check parent links** - L2 overview links to all L3 nodes
4. **Check L1 links** - L1 overview links to this L2

Report any issues found.

### 10. Summary

Output completion summary:

```
Documentation Write Complete!

Section: [section-name]
Source: [source_path]
══════════════════════════════════════

Created:
- docs/10-codebase/[section]/00-overview.md (L2)
- docs/10-codebase/[section]/30-mfa.md (L3)

Updated:
- docs/10-codebase/[section]/20-token-handling.md (L3)
- docs/10-codebase/00-overview.md (L1 - added section link)

Link Validation:
- ✅ All internal links valid
- ✅ All code references exist

Notes file used:
- [notes_file]

Next Steps:
1. Review the generated documentation
2. Edit as needed to refine language and accuracy
3. Run /docs:annotate [source_path] to add L4/L5 to source files
4. Run /docs:audit to verify structure
```

---

## Quality Checklist

Before marking write complete, verify:

- [ ] L2 overview has accurate file tree
- [ ] L2 overview links to all L3 nodes
- [ ] Each L3 node has frontmatter with `covers` and `code-ref`
- [ ] Code references use correct paths
- [ ] No generic placeholder text remains
- [ ] Key insights from notes are captured
- [ ] Cross-references to related sections included
- [ ] L1 overview updated if needed

---

## Output

- Created/updated documentation files
- Link validation results
- Clear summary of what was done
- Next steps for follow-up actions
