# Documentation Operations

Keywords for comments, docstrings, and inline documentation.

## COMMENT

Add inline or block comments explaining code.

```
UPDATE src/algorithms/sort.ts:
    COMMENT quickSort with complexity analysis
    COMMENT partition logic explanation
```

## DOCSTRING

Add function/class documentation strings.

```
UPDATE src/api/users.ts:
    DOCSTRING getUser:
        Description: Fetch user by ID
        Params: id (string) - User identifier
        Returns: User object or null
        Throws: NotFoundError if user doesn't exist
```

```
UPDATE src/models/order.py:
    DOCSTRING class Order:
        Description of order entity
        Attributes documentation
        Usage examples
```

## ANNOTATE

Add type annotations or metadata.

```
UPDATE src/utils/helpers.ts:
    ANNOTATE all functions with return types
    ANNOTATE parameters with JSDoc types
```

```
UPDATE src/api/routes.py:
    ANNOTATE endpoints with OpenAPI decorators
    ANNOTATE request/response models
```
