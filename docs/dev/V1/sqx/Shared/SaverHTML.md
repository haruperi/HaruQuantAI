# SaverHTML.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SaverHTML/SaverHTML.jar`.
- **SHA-256:** `1159ff22c6d8210a59b97b48ee0489c67b4647f5efe93b447d7a363a8c129675`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 1 raw entries; 1 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-RESULTS-SAVER-HTML`, P08; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [223.json](../../../evidence/sqx145/archives/145/223.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/223/001.json) — SHA-256 `c12eef38b1655267e2e0f6182654e04ab9c3a449fda3d34b56415c29e37d14af`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["HTMLReportPlugin"]
    class E0["ReportGenerator"]
    E0 <|-- C0
    class E1["ISaverPlugin"]
    E1 <|.. C0
    class E2["IProgram"]
    E2 <|.. C0
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `com/strategyquant/plugin/Saver/impl/HTML/HTMLReportPlugin.class` | 0 | `5a32828c61c33ed947315086bad79549cf4a57e4848184c8124cb4fdb477616f` | 2 | 10 |
