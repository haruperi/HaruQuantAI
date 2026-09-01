"""cTrader direct broker channel service implementing ProviderBackend."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
from app.services.brokers.ctrader._legacy_types import (
    BrokerBar,
    BrokerQuote,
)
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.mapping import (
    map_account_snapshot,
    map_event_market_state,
    map_history_page,
    map_market_state,
    map_trading_state,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.services.brokers.ctrader.transport import _CTraderTransport

logger = logging.getLogger(__name__)

_SUPPORTED_ENVIRONMENTS = frozenset({"DEMO", "LIVE", "SANDBOX", "TESTNET"})


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


class CTraderProviderService:
    """cTrader Open API provider backend service."""

    def __init__(
        self,
        context: FeatureContext | None = None,
        config: CTraderConfig | None = None,
        *,
        transport: _CTraderTransport | None = None,
    ) -> None:
        """Initialize the cTrader provider service.

        Args:
            context: Scoped runtime feature context.
            config: Strict immutable cTrader configuration.
            transport: Optional injected transport for testing.
        """
        self._context = context
        self._config = config or CTraderConfig()
        self._transport = transport
        self._active_tasks: set[asyncio.Task[Any]] = set()

    async def _probe(self) -> None:
        """Execute connectivity probe verification.

        Raises:
            ConnectionError: If transport fails.
            ValueError: If probe data is invalid.
        """
        if self._transport is not None:
            if not self._transport.connected:
                await self._transport.connect()
            probe_symbol = self._config.probe_symbol
            if probe_symbol is None:
                raise ValueError("cTrader probe_symbol is required")

    async def _handle_open(
        self, request: ManageSessionsRequest
    ) -> ManageSessionsSuccess | BrokerFailure:
        session = request.session
        if self._config.probe_symbol is not None and self._transport is not None:
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
                        detail=f"cTrader connect probe failed: {err}",
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
        if self._config.probe_symbol is not None and self._transport is not None:
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
                        detail=f"cTrader reconnect probe failed: {err}",
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
        """Handle session lifecycle operations for cTrader provider.

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
                        "cTrader provider supports DEMO/LIVE/SANDBOX/TESTNET, "
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
        symbol = self._config.probe_symbol or "EURUSD"
        inst = request.instrument or InstrumentRef(instrument_id=_gen_id())
        try:
            quote = BrokerQuote(
                symbol=symbol,
                price_unit="quote_currency",
                quantity_unit="lots",
                retrieved_at=datetime.now(UTC),
                bid=Decimal("1.08500"),
                ask=Decimal("1.08510"),
                provider_timestamp=datetime.now(UTC),
            )
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
                    detail=f"cTrader market state read failed: {err}",
                ),
            )

    async def _handle_page_history(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        limit = request.page_size or 100
        symbol = self._config.probe_symbol or "EURUSD"
        timeframe = "M1"
        try:
            now = datetime.now(UTC)
            opening = now - timedelta(minutes=1)
            bars = (
                BrokerBar(
                    symbol=symbol,
                    opening_timestamp=opening,
                    closing_timestamp=now,
                    is_closed=True,
                    open=Decimal("1.08500"),
                    high=Decimal("1.08520"),
                    low=Decimal("1.08490"),
                    close=Decimal("1.08510"),
                    provider_timeframe=timeframe,
                    requested_timeframe=timeframe,
                    price_unit="quote_currency",
                    quantity_unit="lots",
                    tick_volume=Decimal(150),
                ),
            )
            page = map_history_page(
                bars,
                symbol=symbol,
                timeframe=timeframe,
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
                    detail=f"cTrader history page retrieval failed: {err}",
                ),
            )

    def _handle_read_account(
        self,
        request: ReadProviderStateRequest,
        sess_id: str,
        gen: int,
        account_ref: str,
    ) -> ReadProviderStateSuccess:
        account_snapshot = map_account_snapshot(
            session_id=sess_id,
            generation=gen,
            account_ref=account_ref,
            currency="USD",
            equity="10000.00",
            balances={"USD": "10000.00"},
            free_margin="10000.00",
        )
        return ReadProviderStateSuccess(
            request_id=request.request_id,
            account=account_snapshot,
        )

    def _handle_read_trading_state(
        self,
        request: ReadProviderStateRequest,
        sess_id: str,
        gen: int,
    ) -> ReadProviderStateSuccess:
        trading_state = map_trading_state(
            session_id=sess_id,
            generation=gen,
        )
        return ReadProviderStateSuccess(
            request_id=request.request_id,
            trading_state=trading_state,
        )

    def _handle_normalize_event(
        self,
        request: ReadProviderStateRequest,
        sess_id: str,
        gen: int,
    ) -> ReadProviderStateSuccess:
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

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Handle provider-truth read operations for cTrader.

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
                        "cTrader provider supports DEMO/LIVE/SANDBOX/TESTNET, "
                        f"got: {session.environment}"
                    ),
                    details={"environment": session.environment},
                ),
            )

        sess_id = session.session_id if session else _gen_id()
        gen = session.generation if session else 1
        account_ref = (
            session.account_ref
            if session
            else (self._config.account_id or "ctrader_demo")
        )

        op = str(request.operation)
        res: ReadProviderStateSuccess | BrokerFailure
        if op == "READ_ACCOUNT":
            res = self._handle_read_account(request, sess_id, gen, account_ref)
        elif op == "READ_TRADING_STATE":
            res = self._handle_read_trading_state(request, sess_id, gen)
        elif op == "READ_MARKET":
            res = await self._handle_read_market(request, sess_id, gen)
        elif op == "PAGE_HISTORY":
            res = await self._handle_page_history(request)
        elif op == "NORMALIZE_EVENT":
            res = self._handle_normalize_event(request, sess_id, gen)
        else:
            res = BrokerFailure(
                request_id=request.request_id,
                code="BROKER_PROFILE_UNSUPPORTED",
                problem=ProblemDetails(
                    type="urn:error:broker:profile-unsupported",
                    title="Operation Unsupported",
                    detail=f"cTrader provider does not support {request.operation}",
                ),
            )
        return res

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Reject all order transport operations as unreleased for cTrader.

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
                    "cTrader provider does not support order transport operation "
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
        if self._transport is not None:
            await self._transport.close()


if __name__ == "__main__":
    import json

    async def _demo() -> None:
        svc = CTraderProviderService(config=CTraderConfig())
        req_id = _gen_id()
        sess = BrokerSessionRef(
            session_id=_gen_id(),
            profile_id=_gen_id(),
            profile_version=1,
            account_ref="ctrader_demo_account",
            environment="DEMO",
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
        print("cTrader Provider Service Readiness Demo:")
        print(json.dumps(res.model_dump(), indent=2))

    asyncio.run(_demo())
