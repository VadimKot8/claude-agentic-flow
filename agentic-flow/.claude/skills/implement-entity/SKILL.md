---
name: implement-entity
description: "Implements JPA entities, enums, value objects, and Flyway migrations to project standards. Use when a [DEVELOP] task adds or changes a persistence type."
---

# Implement Entity Skill

Use this skill when implementing the domain layer, specifically JPA entities and supporting types.

## JPA Entity Mandates

- **No Lombok:** Always use plain Java with standard getters and setters.
- **ID Strategy:** Use UUID server-generated IDs. Annotate the field with
  `@GeneratedValue(strategy = GenerationType.UUID)` and `@Column(updatable = false, nullable = false)`.
  Do NOT use `@GeneratedValue(strategy = GenerationType.IDENTITY)` or `AUTO`.
- **ID Type:** `UUID` (from `java.util.UUID`). Do NOT use `Long`.
- **Table Naming:** Always use `@Table(name = "...")` with pluralized snake_case names (e.g., `voters`, `elections`).
- **Audit Fields:** Use `OffsetDateTime` for timestamps. Use `@Column(updatable = false)` for `createdAt`.
- **Lifecycle Hooks:** Use `@PrePersist` to set `createdAt` if null. Avoid complex lifecycle logic in entities.
- **Encapsulation:** Keep fields private. Use public getters/setters.
- **Validation:** Use Bean Validation annotations (`@NotNull`, `@Size`, etc.) to match DB constraints.

## Enum Mandates

- **Persistence:** Always use `@Enumerated(EnumType.STRING)` for enum fields in entities.
- **Location:** Keep enums in the same package as the entity they primarily support, or a `model` subpackage.

## DB Migration (Flyway)

- **Tool:** Flyway **only** — Liquibase is not used in this project.
- **Location:** `src/main/resources/db/migration/`
- **Naming:** `V<N>__<description>.sql` (e.g., `V1__create_voters.sql`).
- **Constraints:** Define primary keys, foreign keys, and unique constraints in SQL.
- **ID column type:** `UUID` (not `BIGSERIAL`). Example: `id UUID NOT NULL`.
- **Other types:** `VARCHAR(N)` for strings, `TIMESTAMPTZ` for `OffsetDateTime`.

## Example

```java
@Entity
@Table(name = "voters")
public class Voter {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(updatable = false, nullable = false)
    private UUID id;

    @Column(nullable = false, length = 255)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private VoterStatus status = VoterStatus.ACTIVE;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    void prePersist() {
        if (createdAt == null) createdAt = OffsetDateTime.now();
    }

    // Getters and Setters
}
```

Corresponding Flyway migration:

```sql
CREATE TABLE voters (
    id          UUID        NOT NULL,
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ  NOT NULL,
    PRIMARY KEY (id)
);
```
