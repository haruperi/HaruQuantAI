# Plugin Lifecycle

**Feature ID:** `FEAT-PLUG-MANAGE_LIFECYCLE`

## Domain

`plugins`

## Purpose

Provide the `plugins.manage-lifecycle@1` capability for durable, transactional
plugin package installation, workspace activation changes, upgrades, and
removal.

## Provides

`plugins.manage-lifecycle@1`

## Required Capabilities

`plugins.declare-manifests@1`

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | non-blank string | Yes | Explicit SQLite file for lifecycle-owned retained state. |

Unknown, missing, blank, and non-string values are rejected before any
filesystem access. The path has no implicit default or ambient workspace lookup.

## Persistent State

`plugins.lifecycle` schema version 1 retains `plugins`, `plugin_versions`, and
`plugin_activations` in the configured SQLite database. Retention is `retain`:
feature removal and `REMOVE` do not purge package receipts or immutable versions.

## Runtime Effects

Mount validates `plugins.declare-manifests@1` through `FeatureContext` and
stages only `plugins.manage-lifecycle@1`. SQLite connections are opened per
operation, use `BEGIN IMMEDIATE`, enable foreign keys, and close in all paths.

## Operations

`INSTALL` stores an immutable receipt/version and returns no activation.
`ENABLE` creates or transitions one workspace activation to `ENABLED`.
`DISABLE` transitions an enabled activation to `DISABLED`. `UPGRADE` stores the
new immutable version and replaces the addressed activation atomically while
retaining its prior version. `REMOVE` deletes only the workspace activation.
All successful results leave `lifecycle=None`; sandbox lifecycle state belongs
to `FEAT-PLUG-SANDBOX_PERMISSIONS`.

## Failure Behavior

Missing installations or activations, illegal transitions, mismatched upgrade
addressors, immutable receipt conflicts, and failed SQLite transactions return
`PluginFailure` with `PLUGIN_LIFECYCLE_CONFLICT`. Validation and mutation share
one write transaction, so failed upgrades preserve the prior usable activation.

## Removal Behavior

Removing this feature withdraws its scoped provider. Existing receipt, version,
and activation records remain retained and diagnosable; no plugin code executes
and no state is purged by this feature.

## Evidence

Run `uv run python -m app.services.plugins.lifecycle.plugin_lifecycle` for the
bounded install/enable/upgrade/rollback/disable/remove scenario. Focused SQLite,
configuration, and mount evidence lives in `tests/services/plugins/lifecycle/`.
