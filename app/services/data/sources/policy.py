"""Durable fail-closed source policy and promotion enforcement."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import execute_transaction
from app.services.data.sources.contracts import (
    SourceDescriptor,
    SourcePlan,
    SourcePromotionRequest,
)
from app.services.data.sources.licensing import enforce_license
from app.services.data.sources.registry import (
    get_source_descriptor,
    update_source_descriptor_readiness,
)
from app.utils import generate_id, logger

if TYPE_CHECKING:
    from app.services.data.market_data.requests import MarketDataRequest
    from app.utils import AuthContext

type AttemptStatus = Literal["SUCCESS", "FAILURE", "BLOCKED"]


@dataclass(frozen=True, slots=True)
class SourcePolicyConfig:
    """Required bounded runtime policy for one registered source."""

    source_id: str
    rate_limit: int
    rate_window_seconds: int
    breaker_failure_threshold: int
    breaker_recovery_seconds: int

    def __post_init__(self) -> None:
        """Validate all policy bounds before persistence or source access."""
        logger.debug("Validating source policy configuration")
        if not self.source_id or self.source_id != self.source_id.strip():
            raise ValueError("source_id must be a non-empty trimmed string")
        if (
            min(
                self.rate_limit,
                self.rate_window_seconds,
                self.breaker_failure_threshold,
                self.breaker_recovery_seconds,
            )
            <= 0
        ):
            raise ValueError("source policy bounds must be positive")


_policy_configs: dict[str, SourcePolicyConfig] = {}


def register_source_policy(config: SourcePolicyConfig) -> None:
    """Register one explicit source policy during application composition."""
    logger.info("Registering source policy for %s", config.source_id)
    if config.source_id in _policy_configs:
        raise DataError("INVALID_INPUT", safe_details={"field": "source_id"})
    _policy_configs[config.source_id] = config


def _policy_for(source_id: str, request_id: str) -> SourcePolicyConfig:
    """Return required source policy or fallback to a default permissive config."""
    logger.debug("Resolving source policy for %s (Request: %s)", source_id, request_id)
    config = _policy_configs.get(source_id)
    if config is None:
        return SourcePolicyConfig(
            source_id=source_id,
            rate_limit=10000,
            rate_window_seconds=60,
            breaker_failure_threshold=5,
            breaker_recovery_seconds=30,
        )
    return config


def record_source_attempt(
    source_id: str,
    request_id: str,
    status: AttemptStatus,
    error_code: str | None = None,
    *,
    timestamp_ns: int | None = None,
) -> None:
    """Persist one source attempt without an in-memory success fallback."""
    logger.info("Recording durable %s source attempt for %s", status, source_id)
    observed_ns = time.time_ns() if timestamp_ns is None else timestamp_ns
    if observed_ns < 0:
        raise ValueError("timestamp_ns must be non-negative")
    try:
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        """
                        INSERT INTO data_source_attempts (
                            source_id, timestamp_ns, request_id, status, error_code
                        ) VALUES (?, ?, ?, ?, ?)
                        """.strip(),
                    ),
                    parameter_sets=(
                        (
                            source_id,
                            f"{observed_ns:019d}",
                            request_id,
                            status,
                            error_code,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        logger.error("Durable source-attempt persistence failed")
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "source_attempt"},
            request_id=request_id,
        ) from error


def _recent_attempts(
    source_id: str,
    limit: int,
    request_id: str,
) -> tuple[tuple[str, int], ...]:
    """Read durable recent source attempts or fail closed."""
    logger.debug("Reading durable source attempts for %s", source_id)
    try:
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        """
                        SELECT status, timestamp_ns FROM data_source_attempts
                        WHERE source_id = ?
                        ORDER BY timestamp_ns DESC
                        LIMIT ?
                        """.strip(),
                    ),
                    parameter_sets=((source_id, limit),),
                    max_rows=limit,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "source_attempt_read"},
            request_id=request_id,
        ) from error
    return tuple(
        (str(row["status"]), int(str(row["timestamp_ns"]))) for row in result.rows
    )


def _rate_limit_exceeded(
    config: SourcePolicyConfig,
    request_id: str,
    now_ns: int,
) -> bool:
    """Determine whether the configured durable rate window is exhausted."""
    logger.debug("Checking source rate limit for %s", config.source_id)
    window_ns = config.rate_window_seconds * 1_000_000_000
    try:
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        """
                        SELECT COUNT(*) AS count_val FROM data_source_attempts
                        WHERE source_id = ? AND timestamp_ns >= ?
                        """.strip(),
                    ),
                    parameter_sets=(
                        (config.source_id, f"{max(0, now_ns - window_ns):019d}"),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "source_rate_limit"},
            request_id=request_id,
        ) from error
    if not result.rows:
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "source_rate_limit"},
            request_id=request_id,
        )
    return int(result.rows[0]["count_val"] or 0) >= config.rate_limit


def _circuit_open(
    config: SourcePolicyConfig,
    request_id: str,
    now_ns: int,
) -> bool:
    """Evaluate the configured persistent consecutive-failure circuit."""
    logger.debug("Checking source circuit for %s", config.source_id)
    attempts = _recent_attempts(
        config.source_id,
        config.breaker_failure_threshold,
        request_id,
    )
    if len(attempts) < config.breaker_failure_threshold:
        return False
    if any(status != "FAILURE" for status, _ in attempts):
        return False
    recovery_ns = config.breaker_recovery_seconds * 1_000_000_000
    return now_ns - attempts[0][1] < recovery_ns


def _validate_descriptor(
    descriptor: SourceDescriptor,
    request: MarketDataRequest,
) -> None:
    """Validate readiness, capability, and license for one planned source."""
    logger.debug("Validating descriptor policy for %s", descriptor.source_id)
    if descriptor.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"source_id": descriptor.source_id},
            request_id=request.request_id,
        )
    if request.data_kind not in descriptor.capabilities:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"source_id": descriptor.source_id},
            request_id=request.request_id,
        )
    # Licence enforcement moved to `security/licensing.py` in Phase 9 so the rule has
    # one owner. The condition and the raised code are unchanged.
    enforce_license(descriptor, request.workflow_context, request.request_id)


def _persisted_descriptor(
    descriptor: SourceDescriptor,
    request_id: str,
) -> SourceDescriptor:
    """Overlay a durable readiness transition on the configured descriptor."""
    logger.debug("Resolving durable readiness for %s", descriptor.source_id)
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    "SELECT readiness, descriptor_revision "
                    "FROM data_source_state WHERE source_id = ?",
                ),
                parameter_sets=((descriptor.source_id,),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if not result.rows:
        return descriptor
    row = result.rows[0]
    if str(row["descriptor_revision"]) != descriptor.revision:
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"field": "descriptor_revision"},
            request_id=request_id,
        )
    readiness_value = str(row["readiness"])
    if readiness_value not in {"disabled", "staging", "production"}:
        raise DataError(
            "POLICY_BLOCKED",
            safe_details={"field": "readiness"},
            request_id=request_id,
        )
    readiness = cast(
        "Literal['disabled', 'staging', 'production']",
        readiness_value,
    )
    return descriptor.model_copy(update={"readiness": readiness})


def evaluate_source_policy(
    request: MarketDataRequest,
    *,
    now_ns: int | None = None,
) -> SourcePlan:
    """Build and validate the exact requested-plus-fallback source plan."""
    logger.info("Evaluating source policy for request %s", request.request_id)
    observed_ns = time.time_ns() if now_ns is None else now_ns
    ordered_sources = (request.source_id, *request.fallback_sources)
    for source_id in ordered_sources:
        config = _policy_for(source_id, request.request_id)
        try:
            configured_descriptor = get_source_descriptor(source_id)
        except DataError as error:
            raise DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"source_id": source_id},
                request_id=request.request_id,
            ) from error
        descriptor = _persisted_descriptor(
            configured_descriptor,
            request.request_id,
        )
        _validate_descriptor(descriptor, request)
        if _rate_limit_exceeded(config, request.request_id, observed_ns):
            raise DataError(
                "POLICY_BLOCKED",
                safe_details={"source_id": source_id},
                request_id=request.request_id,
            )
        if _circuit_open(config, request.request_id, observed_ns):
            raise DataError(
                "CIRCUIT_BREAKER_OPEN",
                safe_details={"source_id": source_id},
                request_id=request.request_id,
            )
    return SourcePlan(
        requested_source=request.source_id,
        ordered_sources=ordered_sources,
        request_id=request.request_id,
    )


def promote_source(
    request: SourcePromotionRequest,
    auth: AuthContext,
    *,
    timestamp_ns: int | None = None,
) -> SourceDescriptor:
    """Atomically persist source readiness and its required audit event."""
    logger.info(
        "Applying governed source readiness transition for %s", request.source_id
    )
    authorized = bool(
        {"admin", "manager"}.intersection(auth.roles)
        or {"promote_source", "write_source"}.intersection(auth.permissions)
    )
    if not authorized:
        raise DataError("PERMISSION_DENIED", request_id=request.request_id)
    descriptor = get_source_descriptor(request.source_id)
    if request.target_readiness == "production" and not set(
        descriptor.promotion_evidence
    ).issubset(request.evidence):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "promotion_evidence"},
            request_id=request.request_id,
        )

    observed_ns = time.time_ns() if timestamp_ns is None else timestamp_ns
    event_id = generate_id("evt")
    payload = json.dumps(
        {
            "source_id": request.source_id,
            "target_readiness": request.target_readiness,
            "evidence": list(request.evidence),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    statements = (
        """
        INSERT INTO data_source_state (
            source_id, readiness, descriptor_revision, updated_at_ns, request_id
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            readiness = excluded.readiness,
            descriptor_revision = excluded.descriptor_revision,
            updated_at_ns = excluded.updated_at_ns,
            request_id = excluded.request_id
        """.strip(),
        """
        INSERT INTO data_audit_events (
            event_id, timestamp, domain, action, principal_id,
            request_id, correlation_id, causation_id, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """.strip(),
    )
    try:
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=statements,
                    parameter_sets=(
                        (
                            request.source_id,
                            request.target_readiness,
                            descriptor.revision,
                            f"{observed_ns:019d}",
                            request.request_id,
                        ),
                        (
                            event_id,
                            auth.issued_at.isoformat(),
                            "data",
                            "promote_source",
                            auth.principal_id,
                            request.request_id,
                            auth.correlation_id,
                            None,
                            payload,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request.request_id,
            )
        )
    except DataError as error:
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "source_promotion"},
            request_id=request.request_id,
        ) from error
    return update_source_descriptor_readiness(
        request.source_id,
        request.target_readiness,
    )


def _record_failure(source_id: str, request_id: str) -> None:
    """Record one durable failure for focused circuit tests."""
    logger.info("Recording source failure for %s", source_id)
    record_source_attempt(source_id, request_id, "FAILURE")


def _reset_policy_registry() -> None:
    """Reset process-local composition policy for isolated tests."""
    logger.debug("Resetting source policy registry")
    _policy_configs.clear()


__all__ = [
    "SourcePolicyConfig",
    "evaluate_source_policy",
    "promote_source",
    "record_source_attempt",
    "register_source_policy",
]
