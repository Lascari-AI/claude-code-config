# Action Operations

Modification operations for adding, removing, moving, and replacing content.

## ADD

Attaches or supplements an existing entity with new content.

```
UPDATE src/components/Button.tsx:
    ADD prop 'variant' with types: 'primary' | 'secondary' | 'danger'
    ADD default value for variant: 'primary'
```

## REMOVE

Takes something out from an existing entity (opposite of ADD).

```
UPDATE src/utils/helpers.ts:
    REMOVE deprecated import statements
    REMOVE unused utility functions
```

## MOVE

Relocates code/entities from one place to another.

```
MOVE src/utils/validation.ts to src/validators/index.ts:
    Keep all exports intact
    Update import paths in affected files
```

## REPLACE

Substitutes one piece of content for another.

```
UPDATE src/api/client.ts:
    REPLACE axios with fetch:
        Update all HTTP methods
        Maintain error handling patterns
```

## MIRROR

Replicates logic/pattern from an existing place and re-uses it.

```
CREATE src/charts/line_chart.py:
    MIRROR create_bar_chart:
        Same data processing
        Same color scheme logic
        Change chart type to line
```

## MAKE

Commanding version of update/create for direct transformations.

```
UPDATE src/styles/theme.ts:
    MAKE primary color: '#3B82F6'
    MAKE error states use red-500
```

## USE

Rely on or incorporate external code/references as a guide.

```
CREATE src/auth/oauth.ts:
    USE docs/oauth-spec.md as reference
    USE existing session.ts patterns
```

## APPEND

Adds something to the end or final position specifically.

```
UPDATE src/middleware/index.ts:
    APPEND errorHandler to middleware chain
    APPEND logging middleware last
```
