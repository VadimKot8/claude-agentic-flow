# Testing Anti-Patterns

**Load this reference when:** writing or changing tests, adding mocks, or tempted to add test-only methods to production code.

## Overview

Tests must verify real behavior, not mock behavior. Mocks are a means to isolate, not the thing being tested.

**Core principle:** Test what the code does, not what the mocks do.

**Following strict TDD prevents these anti-patterns.**

## The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

## Anti-Pattern 1: Testing Mock Behavior

**The violation:**
```java
// ❌ BAD: Testing that the stub returns what you stubbed
@Test
void getsUserName() {
    UserRepository repo = mock(UserRepository.class);
    when(repo.findName(1L)).thenReturn("Alice");

    assertEquals("Alice", repo.findName(1L));  // Only proves Mockito works!
}
```

**Why this is wrong:**
- You're verifying the mock works, not that the production code works
- Test passes when stub is configured, fails when it's not
- Tells you nothing about real behavior

**your human partner's correction:** "Are we testing the behavior of a mock?"

**The fix:**
```java
// ✅ GOOD: Test real production logic through the class under test
@Test
void getsUserGreeting() {
    UserRepository repo = mock(UserRepository.class);
    when(repo.findName(1L)).thenReturn("Alice");
    UserService service = new UserService(repo);

    assertEquals("Hello, Alice!", service.greet(1L));  // Real logic exercised
}

// OR use the real repository (e.g. in-memory implementation) and don't mock at all
```

### Gate Function

```
BEFORE asserting on any stubbed value or mock interaction:
  Ask: "Am I testing real production behavior or just the stub configuration?"

  IF testing stub configuration:
    STOP - Delete the assertion or remove the mock

  Test real behavior instead
```

## Anti-Pattern 2: Test-Only Methods in Production

**The violation:**
```java
// ❌ BAD: destroy() only used in tests
public class Session {
    public void destroy() {  // Looks like production API!
        if (workspaceManager != null) {
            workspaceManager.destroyWorkspace(id);
        }
        // ... cleanup
    }
}

// In tests
@AfterEach
void tearDown() {
    session.destroy();
}
```

**Why this is wrong:**
- Production class polluted with test-only code
- Dangerous if accidentally called in production
- Violates YAGNI and separation of concerns
- Confuses object lifecycle with entity lifecycle

**The fix:**
```java
// ✅ GOOD: Test utilities handle test cleanup
// Session has no destroy() - it's stateless in production

// In src/test/java/.../testutil/SessionTestUtils.java
public final class SessionTestUtils {
    public static void cleanupSession(Session session, WorkspaceManager manager) {
        WorkspaceInfo workspace = session.getWorkspaceInfo();
        if (workspace != null) {
            manager.destroyWorkspace(workspace.id());
        }
    }
}

// In tests
@AfterEach
void tearDown() {
    SessionTestUtils.cleanupSession(session, workspaceManager);
}
```

### Gate Function

```
BEFORE adding any method to production class:
  Ask: "Is this only used by tests?"

  IF yes:
    STOP - Don't add it
    Put it in test utilities instead

  Ask: "Does this class own this resource's lifecycle?"

  IF no:
    STOP - Wrong class for this method
```

## Anti-Pattern 3: Mocking Without Understanding

**The violation:**
```java
// ❌ BAD: Mock breaks test logic
@Test
void detectsDuplicateServer() {
    // Mock prevents config write that test depends on!
    ToolCatalog catalog = mock(ToolCatalog.class);
    var registry = new ServerRegistry(catalog);

    registry.addServer(config);
    assertThrows(DuplicateServerException.class,
        () -> registry.addServer(config));  // Should throw - but won't!
}
```

**Why this is wrong:**
- Mocked dependency had side effect test depended on (writing config)
- Over-mocking to "be safe" breaks actual behavior
- Test passes for wrong reason or fails mysteriously

**The fix:**
```java
// ✅ GOOD: Mock at correct level
@Test
void detectsDuplicateServer() {
    // Mock the slow part, preserve behavior test needs
    ServerLauncher launcher = mock(ServerLauncher.class);  // Just mock slow server startup
    var registry = new ServerRegistry(new ToolCatalog(launcher));

    registry.addServer(config);  // Config written
    assertThrows(DuplicateServerException.class,
        () -> registry.addServer(config));  // Duplicate detected ✓
}
```

