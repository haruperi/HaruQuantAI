"""Stateful Trading live/demo lifecycle with injected authority dependencies."""

# ruff: noqa: BLE001 - lifecycle boundaries normalize injected failures.

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import datetime
from hashlib import sha256
from typing import TYPE_CHECKING, Any, Literal

from app.composition.logging import get_logger
from app.contracts.common.models import create_audit_event
from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_json
from app.services.brokers import (
    get_broker_adapter_contract_version,
    get_broker_adapter_schema_id,
    get_broker_connection_environment,
    get_broker_connection_id,
    get_broker_feature_flag_environment,
    get_broker_feature_flag_id,
    is_broker_connection_enabled,
)
from app.services.trading.contracts import TradingError
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.services.trading.contracts.models import (
    JsonValue,
    TradingRequest,
)
from app.services.trading.contracts.responses import success_trading_response
from app.services.trading.live.config import _LiveRuntimeConfig, _validate_live_config
from app.services.trading.monitoring import (
    OperationalEvent,
    emit_runtime_event,
)
from app.services.trading.validation import ReadinessAssessment

type StandardResponse[T] = Any
ActionPolicyVerdict = Any
KillSwitchState = Any
RiskDecisionPackage = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

type AuthContext = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.trading.state import TradingStateStore

type _LifecycleStep = Callable[[], Awaitable[bool]]
type BrokerConnection = object
type BrokerAdapter = object
type BrokerFeatureFlags = object
type _RiskDecisionSource = Callable[[TradingRequest], RiskDecisionPackage | None]
type _ActionPolicySource = Callable[[TradingRequest], ActionPolicyVerdict | None]
type _KillSwitchSource = Callable[[TradingRequest], Sequence[KillSwitchState]]
type _ReadinessSource = Callable[
    [TradingRequest, Mapping[str, JsonValue]], ReadinessAssessment
]
type _AdapterCapabilitySource = Callable[[TradingRequest], Mapping[str, JsonValue]]
type _AuthContextSource = Callable[[TradingRequest], AuthContext]
type _AuditSink = Callable[[object], None]
type _EventSink = Callable[[OperationalEvent], None]


