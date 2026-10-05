# AlgoWizard: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppWizard.jar](AppWizard.md) | 1 | `com.strategyquant.plugin.App.impl.Wizard` |
| [ServletAlgoWizard.jar](ServletAlgoWizard.md) | 4 | `com.strategyquant.plugin.Servlet.impl.AlgoWizard` |
| [ServletWizard.jar](ServletWizard.md) | 2 | `com.strategyquant.plugin.Servlet.impl.Wizard` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppWizard/module.js`: title `AlgoWizard`, app code `AlgoWizard`, hidden registration `False`. SHA-256 `d330b271b059cd852d64adace16233c8ecea31d440d8ebc7cbc8d4e3e7df5707`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
