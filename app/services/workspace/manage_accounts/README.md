# Manage Accounts (`FEAT-WS-MANAGE_ACCOUNTS`)

> **Status:** Implemented and verified
> **Capability:** `workspace.manage-accounts@1`

## Domain

`workspace`

## Provides

`workspace.manage-accounts@1`

## Required Capabilities

`workspace.persistence@1`

## Optional Capabilities

None.

## Purpose

Own workstation account registration and account/workspace-bound opaque sessions.
The feature applies versioned scrypt password hashing, stores only session digests,
revalidates every identity read against current retained state, and returns a bounded
identity projection with a safe `authentication_audit_ref`. Interfaces owns cookie
and CSRF transport; this feature does not mint roles or widget permissions.

## Public API and Dependencies

The canonical protocol is `app/contracts/workspace/manage_accounts.py`; request,
success, account, and typed failure wire records remain in
`app/contracts/workspace/models.py` and `app/contracts/workspace/errors.py`.

- Provides: `workspace.manage-accounts@1`.
- Requires: `workspace.persistence@1`, provided by
  `FEAT-WS-EXECUTE_PERSISTENCE`.
- Optional capabilities: none.

Mount fails before registration when persistence is unavailable. All feature-owned
database operations live in `_persistence.py` and use only the public persistence
capability; this package never opens a raw database connection.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | `str` or `Path` | `<repo>/data/database/haruquantai.db` | Path naming the canonical `haruquantai.db` or its parent database directory. |

Unknown keys, wrong types, and non-canonical database filenames fail closed.

## Runtime Effects

Mount applies the two ordered additive migrations through persistence and registers
only `workspace.manage-accounts@1`. It starts no sockets, listeners, or background
tasks. Closing its scope withdraws that capability without closing the shared
persistence provider.

## Persistent State

Namespace `workspace.manage_accounts`, schema version 2, retention policy `RETAIN`.
The namespace owns `users` and `user_sessions`; session material is stored only as
SHA-256 digests, with account/workspace scope and an opaque audit reference.
Closing the feature does not purge retained rows; remounting recovers those rows.

## Failure Behavior

- Invalid username/password policy and duplicate usernames return
  `ACCOUNT_REGISTRATION_FAILED` without partial mutation.
- Unknown credentials, inactive accounts, expired/revoked sessions, and account or
  workspace scope mismatch return `ACCOUNT_AUTHENTICATION_FAILED` before a receiver
  can consume an identity.
- Every `ME` call performs a new persistence read; a captured UI identity is never
  treated as current authorization.
- `LOGOUT` is idempotent for an unknown or already-revoked token.
- Public model serialization, structured logs, and safe audit exports exclude
  passwords, raw session/CSRF tokens, hashes, digests, and broker credentials.

## Removal Behavior

Removal withdraws only `workspace.manage-accounts@1`. The shared persistence
provider and unrelated capabilities remain mounted, and account/session rows remain
available to a later remount. No substitute account provider is selected silently.

## Traceability

| Requirement | Acceptance evidence |
| --- | --- |
| `FR-TRC-WS-MANAGE_ACCOUNTS-001` | `test_traceability.py::test_trc_manage_accounts_001` |
| `FR-TRC-WS-MANAGE_ACCOUNTS-002` | `test_traceability.py::test_trc_manage_accounts_002` |
| `FR-TRC-WS-MANAGE_ACCOUNTS-003` | `test_traceability.py::test_trc_manage_accounts_003` |
| `NFR-TRC-WS-MANAGE_ACCOUNTS-001` | `test_lifecycle.py::test_trc_manage_accounts_nfr_001` |

Composition, logging, configuration, legacy compatibility, Interfaces gateway, API,
UI client/context, and generated-contract checks provide the remaining six-stage
evidence recorded in
`docs/dev/evidence/features/FEAT-WS-MANAGE_ACCOUNTS/acceptance.json`.

## Usage

### Interactive Python API Walkthrough

```python
import asyncio
from uuid import uuid7
from app.contracts.workspace.models import ManageAccountsRequest
from app.services.workspace.execute_persistence.execute_persistence import ExecutePersistenceService
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

async def main() -> None:
    # 1. Initialize services pointing to the central haruquantai.db
    persistence = ExecutePersistenceService()
    accounts = AccountService(persistence, ManageAccountsConfig())

    # 2. Register a new user
    reg_req = ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="REGISTER",
        username="trader_alice",
        password="SuperSecurePassword123!",  # pragma: allowlist secret
        runtime_profile="research",
    )
    reg_res = await accounts.manage_accounts(reg_req)
    print(f"Registered user: {reg_res.user.username} (ID: {reg_res.user.user_id})")

    # 3. Revalidate current session via 'ME'
    me_req = ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="ME",
        session_token=reg_res.session_token,
    )
    me_res = await accounts.manage_accounts(me_req)
    print(f"Session valid for: {me_res.user.username}, expires: {me_res.user.expires_at}")

    # 4. Logout (revokes session token)
    logout_req = ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LOGOUT",
        session_token=reg_res.session_token,
    )
    logout_res = await accounts.manage_accounts(logout_req)
    print(f"Logged out: {logout_res.revoked}")

asyncio.run(main())
```

### Bounded Offline CLI Verification

Run the comprehensive offline verification scenario with:

```powershell
uv run python -m app.services.workspace.manage_accounts._usage
```

It mounts the public persistence provider through entry-point discovery, proves
registration/current identity, wrong-scope denial, revoke-before-revalidation,
safe audit output, exact capability withdrawal, retained-state remount, and cleanup.
