# Plugin Manifests

> **Feature ID:** `FEAT-PLUG-DECLARE_MANIFESTS`
> **Status:** `COMPLETE`

## Domain

`plugins`

## Provides

- `plugins.declare-manifests@1`

## Required Capabilities

None (root feature with respect to the Plugins domain dependency graph).

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `max_package_size_bytes` | `int` | `52428800` | Maximum allowed size in bytes for plugin ZIP package archives. |
| `max_file_count` | `int` | `1000` | Maximum number of files permitted within a plugin ZIP package archive. |
| `strict_signatures` | `bool` | `false` | When true, packages without valid cryptographic signatures are rejected. |

## Purpose

Validate plugin identity, package integrity, compatibility, capabilities, permissions, resource limits, contributions, and migration declarations.

## Requirements and Traceability

| Requirement ID | Responsibility / Required Behavior | Acceptance ID | Expected Oracle |
| --- | --- | --- | --- |
| `FR-TRC-PLUG-DECLARE_MANIFESTS-001` | Validate extension identity/version, contributions, dependencies, compatible contracts, resources/hashes, permission/egress/resource requests and migration declarations. | `AT-PLUG-DECLARE_MANIFESTS-001` | Unknown/overbroad permissions or incompatible majors fail before activation; manifest inspection executes no package code. |
| `FR-TRC-PLUG-DECLARE_MANIFESTS-002` | Return a bounded compatibility/permission/ownership preview with exact versioned metadata. | `AT-PLUG-DECLARE_MANIFESTS-002` | A display name cannot grant authority or replace another contribution identity. |
| `NFR-TRC-PLUG-DECLARE_MANIFESTS-001` | Removing FEAT-PLUG-DECLARE_MANIFESTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. | `ATN-PLUG-DECLARE_MANIFESTS-001` | Disable and physically remove declare_manifests; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |

## Usage Scenarios

Run the executable usage demonstration:

```powershell
uv run --frozen python -m app.services.plugins.declare_manifests._usage
```

## Runtime Effects

- Parses in-memory and on-disk plugin manifests and package ZIP archives statically.
- Rejects path traversal (zip slip), absolute paths, drive letters, symlinks, duplicate entries, case-fold collisions, and decompression bombs.
- Rejects unknown permission keys, absolute paths in permissions, wildcard network endpoints, and malformed secret names.
- Computes canonical SHA-256 package hashes across manifest metadata and verified file checksums.
- Generates bounded previews linking authority exclusively to canonical `(plugin_id, contribution_id)` pairs.

## Persistent State

None. This feature is stateless and performs deterministic in-memory and read-only archive validation.

## Failure Behavior

- Malformed JSON in `plugin.json` raises `PluginManifestError`.
- Invalid reverse-DNS IDs, non-SemVer versions, missing API ranges, invalid types, or invalid resource limits raise `PluginManifestError`.
- Incompatible major versions (e.g. API range demanding host major 2+) raise `PluginManifestError`.
- Malicious ZIP files containing directory traversal (`..`), absolute paths, symlinks, duplicate entries, case-fold collisions, or payload checksum mismatches raise `PluginPackageValidationError`.
- Requests requiring the removed capability yield unavailable state.

## Removal Behavior

Removing this feature withdraws `plugins.declare-manifests@1` from the capability registry. Consumers requesting manifest parsing or package inspection receive an unavailable error. Unrelated capabilities remain completely operational and retained plugin bytes on disk remain intact.
