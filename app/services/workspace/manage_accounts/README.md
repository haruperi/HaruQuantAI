# Manage Accounts (`FEAT-WS-MANAGE_ACCOUNTS`)

## Purpose

Own the workstation's account registry and opaque server-side sessions:
user registration with versioned scrypt password hashing, login with
constant-time verification, digest-only session validation, and session
revocation. The feature persists to the shared workspace database
(`users`, `user_sessions`) and exposes every operation through the
operation-discriminated `workspace.manage-accounts@1` capability. Session
and CSRF tokens are generated here and returned exactly once; only their
SHA-256 digests are stored.

## Domain

`workspace`

## Provides

- `workspace.manage-accounts@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string / Path | `data/database/haruquantai.db` | Shared workspace SQLite database holding the account tables. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Opens exactly one SQLite connection per mounted feature generation and
  ensures the `users` and `user_sessions` tables exist (`IF NOT EXISTS`).
- Registers one scope cleanup callback closing the connection.
- Starts no sockets, listeners, or background tasks.

## Persistent State

Namespace `workspace.manage_accounts` retaining account records and
digest-only session records in the shared workspace database
(`users.user_id`, `user_sessions.session_digest`).

## Failure Behavior

- Username policy violations, short passwords, and duplicate usernames
  return `ACCOUNT_REGISTRATION_FAILED` failures without mutation.
- Unknown credentials, inactive accounts, and invalid or expired sessions
  return `ACCOUNT_AUTHENTICATION_FAILED` failures without mutation.
- LOGOUT of an unknown token succeeds idempotently.

## Removal Behavior

Unmounting the feature withdraws the `workspace.manage-accounts@1`
provider; consumers fail closed. Account and session rows are retained
(removal never purges accounts); re-mounting resumes on the same tables.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.workspace.manage_accounts._usage
```
