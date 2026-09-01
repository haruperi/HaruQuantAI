# Plugin Development Compatibility

> **Feature ID:** `FEAT-PLUG-MAINTAIN_COMPATIBILITY`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.maintain-compatibility@1`

## Required Capabilities

- `plugins.declare-manifests@1`
- `plugins.register-contributions@1`

## Optional Capabilities

None

## Configuration

None. The feature accepts no configuration keys.

## Purpose

Build deterministic local reference ZIP artifacts from canonical manifest bytes
and sorted payload entries, validate them and contribution fixtures through
public capabilities, then publish one global in-memory plugin API compatibility
policy.

## Runtime Effects

- Validates ZIP packages without executing their payloads.
- Produces byte-reproducible reference packages with fixed ZIP metadata.
- Captures only validation-event level counts; log messages, paths, payloads,
  plugin IDs, permission entries, and secret values are never retained.
- Produces package/conformance reports with declaration counts only.
- Publishes one replacement-only compatibility policy scoped to this feature.

## Persistent State

None. Compatibility policy is cleared on unmount and no plugin data is changed.

## Failure Behavior

- Invalid package, fixture, SemVer, or range grammar returns `PLUGIN_VALIDATION_FAILED`.
- A missing policy or unsupported API version returns `PLUGIN_INCOMPATIBLE` with
  a precise plugin-safe diagnostic.
- Ranges allow only ANDed `>`, `>=`, `<`, `<=`, and `=` SemVer 2 comparators;
  prereleases require an explicit prerelease comparator and build metadata has
  no precedence effect.

## Removal Behavior

Removing this feature withdraws `plugins.maintain-compatibility@1` and clears
development/conformance tooling. Installed plugins retain their pinned contracts;
requests for the removed capability degrade as `CAPABILITY_UNAVAILABLE`.

## Evidence

- Usage harness: `plugin_development_compatibility.py::__main__`.
- Focused tests: `tests/services/plugins/development_compatibility/`.
