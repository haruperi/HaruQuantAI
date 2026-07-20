"""Asynchronous execution coordination and lifecycle-mutation primitives.

This module orchestrates broker-independent dispatch coordination: route-based
handler selection (TRD-FR-102), non-blocking asynchronous dispatch with
Futures-based completion callbacks (TRD-FR-103), globally unique
``client_order_id`` generation and broker-metadata-field propagation
(TRD-FR-104), multi-account ``AllocationVector`` dispatch planning
(TRD-FR-105), two-step SL/TP protection outcome evaluation (TRD-FR-106),
partial-fill residual handling policy application (TRD-FR-107), non-atomic
cancel-then-replace modify safety (TRD-FR-108), OCO/bracket mutual-cancellation
coordination (TRD-FR-109/110), multi-leg/spread execution rollback
(TRD-FR-111), transaction cost capture (TRD-FR-112), an in-flight request
counter (TRD-FR-113), and post-response ``TradeStore``/lease/idempotency
finalization (TRD-FR-114).

It performs no broker calls itself and imports no provider SDKs: callers
inject the dispatch callable, executor, and state ports.
"""
# ruff: noqa: SIM102, ARG002 -- nested ifs for coverage; Protocol args are placeholders.

from __future__ import annotations

import hashlib
import threading
import time
from concurrent.futures import Future
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from app.services.trading.contracts import (
    AllocationVector,
    JsonObject,
    TradingAction,
    TradingCommandAccepted,
    TradingContract,
    TradingRoute,
)
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger
from pydantic import Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.services.trading.contracts import (
        NormalizedTradeResult,
        TradingRequestEnvelope,
    )
    from app.services.trading.execution.broker_capability_validation import (
        BrokerCapabilityProfile,
    )
    from app.services.trading.state.ports import RNG, IdempotencyStore, TradeStore

_ROUTE_DISPATCH_TARGETS: dict[TradingRoute, str] = {
    TradingRoute.SIM: "simulator",
    TradingRoute.PAPER: "paper_store",
    TradingRoute.SHADOW: "shadow_comparison",
    TradingRoute.LIVE: "broker_router",
}


def resolve_dispatch_target(*, route: TradingRoute) -> str:
    """Resolve the execution handler target for a runtime route (TRD-FR-102).

    Args:
        route: Requested runtime route.

    Returns:
        str: Stable dispatch target identifier (``simulator``/``paper_store``/
        ``shadow_comparison``/``broker_router``).
    """
    logger.info("Resolving dispatch target for route {}.", route.value)
    target = _ROUTE_DISPATCH_TARGETS[route]
    logger.debug("Route {} resolves to dispatch target {}.", route.value, target)
    return target


class AsyncDispatchExecutor(Protocol):
    """Injected executor that runs a dispatch callable off the request path."""

    def submit(
        self, dispatch_callable: Callable[[], NormalizedTradeResult]
    ) -> Future[NormalizedTradeResult]:
        """Submit a dispatch callable for asynchronous execution.

        Args:
            dispatch_callable: Zero-argument callable performing the broker
                dispatch and returning a normalized result.

        Returns:
            Future[NormalizedTradeResult]: Future resolved on completion.
        """
        logger.debug("AsyncDispatchExecutor.submit protocol placeholder invoked.")
        raise NotImplementedError


class InFlightRequestCounter:
    """Thread-safe in-flight request counter (TRD-FR-113)."""

    def __init__(self) -> None:
        """Initialize the counter at zero under a dedicated lock."""
        logger.debug("Initializing in-flight request counter.")
        self._lock = threading.Lock()
        self._count = 0

    def increment(self) -> int:
        """Increment the in-flight counter.

        Returns:
            int: Updated in-flight count.
        """
        with self._lock:
            self._count += 1
            count = self._count
        logger.debug("In-flight request counter incremented to {}.", count)
        return count

    def decrement(self) -> int:
        """Decrement the in-flight counter, floored at zero.

        Returns:
            int: Updated in-flight count.
        """
        with self._lock:
            if self._count > 0:
                self._count -= 1
            count = self._count
        logger.debug("In-flight request counter decremented to {}.", count)
        return count

    def current(self) -> int:
        """Return the current in-flight count.

        Returns:
            int: Current in-flight count.
        """
        with self._lock:
            count = self._count
        return count

    def is_drained(self) -> bool:
        """Return whether no requests are currently in flight.

        Returns:
            bool: True when the counter is at zero.
        """
        drained = self.current() == 0
        logger.debug("In-flight request counter drained: {}.", drained)
        return drained

    def wait_drained(self, timeout_seconds: float, poll_seconds: float = 0.1) -> bool:
        """Block until no requests are in flight, or the timeout elapses.

        Ports the in-flight drain loop ``trader.Trade.shutdown`` ran before
        flushing state. Suitable as the ``drain`` callback of
        :func:`~app.services.trading.actions.controls.shutdown`.

        Args:
            timeout_seconds: Maximum seconds to wait for the counter to reach
                zero.
            poll_seconds: Interval between checks.

        Returns:
            bool: True when the counter reached zero within the timeout.
        """
        logger.info("Waiting up to {}s for in-flight drain.", timeout_seconds)
        deadline = time.monotonic() + timeout_seconds
        while not self.is_drained():
            if time.monotonic() >= deadline:
                logger.warning(
                    "In-flight drain timed out with {} request(s) pending.",
                    self.current(),
                )
                return False
            time.sleep(poll_seconds)
        return True


