# Architect Output Template — Tier: MAJOR

Use this template for a **new bounded context/module**, OR any task that defines/changes
a **new external API contract** (REST/OpenAPI, gRPC/protobuf, AsyncAPI, SOAP), OR a
cross-cutting change spanning multiple existing bounded contexts.

Every `## Heading` is a stable anchor the planner may cite in `spec_ref.sections` — never cite
by line number. Use consistent, canonical heading names across revisions and do not rename
headings after the planner has cited them. Omit any optional section entirely if it does not
apply — do not leave an empty header or write "N/A".

```markdown
# Feature Analysis: [Feature Name]

## Context
[2-3 sentences: what this task does, its domain context, and its business value. Tier: MAJOR.]

## Executive Summary
[2-3 sentences describing the feature, its domain context, and its business value]

## Architectural Decision
### [Selected Approach Name]
- **Summary:** [Brief description of the chosen approach]
- **Pros:** [List of advantages]
- **Cons:** [List of trade-offs/disadvantages]
- **Selection Rationale:** [Why this approach was chosen over alternatives]

## Visualizations (Mermaid) (optional — only if it adds value)
[Insert Mermaid diagrams here — ER diagrams, sequence diagrams, component diagrams]

## Requirements
### Functional Requirements
- [Detailed list with clear acceptance criteria per requirement]

### Non-Functional Requirements
- [Performance, security, scalability, usability requirements]

## User Stories
- As a [actor], I want [goal] so that [benefit]
[Include 3-5 key user stories with acceptance criteria]

## What Changes
### Paths to changing/made files
| File | Change |
|------|--------|

### API Design
[Endpoints table: method, path, description, success code, error codes]
[OpenAPI contract summary]

### API Format
**Format:** <REST/OpenAPI 3.x | gRPC/protobuf | AsyncAPI 3.x | SOAP/WSDL>
**Rationale:** [one sentence — why this format was chosen over alternatives]
**Spec file path:** `<e.g. src/main/resources/openapi/voting-api.yaml>`
**Code Generator:** <OpenAPI Generator plugin (Gradle or Maven) | protoc / protobuf build plugin | WSDL-to-Java / CXF codegen | N/A — internal only>

### Database Changes (optional)
[Entity design, schema modifications, unique constraints, indexes, relationships]

### Backend Services (optional)
[Services, business logic, state machines, domain invariants]

### Exception Strategy (optional)
[Custom exceptions, @ControllerAdvice mappings, HTTP status decisions]

### Security (optional — only if raw task mentions it)
[Security configurations, OWASP Top 10 considerations]

## Testing Strategy
- Unit tests for [service layer / domain logic]
- Integration tests (MockMvc) for [REST endpoints]
- DB constraint tests using [H2 / Testcontainers]

## Monitoring and Observability (optional - if configured in the project)
[Micrometer metrics, structured logging events, Actuator endpoints, tracing spans]

## Risks & Mitigations
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|

## Dependencies
- [Libraries, other modules, infrastructure requirements]

## Implementation Order
[Phased breakdown: Foundation (optional) → API (optional) → Tests Red phase → Implementation → Review]
```

Save to `.flow/2-architecture/<number>_<feature name>.md`.