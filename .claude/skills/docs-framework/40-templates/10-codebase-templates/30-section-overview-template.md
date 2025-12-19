---
covers: Template for L2 Section Overview navigation hubs.
concepts: [L2, section, overview, navigation, file-tree]
---

# L2 Section Overview Template

Template for `00-overview.md` files that serve as navigation hubs for each major documentation section. L2 overviews help readers understand what a section contains, visualize its structure, and choose which child nodes to explore.

---

## Template

<template>

    ---
    covers: [One sentence describing this section's scope and what it contains]
    type: overview
    ---

    # [Section Name]

    [One sentence describing this section's purpose and what questions it answers. This is the SKIM layer.]

    ---

    ## File Tree

    XX-section-name/
    ├── 00-overview.md              (this file)
    ├── 10-first-node.md            Brief description (3-5 words)
    ├── 20-second-node.md           Brief description
    ├── 30-subsection/              Brief description
    │   ├── 00-overview.md
    │   ├── 10-sub-node.md
    │   └── 20-sub-node.md
    └── 40-last-node.md             Brief description

    ## Section Scope

    [Paragraph explaining what this section covers, what questions it answers,
    and how it relates to the overall system]

    ## Child Nodes / Subsections

    ### [10-first-node.md](10-first-node.md)
    [1-2 sentences explaining what this node contains and its purpose]

    ### [20-second-node.md](20-second-node.md)
    [1-2 sentences explaining what this node contains and its purpose]

    ### [30-subsection/](30-subsection/00-overview.md)
    [1-2 sentences explaining what this subsection covers]

</template>

## Usage Guidelines

### Purpose
Section overviews (L2) are the primary navigation layer. They help readers:
- Understand what a section contains before diving deeper
- Visualize the structure through file trees
- Choose which child nodes are relevant to their task
- Navigate to related sections when needed

### Key Components

1. **Opening Paragraph**:
   - Single sentence that answers "What is this section about?"
   - This is the SKIM layer — agent should know if this section is relevant

2. **File Tree**:
   - Shows immediate children only (not recursive)
   - Include brief descriptions for each item

3. **Child Nodes**:
   - For each child, provide:
     - Link to the node
     - 1-2 sentence description of what it contains

4. **Section Scope**:
   - What domain this section covers
   - What questions it answers
   - How it fits into the larger system

### Numbering Convention

- Use 00, 10, 20, 30... to allow insertion
- Reserve 99 for special purposes (like appendix)
- Subsections follow the same pattern

### File Tree Format

    XX-section-name/
    ├── 00-overview.md              (this file)
    ├── 10-node.md                  What it contains (3-5 words)
    └── 20-subsection/              Topic area
        └── 00-overview.md

Keep descriptions brief but informative. The tree should be scannable.
