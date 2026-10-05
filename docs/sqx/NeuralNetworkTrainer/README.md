# NeuralNetworkTrainer: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppNeuralNetwork.jar](AppNeuralNetwork.md) | 1 | `com.strategyquant.plugin.App.impl.NeuralNetwork` |
| [TaskNeuralNetworkTrainer.jar](TaskNeuralNetworkTrainer.md) | 1 | `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/module.js`: title `Neural Network Trainer`, app code `NEURALNETWORK`, hidden registration `True`. SHA-256 `4860d987eabf930d482379e4d7bd3c6ea565de22c1c14df7164238212e85291b`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
