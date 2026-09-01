"""Yahoo direct broker channel service implementing ProviderBackend."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
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
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.mapping import _provider_interval, map_history_page
from app.services.brokers.yahoo.transport import _YahooTransport

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


class YahooProviderService:
    """Yahoo Finance provider backend service."""

    def __init__(
        self,
        context: FeatureContext | None = None,
        config: YahooConfig | None = None,
        *,
        transport: _YahooTransport | None = None,
    ) -> None:
        """Initialize the Yahoo provider service.

        Args:
            context: Scoped runtime feature context.
            config: Strict immutable Yahoo configuration.
            transport: Optional injected transport for testing.
        """
        self._context = context
        self._config = config or YahooConfig()
        self._transport = transport or _YahooTransport(self._config)

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
                        detail=f"Yahoo connect probe failed: {err}",
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
                        detail=f"Yahoo reconnect probe failed: {err}",
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
        """Handle session lifecycle operations for Yahoo provider.

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
                        "Yahoo provider only supports SANDBOX environment, "
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
        """Handle provider-truth read operations for Yahoo.

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
                        "Yahoo provider only supports SANDBOX environment, "
                        f"got: {session.environment}"
                    ),
                    details={"environment": session.environment},
                ),
            )

        if request.operation == "PAGE_HISTORY":
            limit = request.page_size or 100
            symbol = self._config.probe_symbol or "SPY"
            timeframe = "1d"
            try:
                provider_tf = _provider_interval(timeframe)
                table = await self._transport.history(
                    symbol=symbol,
                    timeframe=provider_tf,
                )
                page = map_history_page(
                    table,
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
            except (OSError, TimeoutError, ValueError, ConnectionError) as err:
                return BrokerFailure(
                    request_id=request.request_id,
                    code="BROKER_VALIDATION_FAILED",
                    problem=ProblemDetails(
                        type="urn:error:broker:validation-failed",
                        title="History Page Retrieval Failed",
                        detail=f"Yahoo historical bar retrieval failed: {err}",
                    ),
                )

        return BrokerFailure(
            request_id=request.request_id,
            code="BROKER_PROFILE_UNSUPPORTED",
            problem=ProblemDetails(
                type="urn:error:broker:profile-unsupported",
                title="Operation Unsupported",
                detail=f"Yahoo provider does not support {request.operation}",
            ),
        )

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Reject all order transport operations as unsupported for research-only Yahoo.

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
                    "Yahoo provider does not support order transport operation "
                    f"{request.operation}"
                ),
            ),
        )

    async def _probe(self) -> None:
        probe_symbol = self._config.probe_symbol
        if probe_symbol is None:
            raise ValueError("Yahoo probe_symbol is required")
        table = await self._transport.history(
            symbol=probe_symbol,
            timeframe="1d",
        )
        if getattr(table, "empty", False):
            raise ValueError("Yahoo probe returned no provider evidence")
