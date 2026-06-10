---
name: verify
description: "Runs the shared quality gate (compile, test suite, optional coverage check) and interprets results. Use when a developer or reviewer needs to verify that the build and tests pass before marking a task done or issuing a verdict."
---
# Verify Skill — Shared Quality Gate

Single source of truth for all build verification commands.
Used by the **developer** agent (post-implementation check) and the **reviewer** agent
(mandatory pre-verdict runtime check). Both run the same gate so results are consistent.

---

## Verification Steps

Run the following tasks **in order** (command mapping for Gradle/Maven: see `CLAUDE.md`
Build Task Vocabulary). Stop at the first failure and report it.

### Step 1 — Compile

Run the compile task (`./gradlew compileJava` or `mvn compile`).

**Pass criterion:** exit code 0, no compiler errors.
**On failure:** report the full compiler error to the caller. Do NOT proceed to Step 2.

### Step 2 — Full Test Suite

Run the test task (`./gradlew test` or `mvn test`).

**Pass criterion:** exit code 0, all tests pass (0 failures, 0 errors).
**On failure:**
- Extract the failing test names and failure messages from the build output.
- Report them in a structured block (see Output Format below).
- Do NOT proceed to Step 3.

### Step 3 — Coverage (optional, if configured)

Run the coverage task (`./gradlew jacocoTestReport jacocoTestCoverageVerification` or
`mvn jacoco:report jacoco:check`).

Run this step **only if** JaCoCo is configured in the build file.
To check: look for the `jacoco` plugin / `jacocoTestCoverageVerification` task in
`build.gradle.kts`, or the `jacoco-maven-plugin` in `pom.xml`.

**Pass criterion:** exit code 0, coverage thresholds met.
**On failure:** report which thresholds were violated (class, line, branch coverage).
This step is advisory — a coverage failure should be reported but does NOT block a DEVELOPER_DONE.
It SHOULD be reported as a Major finding in a REVIEWER_DONE.

---

## Output Format

### All passing

```
## Verification Result: PASS

| Step | Result |
|------|--------|
| Compile | PASS |
| Test suite | PASS (N tests) |
| Coverage | PASS / SKIPPED |
```

### Failure

```
## Verification Result: FAIL

| Step | Result |
|------|--------|
| Compile | PASS / FAIL |
| Test suite | FAIL |
| Coverage | PASS / FAIL / SKIPPED |

### Failing Tests

| Test class | Method | Failure message |
|-----------|--------|----------------|
| com.example.FooTest | shouldDoBar | expected: 200 but was: 404 |
```

---

## Rules for Callers

### Developer agent

After implementing a task:
1. Run Step 1 (compile). Fix any compiler errors before proceeding.
2. Run Step 2 (full test suite). If any test fails:
   - Diagnose and fix (up to 3 build loop attempts).
   - If still failing after 3 attempts: save context to memory, emit `DEVELOPER_DONE: ... tests=FAIL`, and stop.
   - **Never** emit `DEVELOPER_DONE: ... tests=PASS` when tests are failing.
3. If all tests pass: emit `DEVELOPER_DONE: ... tests=PASS`.

### Reviewer agent

Before issuing any verdict (Section 3.8 of `.claude/agents/reviewer.md`):
1. Run Step 2 (full test suite).
2. If any tests fail: add a **Critical finding** titled "Test suite failure" and force verdict to `REQUEST_CHANGES`.
3. Optionally run Step 3 (coverage) — report violations as Major findings.
4. Only issue `APPROVE` after a PASS result.

---

## Build Loop (developer agent only)

On test failure, follow this repair loop (max 3 attempts):

1. Read the failing test name and assertion message.
2. Read the production class(es) involved.
3. Identify the root cause (missing logic, wrong return value, incorrect exception).
4. Apply a targeted fix — do NOT change test code.
5. Re-run the single failing test class (`./gradlew test --tests "<failing.TestClass>"` or `mvn test -Dtest=<FailingTestClass>`) for fast feedback.
6. If the targeted test passes, run the full test task to confirm no regressions.
7. If still failing after fix attempt 3: stop, save state to memory, emit `DEVELOPER_DONE tests=FAIL`.

**Never change test code to make tests pass.** Tests define the contract; production code must conform.
