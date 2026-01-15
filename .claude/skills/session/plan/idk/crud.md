# CRUD Operations

Core operations for creating, updating, and deleting code elements.

## CREATE

Initializes a brand-new entity (file, function, class, variable, etc.).

**Usage**: When you need to make something new that doesn't exist.

```
CREATE src/auth/validators.py:
    CREATE FUNCTION validate_user(user: User) -> bool:
        Check email format
        Verify password strength
        Return validation result
```

```
CREATE src/types/user.ts:
    CREATE TYPE User:
        id: string
        email: string
        createdAt: Date
```

## UPDATE

Modifies an existing entity. Tells the AI to edit or enhance what's already there.

**Usage**: When you need to change existing code without replacing it entirely.

```
UPDATE src/api/routes.py:
    UPDATE FUNCTION get_users():
        ADD pagination parameters
        ADD filtering by status
```

```
UPDATE src/config.ts:
    UPDATE VAR defaultTimeout:
        Change from 5000 to 10000
```

## DELETE

Removes or eliminates an existing entity completely.

**Usage**: When you need to remove code that's no longer needed.

```
DELETE src/deprecated/old_auth.py:
    DELETE entire file
```

```
UPDATE src/api/handlers.py:
    DELETE FUNCTION legacy_endpoint()
```
