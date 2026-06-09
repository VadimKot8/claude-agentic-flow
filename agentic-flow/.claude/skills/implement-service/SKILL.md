---
name: implement-service
description: "Implements service interfaces/impls with constructor injection, observability, and domain-exception mapping. Use when a [DEVELOP] task adds business logic."
---

# Implement Service Skill

Use this skill when implementing business logic and service orchestration.

## Service Mandates

- **Separation of Concerns:** Services should contain business logic, not HTTP or Persistence details.
- **Constructor Injection:** Always use constructor injection. Never use `@Autowired` on fields.
- **Observability:**
    - Log method entry for mutations: `log.info("action=register_voter name={}", name)`.
    - Log errors in catch blocks: `log.error("action=register_voter_failed name={}", name, e)`.
    - Use structured logging keys.
    - Increment Micrometer counters for key business events.
- **Exception Handling:**
    - Catch infrastructure exceptions (e.g., `DataIntegrityViolationException`) and rethrow as domain exceptions (e.g., `BusinessRuleViolationException` or `ConflictException`).
    - Throw `ResourceNotFoundException` when entities are missing.
- **Transactions:** Use `@Transactional` sparingly and only where multi-step atomicity is required. Prefer `@Transactional(readOnly = true)` for query methods.
- **No HTTP Types:** Do not use `HttpServletRequest`, `ResponseEntity`, or generated OpenAPI DTOs in the service layer. Services accept and return domain entities (JPA entity classes). Mapping to/from generated DTOs is the controller's responsibility, done via a Mapper.

## Example

```java
@Service
public class VoterService {
    private final VoterRepository voterRepository;
    private final MeterRegistry meterRegistry;
    private static final Logger log = LoggerFactory.getLogger(VoterService.class);

    public VoterService(VoterRepository voterRepository, MeterRegistry meterRegistry) {
        this.voterRepository = voterRepository;
        this.meterRegistry = meterRegistry;
    }

    public Voter registerVoter(String name) {
        log.info("action=register_voter name={}", name);
        var voter = new Voter();
        voter.setName(name);
        try {
            var saved = voterRepository.save(voter);
            meterRegistry.counter("voters.registered").increment();
            return saved;
        } catch (DataIntegrityViolationException e) {
            throw new ConflictException("DUPLICATE_VOTER", "Voter already exists");
        }
    }
}
```
