# Secure Local Access (`FEAT-WS-SECURE_LOCAL_ACCESS`)

> **Status:** Implemented and verified
> **Capability:** `workspace.secure-local-access@1`

## Domain

`workspace`

## Provides

`workspace.secure-local-access@1`

## Required Capabilities

`workspace.manage-accounts@1`

## Optional Capabilities

None.

## Purpose

Own opaque secret references, permitted adapter-only resolution, local launcher session
issuance, loopback binding enforcement, and operational readiness reporting. Configured
connectors and providers authenticate without exposing credentials to agents, widgets,
or exported artifacts.

## Public API and Dependencies

The canonical protocol is `app/contracts/workspace/secure_local_access.py`; request,
success, secret reference, and typed failure wire records live in
`app/contracts/workspace/secure_local_access.py` and `app/contracts/workspace/errors.py`.

- Provides: `workspace.secure-local-access@1`.
- Requires: `workspace.manage-accounts@1`, provided by `FEAT-WS-MANAGE_ACCOUNTS`.
- Optional capabilities: none.

Mount fails before registration when required account management capabilities are unavailable.
The service stores opaque metadata and plaintext secrets in zeroizable in-memory structures,
guaranteeing memory purge upon revocation and scope closure.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `default_session_ttl_seconds` | `int` | `3600` | Default time-to-live for issued local sessions in seconds (1 to 604800). |
| `enforce_loopback` | `bool` | `True` | Whether to strictly restrict client connections to loopback interfaces. |
| `allowed_remote_subnets` | `tuple[str, ...]` | `()` | Permitted remote subnets/hosts when remote access is authorized. |
| `require_authenticated_remote_policy` | `bool` | `True` | Whether nonlocal host bindings require authenticated remote policy. |

Unknown keys, wrong types, and out-of-bound values fail closed.

## Runtime Effects

Mount registers `workspace.secure-local-access@1`. It starts no unmanaged background
threads or unauthorized listeners. Closing its scope unregisters the capability and
zeroizes all stored secret material in memory.

## Persistent State

None. All secret references and local session tokens are held in bounded,
process-local, zeroizable in-memory structures and are cleared on disposal.
Plaintext secrets are never written to unencrypted disk, audit ledgers,
or wire schemas.

## Failure Behavior

- Secret resolution requests by `ui`, `agentic`, or `unauthorized` caller roles are
  rejected with `SecretResolutionDeniedError` without secret exposure.
- Adapter generation or purpose mismatches raise `SecretResolutionDeniedError`.
- Unknown secret references raise `SecretNotFoundError`.
- Revoked secret references raise `SecretRevokedError`.
- Unconnected launcher clients raise `SessionDeniedError`.
- Non-loopback client access when loopback is enforced raises `NonLoopbackAccessDeniedError`.
- Unauthorized remote host bindings raise `InvalidHostBindingError`.
- Public readiness exports redact all secrets and absolute filesystem paths.

## Removal Behavior

Removal withdraws only `workspace.secure-local-access@1`. Retained workspace and account
records remain intact; dependent connector operations lose secret resolution capability
and fail closed without silent fallback.

## Traceability

| Requirement | Acceptance evidence |
| --- | --- |
| `FR-TRC-WS-SECURE_LOCAL_ACCESS-001` | `test_traceability.py::test_trc_secure_local_access_001` |
| `FR-TRC-WS-SECURE_LOCAL_ACCESS-002` | `test_traceability.py::test_trc_secure_local_access_002` |
| `FR-TRC-WS-SECURE_LOCAL_ACCESS-003` | `test_traceability.py::test_trc_secure_local_access_003` |
| `NFR-TRC-WS-SECURE_LOCAL_ACCESS-001` | `test_lifecycle.py::test_trc_secure_local_access_nfr_001` |

Six-stage evidence is recorded in
`docs/dev/evidence/features/FEAT-WS-SECURE_LOCAL_ACCESS/acceptance.json`.

## Usage

### Interactive Python API Walkthrough

```python
from uuid import uuid7
from app.contracts.workspace.secure_local_access import (
    SecretCreateRequest,
    SecretResolveRequest,
)
from app.services.workspace.secure_local_access.config import SecureLocalAccessConfig
from app.services.workspace.secure_local_access.secure_local_access import (
    SecureLocalAccessService,
)

service = SecureLocalAccessService(config=SecureLocalAccessConfig())

# 1. Create opaque secret reference
ref = service.create_secret_reference(
    SecretCreateRequest(
        workspace_id=str(uuid7()),
        name="binance_key",
        secret_value="api_key_value_12345",  # pragma: allowlist secret
        allowed_adapter_generation="gen-1",
        allowed_purpose="market-data",
    )
)

# 2. Resolve inside adapter boundary
resolved = service.resolve_secret_reference(
    SecretResolveRequest(
        workspace_id=ref.workspace_id,
        secret_id=ref.secret_id,
        adapter_generation="gen-1",
        purpose="market-data",
        caller_role="adapter",
    )
)
print("Secret resolved within adapter boundary successfully.")
```

### Bounded Offline CLI Verification

Run the comprehensive offline verification scenario with:

```powershell
uv run python -m app.services.workspace.secure_local_access._usage
```
