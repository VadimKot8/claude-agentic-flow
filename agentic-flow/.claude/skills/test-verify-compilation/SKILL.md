---
name: test-verify-compilation
description: "Confirms new tests compile against current + generated sources. Use as the final step of a [TEST] task."
---
# Test Compilation Verification Skill

## Purpose
Logic for verifying that newly written tests compile against the current codebase and generated sources.

## Activation
Activate after writing test code to ensure the Red phase is structurally sound.

---

## Logic

### 1. Build Execution
- Step 1: Run `bash ./gradlew openApiGenerate` to refresh types.
- Step 2: Run `bash ./gradlew build -x test`.

### 2. Gradle Loop (Max 3 attempts)
If the build fails:
- **Diagnose:** Differentiate between test-code typos and missing implementation classes.
- **Missing Symbols/Dependencies:** If the error is "cannot find symbol" or a missing package/dependency, you MUST immediately fallback to the **Error Resolution Protocol** in `CLAUDE.md` (db_search -> web_search). Do NOT attempt to use bash, `find`, `jar`, or investigate the Gradle cache to resolve missing classes.
- **Self-Correct:** For typos or local signature mismatches, fix imports, signatures, or typos in the test code.
- **Status Mapping:**
  - `PASS`: Test code is valid.
  - `PENDING_IMPL`: Test code is valid but references non-existent implementation classes (expected).
  - `FAIL`: Unresolved compilation errors in test code after retries.

## Rules
- **Do not run tests:** Only verify compilation (`-x test`).
- **Clean State:** If errors are persistent, try `./gradlew clean` before retrying.
