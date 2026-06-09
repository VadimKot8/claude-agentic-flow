---
name: implement-repository
description: "Implements Spring Data JPA repositories and custom queries. Use when a [DEVELOP] task needs a data-access interface."
---

# Implement Repository Skill

Use this skill when implementing the data access layer.

## Repository Mandates

- **Interface-based:** Extend `JpaRepository<Entity, ID>`.
- **Naming:** Follow `[EntityName]Repository` convention.
- **Queries:**
    - Use query methods for simple lookups (e.g., `findByEmail`).
    - Use `@Query` with JPQL for complex logic.
    - Avoid native queries unless strictly necessary for performance or platform-specific features.
- **Transactions:** Do NOT put `@Transactional` on repository interfaces. Transaction boundaries belong in the Service layer.
- **Pagination:** Use `Pageable` and return `Page<T>` for list endpoints.

## Example

```java
public interface VoterRepository extends JpaRepository<Voter, UUID> {
    Optional<Voter> findByName(String name);

    @Query("SELECT v FROM Voter v WHERE v.status = :status")
    Page<Voter> findByStatus(@Param("status") VoterStatus status, Pageable pageable);
}
```