def generate_client_order_id(*, request_id: str, rng: RNG) -> str:
    """Generate a globally unique ``client_order_id`` (TRD-FR-104).

    Args:
        request_id: Unique request identifier the order originates from.
        rng: Injected deterministic random generator for the disambiguation
            suffix.

    Returns:
        str: Globally unique client order identifier.

    Raises:
        TradingMappedError: If ``request_id`` is blank.
    """
    logger.info("Generating client_order_id for request {}.", request_id)
    if not request_id.strip():
        raise TradingMappedError(
            "request_id must be non-empty to generate a client_order_id.",
            code="INVALID_INPUT",
        )
    suffix = rng.randint(0, 0xFFFFFF)
    material = f"{request_id}:{suffix:06x}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    client_order_id = f"clord-{digest}"
    logger.debug(
        "Generated client_order_id {} for request {}.", client_order_id, request_id
    )
    return client_order_id


def truncate_client_order_id(*, client_order_id: str, max_length: int) -> str:
    """Deterministically truncate a client order ID to fit a broker field.

    A short content-derived hash suffix is preserved so distinct IDs remain
    distinguishable after truncation, while the original ID stays the
    canonical lookup key in ``TradeStore`` (TRD-FR-104).

    Args:
        client_order_id: Full client order identifier.
        max_length: Maximum length supported by the target broker field.

    Returns:
        str: Truncated identifier no longer than ``max_length``.

    Raises:
        TradingMappedError: If ``max_length`` is not positive.
    """
    logger.info(
        "Truncating client_order_id {} to max_length {}.", client_order_id, max_length
    )
    if max_length < 1:
        raise TradingMappedError(
            "max_length must be a positive integer.",
            code="INVALID_INPUT",
        )
    if len(client_order_id) <= max_length:
        return client_order_id
    tail = hashlib.sha256(client_order_id.encode("utf-8")).hexdigest()[:8]
    if max_length <= len(tail) + 1:
        truncated = tail[:max_length]
    else:
        prefix_length = max_length - len(tail) - 1
        truncated = f"{client_order_id[:prefix_length]}-{tail}"
    logger.debug("Truncated client_order_id to {}.", truncated)
    return truncated


class ClientOrderIdMapping(TradingContract):
    """Broker metadata field propagation for one client order ID.

    Attributes:
        client_order_id: Full, canonical client order identifier.
        comment: Deterministically truncated comment-field value.
        external_id: Deterministically truncated external-ID-field value.
        magic_number: Deterministic non-negative integer for magic-number
            fields.
    """

    client_order_id: str
    comment: str
    external_id: str
    magic_number: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_mapping(self) -> ClientOrderIdMapping:
        """Validate the client order ID mapping is well-formed.

        Returns:
            ClientOrderIdMapping: Validated mapping.

        Raises:
            ValueError: If ``client_order_id`` is blank.
        """
        logger.debug("Validating client order id mapping {}.", self.client_order_id)
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must be non-empty.")
        return self


def build_client_order_id_mapping(
    *,
    client_order_id: str,
    comment_max_length: int,
    external_id_max_length: int,
) -> ClientOrderIdMapping:
    """Build broker metadata field propagation for a client order ID.

    Args:
        client_order_id: Full, canonical client order identifier.
        comment_max_length: Maximum length of the broker comment field.
        external_id_max_length: Maximum length of the broker external-ID
            field.

    Returns:
        ClientOrderIdMapping: Deterministic broker metadata field mapping.
    """
    logger.info("Building client order id mapping for {}.", client_order_id)
    digest = hashlib.sha256(client_order_id.encode("utf-8")).hexdigest()
    magic_number = int(digest, 16) % (2**31 - 1)
    mapping = ClientOrderIdMapping(
        client_order_id=client_order_id,
        comment=truncate_client_order_id(
            client_order_id=client_order_id, max_length=comment_max_length
        ),
        external_id=truncate_client_order_id(
            client_order_id=client_order_id, max_length=external_id_max_length
        ),
        magic_number=magic_number,
    )
    logger.debug("Built client order id mapping {}.", mapping.model_dump(mode="json"))
    return mapping


