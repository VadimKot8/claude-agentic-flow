---
name: api-openapi
description: "Use when the task requires authoring or generating an OpenAPI 3.x REST spec, configuring the OpenAPI generator plugin (Gradle or Maven), or verifying generated Spring MVC controller interfaces and DTOs. Also the reference for REST design principles (resource naming, HTTP semantics, status codes, error shape) and REST security checks."
---

# OpenAPI 3.x Format Skill

## When to Use

Activate this skill when the task description contains any of: OpenAPI, OAS, REST, YAML spec,
swagger, HTTP endpoints, paths, controller interface, DTO.

---

## Spec Conventions

### File Structure

```yaml
openapi: "3.0.3"
info:
  title: <Project Name> API
  version: "1.0.0"
servers:
  - url: /
tags:
  - name: <Tag>        # PascalCase, matches useTags grouping
paths:
  /api/<resource>:
    post: ...
components:
  schemas:
    ErrorResponse:
      type: object
      required: [status, message, timestamp]
      properties:
        status:   { type: integer }
        message:  { type: string }
        timestamp: { type: string, format: date-time }
```

> Always use `openapi: "3.0.3"`. The openapi-generator spring generator does not fully support OAS 3.1.x features; using 3.1.x may produce incorrect or incomplete Java output.

### Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Schema names | PascalCase | `CreateVoterRequest`, `VoterResponse` |
| Property names | camelCase | `voterId`, `electionId` |
| Path parameters | camelCase | `{candidateId}` |
| Tags | PascalCase | `Voters`, `Elections` |
| Interface name (generated) | `<Tag>Api` | `VotersApi`, `ElectionsApi` |
| Enum values | UPPER_SNAKE_CASE | `ACTIVE`, `BLOCKED`, `CREATED` |
| `operationId` | camelCase verb+noun | `createVoter`, `getElectionById`, `castVote` |

> With `useTags=true`, the generator names each interface `<TagName>Api.java`. Choose tag names to match the intended interface name — e.g., tag `Voters` → `VotersApi.java`.

> `operationId` must be set on every path operation — it becomes the method name on the generated interface. Omitting it causes the generator to produce unpredictable names like `apiVotersPost`.

### Required Fields and Validation

- All `*Request` schemas: mark required fields in `required:` array
- String fields that must not be blank: add `minLength: 1`
- ID fields: use `type: integer, format: int64`
- Boolean fields: use `type: boolean` (no format)
- Enums: use `type: string` with `enum:` list
- Always define `ErrorResponse` in `components/schemas` and `$ref` it from error responses

### HTTP Status Codes

| Situation | Code |
|-----------|------|
| Resource created | 201 |
| Read / update success | 200 |
| Validation failure | 400 |
| Forbidden action | 403 |
| Resource not found | 404 |
| State conflict / duplicate | 409 |

### Always Include

- `ErrorResponse` schema in `components/schemas`
- Tag all paths with the domain tag
- Use `$ref: '#/components/schemas/ErrorResponse'` for all error responses — never inline

---

## Output Paths

| What | Default Path (Gradle / Maven) |
|------|-------------|
| Spec file | `src/main/resources/openapi/<name>.yaml` |
| Generated API interfaces | `build/generate-resources/main/src/main/java/<apiPackage>/` / `target/generated-sources/openapi/src/main/java/<apiPackage>/` |
| Generated DTO classes | `build/generate-resources/main/src/main/java/<modelPackage>/` / `target/generated-sources/openapi/src/main/java/<modelPackage>/` |

If `Output Paths` are already configured, write the spec to that path instead of the default.

---

## Verification Checklist

After running the OpenAPI code-generation task (`openApiGenerate` on Gradle; `mvn generate-sources` with `openapi-generator-maven-plugin` on Maven):

- [ ] Spec file exists at the configured/default path
- [ ] API interface files exist: one `*Api.java` per tag (e.g., `VotersApi.java`, `ElectionsApi.java`)
- [ ] DTO files exist: one class per schema defined in `components/schemas`
- [ ] Interface method signatures match spec paths and HTTP verbs
- [ ] DTO fields match schema property names (camelCase in Java)
- [ ] Generated controller interfaces: `@Valid` on `@RequestBody` parameters for request schemas
- [ ] Generated DTO classes: `@NotNull` on required fields, `@Size` on string fields with `minLength`/`maxLength`
- [ ] The compile task exits successfully (`./gradlew compileJava` BUILD SUCCESSFUL / `mvn compile` BUILD SUCCESS)
