# Location Keywords

Positioning keywords for placing code before or after existing elements.

## BEFORE

Insert or adjust code ahead of something else.

```
UPDATE src/middleware/auth.ts:
    ADD rate limiting check BEFORE authentication
```

```
UPDATE src/app.ts:
    INSERT error boundary BEFORE main router
```

## AFTER

Insert or adjust code after a specific block or line.

```
UPDATE src/api/users.ts:
    ADD audit logging AFTER successful user creation
```

```
UPDATE src/components/Form.tsx:
    ADD validation feedback AFTER form submission
```

## Combined Examples

```
UPDATE src/pipeline/processor.ts:
    ADD sanitization BEFORE validation
    ADD logging AFTER processing
    ADD error handler AFTER all middleware
```
