# DebugConsole: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppDebugConsole.jar](AppDebugConsole.md) | 1 | `com.strategyquant.plugin.App.impl.DebugConsole` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppDebugConsole/module.js`: title `Debug Console`, app code `DEBUGCONSOLE`, hidden registration `False`. SHA-256 `92a604b47eae70b573d4ebf038901f61784b4f01d245ea45f7ef531647788158`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQPluginLib.jar](../Shared/SQPluginLib.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
