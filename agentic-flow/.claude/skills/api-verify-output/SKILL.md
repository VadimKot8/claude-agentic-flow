---
name: api-verify-output
description: "Compiles and structurally checks generated sources. Use as the final step of an [API] task."
---
# API Output Verification Skill

## Purpose

Procedural executor for the final verification step. Compiles the project and checks the
generated output against the **active format skill's verification checklist**.

> **Not a format reference.** This skill does not define what to check.
> The verification checklist (expected file paths, interface names, field names) comes from
> the active format skill. Always have the format skill active before running this skill.

## Activation

Activate after `api-generate-code` has run.

---

## Logic

### 1. Compilation
Run `./gradlew compileJava`.

### 2. Retry Loop (Max 3 attempts)
If failure occurs:
1. **Diagnose:** Read error output (syntax error, missing dependency, etc.).
2. **Fix:** Update spec or build config — never hand-edit generated sources.
3. **Retry:** Re-run `api-generate-code`, then re-run this skill.
4. **Escalate:** Stop after 3 failed attempts and report errors verbatim.

### 3. Structural Check
Using the **active format skill's verification checklist**, confirm:
- Generated files exist in the expected output directories.
- Names match the format skill's naming rules (e.g., `operationId`-based method names, tag-based interface names).
- DTO/message fields match spec property names.

## Rules
- **Fix the Source:** If generated code is wrong, fix the **spec**, not the generated code.
- **Clean Build:** Try `./gradlew clean` before re-running if errors persist unexpectedly.
- **Format-skill-guided:** What to verify (paths, names, field shapes) comes from the active format skill, not from this skill.