class AllocationDispatchPlan(TradingContract):
    """Multi-account allocation dispatch plan (TRD-FR-105).

    Attributes:
        native_block: Whether a single native block transaction is used.
        child_payloads: Per-sub-account dispatch payloads (empty when
            ``native_block`` is True).
    """

    native_block: bool
    child_payloads: tuple[JsonObject, ...] = Field(default_factory=tuple)


def plan_allocation_dispatch(
    *,
    allocation: AllocationVector,
    base_payload: JsonObject,
    total_volume: Decimal,
    broker_supports_native_allocation: bool,
) -> AllocationDispatchPlan:
    """Plan multi-account allocation-vector dispatch (TRD-FR-105).

    Args:
        allocation: Institutional allocation weights.
        base_payload: Base broker dispatch payload common to every child.
        total_volume: Total requested volume to slice across sub-accounts.
        broker_supports_native_allocation: Whether the adapter can transmit
            a single native block transaction carrying the allocation.

    Returns:
        AllocationDispatchPlan: Native block plan, or a set of sliced
        per-account child payloads.
    """
    logger.info(
        "Planning allocation dispatch for {} sub-account(s).", len(allocation.weights)
    )
    if broker_supports_native_allocation:
        logger.debug("Using native block allocation transaction.")
        return AllocationDispatchPlan(native_block=True, child_payloads=())

    total_weight = sum(allocation.weights.values())
    child_payloads: list[JsonObject] = []
    for account_id, weight in allocation.weights.items():
        child_volume = total_volume * weight / total_weight
        child_payload: JsonObject = dict(base_payload)
        child_payload["account_id"] = account_id
        child_payload["volume"] = str(child_volume)
        child_payloads.append(child_payload)
    logger.debug("Sliced allocation into {} child payload(s).", len(child_payloads))
    return AllocationDispatchPlan(
        native_block=False, child_payloads=tuple(child_payloads)
    )


class TwoStepProtectionResult(TradingContract):
    """Two-step SL/TP protection workflow outcome (TRD-FR-106).

    Attributes:
        open_succeeded: Whether the initial open dispatch succeeded.
        protect_succeeded: Whether the follow-up protective modify succeeded.
        critical_incident: Whether an unprotected open position resulted.
        reason_code: Stable public error code when a critical incident
            occurred.
    """

    open_succeeded: bool
    protect_succeeded: bool
    critical_incident: bool
    reason_code: str | None = None


def requires_two_step_protection(*, profile: BrokerCapabilityProfile) -> bool:
    """Return whether SL/TP must be attached via a two-step workflow.

    Args:
        profile: Declared broker adapter capability profile.

    Returns:
        bool: True when the adapter does not support SL/TP attachment on
        open (TRD-FR-106).
    """
    logger.info("Checking two-step protection requirement for {}.", profile.provider)
    return not profile.supports_sl_tp_attachment


def evaluate_two_step_protection_outcome(
    *,
    open_succeeded: bool,
    protect_succeeded: bool,
) -> TwoStepProtectionResult:
    """Evaluate a two-step open-then-protect workflow outcome (TRD-FR-106).

    An open that succeeds without a confirmed protective modify is a critical
    incident: the position exists unprotected from the state perspective.

    Args:
        open_succeeded: Whether the initial open dispatch succeeded.
        protect_succeeded: Whether the follow-up protective modify succeeded.

    Returns:
        TwoStepProtectionResult: Workflow outcome, flagging a critical
        incident when the position opened without confirmed protection.
    """
    logger.info(
        "Evaluating two-step protection outcome (open={}, protect={}).",
        open_succeeded,
        protect_succeeded,
    )
    if open_succeeded:
        if not protect_succeeded:
            logger.warning("Critical incident: position opened without protection.")
            return TwoStepProtectionResult(
                open_succeeded=True,
                protect_succeeded=False,
                critical_incident=True,
                reason_code="LIVE_PROTECTIVE_MODIFY_FAILED",
            )
    return TwoStepProtectionResult(
        open_succeeded=open_succeeded,
        protect_succeeded=protect_succeeded,
        critical_incident=False,
    )


class ResidualPolicy(StrEnum):
    """Partial-fill residual handling policy (TRD-FR-107)."""

    LEAVE_REMAINING = "leave_remaining"
    CANCEL_REMAINING = "cancel_remaining"
    REPLACE_REMAINING = "replace_remaining"
    RETRY_REMAINING_AFTER_DELAY = "retry_remaining_after_delay"
    ESCALATE_TO_OPERATOR = "escalate_to_operator"


class ResidualHandlingDecision(TradingContract):
    """Resolved residual handling action for a partially filled order.

    Attributes:
        order_id: Local order identifier.
        policy: Applied residual handling policy.
        remaining_volume: Remaining unfilled volume.
        action: Stable action identifier for the caller to dispatch.
    """

    order_id: str
    policy: ResidualPolicy
    remaining_volume: Decimal = Field(ge=0)
    action: str


