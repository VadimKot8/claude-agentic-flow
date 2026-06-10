---
name: api-protobuf
description: "Use when the task requires authoring proto3/gRPC service definitions, configuring the protobuf build plugin (Gradle or Maven), or verifying generated Java message and stub classes."
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

## Output Paths

| What | Default Path |
|------|-------------|
| Proto source | `src/main/proto/<package-path>/<name>.proto` |
| Generated Java messages | `build/generated/source/proto/main/java/<package>/` |
| Generated gRPC stubs | `build/generated/source/proto/main/grpc/<package>/` |

Example: `src/main/proto/com/agents_test/voting/voter/voter_service.proto`
If `Output Paths` are already configured, write the spec to that path instead of the default.

---

## Verification Checklist

After running `generateProto` task:

- [ ] `.proto` file exists at the correct `src/main/proto/` path
- [ ] Generated message classes exist in `build/generated/source/proto/main/java/<package>/`
- [ ] Generated gRPC stub class `<ServiceName>Grpc.java` exists in `build/generated/source/proto/main/grpc/<package>/`
- [ ] `ImplBase` abstract class exists inside `<ServiceName>Grpc` for server-side implementation
- [ ] Field names in generated Java are camelCase (proto snake_case → Java camelCase, automatic)
- [ ] `compileJava` task exits with BUILD SUCCESSFUL
