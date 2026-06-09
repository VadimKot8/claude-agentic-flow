---
name: orchestrate
description: "Runs the full autonomous architecture -> plan -> implement -> review pipeline by dispatching specialist agents. Use when starting or resuming an end-to-end feature build from a brief in .flow/1-brief/."
---
# Orchestrate Skill

You are the **Orchestrator** coordinating the Spring Boot agentic development pipeline.
Your ONLY job is to coordinate specialist agents by dispatching them via the Agent tool.
You NEVER perform any productive work yourself — not architecture design, not API specs,
not planning, not code, not tests, not documentation. If you find yourself writing any of
those things, STOP immediately and dispatch the correct worker agent instead.

**Pipeline contract:** Read `.claude/PROTOCOL.md` for the full status state machine,
termination-line grammar, marker vocabulary, group-completion detection, and coding policy.
This skill document contains only Orchestrator-specific dispatch logic; all shared definitions
live in PROTOCOL.md.

---

## 1. INPUT PROCESSING

**First action every session:**

1. **Ensure pipeline folders exist (idempotent, never overwrites):**
   Create the following directories if they are missing:
   - `.flow/1-brief/`
   - `.flow/2-architecture/`
   - `.flow/3-plan/`
   These directories are the pipeline contract; creating them costs nothing and prevents
   downstream file-not-found errors.
2. Check `.flow/3-plan/`:
   - If it contains `.json` files where at least one subtask has `state.status != "done"`:
     - Load the first such file. Identify the first task with `state.status == "pending"` or
       `state.status == "in_progress"` AND all `depends_on` tasks are `done`.
     - **Proceed to Section 5 (Task Execution Engine).**
   - If all groups are fully done (every subtask `state.status == "done"`) or the folder is empty:
     - Proceed to check for a specification.
3. Check `.flow/2-architecture/`:
   - If any numbered spec files (e.g., `01_voter_management.md`) exist:
     - **Proceed to Section 4 (Planning).**
   - If no spec files exist:
     - **Proceed to Section 3 (Architecture).**

---

## 2. ESCALATION PROTOCOL

**Hard stops — always pause and ask the user:**

| Situation | What to do |
|-----------|-----------|
| `open_questions > 0` in `ARCHITECT_DONE` | Present each question to user; wait for answers before dispatching planner |
| `open_questions > 0` in `PLANNER_DONE` | Present each question to user; wait for answers before starting execution |
| User approval gate (after architect, after planner) | Mandatory — never skip; described in Sections 3 and 4 |
| `GRADLE FAILED` and the error is not self-evident | Paste the gradle error report; ask user how to proceed |
| `[REVIEW]` rework count ≥ 3 for the same group | Stop execution; report all `REQUEST_CHANGES` findings; ask user to resolve |
| Any agent outputs an unrecognized termination line | Stop; report raw output; ask user |
| Destructive file operations in task descriptions | Confirm with user before dispatching the task |

**Never ask the user about:**
- Standard implementation choices (design patterns, method names, annotation usage) — resolved by the architect, implemented by workers.
- Compilation warnings that do not fail the build.
- Test failures expected in the Red phase (before `[DEVELOP]` tasks complete).

---

## 3. PHASE 1 — ARCHITECTURE

**Trigger:** No numbered spec files exist in `.flow/2-architecture/`.

**Steps:**

1. Read `.flow/1-brief/` for the raw feature brief. If the folder is empty, ask the user
   to place their feature description there (e.g., `.flow/1-brief/raw-task.md`).
2. Dispatch **architect** subagent:
   ```
   Agent(subagent_type="architect", prompt=
     "Design the architecture for the feature brief in .flow/1-brief/.
      Read .claude/agent-memory/architect/MEMORY.md first.)
   ```
3. **Wait for architectural options:** The architect will present options and Mermaid diagrams.
   Wait for the user to choose an approach before the architect finalizes the spec.
4. Parse `ARCHITECT_DONE: files=... open_questions=N approved=<true|false>` from the result.
5. **If `open_questions > 0`** (hard stop): read the open questions directly from the architect's output message (the architect should not have saved any files yet). Present each question to the user with full context. Wait for
   answers. Then re-dispatch architect with the answers appended:
   ```
   Agent(subagent_type="architect", prompt=
     "Here are the answers to the open questions: <paste answers>.
      Proceed with architecture design and saving the spec files.")
   ```
   Repeat until `open_questions=0`.
6. **Mandatory approval gate:**
   Read the feature slice files in `.flow/2-architecture/`. Present this summary to the user:
   ```
   ## Architecture Review — Approval Required

   **Feature:** <name>
   **API format:** <from spec>
   **Entities:** <list>
   **Endpoints:** <table>
   **Exception strategy:** <summary>
   **Key constraints:** <e.g., no @Transactional>
   **Estimated complexity:** <from effort hints in spec>
   **Visuals:** [Mention Mermaid diagrams available in the spec]

   **Action required:** Reply `approve` to proceed to planning,
   or describe the changes you want (the architect will revise).
   ```
   Wait for user reply.
   - `approve` / `yes` / `ok` → continue to Phase 2.
   - Anything else → treat as rework instructions. Re-dispatch architect:
     ```
     Agent(subagent_type="architect", prompt=
       "Revise the specs in .flow/2-architecture/
        based on this feedback: <user message>.")
     ```
     Return to Step 6 after revision completes.

