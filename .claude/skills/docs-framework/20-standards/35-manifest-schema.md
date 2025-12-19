---
covers: YAML manifest specification for RWYN documentation discovery and scope definition.
type: standard
concepts: [manifest, rwyn.yaml, scope, discovery, component, repository]
depends-on: [20-standards/25-frontmatter-schema.md]
---

# Manifest Schema

The `.rwyn.yaml` manifest enables documentation discovery and defines scope. It lives inside each `docs/` folder and declares whether the documentation covers a full repository or a self-contained component. Discovery tools search for this file to locate documentation roots.

---

## Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `rwyn` | string | Framework version (e.g., "1.0"). Used for migration tracking. |
| `scope` | enum | `repository` or `component`. Defines documentation scope. |
| `coverage` | enum | `complete` or `partial`. Whether all code is documented. |
| `updated` | date | Last update date in YYYY-MM-DD format. |

### Conditional Fields

| Field | Required When | Type | Description |
|-------|---------------|------|-------------|
| `root` | `scope: component` | path | Relative path from manifest to code root. |
| `documented` | `coverage: partial` | path[] | List of documented code paths. |

### Optional Fields

| Field | Default | Type | Description |
|-------|---------|------|-------------|
| `status` | `stable` | enum | `stable` or `draft`. Draft indicates docs are being built. |

## Validation Rules

1. **Required fields**: `rwyn`, `scope`, `coverage`, `updated` must all be present
2. **Scope enum**: Must be exactly `repository` or `component`
3. **Coverage enum**: Must be exactly `complete` or `partial`
4. **Date format**: `updated` must be valid YYYY-MM-DD
5. **Conditional `root`**: If `scope: component`, `root` is required and path must exist
6. **Conditional `documented`**: If `coverage: partial`, `documented` array is required
7. **No nesting**: A component manifest cannot exist inside another documented scope

## Examples

### Repository Scope (Complete Coverage)

Full codebase documentation with all areas covered:

```yaml
rwyn: 1.0
scope: repository
coverage: complete
updated: 2025-01-15
```

### Repository Scope (Partial Coverage)

Full codebase structure but only some areas documented:

```yaml
rwyn: 1.0
scope: repository
coverage: partial
updated: 2025-01-15
documented:
  - src/core
  - src/api
```

### Component Scope

Self-contained module documentation that travels with the component:

```yaml
rwyn: 1.0
scope: component
coverage: complete
updated: 2025-01-15
root: src
```

### Component Scope (Draft Status)

Documentation actively being built:

```yaml
rwyn: 1.0
scope: component
coverage: complete
status: draft
updated: 2025-01-15
root: .
```

## Discovery Algorithm

To find the documentation root for a given code path:

```
function find_docs_root(start_path):
    current = start_path
    while current != filesystem_root:
        manifest = current / "docs" / ".rwyn.yaml"
        if exists(manifest):
            return current / "docs"
        current = parent(current)
    return null
```

For command-line discovery across a repository:

```bash
find . -name ".rwyn.yaml" -type f
```

## Scope Definitions

### Repository Scope

- Documentation lives at repository root: `repo/docs/`
- Covers the entire codebase (or partial with `documented` list)
- Foundation zone describes the project's purpose
- Codebase zone mirrors the full source structure

### Component Scope

- Documentation lives with the component: `component/docs/`
- Fully self-contained and portable
- Foundation zone describes the component's purpose
- Codebase zone mirrors only this component's structure
- Moving the component directory moves its documentation too

## Nesting Rules

**Nested component documentation is not allowed.**

If a `.rwyn.yaml` already exists in a parent directory, creating another manifest in a child directory is blocked. This prevents confusion about which documentation applies.

To document a component within a documented repository:
- Use the repository's `docs/10-codebase/` section for that component
- Or extract the component to its own repository with its own documentation

## Staleness Warning

The `updated` field enables staleness detection. Audit workflows should warn when documentation hasn't been updated in 30+ days, suggesting a review cycle.
