"""Composable Broker Provider Gateway domain service.

Dispatches explicitly addressed Broker operations to mounted provider backends
through FeatureContext without ranking, selection, fallback, or cross-provider
retries.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    PROVIDER_BINANCE_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
)
from app.contracts.broker.errors import BrokerFailure
from app.contracts.common.models import ProblemDetails
from app.services.brokers.provider_gateway.config import ProviderGatewayConfig

if TYPE_CHECKING:
    from app.contracts.broker.models import (
        BrokerProviderProfile,
        ManageSessionsRequest,
        ManageSessionsSuccess,
        ReadProviderStateRequest,
        ReadProviderStateSuccess,
        TransportOrdersRequest,
        TransportOrdersSuccess,
    )
    from app.contracts.broker.ports import ProviderBackend
    from app.kernel.capability import CapabilityKey
    from app.kernel.context import FeatureContext


_PROVIDER_KIND_MAP: dict[str, CapabilityKey[ProviderBackend]] = {
    "MT5": PROVIDER_METATRADER_CAPABILITY,
    "CTRADER": PROVIDER_CTRADER_CAPABILITY,
    "BINANCE_SPOT": PROVIDER_BINANCE_CAPABILITY,
    "BINANCE_USD_M": PROVIDER_BINANCE_CAPABILITY,
    "BINANCE_COIN_M": PROVIDER_BINANCE_CAPABILITY,
    "DUKASCOPY": PROVIDER_DUKASCOPY_CAPABILITY,
    "YAHOO": PROVIDER_YAHOO_CAPABILITY,
}

_PROVIDER_NAME_MAP: dict[str, CapabilityKey[ProviderBackend]] = {
    "metatrader": PROVIDER_METATRADER_CAPABILITY,
    "mt5": PROVIDER_METATRADER_CAPABILITY,
    "ctrader": PROVIDER_CTRADER_CAPABILITY,
    "binance": PROVIDER_BINANCE_CAPABILITY,
    "dukascopy": PROVIDER_DUKASCOPY_CAPABILITY,
    "yahoo": PROVIDER_YAHOO_CAPABILITY,
}


class ProviderGatewayService:
    """Dispatches explicitly addressed requests to mounted provider backends."""

    def __init__(
        self,
        context: FeatureContext,
        config: ProviderGatewayConfig | None = None,
    ) -> None:
        """Initialize the provider gateway service with runtime context.

        Args:
            context: Scoped runtime context for resolving provider backends.
            config: Optional gateway configuration dataclass.
        """
        self._context = context
        self._config = config or ProviderGatewayConfig()
        self._profiles: dict[str, CapabilityKey[ProviderBackend]] = {}
        self._sessions: dict[str, CapabilityKey[ProviderBackend]] = {}
        self._operations: dict[str, CapabilityKey[ProviderBackend]] = {}

    def register_profile(self, profile: BrokerProviderProfile) -> None:
        """Register a provider profile mapping its ID to the provider capability.

        Args:
            profile: Provider profile containing provider kind and profile ID.
        """
        cap_key = _PROVIDER_KIND_MAP.get(profile.kind)
        if cap_key is not None:
            self._profiles[str(profile.profile_id)] = cap_key

    def bind_profile(
        self,
        profile_id: str,
        capability_key: CapabilityKey[ProviderBackend],
    ) -> None:
        """Explicitly bind a profile ID to a provider capability key.

        Args:
            profile_id: Profile UUID string.
            capability_key: Target provider backend capability key.
        """
        self._profiles[str(profile_id)] = capability_key

    def bind_session(
        self,
        session_id: str,
        capability_key: CapabilityKey[ProviderBackend],
    ) -> None:
        """Explicitly bind a session ID to a provider capability key.

        Args:
            session_id: Session UUID string.
            capability_key: Target provider backend capability key.
        """
        self._sessions[str(session_id)] = capability_key

    def _resolve_session_key(
        self,
        session_id: str | None,
        profile_id: str | None,
    ) -> CapabilityKey[ProviderBackend] | None:
        """Resolve the provider capability key for a session and profile.

        Args:
            session_id: Session UUID string if present.
            profile_id: Profile UUID string if present.

        Returns:
            Resolved CapabilityKey or None if unmapped.
        """
        if session_id is not None and session_id in self._sessions:
            return self._sessions[session_id]
        if profile_id is not None and profile_id in self._profiles:
            key = self._profiles[profile_id]
            if session_id is not None:
                self._sessions[session_id] = key
            return key
        return None

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Dispatch a session lifecycle operation to the addressed backend.

        Args:
            request: Session lifecycle request.

        Returns:
            ManageSessionsSuccess on success, or BrokerFailure on failure.
        """
        session = request.session
        session_id = str(session.session_id) if session is not None else None
        profile_id = str(session.profile_id) if session is not None else None

        key = self._resolve_session_key(session_id, profile_id)
        if key is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail=f"No provider backend mapped for session '{session_id}'",
                ),
            )

        backend = self._context.optional(key)
        if backend is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail=f"Provider capability '{key.identifier}' is not mounted",
                    capability_key=key.identifier,
                ),
            )

        return await backend.manage_sessions(request)

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Dispatch a provider-truth read operation to the addressed backend.

        Args:
            request: Provider-truth read request.

        Returns:
            ReadProviderStateSuccess on success, or BrokerFailure on failure.
        """
        session = request.session
        session_id = str(session.session_id) if session is not None else None
        profile_id = str(session.profile_id) if session is not None else None

        key = self._resolve_session_key(session_id, profile_id)
        if key is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail=f"No provider backend mapped for session '{session_id}'",
                ),
            )

        backend = self._context.optional(key)
        if backend is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail=f"Provider capability '{key.identifier}' is not mounted",
                    capability_key=key.identifier,
                ),
            )

        return await backend.read_provider_state(request)

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Dispatch an order transport operation to the addressed backend.

        Args:
            request: Order transport request.

        Returns:
            TransportOrdersSuccess on success, or BrokerFailure on failure.
        """
        key: CapabilityKey[ProviderBackend] | None = None
        if request.operation == "JOURNAL":
            op_id = str(request.operation_id) if request.operation_id else None
            if op_id is not None and op_id in self._operations:
                key = self._operations[op_id]
        else:
            op_req = request.operation_request
            if op_req is not None:
                session = op_req.session
                session_id = str(session.session_id)
                profile_id = str(session.profile_id)
                key = self._resolve_session_key(session_id, profile_id)
                if key is not None:
                    self._operations[str(op_req.operation_id)] = key

        if key is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail="No provider backend mapped for transport operation",
                ),
            )

        backend = self._context.optional(key)
        if backend is None:
            return BrokerFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    code="CAPABILITY_UNAVAILABLE",
                    detail=f"Provider capability '{key.identifier}' is not mounted",
                    capability_key=key.identifier,
                ),
            )

        return await backend.transport_orders(request)


