# Plugin Manifests

> **Feature ID:** `FEAT-PLUG-DECLARE_MANIFESTS`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.declare-manifests@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| `max_package_size_bytes` | `int` | `52428800` | Maximum allowed size in bytes for plugin ZIP package archives. |
| `max_file_count` | `int` | `1000` | Maximum number of files permitted within a plugin ZIP package archive. |
| `strict_signatures` | `bool` | `false` | When true, packages without valid cryptographic signatures are rejected. |

## Purpose

Validate plugin identity, package integrity, compatibility, capabilities, permissions, and resource declarations.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-PLUG-DECLARE_PLUGIN_MANIFESTS` | `plugin_manifests.py::__main__` Scenario 1 | `tests/services/plugins/manifests/test_plugin_manifests.py::test_plug_declare_plugin_manifests` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.plugins.manifests.plugin_manifests
```

## Runtime Effects

- Inspects in-memory and on-disk plugin manifests and package ZIP archives.
- Rejects path traversal (zip slip), absolute paths, drive letters, symlinks, duplicate entries, case-fold collisions, and decompression bombs.
- Computes canonical package hashes across manifest metadata and file checksums.

## Persistent State

None. This feature is stateless and performs deterministic in-memory and read-only archive validation.

## Failure Behavior

- Malformed JSON in `plugin.json` raises `PluginManifestError`.
- Invalid reverse-DNS IDs, non-SemVer versions, missing API ranges, invalid types, or invalid resource limits raise `PluginManifestError`.
- Malicious ZIP files containing directory traversal (`..`), absolute paths, symlinks, duplicate entries, case-fold collisions, or payload checksum mismatches raise `PluginPackageValidationError`.
- Requests requiring the removed capability return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature makes plugin manifest parsing and package verification unavailable (`CAPABILITY_UNAVAILABLE`). Existing retained plugin bytes remain inert on disk.
