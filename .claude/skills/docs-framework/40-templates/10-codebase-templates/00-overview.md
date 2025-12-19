---
covers: Templates for the Codebase zone — README through L5 function docstrings.
type: overview
concepts: [templates, codebase, L1, L2, L3, L4, L5, README]
---

# Codebase Templates

Templates for the Codebase zone. Layer-specific templates from README through function docstrings (L1-L5) that mirror your source code structure.

---

## File Tree

```
10-codebase-templates/
├── 00-overview.md                 (this file)
├── 10-readme-template.md          Repository root README
├── 20-codebase-overview-template.md L1 Codebase overview
├── 30-section-overview-template.md  L2 section overviews
├── 40-doc-node-template.md        L3 atomic documentation nodes
├── 50-code-header-template.md     L4 top-of-file headers
└── 60-docstring-template.md       L5 function/method docstrings
```

## Section Scope

The Codebase zone mirrors your source code structure. These templates provide the starting point for each documentation layer:

- **README**: Human-friendly entry point at repository root
- **Codebase Overview (L1)**: Navigation hub with architecture and section index
- **Section Overview (L2)**: Domain overviews with file trees
- **Doc Node (L3)**: Atomic concepts, one idea per file
- **Code Header (L4)**: Top-of-file contracts
- **Docstring (L5)**: Function-level documentation

## Child Nodes

### [10-readme-template.md](10-readme-template.md)
Template for repository root `README.md`. Human-friendly project introduction with links to setup and documentation.

### [20-codebase-overview-template.md](20-codebase-overview-template.md)
Template for `docs/10-codebase/00-overview.md`. L1 navigation hub with architecture and section index.

### [30-section-overview-template.md](30-section-overview-template.md)
Template for L2 section overviews. File trees, child descriptions, and section scope.

### [40-doc-node-template.md](40-doc-node-template.md)
Template for L3 atomic documentation nodes. Single concepts with code references.

### [50-code-header-template.md](50-code-header-template.md)
Template for L4 file headers. File responsibilities, dependencies, and public APIs.

### [60-docstring-template.md](60-docstring-template.md)
Template for L5 function/method documentation. Purpose, inputs, outputs, and error cases.
