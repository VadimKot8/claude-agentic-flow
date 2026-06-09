# PROTOCOL.md — Agentic Pipeline Contract

This is the **single source of truth** for the Spring Boot agentic development pipeline.
All agents and the Orchestrator read this file instead of restating the protocol.

---

## 1. Termination-Line Grammar

Every agent ends its session with a machine-readable termination line on its own line.
The Orchestrator parses these lines to drive the state machine.

| Agent | Termination line |
|-------|-----------------|
| architect    | `ARCHITECT_DONE: files=<comma-sep> open_questions=<N> approved=<true\|false>` |
| planner      | `PLANNER_DONE: files=<comma-sep> task_count=<N> open_questions=<N>` |
| api-agent    | `API_AGENT_DONE: task=<ID> spec=<path> generated_files=<N> skeleton_files=<N> compilation=PASS\|FAIL` |
| tester       | `TESTER_DONE: task=<ID> tests_written=<N> compilation=PASS\|FAIL\|PENDING_IMPL` |
| developer    | `DEVELOPER_DONE: task=<ID> files_written=<N> tests=PASS\|FAIL [reason=<summary>]` |
| reviewer     | `REVIEWER_DONE: task=<ID> verdict=APPROVE\|REQUEST_CHANGES critical=<N> major=<M> minor=<K> rework_tasks=<comma-sep or "none">` |
| committer    | `COMMITTER_DONE: commit=<short-SHA> files_staged=<N> pr_description=generated` |
| Orchestrator | `ORCHESTRATOR_DONE: feature=<name> groups_completed=<N> tasks_completed=<N>` |

**Rules:**
- Termination lines are emitted verbatim; no prose surrounds them.
- Unknown or missing termination lines trigger a hard stop (Orchestrator asks user).
- `DEV_DONE` with `tests=FAIL` is a **hard stop** — the task is NOT marked done.

---

## 2. Status State Machine

Task statuses (`state.status`) follow this finite state machine:

```
pending → in_progress → done
                      ↓
                needs_rework → in_progress → done
```

| Status | Set by | Meaning |
|--------|--------|---------|
| `pending` | planner (initial) | Not yet started |
| `in_progress` | worker agent (session start) | Currently being worked |
| `done` | Orchestrator (after successful termination line) | Successfully completed |
| `needs_rework` | reviewer (on REQUEST_CHANGES) | Failed review; awaits rework |

**Forbidden status:** `reviewed` — this value MUST NOT be used. Reviewer writes the verdict into `state.review_verdict`; the Orchestrator sets `done` after user approval.

---

## 3. Task-Group JSON Schema Summary

The full machine-checkable schema is at `.claude/schemas/task-group.schema.json`.

### Group level

```json
{
  "task": "<Human group name>",
  "group": "<stable_snake_case_id>",
  "summary": "<what this group achieves>",
  "depends_on_tasks": ["<stable group id — never a filename>"],
  "subtasks": [ ... ]
}
```

### Subtask level

```json
{
  "id": "<GROUP>-NNN",
  "title": "<short imperative>",
  "marker": "CONFIG|API|DEVELOP|TEST|POSTMAN|REVIEW",
  "depends_on": ["<sibling or cross-group task ids>"],
  "skills": ["implement-service"],
  "target_paths": ["src/main/java/.../VoterServiceImpl.java"],
  "produces": ["com.example.voting.voter.VoterServiceImpl"],
  "consumes": ["com.example.voting.voter.VoterMapper", "<gen> CreateVoterRequest"],
  "instruction": "<what to build — instruction ONLY, no acceptance criteria here>",
  "constraints": ["No @Transactional on service", "409 via real DB constraint"],
  "acceptance_criteria": ["Returns HTTP 409 with ErrorResponse when voter is BLOCKED"],
  "api_format": "openapi",
  "user_stories_covered": ["As a voter, I want to register so that I can vote"],
  "spec_ref": {
    "doc": ".flow/2-architecture/01_voter_management.md",
    "sections": ["## Service Layer", "## Exception Strategy"]
  },
  "state": {
    "status": "pending",
    "review_verdict": null,
    "rework_tasks": []
  }
}
```

### Field presence rules

| Field | Present on |
|-------|-----------|
| `api_format` | `[API]` tasks **only** |
| `user_stories_covered` | `[REVIEW]` tasks **only** |
| `acceptance_criteria` | `[DEVELOP]`, `[TEST]` tasks (non-empty); `[]` on others |
| `instruction` | All tasks |
| `constraints` | All tasks (empty array if none) |
| `produces` | All tasks (`[]` if nothing new is created) |
| `consumes` | All tasks (`[]` if no prior types needed) |

---

## 4. Marker Vocabulary

Markers are stored as **bare tokens** (no brackets) in JSON. The Orchestrator dispatch matrix maps each token to its worker.

| JSON value | Display | Worker |
|------------|---------|--------|
| `CONFIG`  | `[CONFIG]`  | developer |
| `API`     | `[API]`     | api-agent |
| `TEST`    | `[TEST]`    | tester |
| `DEVELOP` | `[DEVELOP]` | developer |
| `POSTMAN` | `[POSTMAN]` | postman-collection-generator |
| `REVIEW`  | `[REVIEW]`  | reviewer |

---

## 5. Group Completion Detection

A group is **done** when **all** of its subtasks have `state.status == "done"`.

Group completion is detected by inspecting the group's subtask array.

---

## 6. Dependency Resolution

- **Within a group:** `depends_on` lists sibling task IDs.
- **Across groups:** `depends_on` references cross-group task IDs by their `<GROUP>-NNN` format.
- **Group ordering:** `depends_on_tasks` at the group level lists **stable group ids** (the `group` field), never filenames.
- **Dispatch ordering:** tasks with no pending `depends_on` items are eligible for dispatch.
- **Parallel dispatch:** dependency-disjoint tasks (no shared `target_paths`, no transitive `depends_on` link) may be dispatched in a single parallel batch. Tasks with overlapping `target_paths` must be dispatched sequentially.
