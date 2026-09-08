"""Structured logging safety tests for FEAT-WS-MANAGE_ACCOUNTS."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid7

import pytest
from app.composition.logging import BoundLogger
from app.contracts.workspace.models import ManageAccountsRequest
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.accounts import AccountService, logger
from app.services.workspace.manage_accounts.config import ManageAccountsConfig


@pytest.mark.asyncio
async def test_account_logs_are_structured_and_credential_free(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Operational events expose stable codes but no sensitive account data."""
    assert isinstance(logger, BoundLogger)
    caplog.set_level(logging.DEBUG, logger="haruquantai")
    persistence = ExecutePersistenceService()
    service = AccountService(
        persistence,
        ManageAccountsConfig(database_path=tmp_path / "workspace"),
    )
    password = "logging-password-sentinel"  # pragma: allowlist secret
    request = ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="REGISTER",
        account_id="account-sensitive-sentinel",
        workspace_id="workspace-sensitive-sentinel",
        username="logging_user",
        password=password,
    )
    result = await service.manage_accounts(request)
    token = getattr(result, "session_token", "")
    rendered = "\n".join(
        f"{record.getMessage()} {getattr(record, 'fields', {})!r}"
        for record in caplog.records
    )
    assert "workspace.accounts.request.admitted" in {
        getattr(record, "event", None) for record in caplog.records
    }
    forbidden = (
        password,
        token,
        "account-sensitive-sentinel",
        "workspace-sensitive-sentinel",
        "logging_user",
        "auth_",
    )
    assert all(value not in rendered for value in forbidden)
    service.close()
    persistence.close()
