---
name: test-verify-prerequisites
description: "Checks generated sources and domain deps exist before test authoring. Use at the start of a [TEST] task."
---
# Test Prerequisite Verification Skill

## Purpose
Logic for ensuring the project environment is ready for test implementation, specifically checking for generated sources and domain dependencies.

## Activation
Activate before writing tests to verify that the target system is "testable" and all required types are available or being generated.

---

## Logic

### 1. Generated Source Verification
- Check if the OpenAPI code-generation task has been run (see `CLAUDE.md` Build Task Vocabulary).
- Inspect the output directory (typically `build/generated/sources/openapi/` for Gradle,
  `target/generated-sources/openapi/` for Maven, or as configured in the project).
- If missing: Run the code-generation task and wait for completion.

### 2. Domain Dependency Check
- Check for the existence of domain entities/classes referenced in the task description.
- If a dependency (e.g., a `[DEVELOP]` task for an entity) is not yet done, proceed but plan to document the reference in the test as "waiting for implementation".

## Rules
- **TDD Awareness:** Proceed even if implementation classes are missing; this is expected in the Red phase.
- **Fail Fast:** If OpenAPI generation fails, stop and diagnose the spec/config before writing tests.
