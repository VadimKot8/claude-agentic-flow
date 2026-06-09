---
name: api-soap
description: "Use when the task requires authoring a WSDL 1.1/SOAP service contract, configuring the wsdl2java Gradle plugin, or verifying generated Service Endpoint Interface and request/response wrapper classes."
---

# SOAP / WSDL Format Skill

## When to Use

Activate when the task description contains any of: WSDL, SOAP, XSD, web service, `.wsdl`,
service endpoint, SOAP binding, document/literal, RPC/literal.

---

## Spec Conventions

### WSDL 1.1 Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions
    name="<ServiceName>"
    targetNamespace="http://agents_test.com/voting/<domain>"
    xmlns="http://schemas.xmlsoap.org/wsdl/"
    xmlns:tns="http://agents_test.com/voting/<domain>"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap12="http://schemas.xmlsoap.org/wsdl/soap12/">

  <types>
    <xsd:schema targetNamespace="http://agents_test.com/voting/<domain>">
      <!-- XSD complex types for request/response/fault -->
    </xsd:schema>
  </types>

  <!-- message elements (wrap portType operations) -->
  <!-- portType (abstract interface) -->
  <!-- binding (SOAP 1.2 document/literal) -->
  <!-- service (endpoint URI) -->
</definitions>
```

### Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Service name | PascalCase + "Service" | `VoterService` |
| Port type name | PascalCase + "PortType" | `VoterPortType` |
| Binding name | PascalCase + "Binding" | `VoterBinding` |
| Port name | PascalCase + "Port" | `VoterPort` |
| Operation names | camelCase | `createVoter`, `blockVoter` |
| XSD complex type names | PascalCase | `CreateVoterRequest`, `VoterResponse` |
| XSD element names | camelCase | `voterId`, `voterName` |
| Target namespace | `http://agents_test.com/voting/<domain>` | `http://agents_test.com/voting/voter` |
| WSDL filename | PascalCase | `VoterService.wsdl` |

### Binding Style

Always use **document/literal wrapped** — the most interoperable style. Every operation's
input wraps a single XSD element whose name matches the operation name:

```xml
<binding name="VoterBinding" type="tns:VoterPortType">
  <soap12:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  <operation name="createVoter">
    <soap12:operation soapAction="createVoter"/>
    <input>  <soap12:body use="literal"/> </input>
    <output> <soap12:body use="literal"/> </output>
    <fault name="ServiceFault"> <soap12:fault name="ServiceFault" use="literal"/> </fault>
  </operation>
</binding>
```

### Error Handling (Fault Types)

Define a `ServiceFault` complex type in the XSD and declare it as a `<fault>` in the portType:

```xml
<!-- In types/schema -->
<xsd:complexType name="ServiceFault">
  <xsd:sequence>
    <xsd:element name="faultCode"    type="xsd:string"/>
    <xsd:element name="faultMessage" type="xsd:string"/>
  </xsd:sequence>
</xsd:complexType>
<!-- Element wrapper required for document/literal message part reference -->
<xsd:element name="ServiceFault" type="tns:ServiceFault"/>

<!-- In portType operations -->
<fault name="ServiceFault" message="tns:ServiceFaultMessage"/>

<!-- In messages -->
<message name="ServiceFaultMessage">
  <part name="fault" element="tns:ServiceFault"/>
</message>
```

### Always Include

- `targetNamespace` on every `<definitions>` element
- SOAP 1.2 binding (not 1.1 — use `xmlns:soap12`)
- `ServiceFault` type for every portType
- One service element with one port pointing to the implementation endpoint

---

## Gradle Toolchain

### Required Plugin

Add to the `plugins {}` block in `build.gradle.kts`:

```kotlin
id("com.github.bjornvester.wsdl2java") version "2.0.2"
// Verify version 2.0.2 is compatible with Gradle 9.x; check https://github.com/bjornvester/wsdl2java for updates
```

### Required Dependencies

Add to the `dependencies {}` block:

```kotlin
implementation("org.springframework.boot:spring-boot-starter-web-services")
implementation("wsdl4j:wsdl4j:1.6.3")
implementation("jakarta.xml.ws:jakarta.xml.ws-api:4.0.1")
implementation("com.sun.xml.ws:jaxws-ri:4.0.2")
```

### Full Configuration Block

Add after the `plugins {}` block:

```kotlin
wsdl2java {
    wsdlDir.set(layout.projectDirectory.dir("src/main/resources/wsdl"))
    generatedSourceDir.set(layout.buildDirectory.dir("generated-sources/wsdl2java"))
    packageName.set("com.agents_test.voting.<domain>.ws")
}

sourceSets {
    main {
        java {
            srcDir(layout.buildDirectory.dir("generated-sources/wsdl2java"))
        }
    }
}

tasks.compileJava {
    dependsOn(tasks.wsdl2java)
}
```

Replace `<domain>` with the actual domain name (e.g., `voter`, `election`).

### Applying to build.gradle.kts (non-destructive)

Before writing any Gradle changes:
1. Read `build.gradle.kts`.
2. If the `com.github.bjornvester.wsdl2java` plugin is **already present** — do not add it again.
3. If the `wsdl2java {}` block is **already present** — add only missing settings; do not overwrite `wsdlDir`, `generatedSourceDir`, or `packageName`.
4. Add only the missing pieces (plugin, config block, dependencies, `sourceSets`, `compileJava` dependency).

---

## Output Paths

| What | Default Path |
|------|-------------|
| WSDL file | `src/main/resources/wsdl/<Name>.wsdl` |
| XSD types (if separate file) | `src/main/resources/wsdl/<Name>.xsd` |
| Generated SEI classes | `build/generated-sources/wsdl2java/<package>/` |

XSD types may be embedded inline in the WSDL `<types>` section or in a separate `.xsd` file
referenced via `<xsd:import schemaLocation="<Name>.xsd"/>`.

---

## Verification Checklist

After running `./gradlew wsdl2java`:

- [ ] WSDL file exists at `src/main/resources/wsdl/<Name>.wsdl`
- [ ] Generated SEI (Service Endpoint Interface) class `<ServiceName>.java` exists in `build/generated-sources/wsdl2java/<package>/`
- [ ] Generated request/response wrapper classes exist for each operation
- [ ] `ServiceFault` exception class or wrapper generated
- [ ] Service implementation class follows the generated SEI interface
- [ ] `./gradlew compileJava` exits with BUILD SUCCESSFUL
