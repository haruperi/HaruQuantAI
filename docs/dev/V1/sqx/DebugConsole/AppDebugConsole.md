# AppDebugConsole.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppDebugConsole/AppDebugConsole.jar`.
- **SHA-256:** `aaaf875f1a4897aa3ea0a415bdca4da672b166bd0ea117bad9f5276723330394`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 1 raw entries; 1 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-HOST-APP-DEBUG-CONSOLE`, P01; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [127.json](../../../evidence/sqx145/archives/145/127.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/127/001.json) — SHA-256 `f3fb78add44358cf593b74e71fc73c7fb732393295fc4b35eba4acc06b614bdd`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["DebugConsoleAppPlugin"]
    class E0["IAppPlugin"]
    E0 <|.. C0
    class E1["IProgram"]
    E1 <|.. C0
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `com/strategyquant/plugin/App/impl/DebugConsole/DebugConsoleAppPlugin.class` | 0 | `fc02d688eaa04d743c4bf563fd2195155abb9734a43a9e3172ff1c89dba5f64b` | 1 | 13 |
