# PROTOCOL.md — Agentic Pipeline Contract

This is the **single source of truth** for the Java + Spring (Spring Framework 6, Java 17+)
agentic development pipeline.
All agents and the Orchestrator read this file instead of restating the protocol.

---

## Termination-Line Grammar

Every agent ends its session with a machine-readable termination line on its own line.
The Orchestrator parses these lines to drive the state machine.

| Agent | Termination line |
|-------|-----------------|
| architect    | `ARCHITECT_DONE: files=<comma-sep> tier=<MICRO\|STANDARD\|MAJOR> open_questions=<N> approved=<true\|false>` |
| planner      | `PLANNER_DONE: files=<comma-sep> task_count=<N> open_questions=<N>` |
| api-agent    | `API_AGENT_DONE: task=<ID> spec=<path> generated_files=<N> skeleton_files=<N> compilation=PASS\|FAIL` |
| tester       | `TESTER_DONE: task=<ID> tests_written=<N> compilation=PASS\|FAIL\|PENDING_IMPL` |
| developer    | `DEVELOPER_DONE: task=<ID> files_written=<N> tests=PASS\|FAIL [reason=<summary>]` |
| reviewer     | `REVIEWER_DONE: task=<ID> verdict=APPROVE\|REQUEST_CHANGES critical=<N> major=<M> minor=<K> rework_tasks=<comma-sep or "none">` |
| postman-collection-generator | `POSTMAN_DONE: task=<ID> group=<group_id> collection=<path> requests=<N> validation=PASS\|FAIL` |
| committer    | `COMMITTER_DONE: commit=<short-SHA> files_staged=<N> pr_description=generated` |
| Orchestrator | `ORCHESTRATOR_DONE: feature=<name> groups_completed=<N> tasks_completed=<N>` |

**Rules:**
- Termination lines are emitted verbatim; no prose surrounds them.
- Unknown or missing termination lines trigger a hard stop (Orchestrator asks user).
- `DEVELOPER_DONE` with `tests=FAIL` is a **hard stop** — the task is NOT marked done.

---

## Status State Machine

Task statuses (`status`) follow this finite state machine:

```
pending → done
   ↑
needs_rework (reset to pending by Orchestrator on rework dispatch)
```

| Status | Set by | Meaning |
|--------|--------|---------|
| `pending` | planner (initial); Orchestrator (rework reset) | Not yet started, or awaiting rework |
| `done` | Orchestrator (after successful termination line) | Successfully completed |
| `needs_rework` | reviewer (on REQUEST_CHANGES) | Failed review; awaits rework |

**Single-writer rule:** worker agents NEVER modify task status. The Orchestrator is the only
writer of `done` and the only agent that resets `needs_rework` tasks back to `pending` before
re-dispatch. The reviewer is the only writer of `needs_rework`. A task keeps `pending` for the
whole time it is being worked — there is no intermediate status.

**Forbidden statuses:** `reviewed` and `in_progress` — these values MUST NOT be used.
Reviewer writes the verdict into the `review_verdict` field; the Orchestrator sets `done`.

---

## Task-Group JSON Schema Summary

The full machine-checkable schema is at `.claude/agents/schemas/task-group.schema.json`.

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
  "files": {
    "touches": ["src/main/java/.../VoterServiceImpl.java"],
    "depends_on_types": ["com.example.voting.voter.VoterMapper", "<gen> CreateVoterRequest"]
  },
  "instruction": [
    "Implement VoterService.blockVoter(UUID id)",
    "Map BLOCKED status changes via VoterMapper"
  ],
  "acceptance_criteria": [
    "No @Transactional on service",
    "Returns HTTP 409 with ErrorResponse when voter is BLOCKED"
  ],
  "api_format": "openapi",
  "user_stories_covered": ["As a voter, I want to register so that I can vote"],
  "spec_ref": {
    "doc": ".flow/2-architecture/01_voter_management.md",
    "sections": ["## Service Layer", "## Exception Strategy"]
  },
  "status": "pending"
}
```

`status`, `review_verdict`, and `rework_tasks` are **flat, top-level fields** on the subtask —
there is no `state` wrapper object. `review_verdict` and `rework_tasks` are absent until the
reviewer writes them.

### Field presence rules

| Field | Present on |
|-------|-----------|
| `api_format` | `[API]` tasks **only** |
| `user_stories_covered` | `[REVIEW]` tasks **only** |
| `acceptance_criteria` | `[DEVELOP]`, `[TEST]` tasks (non-empty); `[]` on others |
| `instruction` | All tasks |
| `files.touches` / `files.depends_on_types` | All tasks (`[]` if none) |
| `review_verdict` | `[REVIEW]` tasks, set by reviewer only |
| `rework_tasks` | `[REVIEW]` tasks after REQUEST_CHANGES only |

---

## Marker Vocabulary

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

## Group Completion Detection

A group is **done** when **all** of its subtasks have `status == "done"`.

Group completion is detected by inspecting the group's subtask array.

---

## Dependency Resolution

- **Within a group:** `depends_on` lists sibling task IDs.
- **Across groups:** `depends_on` references cross-group task IDs by their `<GROUP>-NNN` format.
- **Group ordering:** `depends_on_tasks` at the group level lists **stable group ids** (the `group` field), never filenames.
- **Dispatch ordering:** tasks with no pending `depends_on` items are eligible for dispatch.
- **Parallel dispatch:** dependency-disjoint tasks (no shared `files.touches`, no transitive `depends_on` link) may be dispatched in a single parallel batch. Tasks with overlapping `files.touches` must be dispatched sequentially.
