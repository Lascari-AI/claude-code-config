# Testing Operations

Keywords for tests, assertions, mocks, and verification.

## TEST

Create or update test cases.

```
CREATE tests/auth/login.test.ts:
    TEST valid login returns token
    TEST invalid password returns 401
    TEST locked account returns 403
```

## ASSERT

Define specific assertions within tests.

```
UPDATE tests/utils/format.test.ts:
    ASSERT formatCurrency(100, 'USD') equals '$100.00'
    ASSERT formatCurrency handles negative numbers
    ASSERT formatCurrency throws on invalid currency
```

## MOCK

Create mock implementations for testing.

```
CREATE tests/mocks/api.ts:
    MOCK fetchUser to return test user data
    MOCK createUser to return success response
    MOCK deleteUser to simulate network error
```

## VERIFY

Confirm expected behavior or state.

```
UPDATE tests/integration/checkout.test.ts:
    VERIFY payment service was called once
    VERIFY order status updated to 'completed'
    VERIFY confirmation email was queued
```

## CHECK

Validation or conditional verification.

```
UPDATE src/validators/user.ts:
    CHECK email format is valid
    CHECK password meets strength requirements
    CHECK username is not taken
```
