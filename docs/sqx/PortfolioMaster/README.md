# PortfolioMaster: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppPortfolioMaster.jar](AppPortfolioMaster.md) | 1 | `com.strategyquant.plugin.App.impl.PortfolioMaster` |
| [SettingsAutomaticPortfolioBuilder.jar](SettingsAutomaticPortfolioBuilder.md) | 2 | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder` |
| [TaskAutomaticPortfolioBuilder.jar](TaskAutomaticPortfolioBuilder.md) | 27 | `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder`, `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce`, `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/module.js`: title `Portfolio Master`, app code `PORTFOLIOMASTER`, hidden registration `False`. SHA-256 `d83a98ef9491e3f9ad0e083827b622227eddd02dd666d8af921153ad05de62a5`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
