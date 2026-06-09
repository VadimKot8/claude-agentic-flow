---
name: implement-config
description: "Implements Spring @Configuration / @ConfigurationProperties beans. Use when a [DEVELOP]/[CONFIG] task adds typed configuration or beans."
---

# Implement Config Skill

Use this skill when implementing Spring `@Configuration` classes and Bean definitions.

## Config Mandates

- **Modularity:** Group related beans into specialized configuration classes (e.g., `SecurityConfig`, `WebConfig`, `JpaConfig`).
- **Bean Definitions:** Use `@Bean` for external library classes or complex setups.
- **Profiles:** Use `@Profile` for environment-specific configuration (e.g., `test`, `dev`, `prod`).
- **Properties:** Use `@ConfigurationProperties` for type-safe property binding.
- **Conditional Beans:** Use `@ConditionalOnProperty`, `@ConditionalOnClass`, etc., for flexible configurations.

## Example

```java
@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        return JsonMapper.builder()
            .findAndAddModules()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .build();
    }
}
```
