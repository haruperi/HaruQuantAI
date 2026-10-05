# ProductShells: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppQuantDataManager.jar](AppQuantDataManager.md) | 3 | `com.strategyquant.plugin.App.impl.QuantDataManager` |
| [AppStrategyQuant.jar](AppStrategyQuant.md) | 1 | `com.strategyquant.plugin.App.impl.StrategyQuant` |

## Workspace registration evidence

- `AppQuantDataManager`: no module.js at archive directory root. App-prefix alone does not establish a navigation workspace. See its inspected Java plugin declarations.
- `AppStrategyQuant`: no module.js at archive directory root. App-prefix alone does not establish a navigation workspace. See its inspected Java plugin declarations.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
