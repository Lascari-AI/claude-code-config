# Language Constructs

Keywords for code constructs: variables, functions, classes, types, and files.

## VAR

Refers to a variable that needs manipulation.

```
UPDATE src/config.ts:
    CREATE VAR API_TIMEOUT = 30000
    UPDATE VAR MAX_RETRIES from 3 to 5
```

## FUNCTION

Denotes a function definition (def, function, method).

```
CREATE src/utils/format.ts:
    CREATE FUNCTION formatCurrency(amount: number, currency: string):
        Handle locale formatting
        Return formatted string
```

## CLASS

Denotes a class definition.

```
CREATE src/models/User.ts:
    CREATE CLASS User:
        Private fields: id, email, passwordHash
        Constructor with validation
        Methods: authenticate(), updateEmail()
```

## TYPE

Denotes a type definition (interface, Pydantic model, TypeScript type).

```
CREATE src/types/api.ts:
    CREATE TYPE ApiResponse<T>:
        data: T
        status: number
        message: string
```

```
CREATE src/schemas/user.py:
    CREATE TYPE UserCreate(BaseModel):
        email: EmailStr
        password: str
        name: Optional[str]
```

## FILE

Denotes operations on an entire file.

```
CREATE FILE src/new_module.py:
    Add module docstring
    Add imports
    Add main function
```

## DEFAULT

Ties a value or parameter to a default.

```
UPDATE src/api/config.ts:
    CREATE VAR timeout DEFAULT 5000
    UPDATE FUNCTION fetch() param retries DEFAULT 3
```
