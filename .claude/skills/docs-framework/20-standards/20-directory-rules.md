---
covers: Physical organization of docs/ — zones, mirroring source code, overview requirements, and folder vs file decisions.
concepts: [directory, zones, mirroring, overview, file-tree]
---

# Directory Organization

The physical organization of `docs/`. Three zones by purpose (Foundation/Codebase/Appendix), path mirroring between Codebase zone and `src/`, the `00-overview.md` requirement for every directory, and guidelines for when to use folders vs files.

---

## Top-Level Structure: Three Zones

Every project using this framework organizes `docs/` into three zones:

```
docs/
├── 00-foundation/           # Intent zone (fixed structure)
│   ├── 00-overview.md
│   ├── 10-purpose.md
│   ├── 20-principles.md
│   └── 30-boundaries.md
├── 10-codebase/             # Structure zone (mirrors src/)
│   ├── 00-overview.md       # L1
│   └── [sections...]        # L2-L3
└── 99-appendix/             # Operational zone
    └── ...
```

- **Foundation** (`00-foundation/`): Fixed structure. Purpose, principles, boundaries.
- **Codebase** (`10-codebase/`): Mirrors your source code structure. Contains L1-L6 documentation.
- **Appendix** (`99-appendix/`): Setup guides, tooling, conventions.

---

## Codebase Zone: Mirror Your Code

Within the **Codebase zone**, documentation structure mirrors your application structure:

```
src/                          docs/10-codebase/
├── core/                     ├── 10-core/
│   ├── workflow/             │   ├── 10-workflow/
│   └── validation/           │   └── 20-validation/
├── data/                     ├── 20-data/
└── auth/                     └── 30-auth/
```

If you're working in `src/core/workflow/`, the documentation is in `docs/10-codebase/10-core/10-workflow/`.

**Exception**: Cross-cutting concerns (logging, caching, error handling) go in the most logical primary location rather than being scattered.

---

## The 00-overview.md Requirement

Every folder in docs/ MUST contain a `00-overview.md` file.

**Foundation Overview** — `docs/00-foundation/00-overview.md`:
- Links to purpose, principles, boundaries
- Guidance on when to read Foundation

**Codebase Overview (L1)** — `docs/10-codebase/00-overview.md`:
- System architecture
- Section index with descriptions

**Section Overviews (L2)** — `docs/10-codebase/XX-section/00-overview.md`:
- Section scope and boundaries
- File tree of immediate children
- Brief description for each child

**Subsection Overviews** — Same structure, narrower scope.

---

## File Tree Format

Every 00-overview.md includes a file tree of immediate children:

```markdown
## File Tree

20-data/
├── 00-overview.md              (this file)
├── 10-models/
│   └── 00-overview.md
├── 20-repository-pattern.md
└── 30-migrations.md
```

Rules:
- Show only immediate children (one level deep)
- Include brief description after each item
- Mark "(this file)" for the overview

---

## Folders vs Files

**Create a folder when:**
- Topic needs 3+ related files
- Clear subcategory exists
- Content will grow over time

**Keep it as a file when:**
- Single concept, fully covered in one doc
- Unlikely to expand
- Creating a folder adds bureaucratic overhead

**The smell test**: If you're creating `XX-topic/00-overview.md` with only one other file in it, just use `XX-topic.md`.

---

## Reserved Zones and Sections

```
docs/
├── 00-foundation/           # Reserved: Intent zone (fixed structure)
├── 10-codebase/             # Reserved: Code documentation zone
│   └── 10-80 range          # Your application sections within Codebase
└── 99-appendix/             # Reserved: Operational zone
```

- `00-foundation/` has a fixed structure (purpose, principles, boundaries)
- `10-codebase/` uses 10-80 range for your application sections
- `99-appendix/` is for documentation *about* the project operations, not the application itself

---

## Anti-Patterns

### ❌ Flat Structure
```
docs/
├── user-model.md
├── auth-flow.md
└── api-endpoints.md
```
No hierarchy = hard to navigate.

### ❌ Over-Nesting
```
docs/10-app/10-backend/10-services/10-user/user-service.md
```
Too many levels = tedious traversal.

### ❌ Missing Overviews
```
20-data/
├── models.md        # No 00-overview.md!
└── queries.md
```
No entry point = no navigation aid.

---

## Complete Example

```
my-project/
├── README.md
├── docs/
│   ├── 00-foundation/                     # Intent zone
│   │   ├── 00-overview.md
│   │   ├── 10-purpose.md
│   │   ├── 20-principles.md
│   │   └── 30-boundaries.md
│   ├── 10-codebase/                       # Structure zone
│   │   ├── 00-overview.md                 # L1
│   │   ├── 10-core/
│   │   │   ├── 00-overview.md             # L2
│   │   │   ├── 10-workflow-engine.md      # L3
│   │   │   └── 20-validation-rules.md
│   │   ├── 20-data/
│   │   │   ├── 00-overview.md
│   │   │   ├── 10-models/                 # Subsection
│   │   │   │   ├── 00-overview.md
│   │   │   │   ├── 10-user-model.md
│   │   │   │   └── 20-organization-model.md
│   │   │   └── 20-repository-pattern.md
│   │   └── 30-auth/
│   │       ├── 00-overview.md
│   │       └── 10-jwt-strategy.md
│   └── 99-appendix/                       # Operational zone
│       ├── 00-overview.md
│       └── 10-setup-guide.md
└── src/                                   # Mirrors 10-codebase/
    ├── core/
    ├── data/
    └── auth/
```
