# PortfolioComposer: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppPortfolioComposer.jar](AppPortfolioComposer.md) | 1 | `com.strategyquant.plugin.App.impl.PortfolioComposer` |
| [PortfolioComposer.jar](PortfolioComposer.md) | 15 | `com.strategyquant.plugin.Portfolio.impl.Composer` |
| [ResultsPortfolioComposerChart.jar](ResultsPortfolioComposerChart.md) | 2 | `com.strategyquant.plugin.Results.impl.PortfolioComposerChart` |
| [ResultsPortfolioComposerLog.jar](ResultsPortfolioComposerLog.md) | 2 | `com.strategyquant.plugin.Results.impl.PortfolioComposerLog` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/module.js`: title `Portfolio Composer`, app code `PORTFOLIOCOMPOSER`, hidden registration `False`. SHA-256 `a0b1fd91c4e35db0af1c7b114e1394bfbfec0ad4f1bc34b4f77ec485d785476a`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQDataLib.jar](../Shared/SQDataLib.md) - `Shared`.
- [SQGridLib2.jar](../Shared/SQGridLib2.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
