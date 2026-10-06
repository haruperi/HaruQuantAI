# SettingsMoneyManagement.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar`.
- **SHA-256:** `7798ced63fad323cb8591dcc4f0075a610147b27ccc9522a202e990e4ba8f57d`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 1 raw entries; 1 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-SIMULATOR-SETTINGS-MONEY-MANAGEMENT`, P06; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [254.json](../../../evidence/sqx145/archives/145/254.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/254/001.json) — SHA-256 `ae699f0ea2ce6d93b4ff661f5368dfc26843d990dcea0695797fb13f7cc4b2ab`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["MoneyManagementSettingsPlugin"]
    class E0["ISettingTabPlugin"]
    E0 <|.. C0
    class E1["IServletPlugin"]
    E1 <|.. C0
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `com/strategyquant/plugin/Settings/impl/MoneyManagement/MoneyManagementSettingsPlugin.class` | 0 | `8b0f539e7dc39852c907dbea5de20aff9e1c26b0be332cb54a6d84394b7acf16` | 2 | 13 |