class LiveSession:
    """Own live/demo admission, typed authority sources, and safe shutdown."""

    def __init__(
        self,
        *,
        store: TradingStateStore,
        connection: BrokerConnection | None,
        broker_adapter: BrokerAdapter | None,
        feature_flags: BrokerFeatureFlags | None,
        risk_decision_source: _RiskDecisionSource,
        action_policy_source: _ActionPolicySource,
        kill_switch_source: _KillSwitchSource,
        readiness_source: _ReadinessSource,
        adapter_capability_source: _AdapterCapabilitySource,
        auth_context_source: _AuthContextSource,
        pre_audit_sink: _AuditSink,
        event_sink: _EventSink,
        startup_reconcile: _LifecycleStep,
        drain_in_flight: _LifecycleStep,
        flush_evidence: _LifecycleStep,
        shutdown_reconcile: _LifecycleStep,
        clock: Callable[[], datetime],
    ) -> None:
        """Initialize one dependency-injected lifecycle object.

        Args:
            store: Trading-owned state persistence port.
            connection: Composition-created Brokers connection config.
            broker_adapter: Injected async Brokers adapter.
            feature_flags: Current Brokers capability evidence.
            risk_decision_source: Current exact Risk-decision reader.
            action_policy_source: Current action-policy verdict reader.
            kill_switch_source: Applicable Risk kill-switch hierarchy reader.
            readiness_source: Current Data/route readiness assessor.
            adapter_capability_source: Normalized adapter capability reader.
            auth_context_source: Exact authenticated principal context reader.
            pre_audit_sink: Fail-closed pre-mutation audit boundary.
            event_sink: Operational-event publication boundary.
            startup_reconcile: Startup authority reconciliation operation.
            drain_in_flight: Bounded shutdown drain operation.
            flush_evidence: Bounded evidence flush operation.
            shutdown_reconcile: Final shutdown reconciliation operation.
            clock: Injected aware UTC clock.
        """
        logger.info("Constructing dependency-injected Trading LiveSession")
        self._store = store
        self._connection = connection
        self._broker_adapter = broker_adapter
        self._feature_flags = feature_flags
        self._risk_decision_source = risk_decision_source
        self._action_policy_source = action_policy_source
        self._kill_switch_source = kill_switch_source
        self._readiness_source = readiness_source
        self._adapter_capability_source = adapter_capability_source
        self._auth_context_source = auth_context_source
        self._pre_audit_sink = pre_audit_sink
        self._event_sink = event_sink
        self._startup_reconcile = startup_reconcile
        self._drain_in_flight = drain_in_flight
        self._flush_evidence = flush_evidence
        self._shutdown_reconcile = shutdown_reconcile
        self._clock = clock
        self._config: _LiveRuntimeConfig | None = None
        self._started = False
        self._admission_enabled = False
        self._reconciliation_ready = False
        self._health = "not_started"
        self._unresolved_steps: tuple[str, ...] = ()
        self._lifecycle_request_id = generate_id("req")
        self._lifecycle_workflow_id = generate_id("wf")
        self._lifecycle_correlation_id = generate_id("cor")

    @property
    def config(self) -> _LiveRuntimeConfig:
        """Return validated runtime settings.

        Returns:
            Current validated settings.

        Raises:
            TradingError: If the session has not been configured.
        """
        logger.debug("Reading LiveSession validated config")
        if self._config is None:
            raise TradingError("CONFIGURATION_INVALID", "Live session is unconfigured")
        return self._config

    @property
    def started(self) -> bool:
        """Return whether lifecycle startup has run.

        Returns:
            Actual started state.
        """
        logger.debug("Reading LiveSession started state")
        return self._started

    @property
    def admission_enabled(self) -> bool:
        """Return whether mutation admission is currently enabled.

        Returns:
            Actual admission state.
        """
        logger.debug("Reading LiveSession admission state")
        return self._admission_enabled

    @property
    def reconciliation_ready(self) -> bool:
        """Return whether reconciliation currently proves authority.

        Returns:
            Actual reconciliation state.
        """
        logger.debug("Reading LiveSession reconciliation state")
        return self._reconciliation_ready

    @property
    def store(self) -> TradingStateStore:
        """Return the injected Trading state port.

        Returns:
            Injected state store.
        """
        logger.debug("Reading LiveSession state-store port")
        return self._store

    def risk_decision_for(
        self, request: TradingRequest
    ) -> StandardResponse[RiskDecisionPackage | None]:
        """Read the current Risk decision for a request.

        Args:
            request: Governed Trading request.

        Returns:
            Current Risk decision or ``None``.
        """
        logger.debug("Reading LiveSession Risk decision")
        try:
            value = self._risk_decision_source(request)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            value, operation="trading.live.risk_decision_for", legacy_status="available"
        )

    def action_policy_for(
        self, request: TradingRequest
    ) -> StandardResponse[ActionPolicyVerdict | None]:
        """Read the current Risk action-policy verdict.

        Args:
            request: Governed Trading request.

        Returns:
            Current action-policy verdict or ``None``.
        """
        logger.debug("Reading LiveSession action-policy verdict")
        try:
            value = self._action_policy_source(request)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            value, operation="trading.live.action_policy_for", legacy_status="available"
        )

    def kill_switches_for(
        self, request: TradingRequest
    ) -> StandardResponse[Sequence[KillSwitchState]]:
        """Read every applicable Risk kill-switch scope.

        Args:
            request: Governed Trading request.

        Returns:
            Applicable canonical switch states.
        """
        logger.debug("Reading LiveSession kill-switch hierarchy")
        try:
            value = self._kill_switch_source(request)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            value, operation="trading.live.kill_switches_for", legacy_status="available"
        )

    def readiness_for(
        self,
        request: TradingRequest,
        evidence: Mapping[str, JsonValue],
    ) -> StandardResponse[ReadinessAssessment]:
        """Assess current execution readiness through the injected source.

        Args:
            request: Governed Trading request.
            evidence: JSON-safe readiness facts and references.

        Returns:
            Current deterministic readiness assessment.
        """
        logger.debug("Reading LiveSession execution readiness")
        try:
            value = self._readiness_source(request, evidence)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            value, operation="trading.live.readiness_for", legacy_status="assessed"
        )

    def adapter_capability_for(
        self,
        request: TradingRequest,
    ) -> StandardResponse[Mapping[str, JsonValue]]:
        """Read normalized adapter capability for one request.

        Args:
            request: Governed Trading request.

        Returns:
            Current normalized capability evidence.
        """
        logger.debug("Reading LiveSession adapter capability")
        try:
            value = self._adapter_capability_source(request)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            value,
            operation="trading.live.adapter_capability_for",
            legacy_status="available",
        )

    def _write_pre_audit_value(
        self,
        request: TradingRequest,
        evidence: Mapping[str, JsonValue],
    ) -> None:
        """Write fail-closed pre-mutation audit evidence.

        Args:
            request: Exact governed request being audited.
            evidence: Redacted governed-action evidence.

        Raises:
            TradingError: If authenticated context is absent or trace-mismatched.
        """
        logger.info("Writing LiveSession pre-mutation audit evidence")
        auth = self._auth_context_source(request)
        if (
            auth.request_id != request.request_id
            or auth.workflow_id != request.workflow_id
            or auth.correlation_id != request.correlation_id
        ):
            raise TradingError("AUDIT_FAILED", "Audit context trace is mismatched")
        event = create_audit_event(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=generate_id("evt"),
            timestamp=self._clock(),
            domain="trading",
            action=request.action,
            principal_id=auth.principal_id,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            payload={
                "workflow_id": request.workflow_id,
                "evidence": canonical_json(_redacted_envelope_data(evidence)),
            },
        )
        self._pre_audit_sink(event)

    def write_pre_audit(
        self,
        request: TradingRequest,
        evidence: Mapping[str, JsonValue],
    ) -> StandardResponse[None]:
        """Write pre-mutation audit evidence in a standard response.

        Args:
            request: Governed trading request envelope.
            evidence: Route fact and environment evidence mapping.

        Returns:
            Standard response containing no data or a canonical error.
        """
        try:
            self._write_pre_audit_value(request, evidence)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"request_id": request.request_id})
        return success_trading_response(
            None,
            operation="trading.live.write_pre_audit",
            risk_level="critical",
            read_only=False,
            writes_file=True,
            legacy_status="audited",
        )

    def now(self) -> datetime:
        """Read the injected current UTC time.

        Returns:
            Current injected time.
        """
        logger.debug("Reading LiveSession injected clock")
        return self._clock()

    def _envelope(
        self,
        *,
        operation: str,
        status: str,
        message: str,
        data: Mapping[str, JsonValue],
    ) -> StandardResponse[Mapping[str, JsonValue]]:
        """Build a canonical lifecycle envelope.

        Args:
            operation: Lifecycle operation name.
            status: Canonical result status.
            message: Bounded result summary.
            data: JSON-safe lifecycle facts.

        Returns:
            Canonical Trading envelope.
        """
        logger.debug("Building LiveSession envelope for %s", operation)
        redacted_data = _redacted_envelope_data(data)
        return success_trading_response(
            redacted_data,
            operation=operation,
            message=message,
            risk_level="critical",
            request_id=self._lifecycle_request_id,
            correlation_id=self._lifecycle_correlation_id,
            read_only=operation.endswith(".status"),
            modifies_database=not operation.endswith(".status"),
            places_trade=(
                not operation.endswith(".status")
                and self._config is not None
                and self._config.execution_route == "live"
            ),
            requires_network=(
                not operation.endswith(".status")
                and self._config is not None
                and self._config.execution_route in {"demo", "live"}
            ),
            legacy_status=status,
            extensions={
                "route": self._config.execution_route if self._config else None
            },
        )

    def _publish_health(self, state: str) -> None:
        """Publish current lifecycle health evidence.

        Args:
            state: Actual session health state.

        Raises:
            TradingError: If health evidence cannot be published.
        """
        logger.info("Publishing LiveSession health state %s", state)
        now = self._clock()
        digest = sha256(
            canonical_json({"state": state, "occurred_at": now}).encode()
        ).hexdigest()
        event_response = emit_runtime_event(
            OperationalEvent(
                event_id=f"trd-live-{digest}",
                event_type="HEALTH_CHANGED",
                severity="info" if state in {"ready", "stopped"} else "warning",
                occurred_at=now,
                request_id=self._lifecycle_request_id,
                workflow_id=self._lifecycle_workflow_id,
                correlation_id=self._lifecycle_correlation_id,
                facts={"state": state},
                source_refs={"data_authority_id": self.config.data_authority_id},
            ),
            self._event_sink,
        )
        if event_response.status == "error":
            raise TradingError("SERVICE_UNAVAILABLE", "Lifecycle health event failed")

    def _validate_authorities(self, evidence: Mapping[str, JsonValue]) -> None:
        """Validate injected Brokers/Data authority evidence.

        Args:
            evidence: Startup facts and references.

        Raises:
            TradingError: If authority, security, or environment evidence fails.
        """
        logger.debug("Validating LiveSession injected authorities")
        config = self.config
        connection = self._connection
        flags = self._feature_flags
        adapter = self._broker_adapter
        if connection is None or flags is None or adapter is None:
            raise TradingError(
                "SERVICE_UNAVAILABLE", "Live session authority is absent"
            )
        live_environment = get_broker_connection_environment(connection) == "live"
        if (config.execution_route == "live") != live_environment:
            raise TradingError("CONFIGURATION_INVALID", "Broker environment is unsafe")
        if (
            not is_broker_connection_enabled(connection)
            or get_broker_feature_flag_id(flags) != get_broker_connection_id(connection)
            or get_broker_feature_flag_environment(flags)
            != get_broker_connection_environment(connection)
            or get_broker_adapter_contract_version(adapter) != "v1"
            or get_broker_adapter_schema_id(adapter) != "brokers.adapter.v1"
        ):
            raise TradingError(
                "ADAPTER_INCOMPATIBLE", "Broker authority is incompatible"
            )
        if evidence.get("data_authority_id") != config.data_authority_id:
            raise TradingError("SCOPE_MISMATCH", "Data authority does not match config")
        if evidence.get("adapter_security_profile") != "approved":
            raise TradingError("PERMISSION_DENIED", "Adapter security is not approved")
        if evidence.get("startup_evidence_fresh") is not True:
            raise TradingError("STALE_EVIDENCE", "Startup evidence is not current")

    async def _start_value(
        self,
        config: Mapping[str, JsonValue],
        evidence: Mapping[str, JsonValue],
    ) -> StandardResponse[Mapping[str, JsonValue]]:
        """Validate configuration and reconcile before enabling admission.

        Args:
            config: Exact runtime configuration without secret material.
            evidence: JSON-safe startup facts and references.

        Returns:
            Actual package-only, blocked, or mutation-enabled session status.

        Raises:
            TradingError: If config, authority, security, or reconciliation fails.
        """
        logger.info("Starting Trading LiveSession")
        self._config = _validate_live_config(config)
        self._validate_authorities(evidence)
        self._started = True
        self._admission_enabled = False
        try:
            self._reconciliation_ready = await self._startup_reconcile()
        except Exception as error:
            raise TradingError(
                "RECONCILIATION_REQUIRED",
                "Startup reconciliation dependency failed",
            ) from error
        if not self._reconciliation_ready:
            self._health = "reconciliation_required"
            self._unresolved_steps = ("startup_reconciliation",)
            self._publish_health(self._health)
            return self._envelope(
                operation="live_session.start",
                status="blocked",
                message="Live session remains package-only pending reconciliation",
                data=self._status_data(),
            )
        mutation_requested = (
            self.config.execution_route in {"sim", "demo"}
            or self.config.allow_live_mutations
        )
        self._admission_enabled = mutation_requested
        self._health = "ready" if mutation_requested else "package_only"
        self._unresolved_steps = ()
        self._publish_health(self._health)
        return self._envelope(
            operation="live_session.start",
            status="success" if mutation_requested else "packaged",
            message=(
                "Live session mutation admission enabled"
                if mutation_requested
                else "Live session started in package-only mode"
            ),
            data=self._status_data(),
        )

    def _status_data(self) -> dict[str, JsonValue]:
        """Build JSON-safe actual lifecycle state.

        Returns:
            Current session state mapping.
        """
        logger.debug("Building LiveSession status data")
        return {
            "started": self._started,
            "mode": self._config.execution_route if self._config else "unconfigured",
            "admission_enabled": self._admission_enabled,
            "data_authority_id": (
                self._config.data_authority_id if self._config else None
            ),
            "health": self._health,
            "reconciliation_ready": self._reconciliation_ready,
            "unresolved_steps": list(self._unresolved_steps),
        }

    def status(self) -> StandardResponse[Mapping[str, JsonValue]]:
        """Return actual session readiness without side effects.

        Returns:
            Canonical current lifecycle envelope.
        """
        logger.info("Reading Trading LiveSession status")
        return self._envelope(
            operation="live_session.status",
            status="success",
            message="Live session status reflects current state",
            data=self._status_data(),
        )

    async def _run_shutdown_step(
        self,
        name: str,
        step: _LifecycleStep,
        timeout_seconds: float,
    ) -> bool:
        """Run one shutdown step without hiding dependency failure.

        Args:
            name: Stable shutdown step name.
            step: Injected async lifecycle operation.
            timeout_seconds: Positive remaining monotonic shutdown budget.

        Returns:
            Whether the step completed successfully.
        """
        logger.info("Running LiveSession shutdown step %s", name)
        if timeout_seconds <= 0:
            return False
        try:
            async with asyncio.timeout(timeout_seconds):
                return await step()
        except (
            TimeoutError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
            TradingError,
        ):
            logger.exception("LiveSession shutdown step failed: %s", name)
            return False

    async def _stop_value(self) -> StandardResponse[Mapping[str, JsonValue]]:
        """Stop admission, drain/flush, reconcile, and report incomplete work.

        Returns:
            Canonical complete or partial shutdown evidence.

        Raises:
            TradingError: If the session was never configured.
        """
        logger.info("Stopping Trading LiveSession")
        config = self.config
        self._admission_enabled = False
        loop = asyncio.get_running_loop()
        deadline = loop.time() + float(config.shutdown_budget_seconds)
        steps = (
            ("drain_in_flight", self._drain_in_flight),
            ("flush_evidence", self._flush_evidence),
            ("shutdown_reconciliation", self._shutdown_reconcile),
        )
        results_list: list[tuple[str, bool]] = []
        for name, step in steps:
            remaining = deadline - loop.time()
            results_list.append(
                (name, await self._run_shutdown_step(name, step, remaining))
            )
        results = tuple(results_list)
        unresolved = [name for name, passed in results if not passed]
        if loop.time() > deadline:
            unresolved.append("shutdown_budget_exceeded")
        self._unresolved_steps = tuple(unresolved)
        self._reconciliation_ready = results[-1][1] and not unresolved
        self._started = False
        self._health = "stopped" if not unresolved else "shutdown_incomplete"
        self._publish_health(self._health)
        return self._envelope(
            operation="live_session.stop",
            status="success" if not unresolved else "partial",
            message=(
                "Live session stopped safely"
                if not unresolved
                else "Live session stopped admission with unresolved work"
            ),
            data=self._status_data(),
        )

    async def start(
        self,
        config: Mapping[str, JsonValue],
        evidence: Mapping[str, JsonValue],
    ) -> StandardResponse[Mapping[str, JsonValue]]:
        """Start the session and return a canonical lifecycle response.

        Args:
            config: Session configuration mapping.
            evidence: Route fact and environment evidence mapping.

        Returns:
            Standard response containing lifecycle evidence or an error.
        """
        try:
            return await self._start_value(config, evidence)
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"operation": "live_session.start"})

    async def stop(self) -> StandardResponse[Mapping[str, JsonValue]]:
        """Stop the session and return a canonical lifecycle response.

        Returns:
            Standard response containing shutdown evidence or an error.
        """
        try:
            return await self._stop_value()
        except Exception as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"operation": "live_session.stop"})


__all__ = ["LiveSession"]
