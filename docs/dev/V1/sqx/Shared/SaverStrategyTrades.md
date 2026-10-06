# SaverStrategyTrades.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar`.
- **SHA-256:** `f8419ae945fc288763ebbc667dd65e14f9140859d2cd7c3bb3daf87409238348`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 1 raw entries; 1 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-RESULTS-SAVER-STRATEGY-TRADES`, P08; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [226.json](../../../evidence/sqx145/archives/145/226.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/226/001.json) — SHA-256 `63eac2443be3532e4f149b6ae287bc60207d78dda29cbc0c988d4083645bd50e`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["StrategyTradesSaverPlugin"]
    class E0["ISaverPlugin"]
    E0 <|.. C0
    class E1["IProgram"]
    E1 <|.. C0
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `com/strategyquant/plugin/Saver/impl/StrategyTrades/StrategyTradesSaverPlugin.class` | 0 | `38ac80f0d1fcbc0b4525ef5f6de7f4381064d1e548b099ba10bbb10a38b22cb3` | 2 | 11 |
