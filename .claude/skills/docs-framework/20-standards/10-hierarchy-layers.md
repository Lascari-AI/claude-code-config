---
covers: Three-zone organization (Foundation/Codebase/Appendix) and six-layer hierarchy (L1-L6).
concepts: [zones, layers, L1, L2, L3, L4, L5, L6, foundation, codebase, appendix]
---

# The Hierarchy: Zones and Layers

The framework uses two complementary organization schemes: **Zones** (horizontal) organize by semantic purpose, **Layers** (vertical) organize by depth of detail. Together they create navigable documentation from project intent to implementation.

---

## Two Dimensions of Organization

This framework uses two complementary organization schemes:

- **Zones** (horizontal): Organize by semantic purpose — Foundation, Codebase, Appendix
- **Layers** (vertical): Organize by depth of detail — L1 through L6

```
docs/
├── 00-foundation/           # Intent zone (Purpose, Principles, Boundaries)
│   ├── 00-overview.md
│   ├── 10-purpose.md
│   ├── 20-principles.md
│   └── 30-boundaries.md
├── 10-codebase/             # Structure zone (L1-L6 hierarchy lives here)
│   ├── 00-overview.md       # L1: Navigation hub
│   ├── 10-[section]/        # L2: Domain overviews
│   │   ├── 00-overview.md
│   │   └── [L3 nodes]
│   └── ...
└── 99-appendix/             # Operational zone (setup, tooling)
    └── ...
```

---

## The Three Zones

### Foundation Zone (`00-foundation/`)

Captures intent that precedes and informs all architecture decisions.

**Contains**:
- **Purpose** (`10-purpose.md`): Why this system exists, the problem it solves, who it serves
- **Principles** (`20-principles.md`): Decision-making heuristics that apply everywhere
- **Boundaries** (`30-boundaries.md`): What the system explicitly will NOT do

### Codebase Zone (`10-codebase/`)

Documents what was built and how it works. Mirrors the source code structure.

**Contains**: The L1-L6 hierarchy (detailed below).

### Appendix Zone (`99-appendix/`)

Operational guidance for working with the project.

**Contains**: Setup guides, deployment instructions, tooling configuration, conventions.

---

## The Six Layers (Within Codebase Zone)

The L1-L6 hierarchy lives within the Codebase zone and creates a depth-based structure:

```
Repository Root              → README.md (Human entry point)
L1: Codebase Overview        → docs/10-codebase/00-overview.md
L2: Section Overviews        → Major domains with file trees
L3: Atomic Nodes             → Single concepts, rules, patterns (with code references)
L4: File Headers             → What a file is responsible for
L5: Function Docstrings      → What a function does
L6: Implementation           → How it actually works
```

---

## Repository Root: The Human Entry Point

### File
`README.md` at repository root

### Purpose
- Human-friendly landing page for developers who just cloned the repo
- Allows for easy reading in a GitHub repo as ReadMe's are rendered on the page

### Contains
- Quick explanation of what the application does
- Direct links to practical tasks (setup, deployment, getting started)
- Link to formal documentation entry (docs/00-overview.md)
- Feature highlights and project status

---

## L1: Codebase Overview

### File
`docs/10-codebase/00-overview.md`

### Purpose
Formal documentation entry point for understanding how the system is built.

### Contains
- System's high-level architecture
- Major architectural decisions
- Section index with descriptions of each section
- Links to all L2 section overviews

---

## L2: Section/Domain Overviews

### Files
`docs/10-codebase/XX-section/00-overview.md`

### Purpose
Scoped overviews for major areas (Core, Data Layer, API, Auth, etc.)

### Contains
- File tree showing immediate children (not exhaustive)
- Coverage of the section
- Descriptions for each child node
- Links to L3 nodes with descriptive anchor text

### Template
See [30-section-overview-template.md](../40-templates/30-section-overview-template.md) for structure and examples.

---

## L3: Atomic Nodes (Concepts, Rules, Patterns)

### Files
Individual markdown files in section directories

### Purpose
One coherent idea per file

### Contains
- Single concept, pattern, or architectural decision
- Links to related L3 nodes
- May include diagrams or examples
- Inline references to code files as concepts are discussed
- Optional "Related Files" summary for complex topics

### Characteristics
- **Atomic**: Cannot be split further without losing coherence
- **Link-rich**: Dense cross-referencing
- **Declarative**: States what exists and why
- **Code-connected**: References implementation files naturally in prose

---

## L4: Top-of-Code-File Headers

### Location
First 30-50 lines of code files (as comments)

### Purpose
Bridge between documentation and code - explains "What" without "How"

### Contains
- File path and summary
- Responsibilities (2-3 bullet points)
- Inputs/Outputs and key dependencies
- Contracts, invariants, and error semantics
- Public API exports

### Template
See [50-code-header-template.md](../40-templates/50-code-header-template.md) for structure and examples.

### Critical Rule
Must be ≤50 lines to maintain scannability

---

## L5: Function/Method Docstrings

### Location
Above each major function in code

### Purpose
Concise contract for individual functions

### Contains
- Purpose statement (starts with "Do:")
- Inputs with constraints
- Outputs and side effects
- Pre/post conditions
- Error cases
- Complexity notes if relevant

### Template
See [60-docstring-template.md](../40-templates/60-docstring-template.md) for structure and examples.

---

## L6: Implementation (Code)

### Location
The actual code following headers and docstrings

### Purpose
The "How" - actual implementation details

### Key Point
This is the final layer - read only after L4/L5 indicate this is the right file/function