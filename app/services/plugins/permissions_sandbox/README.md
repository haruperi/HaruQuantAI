# Plugin Permissions Sandbox

> **Feature ID:** `FEAT-PLUG-SANDBOX_PERMISSIONS`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.sandbox-permissions@1`

## Required Capabilities

None

## Optional Capabilities

None

## Purpose

`FEAT-PLUG-SANDBOX_PERMISSIONS` provides `plugins.sandbox-permissions@1` as a
stateless, removable feature. It owns manifest-narrowed grants and pure-Python
execution outside the control-plane process. Grants are in-memory only and are
discarded when the feature scope closes.

The one async capability method supports:

- `GRANT`: validates a supplied immutable manifest, package hash, requested
  permissions, and resource limits. The effective grant is the intersection of
  manifest declarations, the explicit request, and feature ceilings.
- `INSPECT`: reads one exact `(plugin_id, workspace_id, version)` grant.
- `EXECUTE`: resolves that grant, maps its package hash to a process-local root,
  resolves approved `SecretRef` names to host environment-variable names, and
  invokes the manifest entry point through the isolated worker.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `package_roots` | mapping | required | Lowercase SHA-256 package hash to absolute local directory. |
| `secret_env_names` | mapping | `{}` | Workspace `SecretRef` name to host environment-variable name. |
| `ceilings` | mapping | deny by default | Maximum permissions and CPU, memory, elapsed-time, and output limits. |
| `max_protocol_bytes` | integer | `1048576` | Canonical framed JSON input/output bound, at least 256 bytes. |
| `enforcement_mode` | string | `CURRENT_PLATFORM` | Selects the mandatory current-platform OS enforcement backend. |

All keys are strict; unknown or unsafe values fail before publication. Secret
values are read only for `EXECUTE` and never enter contracts or state.

## Runtime Effects

Workers use the base Python executable with `-I`, no shell, a length-prefixed
canonical JSON exchange, a minimized environment, and an audit hook installed
before plugin loading. The hook denies undeclared file, socket, process, shell,
and native-extension access. The parent uses a Windows kill-on-close Job Object
with one active process and hard memory/CPU controls, or a POSIX process group
plus `prlimit`; unsupported enforcement fails closed. The parent enforces
elapsed and output bounds, terminates the group/job on timeout or failure,
validates the complete response before returning it, and discards the temporary
output root on every path.

## Persistent State

None. Effective grants are process-local memory and are cleared on removal.

## Failure Behavior

Failures use `PLUGIN_PERMISSION_DENIED`, `PLUGIN_SECRET_FORBIDDEN`, or
`PLUGIN_SANDBOX_EXECUTION_FAILED`. Diagnostics expose only stable exception
classes. Resolved secret values are recursively replaced with `[REDACTED]`
before response construction.

## Removal Behavior

Closing the feature scope withdraws its capability and clears all in-memory
grants. Running child processes are bounded by kill-on-close jobs or process
groups and are terminated by their owning execution path.

## Evidence

- Primary module and named scenarios:
  `python -m app.services.plugins.permissions_sandbox.plugin_permissions_sandbox`
- Focused tests: `tests/services/plugins/permissions_sandbox/`
- Real current-platform workers: success, timeout, crash, invalid output, Job
  Object/process-group termination, and secret-canary redaction.
- Removal: `test_feature.py` proves failed mount publishes nothing and scope
  close withdraws the provider and clears process-local grants.
