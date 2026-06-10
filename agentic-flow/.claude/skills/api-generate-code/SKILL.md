---
name: api-generate-code
description: "Applies build toolchain changes (Gradle or Maven) and runs the code generator (OpenAPI generator, protoc, ...). Use during an [API] task once the spec is authored."
---
# API Code Generation Skill

## Purpose

Procedural executor for applying build-config changes and running the code generator.
This step owns both **writing the build file** (`build.gradle.kts` or `pom.xml`) and
**running the generation task**.

> The build plugin, config block, dependencies, and non-destructive application rules
> come from the **active format skill** — specifically its non-destructive
> build-configuration section. Follow those rules exactly before running the generator.
> If the format skill shows only Gradle configuration and the project uses Maven, apply
> the equivalent Maven plugin (e.g., `openapi-generator-maven-plugin`,
> `protobuf-maven-plugin`, `cxf-codegen-plugin`) bound to `generate-sources`.

## Activation

Activate after `api-author-spec` (and optionally `api-create-skeletons`) have completed.

---

## Logic

### 1. Apply Configuration Changes
Following the active format skill's non-destructive rules:
- Read project configurations files.
- Add only the missing plugin, config block, dependencies, `sourceSets`, and task wiring.
- Do not modify existing settings.

### 2. Apply Spec File
Write the spec file staged by `api-author-spec` to disk (if not already written).

### 3. Run Generation
Execute the format-specific generation task (Gradle task name shown; on Maven the plugins
bind to `mvn generate-sources`):
- **OpenAPI:** run the `openApiGenerate` task
- **Protobuf:** run the `generateProto` task
- **SOAP:** run the `wsdl2java` task
- **AsyncAPI:** Skip — no generation step; bindings are resolved at runtime.

## Rules
- **Wait for Output:** Always wait for the command to finish before handing off to `api-verify-output`.
- **Log Errors:** Capture full output for diagnosis in the verification phase.
- **Format-skill-guided:** Build-config changes come from the active format skill, not from this skill.
