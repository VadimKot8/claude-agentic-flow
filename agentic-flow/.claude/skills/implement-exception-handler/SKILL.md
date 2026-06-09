---
name: implement-exception-handler
description: "Implements @ControllerAdvice global exception handling. Use when a [DEVELOP] task defines API error responses."
---

# Implement Exception Handler Skill

Use this skill when implementing global error handling logic.

## Exception Handler Mandates

- **Centralization:** Use `@ControllerAdvice` or `@RestControllerAdvice`.
- **Mapping:** Map specific exceptions (both Spring/Persistence and custom Domain exceptions) to the generated `ErrorResponse` DTO.
- **Status Codes:** Use appropriate HTTP status codes (400 for validation/illegal state, 404 for not found, 409 for conflict, 500 for generic).
- **Security:** Do not leak internal stack traces or sensitive system details in the response body.
- **Logging:** Log the full exception at `ERROR` level for 500s, and `WARN` or `INFO` for 4xx errors.

## Example

The generated `ErrorResponse` DTO has exactly three fields (from the OpenAPI spec):
`status` (int), `message` (String), `timestamp` (OffsetDateTime).
Do NOT call `setCode()` — there is no such field.

```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        var error = new ErrorResponse();
        error.setStatus(HttpStatus.NOT_FOUND.value());
        error.setMessage(ex.getMessage());
        error.setTimestamp(OffsetDateTime.now());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<ErrorResponse> handleConflict(ConflictException ex) {
        var error = new ErrorResponse();
        error.setStatus(HttpStatus.CONFLICT.value());
        error.setMessage(ex.getMessage());
        error.setTimestamp(OffsetDateTime.now());
        return ResponseEntity.status(HttpStatus.CONFLICT).body(error);
    }
}
```
