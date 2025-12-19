---
covers: The structural rules — hierarchy, directory structure, numbering systems, and linking conventions.
type: overview
concepts: [standards, hierarchy, zones, layers, numbering, linking]
---

# Standards Capability

The structural rules that make the documentation system navigable. Defines the three zones, six-layer hierarchy, directory organization, numbering conventions, and linking patterns.

---

## The Foundation

The framework organizes `docs/` into three zones and six layers:

**Three Zones** (by purpose):
- `00-foundation/` — Intent (why, principles, boundaries)
- `10-codebase/` — Structure (mirrors code, L1-L6)
- `99-appendix/` — Operations (setup, tooling)

**Six Layers** (progressive depth in Codebase):
- L1-L3: Documentation files (overview → sections → concepts)
- L4-L5: Code annotations (file headers → function docstrings)
- L6: Implementation (the code itself)

## Contents

### [10-hierarchy-layers.md](10-hierarchy-layers.md)
The L1-L6 depth model. Defines what belongs in Foundation vs Codebase, and Headers vs Docstrings.

### [20-directory-rules.md](20-directory-rules.md)
The physical organization of `docs/`. Zones, mirroring source code, and folder vs file decisions.

### [25-frontmatter-schema.md](25-frontmatter-schema.md)
The YAML frontmatter specification for progressive disclosure. Defines `covers`, `concepts`, and `depends-on` fields.

### [35-manifest-schema.md](35-manifest-schema.md)
The `.rwyn.yaml` manifest specification for documentation discovery and scope. Defines repository vs component scopes.

### [30-numbering-system.md](30-numbering-system.md)
The `XX-` prefix system that keeps files ordered and allows for insertion.

### [40-doc-linking.md](40-doc-linking.md)
How to link between documentation files (top-down, declarative anchor text).

### [50-code-linking.md](50-code-linking.md)
How to link from documentation to code (one-way, specific references).
