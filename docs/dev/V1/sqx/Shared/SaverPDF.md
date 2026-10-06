# SaverPDF.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SaverPDF/SaverPDF.jar`.
- **SHA-256:** `030ecc3ebcef0358672b151f15c848d0194ac6375bd018d39bedda723f714e81`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 1 raw entries; 1 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-RESULTS-SAVER-PDF`, P08; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [224.json](../../../evidence/sqx145/archives/145/224.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/224/001.json) — SHA-256 `9b1b352e24ceb611fd7b59474c91869ebbaf7c32806a488458f2e7910c4b82dc`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["PDFReportPlugin"]
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
| `com/strategyquant/plugin/Saver/impl/PDF/PDFReportPlugin.class` | 0 | `84a4913a894e842853ecca3e8b4cc8979ed6ca71736e6ba745fcc7e77497e20b` | 2 | 11 |
