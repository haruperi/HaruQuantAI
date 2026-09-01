# Provider and Broker Mapping

**Feature ID:** `FEAT-CAT-MAP_PROVIDERS`

## Domain

`catalogue`

## Purpose

Provide the `catalogue.map-providers@1` capability for mapping broker and data-provider identities to canonical instruments via versioned adapter records and broker profiles.

## Provides

`catalogue.map-providers@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string or null | No | Optional SQLite database path for persistent storage; defaults to in-memory SQLite. |

## Persistent State

`catalogue.provider_mappings` schema version 1 retains `provider_symbol_mappings` in the configured SQLite database. Retention policy is `retain`: feature unloading or uninstallation preserves immutable provider and broker mapping definitions.

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `catalogue.map-providers@1`. Scoped SQLite connections are opened per operation and closed in all execution paths.

## Operations

- `RESOLVE`: Query active provider symbol mapping by provider reference, broker reference (optional), symbol, and point-in-time timestamp.
- `UPSERT`: Store or update provider symbol mapping, verifying non-overlapping intervals across identical provider/broker/symbol combinations and publishing `catalogue.provider-symbol-mapping-changed`.
- `DELETE`: Safely mark a provider symbol mapping deleted, publishing `catalogue.provider-symbol-mapping-deleted`.

## Failure Behavior

- Unmatched resolution queries or missing mapping deletion attempts return `CATALOGUE_NOT_FOUND`.
- Overlapping active intervals for identical provider, broker, and symbol return `CATALOGUE_MAPPING_OVERLAP`.
- Validation errors return `CATALOGUE_VALIDATION_FAILED`.

## Removal Behavior

Removing this feature withdraws its scoped `catalogue.map-providers@1` provider. Existing mapping records remain retained; subsequent requests fail closed with `CAPABILITY_UNAVAILABLE`.

## Evidence

Run `uv run python -m app.services.catalogue.provider_mapping.provider_mapping` for the executable scenario harness. Automated tests live in `tests/services/catalogue/provider_mapping/`.
