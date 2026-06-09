---
name: bootstrap
description: "Scaffolds the pipeline directory tree (.flow/1-brief, .flow/2-architecture, .flow/3-plan, postman/) and installs blank agent-memory templates for a new project. Use when starting a fresh project, resetting the framework for a new repository, or when the pipeline directories do not yet exist."
---
# Bootstrap Skill

Initializes the agentic pipeline working tree for a new project.
Run this once when dropping the framework into a new repository,
or when you want to reset to a clean state.

---

## What This Skill Does

1. **Creates missing pipeline stage directories** (idempotent — never overwrites existing files).
2. **Creates the `postman/` output directory** at the project root.
3. **Reports** what was created vs what already existed.

---

## Steps

### 1. Check prerequisites

Verify that `.flow/` does not already contain real content (i.e., non-empty `2-architecture/`
or `3-plan/` files). If it does, warn the user:

> "Pipeline already contains content in `.flow/2-architecture/` or `.flow/3-plan/`. Bootstrap
> will only create missing directories and templates — it will NOT overwrite existing files.
> Proceed? (yes/no)"

If the user confirms (or there is no existing content), continue to Step 2.

### 2. Create pipeline stage directories

Create the following directories if they do not exist (use `mkdir -p` equivalent — idempotent):

```
.flow/1-brief/
.flow/2-architecture/
.flow/3-plan/
postman/
.claude/agent-memory
```

### 3. Create brief placeholder

If `.flow/1-brief/raw-task.md` does **not** exist, create a placeholder:

```markdown
# Feature Brief

Describe the feature or application you want to build here.

Replace this file's content with your requirements before running `/orchestrate`.
```

### 4. Report

Output a summary:

```
## Bootstrap Complete

| Item | Status |
|------|--------|
| .flow/1-brief/ | created / already existed |
| .flow/2-architecture/ | created / already existed |
| .flow/3-plan/ | created / already existed |
| postman/ | created / already existed |

**Next step:** Add your feature brief to `.flow/1-brief/raw-task.md`, then run `/orchestrate`.
```

---

## What This Skill Does NOT Do

- Does NOT modify `CLAUDE.md`, `PROTOCOL.md`, or any agent/skill files.
- Does NOT overwrite existing files.
- Does NOT commit changes to git — leave that to the user.
- Does NOT configure MCP servers or Claude Code CLI settings.

---

## Prerequisites

Before bootstrapping a new project, ensure:

1. **Claude Code CLI** is installed and authenticated.
2. **MCP servers** are configured:
   - `web-search` (required by `CLAUDE.md` error protocol)
3. **Java 21** and **Gradle 9.4+** are installed.
4. The project already has a `build.gradle.kts` with Spring Boot dependencies.

See `.claude/README.md` for the full prerequisites list.
