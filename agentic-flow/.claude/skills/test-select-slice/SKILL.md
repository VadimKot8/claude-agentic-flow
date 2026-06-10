---
name: test-select-slice
description: "Maps a scenario to the narrowest Spring test slice (@WebMvcTest/@DataJpaTest/@SpringBootTest). Use when choosing the test type for a [TEST] task."
---
# Spring Test Slice Selection Skill

## Purpose
Logic for mapping business scenarios to the most efficient and appropriate Spring testing slice.

## Activation
Activate when designing the test structure for a task.

---

## Selection Matrix (Spring Boot on classpath)

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

## Selection Matrix (plain Spring Framework 6 — no Boot)

| Scenario Type | Test Approach | Key Construct |
|---------------|---------------|---------------|
| Service / domain logic | Unit test | `@ExtendWith(MockitoExtension.class)` |
| Controller (HTTP contract) | Standalone MockMvc | `MockMvcBuilders.standaloneSetup(controller)` |
| Full HTTP + application context | Spring TestContext | `@SpringJUnitConfig` (+ `@WebAppConfiguration` and `MockMvcBuilders.webAppContextSetup`) |
| JPA queries / DB constraints | TestContext + embedded/Testcontainers DB | `@SpringJUnitConfig` with a test DataSource configuration |

## Rules
- **Narrowest Slice Wins:** With Boot, always prefer `@WebMvcTest` or `@DataJpaTest` over `@SpringBootTest`; without Boot, prefer plain unit tests and standalone `MockMvc` over loading a Spring context. Load a full context only when cross-module interaction is strictly required.
- **Efficiency:** Minimize context restarts by choosing slices that only load the necessary beans.
