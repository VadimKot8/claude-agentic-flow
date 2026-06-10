---
name: api-soap
description: "Use when the task requires authoring a WSDL 1.1/SOAP service contract, configuring the wsdl2java build plugin (Gradle or Maven), or verifying generated Service Endpoint Interface and request/response wrapper classes."
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

## Output Paths

| What | Default Path |
|------|-------------|
| WSDL file | `src/main/resources/wsdl/<Name>.wsdl` |
| XSD types (if separate file) | `src/main/resources/wsdl/<Name>.xsd` |
| Generated SEI classes | `build/generated-sources/wsdl2java/<package>/` |

XSD types may be embedded inline in the WSDL `<types>` section or in a separate `.xsd` file
referenced via `<xsd:import schemaLocation="<Name>.xsd"/>`.

If `Output Paths` are already configured, write the spec to that path instead of the default.

---

## Verification Checklist

After running `wsdl2java` task:

- [ ] WSDL file exists at `src/main/resources/wsdl/<Name>.wsdl`
- [ ] Generated SEI (Service Endpoint Interface) class `<ServiceName>.java` exists in `build/generated-sources/wsdl2java/<package>/`
- [ ] Generated request/response wrapper classes exist for each operation
- [ ] `ServiceFault` exception class or wrapper generated
- [ ] Service implementation class follows the generated SEI interface
- [ ] `compileJava` task exits with BUILD SUCCESSFUL