_RESIDUAL_ACTIONS: dict[ResidualPolicy, str] = {
    ResidualPolicy.LEAVE_REMAINING: "no_op",
    ResidualPolicy.CANCEL_REMAINING: "dispatch_cancel",
    ResidualPolicy.REPLACE_REMAINING: "dispatch_replace",
    ResidualPolicy.RETRY_REMAINING_AFTER_DELAY: "schedule_retry",
    ResidualPolicy.ESCALATE_TO_OPERATOR: "escalate_to_operator",
}


def apply_residual_policy(
    *,
    order_id: str,
    policy: ResidualPolicy,
    remaining_volume: Decimal,
) -> ResidualHandlingDecision:
    """Resolve the dispatch action for a partial-fill residual (TRD-FR-107).

    Args:
        order_id: Local order identifier.
        policy: Residual handling policy fetched from the policy matrix and
            capability profile.
        remaining_volume: Remaining unfilled volume, already updated in
            ``TradeStore``.

    Returns:
        ResidualHandlingDecision: The action the caller must dispatch.
    """
    logger.info(
        "Applying residual policy {} for order {} (remaining={}).",
        policy.value,
        order_id,
        remaining_volume,
    )
    decision = ResidualHandlingDecision(
        order_id=order_id,
        policy=policy,
        remaining_volume=remaining_volume,
        action=_RESIDUAL_ACTIONS[policy],
    )
    logger.debug("Resolved residual action {} for order {}.", decision.action, order_id)
    return decision


class NonAtomicModifyStage(StrEnum):
    """Cancel-then-replace non-atomic modify workflow stage (TRD-FR-108)."""

    RESERVED = "reserved"
    CANCEL_DISPATCHED = "cancel_dispatched"
    CANCEL_CONFIRMED = "cancel_confirmed"
    REPLACE_DISPATCHED = "replace_dispatched"
    REPLACE_CONFIRMED = "replace_confirmed"
    REPLACE_FAILED = "replace_failed"


class NonAtomicModifyState(TradingContract):
    """Stateful non-atomic modify workflow record.

    Attributes:
        order_id: Local order identifier being modified.
        stage: Current workflow stage.
    """

    order_id: str
    stage: NonAtomicModifyStage


_NON_ATOMIC_MODIFY_PRECONDITIONS: dict[str, NonAtomicModifyStage] = {
    "cancel_dispatched": NonAtomicModifyStage.RESERVED,
    "cancel_confirmed": NonAtomicModifyStage.CANCEL_DISPATCHED,
    "replace_dispatched": NonAtomicModifyStage.CANCEL_CONFIRMED,
}


def _advance_non_atomic_modify(
    *,
    state: NonAtomicModifyState,
    transition_name: str,
    next_stage: NonAtomicModifyStage,
) -> NonAtomicModifyState:
    """Advance a non-atomic modify workflow after validating its precondition."""
    required_stage = _NON_ATOMIC_MODIFY_PRECONDITIONS[transition_name]
    if state.stage is not required_stage:
        raise TradingMappedError(
            "Non-atomic modify workflow transition is out of sequence.",
            code="VALIDATION_FAILED",
            details={
                "order_id": state.order_id,
                "current_stage": state.stage.value,
                "required_stage": required_stage.value,
            },
        )
    return state.model_copy(update={"stage": next_stage})


def begin_non_atomic_modify(*, order_id: str) -> NonAtomicModifyState:
    """Reserve an order for a non-atomic cancel-then-replace modify (TRD-FR-108).

    Args:
        order_id: Local order identifier to reserve against concurrent
            actions.

    Returns:
        NonAtomicModifyState: Freshly reserved workflow state.
    """
    logger.info("Reserving order {} for non-atomic modify.", order_id)
    return NonAtomicModifyState(order_id=order_id, stage=NonAtomicModifyStage.RESERVED)


def record_cancel_dispatched(*, state: NonAtomicModifyState) -> NonAtomicModifyState:
    """Record that the cancel step of a non-atomic modify was dispatched.

    Args:
        state: Current non-atomic modify workflow state.

    Returns:
        NonAtomicModifyState: Updated workflow state.

    Raises:
        TradingMappedError: If the workflow is not in the reserved stage.
    """
    logger.info("Recording cancel dispatch for order {}.", state.order_id)
    return _advance_non_atomic_modify(
        state=state,
        transition_name="cancel_dispatched",
        next_stage=NonAtomicModifyStage.CANCEL_DISPATCHED,
    )


def record_cancel_confirmed(*, state: NonAtomicModifyState) -> NonAtomicModifyState:
    """Record confirmed cancellation of the working order.

    Args:
        state: Current non-atomic modify workflow state.

    Returns:
        NonAtomicModifyState: Updated workflow state.

    Raises:
        TradingMappedError: If the workflow is not awaiting cancel
            confirmation.
    """
    logger.info("Recording cancel confirmation for order {}.", state.order_id)
    return _advance_non_atomic_modify(
        state=state,
        transition_name="cancel_confirmed",
        next_stage=NonAtomicModifyStage.CANCEL_CONFIRMED,
    )


