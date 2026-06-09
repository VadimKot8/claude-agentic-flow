---
name: api-create-skeletons
description: "Creates minimal Java stubs for non-generated types referenced by a spec (enums, constants, service interfaces). Use during an [API] task when the spec references types the generator will not produce."
---
# API Domain Skeleton Creation Skill

## Purpose
Logic for creating Java stubs for non-generated types (enums, constants, service interfaces) referenced by API specs.

## Activation
Activate after authoring an API spec if the task mentions domain types NOT produced by the generator.

---

## Logic

### 1. Identification
Inspect task description for types referenced in the spec but not generated (e.g., internal enums, marker interfaces).

### 2. Stub Generation
Create minimal stubs in `src/main/java/`:
- **Enums:** Declare with all values listed.
- **Interfaces:** Declare with method signatures; no body.
- **Classes:** Declare with required fields; throw `UnsupportedOperationException("stub")`.
  Use classic Java classes with getters/setters. **Do NOT use Records** — Records are prohibited
  for DTOs and data-carrier types (project policy, see `.claude/PROTOCOL.md §4`).

## Rules
- **Minimalist:** Write only what is strictly necessary to satisfy the reference.
- **Location:** Place in domain packages, not in generated code directories.
