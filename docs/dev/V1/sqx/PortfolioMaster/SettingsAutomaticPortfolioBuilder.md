# SettingsAutomaticPortfolioBuilder.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar`.
- **SHA-256:** `7d7c8fe7fbc77d52f1aed81a06f8e9104f2d3cbca10e19a9fcba5fdc68177161`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 2 raw entries; 2 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER`, P12; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [240.json](../../../evidence/sqx145/archives/145/240.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/240/001.json) — SHA-256 `509d051a801544f63cc52fd6b59aaa12b2de904ead74c97c5404740fa2a2e95a`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["SettingsAutomaticPortfolioBuilderPlugin"]
    class C1["SettingsAutomaticPortfolioBuilderServlet"]
    class E0["ISettingTabPlugin"]
    E0 <|.. C0
    class E1["IServletPlugin"]
    E1 <|.. C0
    class E2["HttpJSONServlet"]
    E2 <|-- C1
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `com/strategyquant/plugin/Settings/impl/AutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilderPlugin.class` | 0 | `58b60fe4f9fa8ebdf36caa675dcb6102c997ef3a84902d32676940e77ad3e60d` | 3 | 12 |
| `com/strategyquant/plugin/Settings/impl/AutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilderServlet.class` | 0 | `0b8240482c045d06af1779e98628dd8861f8b822ceed8f4fed72809dd6c12070` | 1 | 7 |
