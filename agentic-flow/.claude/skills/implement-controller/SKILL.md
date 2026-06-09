---
name: implement-controller
description: "Implements REST controllers wired to generated OpenAPI interfaces. Use when a [DEVELOP] task exposes an endpoint."
---

# Implement Controller Skill

Use this skill when implementing the web layer.

## Controller Mandates

- **Interface Implementation:** Always implement the generated `*Api` interface from the OpenAPI spec.
- **Thin Controllers:** Controllers should only handle routing, input validation (via annotations), and response mapping. All business logic must be in Services.
- **Constructor Injection:** Use constructor injection for Services and Mappers.
- **Response Mapping:**
    - Use `ResponseEntity` to return proper HTTP status codes.
    - Map domain entities to generated DTOs using a Mapper.
- **Validation:** Rely on `@Valid` and OpenAPI-generated constraints.
- **Pagination:** Map Spring `Page<T>` to generated `Page*Response` DTOs (often requires manual mapping as MapStruct doesn't handle `Page` well).

## Example

```java
@RestController
public class VoterController implements VotersApi {
    private final VoterService voterService;
    private final VoterMapper voterMapper;

    public VoterController(VoterService voterService, VoterMapper voterMapper) {
        this.voterService = voterService;
        this.voterMapper = voterMapper;
    }

    @Override
    public ResponseEntity<VoterResponse> registerVoter(@Valid CreateVoterRequest request) {
        var voter = voterService.registerVoter(request.getName());
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(voterMapper.toResponse(voter));
    }
}
```
