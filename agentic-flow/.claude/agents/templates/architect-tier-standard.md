# Architect Output Template — Tier: STANDARD

Use this template when the task changes **4+ classes within an existing bounded context**,
and/or adds a new entity, service, or repository — but does NOT introduce a new bounded
context and does NOT define a new external API contract.

Every `## Heading` is a stable anchor the planner may cite in `spec_ref.sections`. Omit any
optional section entirely if it does not apply — do not leave an empty header or write "N/A".

```markdown
# Feature Analysis: [Feature Name]

## Context
[2-3 sentences: what this task does, its domain context, and why it's needed. Tier: STANDARD.]

## Architectural Decision
- **Summary:** [Brief description of the chosen approach]
- **Pros:** [List of advantages]
- **Cons:** [List of trade-offs, if any]
- **Selection Rationale:** [Why this approach — only if real alternatives were considered]

## Requirements
### Functional Requirements
- [Detailed list with clear acceptance criteria per requirement]

### Non-Functional Requirements (optional)
- [Only if performance, security, or scalability concerns apply]

## What Changes
### Paths to changing/made files
| File | Change |
|------|--------|

### API Design (optional — only if endpoints are added/changed)
[Endpoints table: method, path, description, success code, error codes]

### Database Changes (optional — only if entities/schema change)
[Entity design, schema modifications, unique constraints, indexes, relationships]

### Backend Services (optional)
[Services, business logic, domain invariants affected]

### Exception Strategy (optional — only if new error cases are introduced)
[Custom exceptions, @ControllerAdvice mappings, HTTP status decisions]

## Testing Strategy
- Unit tests for [service layer / domain logic]
- Integration tests (MockMvc) for [REST endpoints, if any]

## Risks & Mitigations (optional — only if a non-trivial risk exists)
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|

## Implementation Order
[Phased breakdown: Tests Red phase → Implementation → Review]
```

Save to `.flow/2-architecture/<number>_<feature name>.md`.