---
name: test-select-slice
description: "Maps a scenario to the narrowest Spring test slice (@WebMvcTest/@DataJpaTest/@SpringBootTest). Use when choosing the test type for a [TEST] task."
---
# Spring Boot Test Slice Selection Skill

## Purpose
Logic for mapping business scenarios to the most efficient and appropriate Spring Boot testing slice.

## Activation
Activate when designing the test structure for a task.

---

## Selection Matrix

| Scenario Type | Test Slice | Key Annotation |
|---------------|------------|----------------|
| Service / domain logic | Unit test | `@ExtendWith(MockitoExtension.class)` |
| Controller (HTTP contract) | Web slice | `@WebMvcTest(XController.class)` |
| Full HTTP + application context | Integration | `@SpringBootTest` + `@AutoConfigureMockMvc` |
| JPA queries / DB constraints | Persistence slice | `@DataJpaTest` |
| JPA with real DB (Postgres) | Persistence + Testcontainers | `@DataJpaTest` + `@AutoConfigureTestDatabase(replace=NONE)` |
| Security rules / roles | Security slice | `@WebMvcTest` + `@WithMockUser` |
| JSON serialization | JSON slice | `@JsonTest` |
| Full black-box system test | Full integration | `@SpringBootTest(webEnvironment=RANDOM_PORT)` |

## Rules
- **Narrowest Slice Wins:** Always prefer `@WebMvcTest` or `@DataJpaTest` over `@SpringBootTest`. Use `@SpringBootTest` only when a full context (e.g., cross-module interaction) is strictly required.
- **Efficiency:** Minimize context restarts by choosing slices that only load the necessary beans.
