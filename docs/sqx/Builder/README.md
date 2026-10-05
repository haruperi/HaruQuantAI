# Builder: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppBuilder.jar](AppBuilder.md) | 1 | `com.strategyquant.plugin.App.impl.Builder` |
| [ServletBuilder.jar](ServletBuilder.md) | 2 | `com.strategyquant.plugin.Servlet.impl.Builder` |
| [TaskBuild.jar](TaskBuild.md) | 11 | `com.strategyquant.plugin.Task.impl.Build` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`: title `Builder`, app code `BUILDER`, hidden registration `False`. SHA-256 `38d240a27ed8de5ba55635979f8d594bb49437bae85a5debd69271dc12683616`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQGridLib2.jar](../Shared/SQGridLib2.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