def record_replace_dispatched(*, state: NonAtomicModifyState) -> NonAtomicModifyState:
    """Record that the replace step of a non-atomic modify was dispatched.

    Args:
        state: Current non-atomic modify workflow state.

    Returns:
        NonAtomicModifyState: Updated workflow state.

    Raises:
        TradingMappedError: If cancellation has not been confirmed yet.
    """
    logger.info("Recording replace dispatch for order {}.", state.order_id)
    return _advance_non_atomic_modify(
        state=state,
        transition_name="replace_dispatched",
        next_stage=NonAtomicModifyStage.REPLACE_DISPATCHED,
    )


class NonAtomicModifyResolution(TradingContract):
    """Resolved outcome after a non-atomic modify replace step (TRD-FR-108).

    Attributes:
        state: Final workflow state.
        critical_incident: Always True when the replace step failed.
        recommended_action: ``reenter_original_order`` or
            ``escalate_to_dead_letter``, present only on replace failure.
        reason_code: Stable public error code, present only on replace
            failure.
    """

    state: NonAtomicModifyState
    critical_incident: bool
    recommended_action: str | None = None
    reason_code: str | None = None


def resolve_replace_outcome(
    *,
    state: NonAtomicModifyState,
    replace_succeeded: bool,
    reentry_allowed: bool,
) -> NonAtomicModifyResolution:
    """Resolve the outcome of a non-atomic modify replace step (TRD-FR-108).

    If the replace step fails after the working order was already cancelled,
    a critical incident is always journaled by the caller; this function
    recommends whether to attempt re-entry with the new parameters or to
    escalate to a dead-letter recovery review, per policy.

    Args:
        state: Current non-atomic modify workflow state (must be
            ``REPLACE_DISPATCHED``).
        replace_succeeded: Whether the broker confirmed the replacement
            order.
        reentry_allowed: Whether policy permits an automatic re-entry attempt
            with the new parameters.

    Returns:
        NonAtomicModifyResolution: Final workflow state and, on failure, the
        recommended recovery action.

    Raises:
        TradingMappedError: If the workflow is not awaiting a replace
            outcome.
    """
    logger.info("Resolving replace outcome for order {}.", state.order_id)
    if state.stage is not NonAtomicModifyStage.REPLACE_DISPATCHED:
        raise TradingMappedError(
            "Non-atomic modify workflow transition is out of sequence.",
            code="VALIDATION_FAILED",
            details={"order_id": state.order_id, "current_stage": state.stage.value},
        )
    if replace_succeeded:
        confirmed = state.model_copy(
            update={"stage": NonAtomicModifyStage.REPLACE_CONFIRMED}
        )
        logger.debug("Replace confirmed for order {}.", state.order_id)
        return NonAtomicModifyResolution(state=confirmed, critical_incident=False)

    failed = state.model_copy(update={"stage": NonAtomicModifyStage.REPLACE_FAILED})
    action = "reenter_original_order" if reentry_allowed else "escalate_to_dead_letter"
    logger.warning(
        "Critical incident: non-atomic modify replace failed for order {}; action={}.",
        state.order_id,
        action,
    )
    return NonAtomicModifyResolution(
        state=failed,
        critical_incident=True,
        recommended_action=action,
        reason_code="LIVE_NON_ATOMIC_MODIFY_ESCALATED",
    )


class OcoExecutionMode(StrEnum):
    """Resolved OCO/bracket group execution mode (TRD-FR-110)."""

    NATIVE = "native"
    SYNTHETIC_WATCHDOG = "synthetic_watchdog"
    UNSUPPORTED_BLOCKED = "unsupported_blocked"


def resolve_oco_execution_mode(
    *,
    profile: BrokerCapabilityProfile,
    synthetic_emulation_enabled: bool,
) -> OcoExecutionMode:
    """Resolve how an OCO/bracket group should be executed (TRD-FR-110).

    Args:
        profile: Declared broker adapter capability profile.
        synthetic_emulation_enabled: Whether client-side synthetic OCO
            emulation is active for this session.

    Returns:
        OcoExecutionMode: ``NATIVE`` when the adapter supports OCO natively,
        ``SYNTHETIC_WATCHDOG`` when emulation is active, otherwise
        ``UNSUPPORTED_BLOCKED``.
    """
    logger.info("Resolving OCO execution mode for {}.", profile.provider)
    if profile.supports_native_oco:
        return OcoExecutionMode.NATIVE
    if synthetic_emulation_enabled:
        return OcoExecutionMode.SYNTHETIC_WATCHDOG
    return OcoExecutionMode.UNSUPPORTED_BLOCKED


