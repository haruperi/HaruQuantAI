# Instrument Catalogue

**Feature ID:** `FEAT-CAT-CATALOG_INSTRUMENTS`

## Domain

`catalogue`

## Purpose

Provide the `catalogue.catalog-instruments@1` capability for defining, versioning, retaining, and protecting canonical instruments.

## Provides

`catalogue.catalog-instruments@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string or null | No | Optional SQLite database path for persistent storage; defaults to in-memory SQLite. |

## Persistent State

`catalogue.instruments` schema version 1 retains `instruments`, `instrument_versions`, and `manifest_references` in the configured SQLite database. Retention policy is `retain`: feature unloading or uninstallation preserves immutable instrument version definitions.

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `catalogue.catalog-instruments@1`. Scoped SQLite connections are opened per operation and closed in all execution paths.

## Operations

- `GET`: Retrieve specific or latest canonical instrument version by instrument reference.
- `LIST`: Paginated query of active latest canonical instrument versions.
- `UPSERT_VERSION`: Define initial version 1 or create subsequent versions (`version == latest + 1`), updating half-open validity intervals and publishing `catalogue.instrument-version-created`.
- `DELETE_VERSION`: Safely delete unreferenced version matching expected version, enforcing reference protection from committed manifests and publishing `catalogue.instrument-version-deleted`.

## Failure Behavior

- Unknown instrument references return `CATALOGUE_NOT_FOUND`.
- Version mismatches or sequencing violations return `CATALOGUE_VERSION_CONFLICT`.
- Deletion attempts on versions referenced by committed manifests return `CATALOGUE_REFERENCE_PROTECTED`.

## Removal Behavior

Removing this feature withdraws its scoped `catalogue.catalog-instruments@1` provider. Existing version records and manifest references remain retained; subsequent requests fail closed with `CAPABILITY_UNAVAILABLE`.

## Evidence

Run `uv run python -m app.services.catalogue.instrument_catalogue.instrument_catalogue` for the executable scenario harness. Automated tests live in `tests/services/catalogue/instrument_catalogue/`.
