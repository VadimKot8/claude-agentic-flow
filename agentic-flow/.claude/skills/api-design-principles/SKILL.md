---
name: api-design-principles
description: "REST contract design: HTTP semantics, URL conventions, status codes, versioning, and error-response shape for Spring Boot projects. Use before authoring any API spec to ensure the contract is correct."
---

# API Design Principles

## When to Use

Activate this skill **before authoring a spec** when the task requires designing or reviewing
a REST API contract — especially when deciding on resource naming, HTTP status codes,
error shapes, or versioning strategy.

> This is a **design reference skill**, not a code-generation skill.
> It does not generate files or run commands.
> The output of using this skill is a correct, reviewed spec that you then pass to `api-author-spec`.

---

## REST Resource Design

### URL Conventions

| Rule | Good | Bad |
|------|------|-----|
| Use plural nouns | `/api/voters` | `/api/voter` |
| Kebab-case path segments | `/api/election-results` | `/api/electionResults` |
| Nested resource for ownership | `/api/elections/{id}/candidates` | `/api/getCandidatesForElection` |
| No verbs in paths | `POST /api/voters` | `POST /api/createVoter` |

### HTTP Method Semantics

| Method | Semantics | Idempotent | Safe |
|--------|-----------|------------|------|
| GET | Retrieve resource or collection | Yes | Yes |
| POST | Create new resource | No | No |
| PUT | Replace entire resource | Yes | No |
| PATCH | Partial update | No | No |
| DELETE | Remove resource | Yes | No |

### HTTP Status Codes (project standard)

| Situation | Code |
|-----------|------|
| Resource created | 201 |
| Read / update success | 200 |
| No body in response | 204 |
| Validation failure | 400 |
| Unauthenticated | 401 |
| Forbidden action | 403 |
| Resource not found | 404 |
| State conflict / duplicate | 409 |
| Server error | 500 |

---

## Error Response Shape

All error responses must use the shared `ErrorResponse` schema defined in `components/schemas`:

```yaml
ErrorResponse:
  type: object
  required: [status, message, timestamp]
  properties:
    status:    { type: integer }
    message:   { type: string }
    timestamp: { type: string, format: date-time }
```

- Never inline error shapes in individual path responses — always `$ref: '#/components/schemas/ErrorResponse'`.
- Include `ErrorResponse` on every `4xx` and `5xx` response.

---

## API Versioning

Prefer **URL versioning** for this project:

```
/api/v1/voters
```

- Add the version prefix only when a breaking change is introduced.
- Do not version internal or admin-only endpoints until they are stable.

---

## Pagination

For list endpoints returning potentially large collections, use query parameters:

```
GET /api/voters?page=0&size=20
```

Response wrapper:

```yaml
PagedResult:
  type: object
  required: [content, totalElements, totalPages, page, size]
  properties:
    content:       { type: array, items: { $ref: '#/components/schemas/<Item>' } }
    totalElements: { type: integer, format: int64 }
    totalPages:    { type: integer }
    page:          { type: integer }
    size:          { type: integer }
```

---

## Common Pitfalls

- **POST returning 200 instead of 201** — creation must return 201 with a `Location` header.
- **Verbs in paths** — signals resource-model mismatch; redesign as a state transition (e.g., `PATCH /api/voters/{id}` with `{ "status": "BLOCKED" }`).
- **Inconsistent error shapes** — all errors must use the shared `ErrorResponse` schema.
- **Missing `operationId`** — every path operation must have one; it becomes the Java method name.
- **Tight coupling to DB schema** — API resource names and field names must reflect domain language, not table/column names.
