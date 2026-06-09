---
name: api-openapi
description: "Use when the task requires authoring or generating an OpenAPI 3.x REST spec, configuring the openApiGenerate Gradle plugin, or verifying generated Spring MVC controller interfaces and DTOs."
---

# OpenAPI 3.x Format Skill

## When to Use

Activate this skill when the task description contains any of: OpenAPI, OAS, REST, YAML spec,
swagger, HTTP endpoints, paths, `voting-api.yaml`, controller interface, DTO.

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

## Gradle Toolchain

### Required Plugin

Add to the `plugins {}` block in `build.gradle.kts`:

```kotlin
id("org.openapi.generator") version "7.12.0"
```

### Full Configuration Block

Add after the `plugins {}` block:

```kotlin
openApiGenerate {
    generatorName.set("spring")
    inputSpec.set("$projectDir/src/main/resources/openapi/<spec-name>.yaml")  // replace <spec-name> with actual filename from task
    outputDir.set(layout.buildDirectory.dir("generate-resources/main").get().asFile.toString())
    apiPackage.set("com.agents_test.voting.api")
    modelPackage.set("com.agents_test.voting.dto")
    configOptions.set(mapOf(
        "interfaceOnly"                    to "true",
        "useTags"                          to "true",
        "useSpringBoot3"                   to "true",   // selects jakarta.* imports; required for SB3+ including SB4
        "documentationProvider"            to "none",
        "skipDefaultInterface"             to "true",
        "openApiNullable"                  to "false",
        "additionalModelTypeAnnotations"   to "@lombok.Builder\n@lombok.AllArgsConstructor"  // requires lombok compileOnly + annotationProcessor deps
    ))
}

sourceSets {
    main {
        java {
            srcDir(layout.buildDirectory.dir("generate-resources/main/src/main/java"))
        }
    }
}

tasks.compileJava {
    dependsOn(tasks.openApiGenerate)
}
```

### Required Runtime Dependencies

Add to the `dependencies {}` block:

```kotlin
implementation("jakarta.validation:jakarta.validation-api")
implementation("io.swagger.core.v3:swagger-annotations:2.2.28")
compileOnly("org.projectlombok:lombok:1.18.34")
annotationProcessor("org.projectlombok:lombok:1.18.34")
```

### Applying to build.gradle.kts (non-destructive)

Before writing any Gradle changes:
1. Read `build.gradle.kts`.
2. If the `org.openapi.generator` plugin is **already present** — do not add it again.
3. If the `openApiGenerate {}` block is **already present** — note its `inputSpec`, `outputDir`,
   `apiPackage`, and `modelPackage` values; do not overwrite them.
4. Add only the missing pieces (plugin, config block, dependencies, `sourceSets`, `compileJava` dependency).

---

## Output Paths

| What | Default Path |
|------|-------------|
| Spec file | `src/main/resources/openapi/<name>.yaml` |
| Generated API interfaces | `build/generate-resources/main/src/main/java/<apiPackage>/` |
| Generated DTO classes | `build/generate-resources/main/src/main/java/<modelPackage>/` |

If `inputSpec` is already set in `build.gradle.kts`, write the spec to that path instead of the default.

---

## Verification Checklist

After running `./gradlew openApiGenerate`:

- [ ] Spec file exists at the configured/default path
- [ ] API interface files exist: one `*Api.java` per tag (e.g., `VotersApi.java`, `ElectionsApi.java`)
- [ ] DTO files exist: one class per schema defined in `components/schemas`
- [ ] Interface method signatures match spec paths and HTTP verbs
- [ ] DTO fields match schema property names (camelCase in Java)
- [ ] Generated controller interfaces: `@Valid` on `@RequestBody` parameters for request schemas
- [ ] Generated DTO classes: `@NotNull` on required fields, `@Size` on string fields with `minLength`/`maxLength`
- [ ] `./gradlew compileJava` exits with BUILD SUCCESSFUL
