# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.
It is structured in two sections: **Framework Rules** (portable across projects) and
**Project-Specific Settings** (current project only).

---

# PART 1 — Framework Rules

These rules apply to every project using this agentic pipeline framework.
Do NOT remove or modify them when adopting the framework in a new project.

## Agent Outputs

**All outputs from any agent to files MUST be in English and in a readable format.**

## Build Tool Restrictions

- **It is strictly prohibited** for any agent or sub-agent to read the build tool's local
  cache/repository folder (Gradle: `~/.gradle/caches`, `%USERPROFILE%\.gradle\caches`;
  Maven: `~/.m2/repository`, `%USERPROFILE%\.m2\repository`) or to run any command whose sole
  purpose is checking/listing dependencies (e.g., `./gradlew dependencies`,
  `./gradlew dependencyInsight`, `mvn dependency:tree`, `mvn dependency:list`).

## Build Task Vocabulary

The project may use **Gradle** or **Maven**. Detect the build tool from the files present:
`build.gradle.kts` / `build.gradle` → Gradle; `pom.xml` → Maven. Whenever an agent or skill
says "run the X task", it means:

| Phrase | Gradle | Maven |
|--------|--------|-------|
| run build task | `./gradlew build` | `mvn verify` |
| run compile task | `./gradlew compileJava` | `mvn compile` |
| run test task | `./gradlew test` | `mvn test` |
| run a single test class | `./gradlew test --tests "<fqcn>"` | `mvn test -Dtest=<ClassName>` |
| run code-generation task | `./gradlew openApiGenerate` (or format-specific task) | `mvn generate-sources` |
| run coverage task | `./gradlew jacocoTestReport jacocoTestCoverageVerification` | `mvn jacoco:report jacoco:check` |

If the project defines its own commands in `## Build Commands (reference)` (Part 2 below),
those take precedence.

## Error Resolution Protocol

When a stacktrace or build error indicates that a class, interface, annotation, or other symbol
has been **moved, renamed, or removed** in a newer version of a framework, language, or tool —
or when any other dependency/API error occurs — the agent **MUST** follow this protocol
**linearly and without deviation**:

**Step 0 — Determine the resolution mode:**
Check whether the `mcp__web-search` MCP server is connected (its tools `mcp__web-search__db_search`
and `mcp__web-search__web_search` are available).
- If it **is connected**, follow **Mode A (MCP search)** below.
- If it **is NOT connected**, follow **Mode B (internal tools fallback)** below.

### Mode A — MCP search (mcp__web-search is connected)

**Query Format Requirement:**
Before searching, you MUST formulate your query to ask about the dependency first. Use this exact format:
`what dependency should be for <Framework name> <Framework version> in case of problem with <name of class / description of problem>`
*(Examples: "what dependency should be for Spring Boot 4.0.5 in case of problem with class WebMvcTest", "what dependency should be for Spring Boot 4.0.5 in case of problem with Flyway migration")*

1. **Attempt 1:** Run `mcp__web-search__db_search` using the required query format.
   If the result is relevant, apply the fix and check the result. If it works, stop.
2. **Attempt 2:** If Attempt 1 was not relevant or failed, **immediately** run
   `mcp__web-search__web_search` with the exact same query. Try to apply the fix and check the result. No Bash commands or other investigation is permitted before this step.
3. **Attempt 3:** If Attempt 2 failed, rephrase the query (describe the problem in different words) and repeat
   with `mcp__web-search__web_search`. Try to apply the fix and check the result.
4. **Attempt 4:** If Attempt 3 failed, rephrase again and retry `mcp__web-search__web_search`. Try to apply the fix and check the result.
5. **Stop:** After 4 attempts without a solution, **hard stop, explain to the user the problem and ask the user to fix**.
   Do not guess or apply unverified fixes.

### Mode B — Internal tools fallback (mcp__web-search is NOT connected)

Attempt to resolve the error using your internal tools and knowledge
(reading project files, adjusting dependencies/configuration, applying a candidate fix and
verifying it with the compile/test task). The Build Tool Restrictions above still apply.

- An **attempt** = one candidate fix applied and verified by running the compile/test task.
- **Maximum 4 attempts.** After 4 attempts without a solution, **hard stop, explain to the user
  the problem and ask the user to fix**. Do not guess or apply further unverified fixes.
- The CRITICAL RULES below do NOT apply in this mode.

**CRITICAL RULES (Mode A only) — violations are protocol breaches:**
- **Do NOT run investigation commands (file searches, cache inspection, ad-hoc scripts) between
  protocol steps.** Each step must be executed immediately after the previous one. The ONLY
  permitted action between steps is applying the candidate fix and running the compile/test task
  to verify it ("check the result").
- **Do NOT skip web search because db_search seemed irrelevant.** The next step after db_search
  is ALWAYS web_search — no exceptions.
- Direct web search via Bash, curl, or any other tool is **strictly prohibited** — use only
  the MCP web-search tools above.

## Agent Memory Protocol

Each agent uses its dedicated memory file at `.claude/agent-memory/<agent-name>/MEMORY.md`.
If agent folder or `MEMORY.md` file is not exist in `.claude/agent-memory` folder agent should create it. 

### Memory Structure

The file MUST be divided into two distinct sections:

#### 1. Static Memory
- **Purpose:** Long-term storage for self-improvement and project-specific persistence.
- **Content:** Save important information for future use, such as specific patterns discovered,
  user feedback on coding style, or "lessons learned" from reworks requested by the user.
- **Format:** `YYYY-MM-DD: <Short Fact or Instruction>`

#### 2. Temp Context
- **Purpose:** Short-term continuity for interrupted tasks.
- **Content:** If a task is interrupted (due to errors, tool failures, or turn limits), the agent
  must record the current state, progress, and next steps here.
- **Cleanup:** This section should be cleared or marked as "None" once the specific task is
  successfully completed.

### Operational Rules

- **Pre-flight:** Always read the memory file at the start of a task.
- **Updates:** Use Edit or Write to update sections.
- **Brevity:** Keep entries concise. Do not store large blocks of code or logs.
- **Exclusion:** Do not duplicate information found in `CLAUDE.md` or project-level documentation.
- **Comments:** Do not put comments in obvious places. Comment ONLY where something is not obvious.
- **Naming:** Always use self-explanatory names for classes, variables, methods.
  Name should be no longer than 40-50 characters.

## Orchestration

Use `/orchestrate` to run the full autonomous agentic pipeline
(architecture → planning → implementation → review → commit).
The Orchestrator follows the skill directly, dispatching each worker agent via the Agent tool
so their output is visible in the conversation.

For full pipeline documentation, see `.claude/README.md`.
For the shared protocol (termination-line grammar, status state machine, task schema), see `.claude/PROTOCOL.md`.

---

# PART 2 — Project-Specific Settings

These settings are specific to the project.
Replace or update these when adopting the framework for a different project.

## Project Stack

- Java 17+
- Spring Framework 6

## Coding Preferences

## Build Commands (reference)

<!-- Fill in the project's exact commands so agents resolve "run build task" deterministically.
Examples:
- Build: `mvn verify` or `./gradlew build`
- Test: `mvn test` or `./gradlew test`
-->


