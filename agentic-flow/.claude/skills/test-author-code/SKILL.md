---
name: test-author-code
description: "Writes expressive Red-phase Java tests that define the contract. Use to implement the test classes in a [TEST] task."
---
# Test Code Authoring Skill (Red Phase)

## Purpose
Logic for writing high-quality, expressive Java tests that define the contract before implementation exists.

## Activation
Activate during the implementation phase of a `[TEST]` task.

---

## Conventions

### 1. Naming & Structure
- **Location:** Mirror production packages under `src/test/java/`.
- **Class Naming:** `<SubjectClass>Test` or `<SubjectClass>IntegrationTest`.
- **Method Naming:** Choose one style and be consistent (e.g., `should_ReturnResult_WhenCondition()` or `givenContext_whenAction_thenResult()`).
- **Structure:** Use Arrange-Act-Assert (AAA) blocks.

### 2. TDD Red Phase Rigor
- **The Marker:** Every test class must have the `[TDD RED PHASE]` comment block listing the pending `[DEVELOP]` tasks.
- **Builders:** Use the Test Data Builder pattern (located in `testutil/`) for complex entities.
- **Fail First:** Ensure tests express expected behavior that currently fails (e.g., calling a method that doesn't exist or returns null).

### 3. Scenario Coverage
Ensure every `[TEST]` task covers:
- Happy Path (200/201).
- Not Found (404).
- Conflict/Duplicate (409).
- Bad Input (400).
- Business Rule Violation (403/422).
- Boundary conditions (using `@ParameterizedTest`).

## Rules
- **No Production Code:** Never modify `src/main/java/` during this phase.
- **AssertJ:** Use `assertThat()` and `assertThatThrownBy()` for all assertions.
- **Disabled Tests:** If a scenario cannot be tested without a dependency, use `@Disabled("Depends on TASK-ID")`.
