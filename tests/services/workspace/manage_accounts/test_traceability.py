"""Exact functional traceability evidence for FEAT-WS-MANAGE_ACCOUNTS."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import ManageAccountsRequest, ManageAccountsSuccess
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

_PASSWORD = "traceability-password"  # pragma: allowlist secret


class _MutableClock:
    """Deterministic aware clock for expiry acceptance evidence."""

    def __init__(self) -> None:
        self.value = datetime(2026, 9, 8, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, delta: timedelta) -> None:
        self.value += delta


def _request(operation: str, **values: object) -> ManageAccountsRequest:
    return ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        account_id="account-a",
        workspace_id="workspace-a",
        **values,  # type: ignore[arg-type]
    )


def _service(
    root: Path,
    clock: _MutableClock,
) -> tuple[AccountService, ExecutePersistenceService]:
    persistence = ExecutePersistenceService()
    return (
        AccountService(
            persistence,
            ManageAccountsConfig(database_path=root),
            clock=clock,
        ),
        persistence,
    )


@pytest.mark.asyncio
async def test_trc_manage_accounts_001(tmp_path: Path) -> None:
    """AT-WS-MANAGE_ACCOUNTS-001: expiry/revocation/scope deny pre-mutation."""
    clock = _MutableClock()
    service, persistence = _service(tmp_path / "workspace", clock)
    registered = await service.manage_accounts(
        _request("REGISTER", username="scope_user", password=_PASSWORD)
    )
    assert isinstance(registered, ManageAccountsSuccess)
    assert registered.user is not None
    assert registered.user.user_id.startswith("usr_")
    assert registered.user.account_id == "account-a"
    assert registered.user.workspace_id == "workspace-a"
    token = registered.session_token

    receiver: list[str] = []
    wrong_account = await service.manage_accounts(
        ManageAccountsRequest(
            request_id=str(uuid7()),
            capability_snapshot_id=str(uuid7()),
            operation="ME",
            account_id="account-b",
            workspace_id="workspace-a",
            session_token=token,
        )
    )
    if isinstance(wrong_account, ManageAccountsSuccess):
        receiver.append(wrong_account.user.user_id if wrong_account.user else "missing")
    assert isinstance(wrong_account, WorkspaceFailure)
    assert receiver == []

    clock.advance(timedelta(days=8))
    expired = await service.manage_accounts(_request("ME", session_token=token))
    if isinstance(expired, ManageAccountsSuccess):
        receiver.append(expired.user.user_id if expired.user else "missing")
    assert isinstance(expired, WorkspaceFailure)
    assert receiver == []

    logged_in = await service.manage_accounts(
        _request("LOGIN", username="scope_user", password=_PASSWORD)
    )
    assert isinstance(logged_in, ManageAccountsSuccess)
    await service.manage_accounts(
        _request("LOGOUT", session_token=logged_in.session_token)
    )
    revoked = await service.manage_accounts(
        _request("ME", session_token=logged_in.session_token)
    )
    if isinstance(revoked, ManageAccountsSuccess):
        receiver.append(revoked.user.user_id if revoked.user else "missing")
    assert isinstance(revoked, WorkspaceFailure)
    assert receiver == []
    service.close()
    persistence.close()


@pytest.mark.asyncio
async def test_trc_manage_accounts_002(tmp_path: Path) -> None:
    """AT-WS-MANAGE_ACCOUNTS-002: a captured identity is revalidated after revoke."""
    clock = _MutableClock()
    service, persistence = _service(tmp_path / "workspace", clock)
    registered = await service.manage_accounts(
        _request("REGISTER", username="resume_user", password=_PASSWORD)
    )
    assert isinstance(registered, ManageAccountsSuccess)
    assert registered.user is not None
    captured_snapshot = registered.user
    token = registered.session_token

    await service.manage_accounts(_request("LOGOUT", session_token=token))
    handoff_receiver: list[str] = []
    current = await service.manage_accounts(_request("ME", session_token=token))
    if isinstance(current, ManageAccountsSuccess):
        handoff_receiver.append(captured_snapshot.user_id)
    assert isinstance(current, WorkspaceFailure)
    assert current.code == "ACCOUNT_AUTHENTICATION_FAILED"
    assert handoff_receiver == []
    service.close()
    persistence.close()


@pytest.mark.asyncio
async def test_trc_manage_accounts_003(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AT-WS-MANAGE_ACCOUNTS-003: wire/log/audit fixtures contain no credentials."""
    caplog.set_level(logging.DEBUG, logger="haruquantai")
    clock = _MutableClock()
    service, persistence = _service(tmp_path / "workspace", clock)
    request = _request("REGISTER", username="audit_user", password=_PASSWORD)
    registered = await service.manage_accounts(request)
    assert isinstance(registered, ManageAccountsSuccess)
    token = registered.session_token
    csrf = registered.csrf_token
    audit = service.safe_session_audit_records(
        request_id=str(uuid7()),
        account_id="account-a",
    )
    assert audit

    wire = request.model_dump_json() + registered.model_dump_json()
    exported = json.dumps([asdict(row) for row in audit], sort_keys=True)
    rendered_logs = "\n".join(
        f"{record.getMessage()} {getattr(record, 'fields', {})!r}"
        for record in caplog.records
    )
    combined = wire + exported + rendered_logs
    forbidden = (
        _PASSWORD,
        token,
        csrf,
        "password_hash",
        "session_digest",
        "broker-secret",
    )
    assert all(value not in combined for value in forbidden)
    assert audit[0].authentication_audit_ref.startswith("auth_")
    service.close()
    persistence.close()