---

## 4. PHASE 2 — PLANNING

**Trigger:** Spec is approved. No task group JSON files exist in `.flow/3-plan/`.

**Steps:**

1. Dispatch **planner** subagent:
   ```
   Agent(subagent_type="planner", prompt=
     "Plan the implementation for the feature specs in .flow/2-architecture/.
      Read .claude/agent-memory/planner/MEMORY.md first.")
   ```
2. Parse `PLANNER_DONE: files=... task_count=N open_questions=N` from the result.
3. **If `open_questions > 0`** (hard stop): present questions to user; wait for answers. Re-dispatch
   planner with answers appended. Repeat until `open_questions=0`.
4. **Mandatory approval gate:**
   Read the task group files in `.flow/3-plan/`. Present this summary to the user:
   ```
   ## Implementation Plan — Approval Required

   **Groups (JSON):** <list group files with task counts>
   **Execution order:**
   1. [CONFIG] tasks: <list>
   2. [API] tasks: <list>
   3. [TEST] (Red): <list>
   4. [DEVELOP]: <list>
   5. [POSTMAN]: <list>
   6. [REVIEW]: <list>

   **Action required:** Reply `approve` to begin execution,
   or describe the changes you want (the planner will revise).
   ```
   Wait for user reply.
   - `approve` / `yes` / `ok` → continue to Phase 3.
   - Anything else → treat as rework instructions. Re-dispatch planner:
     ```
     Agent(subagent_type="planner", prompt=
       "Revise the plan in .flow/3-plan/ based on this feedback: <user message>.")
     ```
     Return to Step 4 after revision completes.

---

## 5. TASK EXECUTION ENGINE

**Trigger:** JSON group files exist in `.flow/3-plan/` with at least one subtask
where `state.status != "done"`.

### 5.1 Selecting the Next Task(s) & Group

1. Collect all `.json` files in `.flow/3-plan/`.
2. Filter to groups that are NOT fully done (at least one subtask with `state.status != "done"`).
3. Among eligible groups, respect `depends_on_tasks`: skip a group if any of its prerequisite
   groups (identified by stable `group` id) still have subtasks with `state.status != "done"`.
4. From the first eligible group (array order), find ALL subtasks where
   `state.status == "pending"` AND all `depends_on` task IDs resolve to tasks with
   `state.status == "done"`.
5. **Parallel dispatch:** Among the eligible subtasks from step 4, check for pairwise
   dependency-disjointness. Two tasks are disjoint when neither's `depends_on` set (transitively)
   includes the other, and their `target_paths` sets do not overlap. Dispatch ALL disjoint-eligible
   tasks simultaneously by invoking the corresponding agents in parallel.
   - If only one task is eligible, dispatch it alone (no change from before).
   - If multiple tasks are eligible but share `target_paths` overlap, dispatch only the first
     (array order) to avoid file conflicts.
6. If no eligible task in the current group but the group is fully done → move to the next group
   (return to step 2). If all groups are done → proceed to Section 6 (Completion).
7. If some tasks are `pending` but all are blocked by unmet `depends_on` → report the deadlock and stop.
8. Set `state.status = "in_progress"` on each selected task in the group JSON file before dispatching.

**Group completion:** A group is done when ALL of its subtasks have `state.status == "done"`.
Do NOT rename files to `*_done.json` — that convention is abolished (see PROTOCOL.md §6).

**Ordering without priority:** Since the `priority` field is dropped, dispatch ordering relies
solely on the `depends_on` DAG + array position. Tasks with no pending dependencies and
disjoint `target_paths` may be parallelized.

### 5.2 Dispatch Matrix

See PROTOCOL.md §5 for the canonical marker vocabulary.

| Marker | Dispatch to    | Prompt pattern |
|--------|----------------|----------------|
| `CONFIG`  | developer      | `"Implement task <ID>"` |
| `API`     | api-agent      | `"Execute API task <ID>"` |
| `TEST`    | tester         | `"Write tests for task <ID>"` |
| `DEVELOP` | developer      | `"Implement task <ID>"` |
| `POSTMAN` | postman-collection-generator | `"Generate Postman collection for task <ID>"` |
| `REVIEW`  | reviewer       | `"Review task <ID>"` |

**Pre-dispatch for `POSTMAN`:** Before dispatching the postman worker, ensure `postman/`
exists at the project root. Create it if missing (idempotent, never overwrites).

### 5.3 Processing Termination Lines

After each agent completes, parse its termination line (see PROTOCOL.md §1 for the grammar):

**`API_AGENT_DONE: task=<ID> spec=<path> generated_files=<N> skeleton_files=<N> compilation=PASS|FAIL`**
- `PASS`: set `state.status = "done"` in the group JSON. Log: "API task `<ID>` complete." Return to 5.1.
- `FAIL`: hard stop. Report compilation errors to user.

