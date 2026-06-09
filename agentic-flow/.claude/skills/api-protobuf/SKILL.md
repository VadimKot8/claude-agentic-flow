---
name: api-protobuf
description: "Use when the task requires authoring proto3/gRPC service definitions, configuring the protobuf Gradle plugin, or verifying generated Java message and stub classes."
---

# Protobuf / gRPC Format Skill

## When to Use

Activate when the task description contains any of: proto, protobuf, gRPC, `.proto`, service
definition, RPC, streaming, stub, ServerStreamingCall, BidiStreaming.

---

## Spec Conventions

### File Header

```proto
syntax = "proto3";

package com.agents_test.voting.<domain>;

option java_package = "com.agents_test.voting.<domain>.grpc";
option java_multiple_files = true;
option java_outer_classname = "<Domain>Proto";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";
```

### Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Message names | PascalCase | `CreateVoterRequest`, `VoterResponse` |
| Field names | snake_case | `voter_id`, `election_id` |
| Service names | PascalCase + "Service" | `VoterService`, `ElectionService` |
| RPC method names | PascalCase verb | `CreateVoter`, `GetVoterById` |
| Enum type names | PascalCase | `VoterStatus` |
| Enum value names | UPPER_SNAKE_CASE with type prefix | `VOTER_STATUS_ACTIVE`, `VOTER_STATUS_BLOCKED` |
| Package | lowercase dot-separated | `com.agents_test.voting.voter` |
| .proto filename | snake_case | `voter_service.proto` |

### Field Numbering

- Start at 1; never reuse field numbers once published
- Group related fields together
- Reserve removed field numbers: `reserved 5, 6;`
- `string` fields compile to `""` by default in proto3 — use wrapper types for nullable semantics

### Service Definition Patterns

```proto
service VoterService {
  // Unary
  rpc CreateVoter (CreateVoterRequest) returns (VoterResponse);
  rpc GetVoter    (GetVoterRequest)    returns (VoterResponse);
  rpc ListVoters  (google.protobuf.Empty) returns (ListVotersResponse);
  rpc BlockVoter  (VoterIdRequest)    returns (VoterResponse);

  // Server streaming
  rpc WatchElection (WatchRequest) returns (stream ElectionEvent);
}
```

### Well-Known Types

| Use case | Import | Type |
|----------|--------|------|
| Timestamps | `google/protobuf/timestamp.proto` | `google.protobuf.Timestamp` |
| Empty request/response | `google/protobuf/empty.proto` | `google.protobuf.Empty` |
| Nullable string | `google/protobuf/wrappers.proto` | `google.protobuf.StringValue` |
| Nullable int64 | `google/protobuf/wrappers.proto` | `google.protobuf.Int64Value` |

### Always Include

- `syntax = "proto3";` as the first non-comment line
- `java_package`, `java_multiple_files = true`, `java_outer_classname` options
- One service per `.proto` file
- Unary RPCs preferred unless streaming is explicitly required by the task

---

## Gradle Toolchain

### Required Plugin

Add to the `plugins {}` block in `build.gradle.kts`:

```kotlin
id("com.google.protobuf") version "0.9.4"
```

### Required Dependencies

Add to the `dependencies {}` block:

```kotlin
implementation("io.grpc:grpc-stub:1.63.0")
implementation("io.grpc:grpc-protobuf:1.63.0")
implementation("io.grpc:grpc-netty-shaded:1.63.0")
implementation("com.google.protobuf:protobuf-java:3.25.3")
compileOnly("jakarta.annotation:jakarta.annotation-api:2.1.1")
```

**Note:** These dependencies are sufficient for code generation and compilation of gRPC stubs. Wiring the generated service stubs into a Spring Boot application context requires additional server integration setup (e.g., a Spring gRPC starter), which is handled in the implementation task, not here.

### Full Configuration Block

Add after the `plugins {}` block:

```kotlin
protobuf {
    protoc {
        artifact = "com.google.protobuf:protoc:3.25.3"
    }
    plugins {
        create("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:1.63.0"
        }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins {
                create("grpc")
            }
        }
    }
}

sourceSets {
    main {
        java {
            srcDirs(
                layout.buildDirectory.dir("generated/source/proto/main/java"),
                layout.buildDirectory.dir("generated/source/proto/main/grpc")
            )
        }
    }
}
```

### Applying to build.gradle.kts (non-destructive)

Before writing any Gradle changes:
1. Read `build.gradle.kts`.
2. If the `com.google.protobuf` plugin is **already present** — do not add it again.
3. If the `protobuf {}` block is **already present** — add only missing inner blocks
   (`protoc`, `plugins`, `generateProtoTasks`); do not overwrite existing settings.
4. Add only the missing pieces (plugin, config block, dependencies, `sourceSets`).

---

## Output Paths

| What | Default Path |
|------|-------------|
| Proto source | `src/main/proto/<package-path>/<name>.proto` |
| Generated Java messages | `build/generated/source/proto/main/java/<package>/` |
| Generated gRPC stubs | `build/generated/source/proto/main/grpc/<package>/` |

Example: `src/main/proto/com/agents_test/voting/voter/voter_service.proto`

---

## Verification Checklist

After running `./gradlew generateProto`:

- [ ] `.proto` file exists at the correct `src/main/proto/` path
- [ ] Generated message classes exist in `build/generated/source/proto/main/java/<package>/`
- [ ] Generated gRPC stub class `<ServiceName>Grpc.java` exists in `build/generated/source/proto/main/grpc/<package>/`
- [ ] `ImplBase` abstract class exists inside `<ServiceName>Grpc` for server-side implementation
- [ ] Field names in generated Java are camelCase (proto snake_case → Java camelCase, automatic)
- [ ] `./gradlew compileJava` exits with BUILD SUCCESSFUL