### Gate Function

```
BEFORE mocking any method:
  STOP - Don't mock yet

  1. Ask: "What side effects does the real method have?"
  2. Ask: "Does this test depend on any of those side effects?"
  3. Ask: "Do I fully understand what this test needs?"

  IF depends on side effects:
    Mock at lower level (the actual slow/external operation)
    OR use test doubles that preserve necessary behavior
    NOT the high-level method the test depends on

  IF unsure what test depends on:
    Run test with real implementation FIRST
    Observe what actually needs to happen
    THEN add minimal mocking at the right level

  Red flags:
    - "I'll mock this to be safe"
    - "This might be slow, better mock it"
    - Mocking without understanding the dependency chain
```

## Anti-Pattern 4: Incomplete Mocks

**The violation:**
```java
// ❌ BAD: Partial mock - only fields you think you need
var mockResponse = new ApiResponse(
    "success",
    new UserData("123", "Alice"),
    null  // Missing: metadata that downstream code uses
);

// Later: NullPointerException when code accesses response.metadata().requestId()
```

**Why this is wrong:**
- **Partial mocks hide structural assumptions** - You only mocked fields you know about
- **Downstream code may depend on fields you didn't include** - Silent failures
- **Tests pass but integration fails** - Mock incomplete, real API complete
- **False confidence** - Test proves nothing about real behavior

**The Iron Rule:** Mock the COMPLETE data structure as it exists in reality, not just fields your immediate test uses.

**The fix:**
```java
// ✅ GOOD: Mirror real API completeness
var mockResponse = new ApiResponse(
    "success",
    new UserData("123", "Alice"),
    new Metadata("req-789", 1234567890L)
    // All fields real API returns
);
```

### Gate Function

```
BEFORE creating mock responses:
  Check: "What fields does the real API response contain?"

  Actions:
    1. Examine actual API response from docs/examples
    2. Include ALL fields system might consume downstream
    3. Verify mock matches real response schema completely

  Critical:
    If you're creating a mock, you must understand the ENTIRE structure
    Partial mocks fail silently when code depends on omitted fields

  If uncertain: Include all documented fields
```

## Anti-Pattern 5: Integration Tests as Afterthought

**The violation:**
```
✅ Implementation complete
❌ No tests written
"Ready for testing"
```

**Why this is wrong:**
- Testing is part of implementation, not optional follow-up
- TDD would have caught this
- Can't claim complete without tests

**The fix:**
```
TDD cycle:
1. Write failing test
2. Implement to pass
3. Refactor
4. THEN claim complete
```

## When Mocks Become Too Complex

**Warning signs:**
- Mock setup longer than test logic
- Mocking everything to make test pass
- Mocks missing methods real components have
- Test breaks when mock changes

**your human partner's question:** "Do we need to be using a mock here?"

**Consider:** Integration tests with real components often simpler than complex mocks

## TDD Prevents These Anti-Patterns

**Why TDD helps:**
1. **Write test first** → Forces you to think about what you're actually testing
2. **Watch it fail** → Confirms test tests real behavior, not mocks
3. **Minimal implementation** → No test-only methods creep in
4. **Real dependencies** → You see what the test actually needs before mocking

**If you're testing mock behavior, you violated TDD** - you added mocks without watching test fail against real code first.

## Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| Assert on stubbed values | Test real production logic or remove the mock |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first, mock minimally |
| Incomplete mocks | Mirror real API completely |
| Tests as afterthought | TDD - tests first |
| Over-complex mocks | Consider integration tests |

## Red Flags

- Assertion directly verifies a value you just stubbed with `when(...).thenReturn(...)`
- Production methods only called from test code
- Mock setup is >50% of test
- Test fails when you remove mock
- Can't explain why mock is needed
- Mocking "just to be safe"

## The Bottom Line

**Mocks are tools to isolate, not things to test.**

If TDD reveals you're testing mock behavior, you've gone wrong.

Fix: Test real behavior or question why you're mocking at all.