def require_oco_submission_allowed(*, mode: OcoExecutionMode) -> None:
    """Fail closed on OCO submission when no execution mode is available.

    Args:
        mode: Resolved OCO execution mode.

    Raises:
        TradingMappedError: If ``mode`` is ``UNSUPPORTED_BLOCKED``.
    """
    logger.info("Checking OCO submission allowance for mode {}.", mode.value)
    if mode is OcoExecutionMode.UNSUPPORTED_BLOCKED:
        raise TradingMappedError(
            "Broker lacks native OCO support and synthetic emulation is disabled.",
            code="OCO_UNSUPPORTED",
        )


_OCO_TRIGGER_STATES = frozenset({"Filled", "Partially Filled"})


def evaluate_oco_sibling_cancellation(
    *,
    filled_order_id: str,
    sibling_order_ids: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve sibling orders to cancel after an OCO leg fills (TRD-FR-109).

    Args:
        filled_order_id: Order ID that reported a fill or partial fill.
        sibling_order_ids: All order IDs registered in the OCO group.

    Returns:
        tuple[str, ...]: Sibling order IDs (excluding ``filled_order_id``)
        that must be cancelled.
    """
    logger.info("Evaluating OCO sibling cancellation for {}.", filled_order_id)
    siblings = tuple(
        order_id for order_id in sibling_order_ids if order_id != filled_order_id
    )
    logger.debug("Resolved {} sibling(s) to cancel.", len(siblings))
    return siblings


class OcoWatchdog:
    """Client-side synthetic OCO mutual-cancellation watchdog (TRD-FR-109/110).

    Listens for execution reports on registered groups and resolves sibling
    cancellation dispatch once any leg fills or partially fills. Each group
    resolves at most once to avoid duplicate cancellation dispatch.
    """

    def __init__(self) -> None:
        """Initialize the watchdog with no registered groups."""
        logger.debug("Initializing OCO watchdog.")
        self._groups: dict[str, tuple[str, ...]] = {}
        self._resolved_groups: set[str] = set()

    def register_group(self, *, group_id: str, order_ids: tuple[str, ...]) -> None:
        """Register an OCO/bracket group for watchdog tracking.

        Args:
            group_id: OCO group identifier.
            order_ids: Every order ID belonging to the group.
        """
        logger.info(
            "Registering OCO group {} with {} order(s).", group_id, len(order_ids)
        )
        self._groups[group_id] = order_ids

    def on_execution_report(
        self,
        *,
        group_id: str,
        order_id: str,
        execution_state: str,
    ) -> tuple[str, ...]:
        """Process an execution report and resolve sibling cancellations.

        Args:
            group_id: OCO group identifier.
            order_id: Order ID the execution report concerns.
            execution_state: FIX-style execution state string reported.

        Returns:
            tuple[str, ...]: Sibling order IDs to cancel. Empty when the
            group is unregistered, already resolved, or the report does not
            trigger mutual cancellation.
        """
        logger.info(
            "OCO watchdog processing report for group {} order {} state {}.",
            group_id,
            order_id,
            execution_state,
        )
        if group_id not in self._groups:
            logger.debug("OCO group {} is not registered.", group_id)
            return ()
        if group_id in self._resolved_groups:
            logger.debug("OCO group {} already resolved.", group_id)
            return ()
        if execution_state not in _OCO_TRIGGER_STATES:
            return ()
        siblings = evaluate_oco_sibling_cancellation(
            filled_order_id=order_id,
            sibling_order_ids=self._groups[group_id],
        )
        self._resolved_groups.add(group_id)
        logger.debug(
            "OCO group {} resolved with {} cancellation(s).", group_id, len(siblings)
        )
        return siblings


class MultiLegDecision(TradingContract):
    """Multi-leg execution rollback decision (TRD-FR-111).

    Attributes:
        rollback_required: Whether rollback of sibling legs is required.
        legs_to_rollback: Leg order IDs requiring cancel/close dispatch.
        reason_code: Stable public error code when rollback is required.
    """

    rollback_required: bool
    legs_to_rollback: tuple[str, ...] = Field(default_factory=tuple)
    reason_code: str | None = None


class MultiLegExecutionCoordinator:
    """Synthetic multi-leg/spread execution watchdog (TRD-FR-111).

    If any registered leg rejects, fails, or partially fills beyond the
    configured tolerance, every other filled or working leg in the group must
    be rolled back to restore the pre-trade portfolio state.
    """

    def __init__(self, *, partial_fill_tolerance: Decimal) -> None:
        """Initialize the coordinator with a partial-fill tolerance.

        Args:
            partial_fill_tolerance: Maximum acceptable unfilled fraction
                (0 to 1) before a partial fill triggers rollback.

        Raises:
            TradingMappedError: If the tolerance is outside ``[0, 1]``.
        """
        if partial_fill_tolerance < 0 or partial_fill_tolerance > 1:
            raise TradingMappedError(
                "partial_fill_tolerance must be between 0 and 1.",
                code="INVALID_INPUT",
            )
        logger.debug(
            "Initializing multi-leg coordinator with tolerance {}.",
            partial_fill_tolerance,
        )
        self._tolerance = partial_fill_tolerance
        self._groups: dict[str, tuple[str, ...]] = {}
        self._resolved_groups: set[str] = set()

    def register_legs(self, *, group_id: str, leg_order_ids: tuple[str, ...]) -> None:
        """Register the leg order IDs belonging to a multi-leg group.

        Args:
            group_id: Multi-leg group identifier.
            leg_order_ids: Every order ID belonging to the group.
        """
        logger.info(
            "Registering multi-leg group {} with {} leg(s).",
            group_id,
            len(leg_order_ids),
        )
        self._groups[group_id] = leg_order_ids

    def on_leg_outcome(
        self,
        *,
        group_id: str,
        leg_order_id: str,
        rejected: bool,
        unfilled_fraction: Decimal,
    ) -> MultiLegDecision:
        """Evaluate a leg outcome and resolve rollback of sibling legs.

        Args:
            group_id: Multi-leg group identifier.
            leg_order_id: Order ID the outcome concerns.
            rejected: Whether this leg was rejected or failed outright.
            unfilled_fraction: Fraction of this leg's volume left unfilled
                (0 means fully filled).

        Returns:
            MultiLegDecision: Rollback requirement and sibling legs to roll
            back. No rollback is required when the group is unregistered,
            already resolved, or the leg outcome is within tolerance.
        """
        logger.info(
            "Multi-leg coordinator processing group {} leg {} "
            "(rejected={}, unfilled={}).",
            group_id,
            leg_order_id,
            rejected,
            unfilled_fraction,
        )
        if group_id not in self._groups:
            return MultiLegDecision(rollback_required=False)
        if group_id in self._resolved_groups:
            return MultiLegDecision(rollback_required=False)

        breach = rejected or unfilled_fraction > self._tolerance
        if not breach:
            return MultiLegDecision(rollback_required=False)

        siblings = tuple(
            order_id for order_id in self._groups[group_id] if order_id != leg_order_id
        )
        self._resolved_groups.add(group_id)
        logger.warning(
            "Multi-leg rollback triggered for group {}; rolling back {} leg(s).",
            group_id,
            len(siblings),
        )
        return MultiLegDecision(
            rollback_required=True,
            legs_to_rollback=siblings,
            reason_code="LIVE_MULTI_LEG_ROLLBACK_TRIGGERED",
        )


class TransactionCostFacts(TradingContract):
    """Captured transaction cost facts for one order (TRD-FR-112).

    Attributes:
        commission: Broker commission charged.
        spread_cost: Realized spread cost.
        swap: Overnight swap/rollover cost.
        exchange_fees: Exchange or venue fees.
        realized_slippage: Realized slippage versus the reference quote.
        other_fees: Any other transaction cost facts.
    """

    commission: Decimal = Field(default=Decimal(0))
    spread_cost: Decimal = Field(default=Decimal(0))
    swap: Decimal = Field(default=Decimal(0))
    exchange_fees: Decimal = Field(default=Decimal(0))
    realized_slippage: Decimal = Field(default=Decimal(0))
    other_fees: Decimal = Field(default=Decimal(0))


class CostAdjustmentEvent(TradingContract):
    """Transaction cost capture or later adjustment event (TRD-FR-112).

    Attributes:
        order_id: Local order identifier the costs are attributed to.
        cost_facts: Captured transaction cost facts.
        recorded_at: UTC timestamp supplied by an injected Clock.
        is_adjustment: Whether this event adjusts a previously captured cost
            (e.g. a later deal-history correction) rather than the first
            capture.
    """

    order_id: str
    cost_facts: TransactionCostFacts
    recorded_at: str
    is_adjustment: bool = False


def capture_transaction_cost(
    *,
    order_id: str,
    cost_facts: TransactionCostFacts,
    recorded_at: str,
    is_adjustment: bool = False,
) -> CostAdjustmentEvent:
    """Capture transaction cost facts for an order (TRD-FR-112).

    Args:
        order_id: Local order identifier.
        cost_facts: Commission, spread, swap, exchange fee, and slippage
            facts.
        recorded_at: UTC timestamp supplied by an injected Clock.
        is_adjustment: Whether this is a later cost-adjustment event rather
            than the initial capture.

    Returns:
        CostAdjustmentEvent: JSON-safe cost capture/adjustment event.

    Raises:
        TradingMappedError: If ``order_id`` is blank.
    """
    logger.info(
        "Capturing transaction cost facts for order {} (adjustment={}).",
        order_id,
        is_adjustment,
    )
    if not order_id.strip():
        raise TradingMappedError(
            "order_id must be non-empty to capture transaction cost.",
            code="INVALID_INPUT",
        )
    event = CostAdjustmentEvent(
        order_id=order_id,
        cost_facts=cost_facts,
        recorded_at=recorded_at,
        is_adjustment=is_adjustment,
    )
    logger.debug("Captured cost event for order {}.", order_id)
    return event


def finalize_dispatch_outcome(
    *,
    trade_store: TradeStore,
    route: TradingRoute,
    tenant_id: str,
    order_state: JsonObject,
    expected_version: int | None,
    idempotency_store: IdempotencyStore,
    idempotency_key: str,
    idempotency_outcome: JsonObject,
    completed_at: object,
    release_concurrency_lease: Callable[[], None] | None = None,
) -> str:
    """Finalize post-response state after a dispatch completes (TRD-FR-114).

    Persists the updated order state through ``TradeStore``, releases the
    concurrency lease when a release callback is injected (seam for the
    future ``runtime/coordination.py`` unit), and completes the idempotency
    lease so later duplicate requests return the cached outcome.

    Args:
        trade_store: Injected trade projection store.
        route: Runtime route.
        tenant_id: Tenant or session namespace.
        order_state: JSON-safe updated order state projection.
        expected_version: Optimistic concurrency version.
        idempotency_store: Injected idempotency reservation store.
        idempotency_key: Idempotency key reserved for this request.
        idempotency_outcome: JSON-safe final outcome to cache.
        completed_at: Completion timestamp from an injected Clock.
        release_concurrency_lease: Optional callback releasing a held
            concurrency lease.

    Returns:
        str: Persisted order state reference.
    """
    logger.info("Finalizing dispatch outcome for tenant {}.", tenant_id)
    reference = trade_store.save_order_state(
        route=route,
        tenant_id=tenant_id,
        order_state=order_state,
        expected_version=expected_version,
    )
    if release_concurrency_lease is not None:
        release_concurrency_lease()
        logger.debug("Released concurrency lease for tenant {}.", tenant_id)
    idempotency_store.complete(
        route=route,
        tenant_id=tenant_id,
        key=idempotency_key,
        outcome=idempotency_outcome,
        completed_at=completed_at,  # type: ignore[arg-type]
    )
    logger.debug(
        "Completed idempotency lease {} for tenant {}.", idempotency_key, tenant_id
    )
    return reference


class ExecutionCoordinator:
    """Broker-independent asynchronous dispatch coordinator."""

    def __init__(self) -> None:
        """Initialize the coordinator with its own in-flight request counter."""
        self.in_flight = InFlightRequestCounter()

    def build_broker_dispatch_payload(
        self,
        request: TradingRequestEnvelope,
    ) -> JsonObject:
        """Build a JSON-safe broker dispatch payload.

        Args:
            request: Trading request envelope.

        Returns:
            JsonObject: Dispatch payload with regulatory tags propagated.
        """
        logger.info("Building broker dispatch payload for {}.", request.request_id)
        return request.to_broker_dispatch_payload()

    def dispatch_async(
        self,
        *,
        request_id: str,
        action: TradingAction,
        accepted_at: str,
        executor: AsyncDispatchExecutor,
        dispatch_callable: Callable[[], NormalizedTradeResult],
        on_complete: Callable[[NormalizedTradeResult | BaseException], None],
    ) -> TradingCommandAccepted:
        """Dispatch a request asynchronously and return control immediately.

        Increments the in-flight counter (TRD-FR-113), submits the dispatch
        callable to the injected executor, and registers a completion
        callback that always decrements the counter before delegating to the
        caller-supplied ``on_complete`` handler — regardless of whether the
        dispatch succeeded or raised (TRD-FR-103).

        Args:
            request_id: Unique request identifier.
            action: Requested trading action.
            accepted_at: UTC acceptance timestamp from an injected Clock.
            executor: Injected asynchronous dispatch executor.
            dispatch_callable: Zero-argument callable performing the broker
                dispatch.
            on_complete: Callback invoked with the normalized result, or the
                raised exception, once the future resolves.

        Returns:
            TradingCommandAccepted: Local command acceptance event, returned
            before broker dispatch completes.
        """
        logger.info("Dispatching request {} asynchronously.", request_id)
        self.in_flight.increment()
        request_digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
        command_id = f"cmd-{request_digest[:16]}"

        def _on_future_done(future: Future[NormalizedTradeResult]) -> None:
            self.in_flight.decrement()
            error = future.exception()
            if error is not None:
                logger.warning("Async dispatch for {} failed: {}.", request_id, error)
                on_complete(error)
                return
            logger.debug("Async dispatch for {} completed.", request_id)
            on_complete(future.result())

        future = executor.submit(dispatch_callable)
        future.add_done_callback(_on_future_done)
        logger.debug("Registered completion callback for request {}.", request_id)
        return TradingCommandAccepted(
            request_id=request_id,
            command_id=command_id,
            accepted_at=accepted_at,
            action=action,
        )
