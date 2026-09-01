"""Binance gateway for focused Broker runtime contracts."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerAccountSnapshot,
    BrokerHistoryPage,
    BrokerSessionReadiness,
    BrokerSessionState,
    BrokerTradingState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ProviderRecord,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.common.models import JsonObject, Money, ProblemDetails
from app.kernel.identity import generate_uuid7
from app.kernel.serialization import to_json_safe
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.brokers.binance.adapter import BinanceBrokerAdapter
from app.services.brokers.binance.config import BinanceConfig

if TYPE_CHECKING:
    from app.contracts.broker.models import BrokerProviderKind, BrokerSessionRef
    from app.contracts.common.models import Uuid7


def _failure(request_id: Uuid7, code: str, detail: str) -> BrokerFailure:
    return BrokerFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(status=503 if code == "CAPABILITY_UNAVAILABLE" else 422, code=code, detail=detail, request_id=request_id),
    )


def _provider_record(value: object) -> ProviderRecord:
    raw = cast(JsonObject, to_json_safe(asdict(value)))
    provider_id = "unknown"
    for name in ("position_id", "order_id", "deal_id", "transaction_id"):
        candidate = getattr(value, name, None)
        if candidate is not None:
            provider_id = str(candidate)
            break
    return ProviderRecord(provider_id=provider_id, record=raw)


class BinanceGateway:
    """Provider-local Binance gateway consumed only by the dispatcher."""

    supports_order_transport = False

    def __init__(self, config: BinanceConfig) -> None:
        self._config = config
        self._adapter = BinanceBrokerAdapter(config.to_legacy_connection())

    @property
    def provider_kind(self) -> BrokerProviderKind:
        return cast("BrokerProviderKind", self._config.provider_kind)

    @property
    def profile_id(self) -> Uuid7:
        return cast("Uuid7", self._config.profile_id)

    async def close(self) -> None:
        """Release the owned Binance client/session."""
        await self._adapter.disconnect()

    def accepts(self, session: BrokerSessionRef) -> bool:
        return session.profile_id == self._config.profile_id and session.profile_version == self._config.profile_version

    def _validate_session(self, session: BrokerSessionRef, request_id: Uuid7) -> BrokerFailure | None:
        if not self.accepts(session):
            return _failure(request_id, "BROKER_PROFILE_UNSUPPORTED", "Session profile is not owned by this Binance feature")
        if session.environment != self._config.environment:
            return _failure(request_id, "BROKER_ENVIRONMENT_MISMATCH", "Configured and requested Binance environments differ")
        if session.account_ref != self._config.account_ref:
            return _failure(request_id, "BROKER_VALIDATION_FAILED", "Session account does not match the configured Binance account")
        return None

    async def manage_sessions(self, request: ManageSessionsRequest) -> ManageSessionsSuccess | BrokerFailure:
        assert request.session is not None
        session = request.session
        if failure := self._validate_session(session, request.request_id):
            return failure
        now = format_utc_timestamp(utc_now())
        if request.operation == "TRANSITION":
            assert request.state is not None
            return ManageSessionsSuccess(request_id=request.request_id, session=session, state=request.state)
        if request.operation == "OPEN":
            result = await self._adapter.connect()
            state_name = "READY" if result.status == "success" else "FAILED"
        elif request.operation == "RECONNECT":
            result = await self._adapter.reconnect()
            state_name = "READY" if result.status == "success" else "FAILED"
        elif request.operation == "CLOSE":
            result = await self._adapter.disconnect()
            state_name = "DISCONNECTED" if result.status == "success" else "FAILED"
        else:
            connected = await self._adapter.is_connected()
            ready = connected.status == "success" and bool(connected.data)
            readiness = BrokerSessionReadiness(
                session_id=session.session_id,
                generation=session.generation,
                transport="READY" if ready else "NOT_READY",
                authentication="READY" if ready and bool(self._config.credentials) else "NOT_READY",
                account_authorization="READY" if ready and bool(self._config.credentials) else "NOT_READY",
                trading_permission="NOT_READY",
                subscriptions="READY" if ready else "NOT_READY",
                environment_verified=session.environment == self._config.environment,
                resynchronized=ready,
                assessed_at=now,
            )
            return ManageSessionsSuccess(request_id=request.request_id, session=session, readiness=readiness)
        if state_name == "FAILED":
            return _failure(request.request_id, "BROKER_SESSION_NOT_READY", f"Binance {request.operation.lower()} failed")
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(session_id=session.session_id, generation=session.generation, connection_state=state_name, transitioned_at=now, reason=request.operation.lower()),  # type: ignore[arg-type]
        )

    async def read_provider_state(self, request: ReadProviderStateRequest) -> ReadProviderStateSuccess | BrokerFailure:
        assert request.session is not None
        session = request.session
        if failure := self._validate_session(session, request.request_id):
            return failure
        if request.operation == "READ_ACCOUNT":
            result = await self._adapter.get_account_info()
            if result.status != "success" or result.data is None:
                return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "This Binance profile does not expose account state through the donor adapter")
            info = result.data
            if info.currency is None or info.equity is None:
                return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "Binance account response lacks currency or equity")
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                account=BrokerAccountSnapshot(
                    session_id=session.session_id,
                    generation=session.generation,
                    account_ref=session.account_ref,
                    currency=info.currency,
                    equity=Money(amount=str(info.equity), currency=info.currency),
                    retrieved_at=format_utc_timestamp(info.retrieved_at),
                    balances={},
                    margin=Money(amount=str(info.margin), currency=info.currency) if info.margin is not None else None,
                    free_margin=Money(amount=str(info.free_margin), currency=info.currency) if info.free_margin is not None else None,
                    permissions=(),
                    provider_time=format_utc_timestamp(info.provider_timestamp) if info.provider_timestamp is not None else None,
                ),
            )
        if request.operation == "READ_TRADING_STATE":
            positions = await self._adapter.get_positions(limit=1_000)
            orders = await self._adapter.get_orders(limit=1_000)
            deals = await self._adapter.list_deal_history(limit=1_000)
            if any(result.status != "success" for result in (positions, orders, deals)):
                return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "This Binance profile does not expose complete trading state")
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                trading_state=BrokerTradingState(
                    session_id=session.session_id,
                    generation=session.generation,
                    retrieved_at=format_utc_timestamp(utc_now()),
                    positions=tuple(_provider_record(item) for item in positions.data.items) if positions.data is not None else (),
                    orders=tuple(_provider_record(item) for item in orders.data.items) if orders.data is not None else (),
                    deals=tuple(_provider_record(item) for item in deals.data.items) if deals.data is not None else (),
                ),
            )
        if request.operation == "PAGE_HISTORY":
            limit = request.page_size or 1_000
            page = await self._adapter.list_order_history(cursor=request.page_cursor, limit=limit)
            if page.status != "success" or page.data is None:
                return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "This Binance profile does not expose provider history through the donor adapter")
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                page=BrokerHistoryPage(
                    page_id=generate_uuid7(),
                    requested_count=limit,
                    returned_count=len(page.data.items),
                    is_truncated=page.data.truncated,
                    retrieved_at=format_utc_timestamp(utc_now()),
                    provider_cursor=page.data.next_cursor,
                    records=tuple(_provider_record(item) for item in page.data.items),
                ),
            )
        if request.operation == "READ_MARKET":
            return _failure(request.request_id, "BROKER_VALIDATION_FAILED", "READ_MARKET v1 does not carry the exact provider_symbol required by the Broker boundary")
        return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "Provider event normalization is published through the Kernel event bus")

    async def transport_orders(self, request: TransportOrdersRequest) -> TransportOrdersSuccess | BrokerFailure:
        """Fail closed because the current Binance donor has no released writes."""
        return _failure(request.request_id, "CAPABILITY_UNAVAILABLE", "Binance order transport is not implemented by this provider feature")
