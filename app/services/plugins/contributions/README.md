# Plugin Contributions

> **Feature ID:** `FEAT-PLUG-REGISTER_CONTRIBUTIONS`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.register-contributions@1`

## Required Capabilities

- `plugins.declare-manifests@1`

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| `strict_contract_tests` | `bool` | `true` | When true, contributions failing contract tests cause registration to fail. |
| `max_contributions_per_plugin` | `int` | `100` | Maximum number of typed contributions a single plugin may register. |

## Purpose

Register typed plugin contribution capabilities across all supported plugin types and execute contract tests before stable enablement.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-PLUG-REGISTER_PLUGIN_CONTRIBUTIONS` | `plugin_contributions.py::__main__` Scenario 1 | `tests/services/plugins/contributions/test_plugin_contributions.py::test_plug_register_plugin_contributions` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.plugins.contributions.plugin_contributions
```

## Runtime Effects

- Registers and indexes typed plugin contribution descriptors (`BLOCK`, `INDICATOR`, `METRIC`, `FILTER`, `FITNESS`, `RESEARCH_METHOD`, `DATA_CONNECTOR`, `PROJECT_TASK`, `SOURCE_EMITTER`, `RESULT_PANEL`).
- Executes type-specific contract tests validating method interfaces, callable contracts, and schemas.
- Unregisters contributions transactionally on plugin removal or lifecycle disablement.

## Persistent State

None. This feature maintains in-memory active contribution indices during process lifecycle.

## Failure Behavior

- Registering contributions whose type was not declared in the manifest raises `PluginContributionError`.
- Registering contributions from mismatched plugin IDs or exceeding max limit raises `PluginContributionError`.
- Contributions failing type-specific contract verification raise `PluginContractTestError` when `strict_contract_tests` is enabled.
- Requests requiring a removed capability return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws all registered third-party contributions from the active runtime registry. Consuming domains and built-in capability providers continue operating normally.
