---
name: implement-mapper
description: "Implements entity<->DTO mappers (MapStruct or static). Use when a [DEVELOP] task converts between persistence and API types."
---

# Implement Mapper Skill

Use this skill when implementing object-to-object mapping, typically Entity ↔ DTO.

## Mapper Mandates

- **MapStruct Preference:** Use MapStruct for boilerplate mappings. Before adding MapStruct code, verify `build.gradle.kts` contains `org.mapstruct:mapstruct` in `dependencies`. If missing, add:
  ```kotlin
  implementation("org.mapstruct:mapstruct:1.5.5.Final")
  annotationProcessor("org.mapstruct:mapstruct-processor:1.5.5.Final")
  ```
- **Configuration:** Use `@Mapper(componentModel = "spring")`.
- **Naming:** Follow `[EntityName]Mapper` convention.
- **Manual Mapping:** For complex types like Spring `Page<T>`, implement manual mapping logic in the Mapper or Controller if MapStruct is insufficient.
- **Bidirectional:** Ensure both `toEntity` and `toResponse` methods are provided if the task requires it.

## Example

```java
@Mapper(componentModel = "spring")
public interface VoterMapper {
    VoterResponse toResponse(Voter voter);
    List<VoterResponse> toResponseList(List<Voter> voters);

    default PageVoterResponse toPageResponse(Page<Voter> page) {
        var response = new PageVoterResponse();
        response.setContent(toResponseList(page.getContent()));
        response.setTotalElements(page.getTotalElements());
        // ... set other page fields
        return response;
    }
}
```