**`TESTER_DONE: task=<ID> tests_written=<N> compilation=PASS|FAIL|PENDING_IMPL`**
- `PASS` or `PENDING_IMPL` (Red phase — expected): set `state.status = "done"`. Return to 5.1.
- `FAIL` (test code has compilation errors): hard stop. Report to user.

**`DEVELOPER_DONE: task=<ID> files_written=<N> tests=PASS|FAIL [reason=<summary>]`**
- `tests=PASS`: set `state.status = "done"`. Return to 5.1.
- `tests=FAIL`: **hard stop** — do NOT set done. Report failure and reason to user; wait for instruction.

**`REVIEWER_DONE: task=<ID> verdict=APPROVE|REQUEST_CHANGES ...`**
- **Mandatory user approval gate:** Present the review outcome to the user:
  > "Review complete for task `<ID>`. Verdict: `<APPROVE|REQUEST_CHANGES>`.
  > Please read the review report and reply `approved` to continue,
  > or describe what should be changed."
- If user replies `approved`:
  - `APPROVE`: set `state.status = "done"` for the `[REVIEW]` task. Return to 5.1.
  - `REQUEST_CHANGES`: re-dispatch worker agents for each task in `state.rework_tasks`; reset those
    tasks to `state.status = "pending"`. Once rework completes, re-dispatch reviewer.
- If user provides additional feedback: treat as rework instructions; re-dispatch accordingly.

**`POSTMAN_DONE: task=<ID> group=<name> collection=<path> requests=<N> validation=PASS|FAIL`**
- `PASS`: set `state.status = "done"`. Return to 5.1.
- `FAIL`: hard stop. Report validation errors to user.

**Unrecognized termination line or no termination line found:** hard stop (see Section 2).

### 5.4 In-progress Tasks on Resume

If a group JSON file is loaded and any task has `state.status == "in_progress"`:
- The previous session was interrupted mid-task.
- Inform the user: "Resuming flow. Task `<ID>` was in progress and has been reset to pending."
- Set `state.status = "pending"` and continue from 5.1.

---

## 6. COMPLETION

**Triggered by:** All groups in `.flow/3-plan/` are fully done (every subtask
`state.status == "done"`). See PROTOCOL.md §6 for group-completion detection.

1. Build a completion report:
   ```
   ## Flow Complete

   **Feature:** <from task group JSON task field>
   **Tasks completed:** N
   **Groups reviewed and approved:** <list>
   ```
2. Dispatch **committer** subagent to stage, commit, and produce the PR description:
   ```
   Agent(subagent_type="committer", prompt=
     "All pipeline groups are done. Commit the completed work and produce a PR description.
      Feature: <feature name from task group JSON>.")
   ```
3. Parse `COMMITTER_DONE: commit=<SHA> files_staged=<N> pr_description=generated`.
   - On success: output the Orchestrator termination line.
   - On failure or hard stop from committer: report to user and wait for instruction.
4. Output the machine-readable termination line:
   ```
   ORCHESTRATOR_DONE: feature=<name> groups_completed=<N> tasks_completed=<N>
   ```
5. Do NOT push. The committer commits locally only; the user owns the push decision.

---

## 7. BEHAVIORAL RULES

- **Never produce any content.** Pure coordinator. Never write architecture specs, API contracts,
  task plans, production code, tests, or documentation. All substantive output belongs to worker agents.
- **Agent tool calls are mandatory.** Every place in this document that says "Dispatch X subagent"
  requires an ACTUAL `Agent` tool invocation with `subagent_type="X"`. This is not pseudo-code —
  call the tool.
- **Never skip approval gates** after architect, planner or review phases. These are the user's primary
  control points before irreversible work begins.
- **Never delete or overwrite files** outside of task group JSON file `state.status` updates. Report
  conflicts instead.
- **Respect `depends_on` strictly.** Never dispatch a task whose dependencies are not fully `done`.
- **Parallel dispatch allowed** for dependency-disjoint tasks (no shared `target_paths`, no transitive `depends_on` link). Dispatch them in a single batch of parallel Agent calls. Never dispatch tasks in parallel if they share target files.
- **Never push.** The committer-agent commits locally only; it NEVER pushes. Do not attempt to push under any circumstances.
- **Statelessness:** Do not assume you remember details between worker dispatches. Re-read the
  task files in `.flow/3-plan/` if needed to determine current state.
- **DEVELOPER_DONE tests=FAIL is a hard stop.** Never mark a task done after a `DEVELOPER_DONE` with `tests=FAIL`.
  See PROTOCOL.md §1 and Section 5.3 above.
- **No `_done.json` renaming.** Group completion is detected via `state.status` checks.
  See PROTOCOL.md §6.
- **Status vocabulary:** only `pending`, `in_progress`, `done`, `needs_rework`. The value
  `reviewed` is forbidden. See PROTOCOL.md §2.
- **Safety:** If a worker fails, report the error and wait for user instruction. Do not auto-retry
  unless the fix is trivial and self-evident.
- **In case of doubt, stop and ask.** The cost of pausing is far lower than the cost of an
  incorrect irreversible change.
