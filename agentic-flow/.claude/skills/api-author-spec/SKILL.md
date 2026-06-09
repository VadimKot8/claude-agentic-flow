---
name: api-author-spec
description: "Authors the API specification file from the task description. Use during an [API] task after the format and toolchain are known."
---
# API Specification Authoring Skill

## Purpose

Procedural executor for writing the API specification file. Extracts domain knowledge from the
task description and produces the spec file using naming rules, structural conventions,
and schema patterns defined by the **active format skill**.

> **Not a format reference.** This skill does not define spec structure or naming conventions.
> Those come from the active format skill (`api-openapi`, `api-protobuf`, `api-asyncapi`,
> or `api-soap`). Always have the format skill active before running this skill.

## Activation

Activate when the API format has been detected (format skill is active and fully read).

---

## Logic

### 1. Domain Extraction
Extract from task description:
- **Entities/Schemas:** Names, fields, requirements, validation constraints.
- **Operations/Paths:** HTTP methods, path params, request/response bodies, status codes.
- **Messages/Services:** For AsyncAPI/Protobuf/SOAP, identify methods/channels/operations.

### 2. Path Determination
- **Primary:** Check `build.gradle.kts` for `inputSpec` or `sourceDir` — write to that path.
- **Default:** Use the canonical path from the active format skill.

### 3. Construction
- Apply all naming rules from the active format skill (operationIds, schema names, tag names).
- Cross-reference project memory for consistent naming across specs.
- Use `$ref` for shared components; never inline repeated schemas.
- Ensure all operations have an `operationId`.

## Rules
- **Scope Discipline:** Only implement what is in the task description.
- **No Hand-written DTOs:** All DTOs must be derivable from the spec.
- **Format-skill-guided:** Spec structure, naming conventions, and required fields come from the active format skill, not from this skill.
