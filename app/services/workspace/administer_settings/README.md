# Administer Settings (`FEAT-WS-ADMINISTER_SETTINGS`)

## Purpose

Own the workstation's administrator settings surface: the authoritative
manifest of editable non-secret system-setting definitions (value kinds,
allowed values, bounds, hot vs restart-required activation), versioned
system settings persistence served under the legacy uppercase wire keys the
workstation reads, write-only credential slots with audit history, and the
MT5 snapshot bridge runtime projection consumed by the composition root.

## Domain

`workspace`

## Provides

- `workspace.administer-settings@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string / Path | `data/database/haruquantai.db` | Shared workspace SQLite database holding `settings` and `settings_history`. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Holds no open connections; each operation opens one short-lived SQLite
  connection to the configured database.
- Starts no sockets, listeners, or background tasks.

## Persistent State

Namespace `workspace.administer_settings` retaining settings rows
(`settings.key`) and audit history (`settings_history.key`) in the shared
workspace database.

## Failure Behavior

- Absent database file raises `FileNotFoundError` to the caller; the
  capability reports no partial state.
- Credential material is stored write-only and never projected back.

## Removal Behavior

Unmounting the feature withdraws the `workspace.administer-settings@1`
provider; consumers fail closed. Settings rows and audit history are
retained; re-mounting resumes on the same tables.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.workspace.administer_settings._usage
```
