# Retester: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppRetester.jar](AppRetester.md) | 1 | `com.strategyquant.plugin.App.impl.Retester` |
| [TaskAutomaticRetest.jar](TaskAutomaticRetest.md) | 6 | `com.strategyquant.plugin.Task.impl.AutomaticRetest` |
| [TaskRetest.jar](TaskRetest.md) | 4 | `com.strategyquant.plugin.Task.impl.Retest` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppRetester/module.js`: title `Retester`, app code `RETESTER`, hidden registration `False`. SHA-256 `83371fe9535dc8a2ecff6e816b20be5f58400c42ba9bd2843f18c52ca109653b`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQDataLib.jar](../Shared/SQDataLib.md) - `Shared`.
- [SQGridLib2.jar](../Shared/SQGridLib2.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
