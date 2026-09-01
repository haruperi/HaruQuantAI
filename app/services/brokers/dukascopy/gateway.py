"""Dukascopy sandbox gateway for focused Broker runtime contracts."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerSessionReadiness,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.common.models import ProblemDetails
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.brokers.dukascopy.adapter import DukascopyBrokerAdapter
from app.services.brokers.dukascopy.config import DukascopyConfig

if TYPE_CHECKING:
    from app.contracts.broker.models import BrokerProviderKind, BrokerSessionRef
    from app.contracts.common.models import Uuid7


def _failure(request_id: Uuid7, code: str, detail: str) -> BrokerFailure:
    return BrokerFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(status=503 if code == "CAPABILITY_UNAVAILABLE" else 422, code=code, detail=detail, request_id=request_id),
    )


class DukascopyGateway:
    """Read-only Dukascopy provider gateway."""

    provider_kind: BrokerProviderKind = "DUKASCOPY"
    supports_order_transport = False

    def __init__(self, config: DukascopyConfig) -> None:
        self._config = config
        self._adapter = DukascopyBrokerAdapter(config.to_legacy_connection())

    @property
    def profile_id(self) -> Uuid7:
        return cast("Uuid7", self._config.profile_id)

    async def close(self) -> None:
        """Release provider-local state."""
        await self._adapter.disconnect()

    def accepts(self, session: BrokerSessionRef) -> bool:
        return session.profile_id == self._config.profile_id and session.profile_version == self._config.profile_version

    def _validate(self, session: BrokerSessionRef, request_id: Uuid7) -> BrokerFailure | None:
        if not self.accepts(session):
            return _failure(request_id, "BROKER_PROFILE_UNSUPPORTED", "Session profile is not owned by this Dukascopy feature")
        if session.environment != "SANDBOX":
            return _failure(request_id, "BROKER_ENVIRONMENT_MISMATCH", "Dukascopy sessions must be SANDBOX")
        if session.account_ref != self._config.account_ref:
            return _failure(request_id, "BROKER_VALIDATION_FAILED", "Session account_ref does not match the configured Dukascopy research profile")
        return None

    async def _probe(self) -> bool:
        """Probe the explicitly configured provider symbol without hidden aliases."""
        end = utc_now()
        result = await self._adapter.get_historical_bars(
            self._config.probe_symbol,
            "H1",
            end - timedelta(days=7),
            end,
            limit=1,
        )
        return result.status == "success" and result.data is not None and bool(result.data.items)

    async def manage_sessions(self, request: ManageSessionsRequest) -> ManageSessionsSuccess | BrokerFailure:
        assert request.session is not None
        session = request.session
        if failure := self._validate(session, request.request_id):
            return failure
        now = format_utc_timestamp(utc_now())
        if request.operation == "TRANSITION":
            assert request.state is not None
            return ManageSessionsSuccess(request_id=request.request_id, session=session, state=request.state)
        if request.operation in {"OPEN", "RECONNECT"}:
            ready = await self._probe()
            state_name = "READY" if ready else "FAILED"
        elif request.operation == "CLOSE":
            result = await self._adapter.disconnect()
            state_name = "DISCONNECTED" if result.status == "success" else "FAILED"
        else:
            ready = await self._probe()
            return ManageSessionsSuccess(
                request_id=request.request_id,
                session=session,
                readiness=BrokerSessionReadiness(
                    session_id=session.session_id,
                    generation=session.generation,
                    transport="READY" if ready else "NOT_READY",
                    authentication="READY" if ready else "NOT_READY",
                    account_authorization="NOT_READY",
                    trading_permission="NOT_READY",
                    subscriptions="NOT_READY",
                    environment_verified=True,
                    resynchronized=ready,
                    assessed_at=now,
                ),
            )
        if state_name == "FAILED":
            return _failure(request.request_id, "BROKER_SESSION_NOT_READY", f"Dukascopy {request.operation.lower()} failed")
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(session_id=session.session_id, generation=session.generation, connection_state=state_name, transitioned_at=now, reason=request.operation.lower()),  # type: ignore[arg-type]
        )

    async def read_provider_state(self, request: ReadProviderStateRequest) -> ReadProviderStateSuccess | BrokerFailure:
        assert request.session is not None
        if failure := self._validate(request.session, request.request_id):
            return failure
        if request.operation == "READ_MARKET":
            return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "READ_MARKET v1 lacks the exact provider_symbol/timeframe required for Dukascopy reads")
        return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "Dukascopy is a read-only market-data provider and this v1 operation is not representable")

    async def transport_orders(self, request: TransportOrdersRequest) -> TransportOrdersSuccess | BrokerFailure:
        """Reject all Dukascopy mutations structurally."""
        return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "Dukascopy is read-only and cannot transport orders")
