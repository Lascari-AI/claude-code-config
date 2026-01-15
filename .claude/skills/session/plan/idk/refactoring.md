# Refactoring Operations

Keywords for restructuring, renaming, splitting, and merging code.

## REFACTOR

Restructure code without changing external behavior.

```
REFACTOR src/api/handlers.ts:
    Extract common error handling
    Reduce code duplication
    Improve readability
```

## RENAME

Change the name of an entity throughout the codebase.

```
RENAME getUserData to fetchUserProfile:
    Update all call sites
    Update test files
    Update documentation
```

## SPLIT

Divide a single entity into multiple parts.

```
SPLIT src/utils/helpers.ts:
    CREATE src/utils/string.ts with string helpers
    CREATE src/utils/date.ts with date helpers
    CREATE src/utils/array.ts with array helpers
```

## MERGE

Combine multiple entities into one.

```
MERGE src/validators/:
    Combine user.ts, email.ts, password.ts
    CREATE src/validators/index.ts
    Export all validators
```

## EXTRACT

Pull out code into a separate entity.

```
UPDATE src/components/Dashboard.tsx:
    EXTRACT chart rendering into ChartWidget component
    EXTRACT data fetching into useDataFetch hook
```

## INLINE

Move code from a separate entity back into the caller.

```
UPDATE src/utils/config.ts:
    INLINE getDefaultConfig() into constructor
    Remove unused function
```

## INSERT

Add new code at a specific position.

```
UPDATE src/middleware/index.ts:
    INSERT corsMiddleware at position 2
    INSERT rateLimiter after auth
```

## WRAP

Surround existing code with additional logic.

```
UPDATE src/api/client.ts:
    WRAP fetch calls with retry logic
    WRAP responses with error normalization
```
