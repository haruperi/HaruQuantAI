# opentelemetry-semconv-1.40.0.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-1.40.0.jar`.
- **SHA-256:** `27eb65c14b91487cc25d35bd6f455193aac981d1ebe1b9472d5160cece573ba4`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 25 raw entries; 25 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-HOST-OPENTELEMETRY-SEMCONV`, P01; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [094.json](../../../evidence/sqx145/archives/145/094.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/094/001.json) — SHA-256 `a9b9fe31cb2bcfac7846ebdd86f87ac5a4b676a12064a19969832b657caa7833`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["AttributeKeyTemplate"]
    class C1["ClientAttributes"]
    class C2["CodeAttributes"]
    class C3["DbAttributes"]
    class C4["ErrorAttributes"]
    class C5["ExceptionAttributes"]
    class C6["HttpAttributes"]
    class C7["JvmAttributes"]
    class C8["NetworkAttributes"]
    class C9["OtelAttributes"]
    class C10["SchemaUrls"]
    class C11["ServerAttributes"]
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `io/opentelemetry/semconv/AttributeKeyTemplate.class` | 0 | `40b3c8b7b6b112d8d61240ac78742805d82d07c8b7fc2d2e984860e3bdec3c31` | 3 | 11 |
| `io/opentelemetry/semconv/ClientAttributes.class` | 0 | `0fec4a26fda01f26d61ad174fff53bbe0bb38a208fc2d8ed6857ef1d4188c66b` | 2 | 2 |
| `io/opentelemetry/semconv/CodeAttributes.class` | 0 | `e8b7e113001ceb7ffbf0b05793960b01fb7af56a9eacf61675cef96a21e1f92c` | 5 | 2 |
| `io/opentelemetry/semconv/DbAttributes$DbSystemNameValues.class` | 0 | `4b11955243b252c0cc68a393c62877036a13698e89b7d50010bde8e7ad365206` | 4 | 1 |
| `io/opentelemetry/semconv/DbAttributes.class` | 0 | `b535c06b904f35485adf11f9018257ff1c5bf3dcfbeb8a6a0169050ba7d6b718` | 9 | 2 |
| `io/opentelemetry/semconv/ErrorAttributes$ErrorTypeValues.class` | 0 | `4b19f3b7f6c069b9d3d38ebac8af3022a38f49674186b845db2b0cd76129cf75` | 1 | 1 |
| `io/opentelemetry/semconv/ErrorAttributes.class` | 0 | `7fedf90709e6c6414d98f38b6b806cdf41bfa75c0ed8c6c0589972bc3567dfcd` | 1 | 2 |
| `io/opentelemetry/semconv/ExceptionAttributes.class` | 0 | `41e8e41a27364e520de3a9df31d6cff5128253ae32d9c014de9529ff69046b31` | 3 | 2 |
| `io/opentelemetry/semconv/HttpAttributes$HttpRequestMethodValues.class` | 0 | `4ffabfe654065cda96e3e2d944d6979a473cbbf5d40d1eb8f5484734db155d72` | 10 | 1 |
| `io/opentelemetry/semconv/HttpAttributes.class` | 0 | `19d7201c45228a137df319e8a34a46123e5364cc196de694c1485a47f4e6c2cd` | 7 | 2 |
| `io/opentelemetry/semconv/JvmAttributes$JvmMemoryTypeValues.class` | 0 | `130d76866290994f1e17b77af136801ce8933a360af59a18d20b853afd1a3ba9` | 2 | 1 |
| `io/opentelemetry/semconv/JvmAttributes$JvmThreadStateValues.class` | 0 | `71e0bb95bc51c6eceae7cbe09f1551653f2263fe26076bff5a3f9e92a741fc18` | 6 | 1 |
| `io/opentelemetry/semconv/JvmAttributes.class` | 0 | `7fa96f9790bb4aa5bb337fb70c526c18a23a9d45ecc9e777de04fa8064242f88` | 6 | 2 |
| `io/opentelemetry/semconv/NetworkAttributes$NetworkTransportValues.class` | 0 | `71ee3bf65b2902c36a4d92b03a2f2218b85755bab7d49733efc5b11b7a938a26` | 5 | 1 |
| `io/opentelemetry/semconv/NetworkAttributes$NetworkTypeValues.class` | 0 | `41b41d945017c78c665e79653d5dcd6d301006ca3437121ea9ab6746229f4190` | 2 | 1 |
| `io/opentelemetry/semconv/NetworkAttributes.class` | 0 | `e5eb1e1a9b16d48d86c1c02930acc86571e2937b03f4c170061dabf51e47a286` | 8 | 2 |
| `io/opentelemetry/semconv/OtelAttributes$OtelStatusCodeValues.class` | 0 | `661ce17f9b83af04e9d43ee44856671272e933371e38ff086d1a0acce141d203` | 2 | 1 |
| `io/opentelemetry/semconv/OtelAttributes.class` | 0 | `d62e62b30a73315f04283928e8d58824754353dff7af4ece02c80cbb45f586dc` | 4 | 2 |
| `io/opentelemetry/semconv/SchemaUrls.class` | 0 | `b2877266ea124a6a33a439f117d207e5c2ab4be51cbcedc3ae8bb9e6bc9b6ae3` | 17 | 1 |
| `io/opentelemetry/semconv/ServerAttributes.class` | 0 | `ccf401a3132c32c59e9c6d1b833f07d782ba3ef2f7e365c18d00356b120de89b` | 2 | 2 |
| `io/opentelemetry/semconv/ServiceAttributes.class` | 0 | `ac043c3c22fe61a5989bb8da117590a7652f68dc47cee1f8c78a47fd9a2fcabe` | 4 | 2 |
| `io/opentelemetry/semconv/TelemetryAttributes$TelemetrySdkLanguageValues.class` | 0 | `11ba2a8928b7ad3e612b070998ef4c5bc5b0a8e0e7071b160c58ef7f58d55731` | 12 | 1 |
| `io/opentelemetry/semconv/TelemetryAttributes.class` | 0 | `97c8c31d2ba8479462d4f13364337f1269521d78b62435a1fef0d95bc9391b18` | 3 | 2 |
| `io/opentelemetry/semconv/UrlAttributes.class` | 0 | `909a6536b3527f12f6137533b5a265065ca48f7507299fe8b85e42f01535aad3` | 5 | 2 |
| `io/opentelemetry/semconv/UserAgentAttributes.class` | 0 | `085ac6436d309ae7b008a8ab8a2b91a7ac284f14dd19e4beffe41386fc67b807` | 1 | 2 |
