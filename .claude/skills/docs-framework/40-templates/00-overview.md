---
covers: Reusable templates for every layer of the documentation hierarchy.
type: overview
concepts: [templates, foundation, codebase, L1, L2, L3]
---

# Templates Capability

Reusable templates for every documentation layer. Foundation templates for purpose, principles, and boundaries. Codebase templates from README through function docstrings. Each template includes frontmatter patterns and opening paragraph conventions for progressive disclosure.

---

## File Tree

```
40-templates/
├── 00-overview.md                    (this file)
├── 00-foundation-templates/          Foundation zone templates
│   ├── 00-overview.md
│   ├── 10-foundation-overview-template.md
│   ├── 20-purpose-template.md
│   ├── 30-principles-template.md
│   └── 40-boundaries-template.md
└── 10-codebase-templates/            Codebase zone templates
    ├── 00-overview.md
    ├── 10-readme-template.md
    ├── 20-codebase-overview-template.md
    ├── 30-section-overview-template.md
    ├── 40-doc-node-template.md
    ├── 50-code-header-template.md
    └── 60-docstring-template.md
```

## Purpose

This capability provides copy-and-paste templates for every type of documentation, organized by zone:

- **Foundation Templates**: Fixed-structure documents for purpose, principles, and boundaries
- **Codebase Templates**: Layer-specific documents from README through function docstrings

Each template:
- Includes YAML frontmatter with `covers` field for progressive disclosure
- Shows opening paragraph convention (summary before first `---`)
- Follows the structural rules defined in Standards
- Provides guidance on how to fill in each section

## Contents

### [00-foundation-templates/](00-foundation-templates/00-overview.md)
Templates for the Foundation zone. Purpose, principles, and boundaries documents that capture system intent and guide all decisions.

### [10-codebase-templates/](10-codebase-templates/00-overview.md)
Templates for the Codebase zone. README, L1 codebase overview, L2 section overviews, L3 doc nodes, L4 code headers, and L5 function docstrings.
