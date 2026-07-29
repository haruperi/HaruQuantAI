"""Integration evidence for WF-DATA-013 broker read-only enforcement."""

from __future__ import annotations

import pytest
from app.services.data import (
    build_account_snapshot_request,
    build_data_error,
    get_account_state_snapshot,
    is_read_only_broker_proxy,
)
from app.utils import generate_id


def test_account_evidence_wraps_every_injected_broker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The evidence boundary passes only a read-only proxy to its broker reader."""
    observed: list[bool] = []

    async def inspect_proxy(adapter: object, _request_id: str) -> object:
        observed.append(is_read_only_broker_proxy(adapter))
        raise build_data_error("SOURCE_UNAVAILABLE")

    monkeypatch.setattr(
        "app.services.data.evidence.account_state._fetch_from_adapter",
        inspect_proxy,
    )
    request = build_account_snapshot_request(
        source_id="fixture",
        account_id="account-1",
        max_age_seconds=60,
        request_id=generate_id("req"),
    )
    res = get_account_state_snapshot(request, object())  # type: ignore[arg-type]
    assert res.status == "error"
    assert res.error is not None
    assert res.error.code == "SOURCE_UNAVAILABLE"

    assert observed == [True]
