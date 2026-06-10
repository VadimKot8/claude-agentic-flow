---
name: api-asyncapi
description: "Use when the task requires authoring an AsyncAPI 3.x event-driven spec, configuring Spring Cloud Stream Kafka bindings, or verifying async message contracts for Kafka/AMQP/MQTT channels."
---

# AsyncAPI Format Skill

## When to Use

Activate when the task description contains any of: AsyncAPI, event, Kafka, AMQP, MQTT, topic,
channel, message broker, publish, subscribe, produce, consume, event-driven, stream.

---

## Spec Conventions

### File Structure (AsyncAPI 3.0)

```yaml
asyncapi: "3.0.0"
info:
  title: <Project> Events
  version: "1.0.0"
  description: Event-driven API for <domain>

servers:
  kafka:
    host: localhost:9092
    protocol: kafka
    description: Local Kafka broker

channels:
  <channel-name>:                     # kebab-case
    address: <topic-name>             # dot-separated, matches Kafka topic name
    messages:
      <MessageName>:
        $ref: '#/components/messages/<MessageName>'

operations:
  <operationId>:                      # camelCase
    action: send                      # or receive
    channel:
      $ref: '#/channels/<channel-name>'
    messages:
      - $ref: '#/channels/<channel-name>/messages/<MessageName>'

components:
  messages:
    <MessageName>:
      payload:
        $ref: '#/components/schemas/<MessageName>'
  schemas:
    <MessageName>:
      type: object
      required: [field1, field2]
      properties:
        field1: { type: string }
        field2: { type: integer, format: int64 }
```

### Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Channel names | kebab-case | `voter-registered`, `election-started` |
| Topic names (Kafka) | dot-separated with domain prefix | `voting.voter.registered` |
| Message names | PascalCase + "Event" suffix | `VoterRegisteredEvent`, `ElectionStartedEvent` |
| Operation IDs | camelCase verb+noun | `publishVoterRegistered`, `receiveElectionStarted` |
| Schema property names | camelCase | `voterId`, `occurredAt` |
| Server names | lowercase | `kafka`, `rabbitmq` |

### Required Fields in All Event Schemas

Every event message schema must include:

```yaml
eventId:    { type: string, format: uuid }     # for idempotency
occurredAt: { type: string, format: date-time } # event timestamp
```

Plus domain-specific fields from the task description.

### Action Values

| Producer side | `action: send` |
| Consumer side | `action: receive` |

One operation per channel direction. If the same channel has both producers and consumers,
define two operations with different `operationId` values.

---

### Application Binding Config

Add to `src/main/resources/application.yaml` (create the file if it does not exist):

```yaml
spring:
  cloud:
    stream:
      bindings:
        <operationId>-out-0:           # producer: matches @Bean Supplier<Message<T>> operationId()
          destination: <topic-name>
        <operationId>-in-0:            # consumer: matches @Bean Consumer<Message<T>> operationId()
          destination: <topic-name>
          group: <consumer-group-name>
      kafka:
        binder:
          brokers: localhost:9092
```

Binding name convention: `<bean-method-name>-out-0` for producers, `<bean-method-name>-in-0` for consumers.

### Alternative: asyncapi-generator (contract-first codegen)

Use only when the task explicitly requires code generation from the spec file:

```bash
npx @asyncapi/generator <spec-file>.yaml @asyncapi/java-spring-cloud-stream-template \
    -o src/main/java \
    --force-write
```

---

## Output Paths

| What | Default Path |
|------|-------------|
| AsyncAPI spec file | `src/main/resources/asyncapi/<name>.yaml` |
| Spring Cloud Stream bindings | `src/main/resources/application.yaml` (additions) |
| Generated code (asyncapi-generator only) | `src/main/java/<package>/` |

If `Output Paths` are already configured, write the spec to that path instead of the default.

---

## Verification Checklist

After authoring the spec and configuring bindings:

- [ ] AsyncAPI spec file exists at `src/main/resources/asyncapi/<name>.yaml`
- [ ] All channels have an `address` field (Kafka topic name)
- [ ] All messages reference schemas via `$ref` (no inline payload definitions)
- [ ] All event schemas include `eventId` (uuid) and `occurredAt` (date-time) fields
- [ ] Spring Cloud Stream binding names follow `<operationId>-out-0` / `<operationId>-in-0` pattern
- [ ] `application.yaml` bindings `destination` values match channel `address` values in the spec
- [ ] `compileJava` exits with BUILD SUCCESSFUL
