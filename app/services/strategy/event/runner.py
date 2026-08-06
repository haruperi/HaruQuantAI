"""Atomic typed-hook event-driven Strategy evaluation."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from app.services.strategy.contracts.execution import (  # noqa: TC001
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
)
from app.services.strategy.contracts.outcomes import (
    failure,
)
from app.services.strategy.contracts.references import (  # noqa: TC001
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.responses import (
    guard_strategy_boundary,
    unwrap_evaluator_result,
    unwrap_strategy_response,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.utils import canonical_digest, canonical_json, get_logger

type StandardResponse[T] = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    AccountStateSnapshot = Any
    from app.services.strategy.contracts._base import JsonValue


@runtime_checkable
class EventStrategyEvaluator(Protocol):
    """Structural protocol for concrete event-driven strategy evaluators."""

    strategy_id: str
    strategy_version: str
    module_path: str
    source_hash: str
    artifact_hash: str
    dependency_hash: str

    def on_bar(
        self,
        ref: ValidatedStrategyRef,
        config: ValidatedStrategyConfig,
        event: StrategyEvent,
        context: StrategyExecutionContext,
        account_snapshot: AccountStateSnapshot | None = None,
        local_state: Mapping[str, JsonValue] | None = None,
    ) -> StandardResponse[StrategyExecutionResult] | StrategyExecutionResult:
        """Evaluate one bar event hook."""
        ...


def _validate_event_evaluator(
    evaluator: EventStrategyEvaluator,
    ref: ValidatedStrategyRef,
    context: StrategyExecutionContext,
) -> None:
    """Validate evaluator identity against registered manifest."""
    manifest = ref.manifest
    if (
        evaluator.strategy_id != manifest.strategy_id
        or evaluator.strategy_version != manifest.strategy_version
        or evaluator.module_path != manifest.module_path
    ):
        failure(
            StrategyErrorCode.UNAPPROVED_MODULE,
            "evaluator identity does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if (
        evaluator.source_hash != manifest.source_hash
        or evaluator.artifact_hash != manifest.artifact_hash
    ):
        failure(
            StrategyErrorCode.ARTIFACT_HASH_MISMATCH,
            "evaluator artifact hash does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if evaluator.dependency_hash != manifest.dependency_hash:
        failure(
            StrategyErrorCode.DEPENDENCY_HASH_MISMATCH,
            "evaluator dependency hash does not match registry",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )


def _validate_event_readiness(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    event: StrategyEvent,
    context: StrategyExecutionContext,
    account_snapshot: object | None,
    local_state: Mapping[str, JsonValue] | None,
) -> None:
    """Validate event execution readiness before evaluator invocation."""
    if config.strategy_id != ref.manifest.strategy_id:
        failure(
            StrategyErrorCode.INVALID_CONFIG,
            "configuration strategy_id mismatch",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if event.occurred_at > context.decision_timestamp:
        failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "event occurred_at exceeds decision timestamp",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if context.dependency_status.get("last_event_sequence") is not None:
        failure(
            StrategyErrorCode.LOOKAHEAD_DETECTED,
            "event sequence constraint violated",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if local_state is not None:
        state_bytes = len(canonical_json(local_state).encode("utf-8"))
        if state_bytes > ref.manifest.max_local_state_bytes:
            failure(
                StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
                "local state size exceeds manifest limit",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )
    if ref.manifest.requires_account_snapshot and account_snapshot is None:
        failure(
            StrategyErrorCode.MISSING_REQUIRED_DATA,
            "strategy requires account snapshot",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
    if account_snapshot is not None:
        snapshot_at = getattr(
            account_snapshot,
            "snapshot_at",
            account_snapshot.get("snapshot_at")
            if isinstance(account_snapshot, Mapping)
            else None,
        )
        expires_at = getattr(
            account_snapshot,
            "expires_at",
            account_snapshot.get("expires_at")
            if isinstance(account_snapshot, Mapping)
            else None,
        )
        if (
            snapshot_at is not None
            and expires_at is not None
            and not (snapshot_at <= context.decision_timestamp < expires_at)
        ):
            failure(
                StrategyErrorCode.STALE_DATA,
                "account snapshot is stale or future-dated",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )


@guard_strategy_boundary
def run_event_strategy_hook(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    event: StrategyEvent,
    context: StrategyExecutionContext,
    evaluator: EventStrategyEvaluator,
    account_snapshot: AccountStateSnapshot | None = None,
    local_state: Mapping[str, JsonValue] | None = None,
) -> StrategyExecutionResult:
    """Execute one bar event hook with deterministic validation.

    Args:
        ref: Validated exact strategy reference.
        config: Validated strategy configuration.
        event: Strategy event payload.
        context: Execution context.
        evaluator: Injected event strategy evaluator.
        account_snapshot: Optional account snapshot.
        local_state: Optional local state mapping.

    Returns:
        StrategyExecutionResult contract.
    """
    logger.info("Executing event-driven strategy hook for %s", ref.manifest.strategy_id)
    _validate_event_evaluator(evaluator, ref, context)
    _validate_event_readiness(
        ref, config, event, context, account_snapshot, local_state
    )
    raw_res = evaluator.on_bar(
        ref,
        config,
        event,
        context,
        account_snapshot=account_snapshot,
        local_state=local_state,
    )
    result = unwrap_evaluator_result(
        raw_res, operation="event_strategy_evaluator.on_bar"
    )
    candidate_states = []
    if (
        hasattr(result, "candidate_local_state")
        and result.candidate_local_state is not None
    ):
        candidate_states.append(result.candidate_local_state)
    elif isinstance(result, (tuple, list)):
        for item in result:
            st = getattr(item, "candidate_local_state", None)
            if st is not None:
                candidate_states.append(st)
    for st in candidate_states:
        st_bytes = len(canonical_json(st).encode("utf-8"))
        if st_bytes > ref.manifest.max_local_state_bytes:
            failure(
                StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
                "local state size exceeds manifest limit",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )

    if hasattr(result, "model_dump"):
        _ = canonical_digest(result.model_dump(mode="json"))
    elif isinstance(result, (tuple, list)):
        local_states = [
            getattr(item, "candidate_local_state", None)
            for item in result
            if getattr(item, "candidate_local_state", None) is not None
        ]
        if len(local_states) > 1 and any(
            s != local_states[0] for s in local_states[1:]
        ):
            failure(
                StrategyErrorCode.INVALID_CONFIG,
                "multiple decisions carry conflicting candidate local state updates",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )
        _ = canonical_digest(
            [
                item.model_dump(mode="json")
                if hasattr(item, "model_dump")
                else str(item)
                for item in result
            ]
        )
    else:
        _ = canonical_digest(str(result))
    return cast("StrategyExecutionResult", result)


@guard_strategy_boundary
def initialize_strategy_runtime_state(
    config_id: str,
    request_id: str = "",
    correlation_id: str = "",
) -> Mapping[str, Any]:
    """Idempotently initialize empty evaluator-local state.

    Args:
        config_id: Strategy configuration identifier.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        Initial state mapping.
    """
    from app.services.strategy.persistence import read_strategy_state_record

    logger.info("Initializing Strategy runtime state for %s", config_id)
    rows = read_strategy_state_record(config_id, request_id)
    if rows:
        return dict(rows[0])
    return {
        "config_id": config_id,
        "state_version": 0,
        "evaluation_status": "initialized",
        "bars_processed": 0,
        "last_evidence_at": None,
        "last_signal_id": None,
        "local_state": {},
        "local_state_hash": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",  # pragma: allowlist secret
        "request_id": request_id,
        "correlation_id": correlation_id,
    }


@guard_strategy_boundary
def load_strategy_runtime_state(
    config_id: str,
) -> Mapping[str, Any] | None:
    """Load current evaluator-local state for a configuration.

    Args:
        config_id: Strategy configuration identifier.

    Returns:
        State mapping or None if uninitialized.
    """
    from app.services.strategy.persistence import read_strategy_state_record
    from app.utils import generate_id

    logger.info("Loading Strategy runtime state for %s", config_id)
    request_id = generate_id("req")
    rows = read_strategy_state_record(config_id, request_id)
    if not rows:
        return None
    return dict(rows[0])


@guard_strategy_boundary
def commit_strategy_runtime_state(
    config_id: str,
    *,
    expected_state_version: int,
    evaluation_status: str,
    bars_processed: int,
    last_evidence_at: object | None = None,
    last_signal_id: str | None = None,
    local_state: Mapping[str, Any] | None = None,
    request_id: str = "",
    correlation_id: str = "",
) -> Mapping[str, Any]:
    """Compare-and-commit one validated local-state transition using optimistic concurrency.

    Args:
        config_id: Configuration identifier.
        expected_state_version: Expected current state version.
        evaluation_status: New evaluation status string.
        bars_processed: Total bars processed.
        last_evidence_at: Evidence ISO timestamp.
        last_signal_id: Identifier of last emitted signal.
        local_state: Local evaluator state mapping.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        Committed state mapping.
    """
    from app.services.strategy.persistence import update_strategy_runtime_state_record

    logger.info("Committing Strategy state transition for %s", config_id)
    state_dict = dict(local_state) if local_state is not None else {}
    local_state_json = canonical_json(state_dict)
    local_state_hash = canonical_digest(local_state_json)
    evidence_str = (
        last_evidence_at.isoformat()
        if hasattr(last_evidence_at, "isoformat")
        else str(last_evidence_at)
        if last_evidence_at is not None
        else None
    )

    success_commit = update_strategy_runtime_state_record(
        config_id=config_id,
        expected_state_version=expected_state_version,
        evaluation_status=evaluation_status,
        bars_processed=bars_processed,
        last_evidence_at=evidence_str,
        last_signal_id=last_signal_id,
        local_state_json=local_state_json,
        local_state_hash=local_state_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    if not success_commit:
        failure(
            StrategyErrorCode.INTERNAL_ERROR,
            f"Stale state version check failed for config {config_id}",
            request_id=request_id,
            correlation_id=correlation_id,
        )
    return {
        "config_id": config_id,
        "state_version": expected_state_version + 1,
        "evaluation_status": evaluation_status,
        "bars_processed": bars_processed,
        "last_evidence_at": evidence_str,
        "last_signal_id": last_signal_id,
        "local_state": state_dict,
        "local_state_hash": local_state_hash,
        "request_id": request_id,
        "correlation_id": correlation_id,
    }


@guard_strategy_boundary
def run_persisted_event_strategy_hook(
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    config_id: str,
    event: StrategyEvent,
    context: StrategyExecutionContext,
    evaluator: EventStrategyEvaluator,
    account_snapshot: AccountStateSnapshot | None = None,
) -> StrategyExecutionResult:
    """Load state, evaluate event, and atomically commit accepted local state results.

    Args:
        ref: Validated exact strategy reference.
        config: Validated strategy configuration.
        config_id: Strategy configuration record identifier.
        event: Strategy event payload.
        context: Execution context.
        evaluator: Injected event strategy evaluator.
        account_snapshot: Optional account snapshot.

    Returns:
        StrategyExecutionResult contract.
    """
    logger.info(
        "Running persisted event strategy hook for %s", ref.manifest.strategy_id
    )
    state_res = unwrap_strategy_response(
        load_strategy_runtime_state(config_id),
        operation="strategy.event.load_strategy_runtime_state",
    )
    local_state = state_res.get("local_state", {}) if state_res else None

    result = unwrap_strategy_response(
        run_event_strategy_hook(
            ref,
            config,
            event,
            context,
            evaluator,
            local_state=local_state,
            account_snapshot=account_snapshot,
        ),
        operation="strategy.event.run_event_strategy_hook",
    )
    if result.local_state_update is not None and state_res:
        unwrap_strategy_response(
            commit_strategy_runtime_state(
                config_id,
                expected_state_version=int(state_res.get("state_version", 0)),
                evaluation_status="ready",
                bars_processed=int(state_res.get("bars_processed", 0)) + 1,
                last_evidence_at=context.decision_timestamp,
                local_state=result.local_state_update,
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            ),
            operation="strategy.event.commit_strategy_runtime_state",
        )
    return result


__all__ = [
    "EventStrategyEvaluator",
    "commit_strategy_runtime_state",
    "initialize_strategy_runtime_state",
    "load_strategy_runtime_state",
    "run_event_strategy_hook",
    "run_persisted_event_strategy_hook",
]
