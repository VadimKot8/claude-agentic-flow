---
name: api-generate-code
description: "Applies Gradle toolchain changes and runs the code generator (openApiGenerate, protoc, ...). Use during an [API] task once the spec is authored."
---
# API Code Generation Skill

## Purpose

Procedural executor for applying Gradle changes and running the code generator.
This step owns both **writing `build.gradle.kts`** and **running the generation task**.

> The Gradle plugin, config block, dependencies, and non-destructive application rules
> come from the **active format skill** — specifically its "Applying to build.gradle.kts
> (non-destructive)" section. Follow those rules exactly before running the generator.

## Activation

Activate after `api-author-spec` (and optionally `api-create-skeletons`) have completed.

---

## Logic

### 1. Apply Gradle Changes
Following the active format skill's non-destructive rules:
- Read `build.gradle.kts`.
- Add only the missing plugin, config block, dependencies, `sourceSets`, and task wiring.
- Do not modify existing settings.

### 2. Apply Spec File
Write the spec file staged by `api-author-spec` to disk (if not already written).

### 3. Run Generation
Execute the format-specific command:
- **OpenAPI:** `./gradlew openApiGenerate`
- **Protobuf:** `./gradlew generateProto`
- **SOAP:** `./gradlew wsdl2java`
- **AsyncAPI:** Skip — no generation step; bindings are resolved at runtime.

## Rules
- **Wait for Output:** Always wait for the command to finish before handing off to `api-verify-output`.
- **Log Errors:** Capture full output for diagnosis in the verification phase.
- **Format-skill-guided:** Gradle changes come from the active format skill, not from this skill.
