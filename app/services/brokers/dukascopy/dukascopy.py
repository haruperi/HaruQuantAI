"""Dukascopy direct broker channel service implementing ProviderBackend."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

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
from app.contracts.common.models import ProblemDetails
from app.services.brokers.dukascopy.candle_mapping import map_history_page
from app.services.brokers.dukascopy.candle_transport import _DukascopyCandleTransport
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.transport import _DukascopyTransport

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = logging.getLogger(__name__)


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


class DukascopyProviderService:
    """Dukascopy provider backend service."""

    def __init__(
        self,
        context: FeatureContext | None = None,
        config: DukascopyConfig | None = None,
        *,
        transport: _DukascopyTransport | None = None,
        candle_transport: _DukascopyCandleTransport | None = None,
    ) -> None:
        """Initialize the Dukascopy provider service.

        Args:
            context: Scoped runtime feature context.
            config: Strict immutable Dukascopy configuration.
            transport: Optional injected tick transport for testing.
            candle_transport: Optional injected candle transport for testing.
        """
        self._context = context
        self._config = config or DukascopyConfig()
        self._transport = transport or _DukascopyTransport(self._config)
        self._candle_transport = candle_transport or _DukascopyCandleTransport(
            self._config
        )

    async def _handle_open(
        self, request: ManageSessionsRequest
    ) -> ManageSessionsSuccess | BrokerFailure:
        session = request.session
        if self._config.probe_symbol is not None:
            try:
                await self._probe()
            except (OSError, TimeoutError, ValueError, ConnectionError) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_SESSION_NOT_READY",
                    problem=ProblemDetails(
                        type="urn:error:broker:session-not-ready",
                        title="Session Not Ready",
                        detail=f"Dukascopy connect probe failed: {err}",
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
            except (OSError, TimeoutError, ValueError, ConnectionError) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_SESSION_NOT_READY",
                    problem=ProblemDetails(
                        type="urn:error:broker:session-not-ready",
                        title="Session Not Ready",
                        detail=f"Dukascopy reconnect probe failed: {err}",
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
        """Handle session lifecycle operations for Dukascopy provider.

        Args:
            request: Session lifecycle request.

        Returns:
            ManageSessionsSuccess or BrokerFailure.
        """
        session = request.session
        if session is not None and session.environment != "SANDBOX":
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_ENVIRONMENT_MISMATCH",
                problem=ProblemDetails(
                    type="urn:error:broker:environment-mismatch",
                    title="Environment Mismatch",
                    detail=(
                        "Dukascopy provider only supports SANDBOX environment, "
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

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Handle provider-truth read operations for Dukascopy.

        Args:
            request: Provider-truth read request.

        Returns:
            ReadProviderStateSuccess or BrokerFailure.
        """
        session = request.session
        if session is not None and session.environment != "SANDBOX":
            return BrokerFailure(
                request_id=request.request_id,
                code="BROKER_ENVIRONMENT_MISMATCH",
                problem=ProblemDetails(
                    type="urn:error:broker:environment-mismatch",
                    title="Environment Mismatch",
                    detail=(
                        "Dukascopy provider only supports SANDBOX environment, "
                        f"got: {session.environment}"
                    ),
                    details={"environment": session.environment},
                ),
            )

        if request.operation == "PAGE_HISTORY":
            limit = request.page_size or 100
            symbol = self._config.probe_symbol or "EURUSD"
            timeframe = "H1"
            end = datetime.now(UTC)
            start = end - timedelta(days=7)
            try:
                batch = await self._candle_transport.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    limit=limit,
                )
                page = map_history_page(
                    batch.rows,
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    page_id=_gen_id(),
                    retrieved_at=_utc_now(),
                    start=start,
                    end=end,
                    truncated=batch.truncated,
                    requested_timeframe=timeframe,
                )
                return ReadProviderStateSuccess(
                    request_id=request.request_id,
                    page=page,
                )
            except (OSError, TimeoutError, ValueError, ConnectionError) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_VALIDATION_FAILED",
                    problem=ProblemDetails(
                        type="urn:error:broker:validation-failed",
                        title="History Page Retrieval Failed",
                        detail=f"Dukascopy historical candle retrieval failed: {err}",
                    ),
                )

        return BrokerFailure(
            request_id=request.request_id,
            code="BROKER_PROFILE_UNSUPPORTED",
            problem=ProblemDetails(
                type="urn:error:broker:profile-unsupported",
                title="Operation Unsupported",
                detail=f"Dukascopy provider does not support {request.operation}",
            ),
        )

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Reject all order transport operations as unsupported for Dukascopy.

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
                    "Dukascopy provider does not support order transport operation "
                    f"{request.operation}"
                ),
            ),
        )

    async def _probe(self) -> None:
        probe_symbol = self._config.probe_symbol or "EURUSD"
        end = datetime.now(UTC)
        start = end - timedelta(days=7)
        batch = await self._candle_transport.get_candles(
            symbol=probe_symbol,
            timeframe="H1",
            start=start,
            end=end,
            limit=1,
        )
        if not batch.rows:
            raise ValueError("Dukascopy probe returned no candle evidence")
