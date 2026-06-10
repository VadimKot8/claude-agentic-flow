# Architect Output Template — Tier: MICRO

Use this template when the task touches **up to 3 classes**, introduces no new entities,
no new external API contract, and stays within an existing bounded context.

Keep every section short — a developer should be able to start implementing after reading
just `## Architectural Decision` and `## What Changes`.

```markdown
# Feature Analysis: [Feature Name]

## Context
[1-2 sentences: what this task does and why. Tier: MICRO.]

## Architectural Decision
- **Summary:** [What will change and the approach taken]
- **Rationale:** [Why this approach — only if a real alternative existed; omit if obvious]

## What Changes
| File | Change |
|------|--------|
| `path/to/Class.java` | [created / modified — one line description] |

## Implementation Order
1. [Step 1]
2. [Step 2]
```

Save to `.flow/2-architecture/<number>_<feature name>.md`.