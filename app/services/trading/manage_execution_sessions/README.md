# Manage Execution Sessions (`FEAT-TRD-MANAGE_EXECUTION_SESSIONS`)

## Purpose

Own trading execution sessions, default session selection, lifecycle state
transitions (active/stopped), account profile projections, and instrument
constraints. The feature persists to the shared workspace database
(`trading_profiles`, `instruments`) and exposes every operation through the
operation-discriminated `trading.manage-execution-sessions@1` capability.

## Domain

`trading`

## Provides

- `trading.manage-execution-sessions@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string / Path | `data/database/haruquantai.db` | Shared workspace SQLite database holding trading profiles and instrument tables. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Opens exactly one SQLite connection per mounted feature generation and
  ensures the `trading_profiles` and `instruments` tables exist (`IF NOT EXISTS`).
- Seeds default paper/demo execution profiles and default instruments if missing.
- Registers one scope cleanup callback closing the connection.
- Starts no sockets, listeners, or background tasks.

## Persistent State

Namespace `trading.manage_execution_sessions` retaining execution session
profiles (`trading_profiles`) and instrument definitions (`instruments`) in
the database.

## Failure Behavior

- Requesting an unknown session for STOP returns `SESSION_NOT_FOUND` failure.
- Specifying an invalid mode or missing required parameters returns
  `TRADING_VALIDATION_FAILED` failure without mutation.
- Unsupported operation discriminators return `TRADING_QUERY_INVALID` failure.

## Removal Behavior

Unmounting the feature withdraws the `trading.manage-execution-sessions@1`
provider; consumers fail closed. Profile and instrument rows are retained
in the database; re-mounting resumes on the existing records.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.trading.manage_execution_sessions._usage
```
