"""Integration evidence for WF-DATA-013 broker read-only enforcement."""

from __future__ import annotations

import pytest
from app.services.data.contracts import DataError
from app.services.data.evidence.account_contracts import (
    AccountSnapshotRequest,
)
from app.services.data.sources.read_only import ReadOnlyBrokerProxy
from app.utils import generate_id


def test_account_evidence_wraps_every_injected_broker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The evidence boundary passes only a read-only proxy to its broker reader."""
    observed: list[bool] = []

    async def inspect_proxy(adapter: object, _request_id: str) -> object:
        observed.append(isinstance(adapter, ReadOnlyBrokerProxy))
        raise DataError("SOURCE_UNAVAILABLE")

    monkeypatch.setattr(
        "app.services.data.evidence.account_state._fetch_from_adapter",
        inspect_proxy,
    )
    from app.services.data.evidence.account_state import get_account_state_snapshot

    request = AccountSnapshotRequest(
        source_id="fixture",
        account_id="account-1",
        max_age_seconds=60,
        request_id=generate_id("req"),
    )
    with pytest.raises(DataError):
        get_account_state_snapshot(request, object())  # type: ignore[arg-type]

    assert observed == [True]
