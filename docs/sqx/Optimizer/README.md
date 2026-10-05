# Optimizer: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppOptimizer.jar](AppOptimizer.md) | 1 | `com.strategyquant.plugin.App.impl.Optimizer` |
| [TaskOptimize.jar](TaskOptimize.md) | 10 | `com.strategyquant.plugin.Task.impl.Optimize` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppOptimizer/module.js`: title `Optimizer`, app code `OPTIMIZER`, hidden registration `False`. SHA-256 `06fc34b51e0e2e176389f95e4ce3bd1c3032dedc64b0c7369b80708ccb147d9d`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