async def _run_usage_scenario() -> int:
    """Execute scenario harness verifying ProviderGatewayService behavior.

    Returns:
        Zero on successful scenario run.
    """
    import uuid
    from datetime import UTC, datetime

    from app.contracts.broker.models import (
        BrokerSessionReadiness,
        BrokerSessionRef,
        BrokerSessionState,
        ManageSessionsRequest,
        ManageSessionsSuccess,
    )
    from app.kernel.context import DefaultFeatureContext
    from app.kernel.scope import FeatureScope

    # Mock provider backend
    class MockProviderBackend:
        async def manage_sessions(
            self,
            request: ManageSessionsRequest,
        ) -> ManageSessionsSuccess | BrokerFailure:
            sess_id = (
                request.session.session_id
                if request.session is not None
                else str(uuid.uuid7())
            )
            gen = request.session.generation if request.session is not None else 1
            return ManageSessionsSuccess(
                request_id=request.request_id,
                session=request.session,
                state=BrokerSessionState(
                    session_id=sess_id,
                    generation=gen,
                    connection_state="READY",
                    transitioned_at=datetime.now(UTC).strftime(
                        "%Y-%m-%dT%H:%M:%S.000000Z"
                    ),
                ),
                readiness=BrokerSessionReadiness(
                    session_id=sess_id,
                    generation=gen,
                    transport="READY",
                    authentication="READY",
                    account_authorization="READY",
                    trading_permission="READY",
                    subscriptions="READY",
                    environment_verified=True,
                    resynchronized=True,
                    assessed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
                ),
            )

        async def read_provider_state(
            self,
            request: ReadProviderStateRequest,
        ) -> ReadProviderStateSuccess | BrokerFailure:
            from app.contracts.broker.models import ReadProviderStateSuccess

            return ReadProviderStateSuccess(request_id=request.request_id)

        async def transport_orders(
            self,
            request: TransportOrdersRequest,
        ) -> TransportOrdersSuccess | BrokerFailure:
            from app.contracts.broker.models import TransportOrdersSuccess

            return TransportOrdersSuccess(request_id=request.request_id)

    from app.services.brokers.provider_gateway.manifest import SPEC

    mock_backend = MockProviderBackend()
    providers: dict[object, object] = {PROVIDER_METATRADER_CAPABILITY: mock_backend}
    scope = FeatureScope(owner_id="FEAT-BRK-DISPATCH_PROVIDERS")
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=providers.get,
        provider_registrar=lambda cap, impl, _sc: providers.__setitem__(cap, impl),
    )
    gateway = ProviderGatewayService(context=context)

    # Generate synthetic session
    profile_id = str(uuid.uuid7())
    session_id = str(uuid.uuid7())
    gateway.bind_profile(profile_id, PROVIDER_METATRADER_CAPABILITY)

    session_ref = BrokerSessionRef(
        session_id=session_id,
        profile_id=profile_id,
        profile_version=1,
        account_ref="acc_123",
        environment="DEMO",
        generation=1,
    )
    req = ManageSessionsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="OPEN",
        session=session_ref,
    )

    result = await gateway.manage_sessions(req)
    if isinstance(result, BrokerFailure):
        print(f"[FAIL] Expected success, got BrokerFailure: {result.code}")
        return 1

    print(f"[PASS] ManageSessions result: {result.outcome}")

    # Test unavailable capability
    unavail_profile = str(uuid.uuid7())
    unavail_session = str(uuid.uuid7())
    gateway.bind_profile(unavail_profile, PROVIDER_CTRADER_CAPABILITY)
    unavail_session_ref = BrokerSessionRef(
        session_id=unavail_session,
        profile_id=unavail_profile,
        profile_version=1,
        account_ref="acc_456",
        environment="DEMO",
        generation=1,
    )
    unavail_req = ManageSessionsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="OPEN",
        session=unavail_session_ref,
    )
    unavail_res = await gateway.manage_sessions(unavail_req)
    if (
        not isinstance(unavail_res, BrokerFailure)
        or unavail_res.code != "CAPABILITY_UNAVAILABLE"
    ):
        print(f"[FAIL] Expected CAPABILITY_UNAVAILABLE, got {unavail_res}")
        return 1

    print("[PASS] Unavailable provider correctly returned CAPABILITY_UNAVAILABLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run_usage_scenario()))
