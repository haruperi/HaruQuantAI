# Plugin Contributions

> **Feature ID:** `FEAT-PLUG-REGISTER_CONTRIBUTIONS`
> **Status:** `Complete` · **Evidence:** `VERIFIED`
> **Domain:** `plugins`
> **First release milestone:** `U1`

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
| --- | --- | --- | --- |
| `strict_contract_tests` | `bool` | `true` | When true, contributions failing contract tests cause registration to fail. |
| `max_contributions_per_plugin` | `int` | `100` | Maximum number of typed contributions a single plugin may register. |

## Purpose

Register and dispose exact extension contributions with owner-scoped generation tracking, disposer handles, duplicate/conflict rejection, and deterministic exposure.

## Requirements and Traceability

| Requirement ID | Responsibility | Acceptance Oracle | Test Target |
| --- | --- | --- | --- |
| `FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001` | Register immutable owner-scoped contributions with exact ID/version/generation and return a disposer handle. | `AT-PLUG-REGISTER_CONTRIBUTIONS-001` | `tests/services/plugins/register_contributions/test_traceability.py` |
| `FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-002` | Expose compatible contributions deterministically and withdraw them on removal/replacement. | `AT-PLUG-REGISTER_CONTRIBUTIONS-002` | `tests/services/plugins/register_contributions/test_traceability.py` |
| `NFR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001` | Removing FEAT-PLUG-REGISTER_CONTRIBUTIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. | `ATN-PLUG-REGISTER_CONTRIBUTIONS-001` | `tests/services/plugins/register_contributions/test_lifecycle.py` |

## Executable Usage Demonstration

```bash
uv run --frozen python -m app.services.plugins.register_contributions._usage
```

## Runtime Effects

- Registers and indexes typed plugin contribution descriptors across all 10 supported types.
- Tracks exact monotonic generations per plugin and returns a callable `ContributionDisposer` handle.
- Enforces duplicate and conflict rejection so an active ID cannot be hijacked or overwritten.
- Executes type-specific contract tests validating callable methods, protocols, and schemas.
- Unregisters contributions transactionally on plugin removal or generation disposal.
- Disposes only its own generation without purging other generations or matching names.

## Persistent State

None. This feature maintains in-memory active contribution indices during process lifecycle.

## Failure Behavior

- Registering contributions whose type was not declared in the manifest raises `PluginContributionError`.
- Registering contributions with mismatched plugin IDs, empty IDs, or exceeding max limit raises `PluginContributionError`.
- Duplicate contribution IDs within a request or active conflicting IDs raise `PluginContributionError`.
- Contributions failing contract tests raise `PluginContractTestError` when `strict_contract_tests` is enabled.
- Requests requiring an unmounted capability return `CapabilityUnavailableError`.

## Removal Behavior

Removing this feature withdraws all registered third-party contributions from the active runtime registry. Unrelated capabilities remain usable and retained objects unchanged.
