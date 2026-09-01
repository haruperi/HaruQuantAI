"""Focused behavior tests for explicit Broker provider dispatch."""

from __future__ import annotations

from typing import cast

import pytest

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
)
from app.kernel.identity import generate_uuid7
from app.services.brokers.dispatch_providers.config import DispatchProvidersConfig
from app.services.brokers.dispatch_providers.dispatch import DispatchProvidersService


class _Gateway:
    provider_kind = "YAHOO"
    supports_order_transport = False

    def __init__(self, profile_id: str) -> None:
        self._profile_id = profile_id

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def accepts(self, session: BrokerSessionRef) -> bool:
        return session.profile_id == self._profile_id

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess:
        assert request.session is not None
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=request.session,
            state=BrokerSessionState(
                session_id=request.session.session_id,
                generation=request.session.generation,
                connection_state="READY",
                transitioned_at="2026-09-01T00:00:00.000000Z",
            ),
        )

    async def read_provider_state(self, request: object) -> object:
        return request

    async def transport_orders(self, request: object) -> object:
        return request


def _session(profile_id: str) -> BrokerSessionRef:
    return BrokerSessionRef(
        session_id=generate_uuid7(),
        profile_id=profile_id,
        profile_version=1,
        account_ref="research",
        environment="SANDBOX",
        generation=1,
    )


@pytest.mark.asyncio
async def test_dispatches_to_exact_profile_without_fallback() -> None:
    profile_id = generate_uuid7()
    gateway = _Gateway(profile_id)
    service = DispatchProvidersService(
        (cast("object", gateway),),  # type: ignore[arg-type]
        DispatchProvidersConfig(),
    )
    session = _session(profile_id)
    result = await service.manage_sessions(
        ManageSessionsRequest(
            request_id=generate_uuid7(),
            capability_snapshot_id=generate_uuid7(),
            operation="OPEN",
            session=session,
        )
    )
    assert isinstance(result, ManageSessionsSuccess)
    assert result.session == session


@pytest.mark.asyncio
async def test_missing_profile_fails_instead_of_falling_back() -> None:
    service = DispatchProvidersService(
        (cast("object", _Gateway(generate_uuid7())),),  # type: ignore[arg-type]
        DispatchProvidersConfig(),
    )
    result = await service.manage_sessions(
        ManageSessionsRequest(
            request_id=generate_uuid7(),
            capability_snapshot_id=generate_uuid7(),
            operation="OPEN",
            session=_session(generate_uuid7()),
        )
    )
    assert isinstance(result, BrokerFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"


def test_duplicate_profile_ownership_is_rejected() -> None:
    profile_id = generate_uuid7()
    with pytest.raises(ValueError, match="profile_id ownership"):
        DispatchProvidersService(
            (
                cast("object", _Gateway(profile_id)),
                cast("object", _Gateway(profile_id)),
            ),  # type: ignore[arg-type]
            DispatchProvidersConfig(),
        )
