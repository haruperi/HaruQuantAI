"""Binance direct broker channel service implementing ProviderBackend."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    BrokerSessionReadiness,
    BrokerSessionRef,
    BrokerSessionState,
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import ProblemDetails
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.mapping import (
    _map_quote,
    _provider_interval,
    map_event_market_state,
    map_history_page,
    map_market_state,
)
from app.services.brokers.binance.transport import _BinanceTransport

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = logging.getLogger(__name__)

_SUPPORTED_ENVIRONMENTS = frozenset({"TESTNET", "SANDBOX", "LIVE"})


def _gen_id() -> str:
    return str(uuid.uuid7())


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def _readiness(session: BrokerSessionRef | None) -> BrokerSessionReadiness:
    return BrokerSessionReadiness(
        session_id=session.session_id if session else _gen_id(),
        generation=session.generation if session else 1,
        transport="READY",
        authentication="READY",
        account_authorization="READY",
        trading_permission="NOT_READY",
        subscriptions="NOT_READY",
        environment_verified=True,
        resynchronized=True,
        assessed_at=_utc_now(),
    )


class BinanceProviderService:
    """Binance Spot provider backend service."""

    def __init__(
        self,
        context: FeatureContext | None = None,
        config: BinanceConfig | None = None,
        *,
        transport: _BinanceTransport | None = None,
    ) -> None:
        """Initialize the Binance provider service.

        Args:
            context: Scoped runtime feature context.
            config: Strict immutable Binance configuration.
            transport: Optional injected transport for testing.
        """
        self._context = context
        self._config = config or BinanceConfig()
        self._transport = transport or _BinanceTransport(self._config)
        self._active_tasks: set[asyncio.Task[Any]] = set()

    async def _probe(self) -> None:
        """Execute connectivity probe verification.

        Raises:
            ValueError: If probe ticker data is invalid.
        """
        if not self._transport.is_connected:
            await self._transport.connect()
        else:
            await self._transport.call("ping")
        probe_symbol = self._config.probe_symbol
        if probe_symbol is not None:
            value = await self._transport.call(
                "get_orderbook_ticker", symbol=probe_symbol
            )
            if not value or "bidPrice" not in value:
                raise ValueError("Binance probe returned invalid ticker evidence")

    async def _handle_open(
        self, request: ManageSessionsRequest
    ) -> ManageSessionsSuccess | BrokerFailure:
        session = request.session
        if self._config.probe_symbol is not None:
            try:
                await self._probe()
            except (
                ImportError,
                OSError,
                TimeoutError,
                ValueError,
                ConnectionError,
            ) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_SESSION_NOT_READY",
                    problem=ProblemDetails(
                        type="urn:error:broker:session-not-ready",
                        title="Session Not Ready",
                        detail=f"Binance connect probe failed: {err}",
                    ),
                )
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(
                session_id=session.session_id if session else _gen_id(),
                generation=session.generation if session else 1,
                connection_state="READY",
                transitioned_at=_utc_now(),
            ),
            readiness=_readiness(session),
        )

    async def _handle_reconnect(
        self, request: ManageSessionsRequest
    ) -> ManageSessionsSuccess | BrokerFailure:
        session = request.session
        if self._config.probe_symbol is not None:
            try:
                await self._probe()
            except (
                ImportError,
                OSError,
                TimeoutError,
                ValueError,
                ConnectionError,
            ) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_SESSION_NOT_READY",
                    problem=ProblemDetails(
                        type="urn:error:broker:session-not-ready",
                        title="Session Not Ready",
                        detail=f"Binance reconnect probe failed: {err}",
                    ),
                )
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(
                session_id=session.session_id if session else _gen_id(),
                generation=session.generation if session else 1,
                connection_state="READY",
                transitioned_at=_utc_now(),
            ),
        )

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Handle session lifecycle operations for Binance provider.

        Args:
            request: Session lifecycle request.

        Returns:
            ManageSessionsSuccess or BrokerFailure.
        """
        session = request.session
        if session is not None and session.environment not in _SUPPORTED_ENVIRONMENTS:
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_ENVIRONMENT_MISMATCH",
                problem=ProblemDetails(
                    type="urn:error:broker:environment-mismatch",
                    title="Environment Mismatch",
                    detail=(
                        "Binance provider supports TESTNET/SANDBOX/LIVE, "
                        f"got: {session.environment}"
                    ),
                    details={"environment": session.environment},
                ),
            )

        if request.operation == "OPEN":
            return await self._handle_open(request)
        if request.operation == "TRANSITION":
            return ManageSessionsSuccess(
                request_id=request.request_id, session=session, state=request.state
            )
        if request.operation == "RECONNECT":
            return await self._handle_reconnect(request)
        if request.operation == "ASSESS_READINESS":
            return ManageSessionsSuccess(
                request_id=request.request_id,
                session=session,
                readiness=_readiness(session),
            )
        # CLOSE
        await self.close()
        return ManageSessionsSuccess(
            request_id=request.request_id,
            session=session,
            state=BrokerSessionState(
                session_id=session.session_id if session else _gen_id(),
                generation=session.generation if session else 1,
                connection_state="DISCONNECTED",
                transitioned_at=_utc_now(),
            ),
        )

    async def _handle_read_market(
        self,
        request: ReadProviderStateRequest,
        sess_id: str,
        gen: int,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        symbol = self._config.probe_symbol or "BTCUSDT"
        inst = request.instrument or InstrumentRef(instrument_id=_gen_id())
        try:
            value = await self._transport.call("get_orderbook_ticker", symbol=symbol)
            quote = _map_quote(value, symbol)
            market_state = map_market_state(
                session_id=sess_id,
                generation=gen,
                instrument=inst,
                provider_symbol=symbol,
                quote=quote,
            )
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                market=market_state,
            )
        except (
            ImportError,
            OSError,
            TimeoutError,
            ValueError,
            ConnectionError,
        ) as err:
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:broker:validation-failed",
                    title="Market Read Failed",
                    detail=f"Binance market state read failed: {err}",
                ),
            )

    async def _handle_page_history(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        limit = request.page_size or 100
        symbol = self._config.probe_symbol or "BTCUSDT"
        timeframe = "1h"
        try:
            provider_tf = _provider_interval(timeframe)
            values = await self._transport.call(
                "get_klines",
                symbol=symbol,
                interval=provider_tf,
                limit=limit,
            )
            page = map_history_page(
                values,
                symbol=symbol,
                timeframe=provider_tf,
                limit=limit,
                page_id=_gen_id(),
                retrieved_at=_utc_now(),
                requested_timeframe=timeframe,
            )
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                page=page,
            )
        except (
            ImportError,
            OSError,
            TimeoutError,
            ValueError,
            ConnectionError,
        ) as err:
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:broker:validation-failed",
                    title="History Page Retrieval Failed",
                    detail=f"Binance historical kline retrieval failed: {err}",
                ),
            )

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Handle provider-truth read operations for Binance.

        Args:
            request: Provider-truth read request.

        Returns:
            ReadProviderStateSuccess or BrokerFailure.
        """
        session = request.session
        if session is not None and session.environment not in _SUPPORTED_ENVIRONMENTS:
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_ENVIRONMENT_MISMATCH",
                problem=ProblemDetails(
                    type="urn:error:broker:environment-mismatch",
                    title="Environment Mismatch",
                    detail=(
                        "Binance provider supports TESTNET/SANDBOX/LIVE, "
                        f"got: {session.environment}"
                    ),
                    details={"environment": session.environment},
                ),
            )

        sess_id = session.session_id if session else _gen_id()
        gen = session.generation if session else 1

        if request.operation == "READ_MARKET":
            return await self._handle_read_market(request, sess_id, gen)
        if request.operation == "PAGE_HISTORY":
            return await self._handle_page_history(request)
        if request.operation == "NORMALIZE_EVENT":
            raw_event = request.raw_event or {}
            market_state = map_event_market_state(
                session_id=sess_id,
                generation=gen,
                raw_event=raw_event,
                instrument=request.instrument,
            )
            return ReadProviderStateSuccess(
                request_id=request.request_id,
                market=market_state,
            )

        return BrokerFailure(
            request_id=request.request_id,
            code="BROKER_PROFILE_UNSUPPORTED",
            problem=ProblemDetails(
                type="urn:error:broker:profile-unsupported",
                title="Operation Unsupported",
                detail=f"Binance provider does not support {request.operation}",
            ),
        )

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Reject all order transport operations as unreleased for Binance.

        Args:
            request: Order transport request.

        Returns:
            BrokerFailure with BROKER_PROFILE_UNSUPPORTED.
        """
        return BrokerFailure(
            request_id=request.request_id,
            code="BROKER_PROFILE_UNSUPPORTED",
            problem=ProblemDetails(
                type="urn:error:broker:profile-unsupported",
                title="Operation Unsupported",
                detail=(
                    "Binance provider does not support order transport operation "
                    f"{request.operation}"
                ),
            ),
        )

    async def close(self) -> None:
        """Close transport and cancel tracked background tasks."""
        for task in tuple(self._active_tasks):
            if not task.done():
                task.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            self._active_tasks.clear()
        await self._transport.close()


if __name__ == "__main__":
    import json

    async def _demo() -> None:
        svc = BinanceProviderService(config=BinanceConfig())
        req_id = _gen_id()
        sess = BrokerSessionRef(
            session_id=_gen_id(),
            profile_id=_gen_id(),
            profile_version=1,
            account_ref="testnet_account",
            environment="TESTNET",
            generation=1,
        )
        res = await svc.manage_sessions(
            ManageSessionsRequest(
                request_id=req_id,
                capability_snapshot_id=_gen_id(),
                operation="ASSESS_READINESS",
                session=sess,
            )
        )
        print("Binance Provider Service Readiness Demo:")
        print(json.dumps(res.model_dump(), indent=2))

    asyncio.run(_demo())
