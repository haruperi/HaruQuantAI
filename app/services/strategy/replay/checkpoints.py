"""Bounded persisted Strategy-local checkpoint operations."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from app.services.data.contracts import DataError, StatementPlan, TransactionRequest
from app.services.data.storage import execute_transaction
from app.services.strategy.contracts.models import (  # noqa: TC001
    JsonValue,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.migrations import ensure_strategy_storage
from app.services.strategy.replay.models import StrategyCheckpoint
from app.utils import (
    AuthContext,
    RedactionPolicy,
    canonical_json,
    logger,
    redact_mapping_value,
)

_CHECKPOINT_PERMISSION = "strategy:checkpoint"
_PROHIBITED_STATE_KEYS = frozenset(
    {"account", "broker", "fill", "order", "position", "risk_decision"}
)


def create_strategy_checkpoint(  # noqa: PLR0911
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    state: Mapping[str, JsonValue],
    authorization_ref: str,
    auth: AuthContext,
) -> StrategyOutcome[StrategyCheckpoint]:
    """Redact, bound, checksum, and persist Strategy-local state.

    Args:
        ref: Validated exact strategy reference.
        config: Validated exact configuration.
        state: Candidate Strategy-local JSON state.
        authorization_ref: Explicit authorization evidence reference.
        auth: Authenticated principal and trace context.

    Returns:
        Persisted checkpoint or deterministic validation/storage failure.
    """
    logger.info("Creating persisted Strategy checkpoint")
    if (
        _CHECKPOINT_PERMISSION not in auth.permissions
        or authorization_ref not in auth.scopes
    ):
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "checkpoint authorization is invalid",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    if config.strategy_id != ref.manifest.strategy_id or _contains_official_state(
        state
    ):
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "checkpoint contains incompatible or official state",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    try:
        redacted = redact_mapping_value(
            state,
            RedactionPolicy(
                max_text_length=ref.manifest.max_checkpoint_bytes,
                max_depth=ref.validation_policy.max_config_nesting_depth,
                max_items=ref.validation_policy.max_config_collection_items,
            ),
        )
        if not isinstance(redacted.value, dict):
            return failure(
                StrategyErrorCode.CHECKPOINT_INVALID,
                "checkpoint state is invalid",
                request_id=auth.request_id,
                correlation_id=auth.correlation_id,
            )
        state_json = canonical_json(redacted.value)
        payload_bytes = len(state_json.encode("utf-8"))
        if payload_bytes > ref.manifest.max_checkpoint_bytes:
            return failure(
                StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
                "checkpoint exceeds the approved resource budget",
                request_id=auth.request_id,
                correlation_id=auth.correlation_id,
            )
        checksum = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
        identity = canonical_json(
            {
                "strategy_id": ref.manifest.strategy_id,
                "strategy_version": ref.manifest.strategy_version,
                "config_hash": config.config_hash,
                "state_checksum": checksum,
                "authorization_ref": authorization_ref,
            }
        )
        checkpoint_id = (
            f"checkpoint-{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"
        )
        checkpoint = StrategyCheckpoint(
            checkpoint_id=checkpoint_id,
            strategy_id=ref.manifest.strategy_id,
            strategy_version=ref.manifest.strategy_version,
            config_hash=config.config_hash,
            state=redacted.value,
            state_checksum=checksum,
            authorization_ref=authorization_ref,
            created_at=auth.issued_at,
            request_id=auth.request_id,
            payload_bytes=payload_bytes,
            redacted_paths=redacted.redacted_paths,
        )
        ensure_strategy_storage(auth.request_id)
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_checkpoints "
                        "(checkpoint_id, checkpoint_json, checksum, "
                        "authorization_ref, request_id) VALUES (?, ?, ?, ?, ?)",
                    ),
                    parameter_sets=(
                        (
                            checkpoint.checkpoint_id,
                            checkpoint.model_dump_json(),
                            checkpoint.state_checksum,
                            checkpoint.authorization_ref,
                            checkpoint.request_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=auth.request_id,
            )
        )
        return success(checkpoint)
    except DataError:
        logger.error("Strategy checkpoint persistence failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "checkpoint persistence failed",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    except ValueError:
        logger.warning("Strategy checkpoint serialization failed")
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "checkpoint state is invalid",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )


def validate_strategy_checkpoint(
    checkpoint: StrategyCheckpoint,
    ref: ValidatedStrategyRef,
    config: ValidatedStrategyConfig,
    auth: AuthContext,
) -> StrategyOutcome[Mapping[str, JsonValue]]:
    """Load and validate a persisted checkpoint before restore.

    Args:
        checkpoint: Caller-supplied checkpoint identity and content.
        ref: Validated exact strategy reference.
        config: Validated exact configuration.
        auth: Authenticated principal and trace context.

    Returns:
        Immutable local state or deterministic incompatibility failure.
    """
    logger.info("Validating persisted Strategy checkpoint")
    if (
        _CHECKPOINT_PERMISSION not in auth.permissions
        or checkpoint.authorization_ref not in auth.scopes
    ):
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "checkpoint authorization is invalid",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    try:
        ensure_strategy_storage(auth.request_id)
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "SELECT checkpoint_json FROM strategy_checkpoints "
                        "WHERE checkpoint_id = ?",
                    ),
                    parameter_sets=((checkpoint.checkpoint_id,),),
                    max_rows=1,
                ),
                request_id=auth.request_id,
            )
        )
    except DataError:
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "checkpoint persistence read failed",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    if not result.rows:
        return failure(
            StrategyErrorCode.CHECKPOINT_INVALID,
            "checkpoint is unknown",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    stored = StrategyCheckpoint.model_validate_json(
        str(result.rows[0]["checkpoint_json"])
    )
    state_json = canonical_json(stored.state)
    checksum = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
    compatible = (
        stored == checkpoint
        and stored.strategy_id == ref.manifest.strategy_id
        and stored.strategy_version == ref.manifest.strategy_version
        and stored.config_hash == config.config_hash
        and stored.state_checksum == checksum
        and stored.payload_bytes <= ref.manifest.max_checkpoint_bytes
        and not _contains_official_state(stored.state)
    )
    if not compatible:
        return failure(
            StrategyErrorCode.CHECKPOINT_INCOMPATIBLE,
            "checkpoint identity or checksum is incompatible",
            request_id=auth.request_id,
            correlation_id=auth.correlation_id,
        )
    return success(stored.state)


def _contains_official_state(value: JsonValue) -> bool:
    """Return whether JSON material contains prohibited official state.

    Args:
        value: Candidate local state.

    Returns:
        Whether a prohibited key is present recursively.
    """
    logger.debug("Scanning Strategy checkpoint for official state")
    if isinstance(value, Mapping):
        if any(str(key).casefold() in _PROHIBITED_STATE_KEYS for key in value):
            return True
        return any(_contains_official_state(item) for item in value.values())
    if isinstance(value, tuple):
        return any(_contains_official_state(item) for item in value)
    return False


__all__ = ["create_strategy_checkpoint", "validate_strategy_checkpoint"]
