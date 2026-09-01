"""Durable state mutation operations for Strategy records."""

# ruff: noqa: E501

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.strategy.contracts.responses import unwrap_data_response

if TYPE_CHECKING:
    from app.services.strategy.contracts.outcomes import StrategyMutationResult
    from app.services.strategy.contracts.references import ValidatedStrategyConfig

logger = get_logger(__name__)


def update_strategy_configuration_record(
    config: ValidatedStrategyConfig,
    mutation: StrategyMutationResult,
    command_id: str,
    request_id: str,
) -> None:
    """Atomically record an immutable configuration update, mutation, and initial state.

    Args:
        config: Validated immutable Strategy configuration.
        mutation: Initial mutation publication record.
        command_id: Stable caller idempotency identifier.
        request_id: Request trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info(
        "Updating Strategy configuration, mutation, and initial state persistence"
    )
    config_id = getattr(
        config,
        "config_id",
        f"{config.strategy_id}@{config.strategy_version}#{config.config_hash}",
    )
    version_id = f"{config.strategy_id}@{config.strategy_version}"
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_configs (config_id, version_id, "
                        "strategy_id, strategy_version, config_hash, config_schema_version, "
                        "config_json, policy_version, runtime_profile, lifecycle_status, "
                        "request_id, correlation_id, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'RESEARCH', 'active', ?, "
                        "'cor-00000000-0000-4000-8000-000000000000', "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                        "INSERT INTO strategy_mutations (command_id, mutation_type, "
                        "strategy_id, strategy_version, mutation_json, publication_pending, "
                        "request_id, correlation_id, created_at) VALUES "
                        "(?, 'UPDATE_PARAMETERS', ?, ?, ?, 1, ?, "
                        "'cor-00000000-0000-4000-8000-000000000000', "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                        "INSERT OR IGNORE INTO strategy_state (config_id, state_version, "
                        "evaluation_status, bars_processed, last_evidence_at, last_signal_id, "
                        "local_state_json, local_state_hash, request_id, correlation_id, "
                        "created_at, updated_at) "
                        "VALUES (?, 0, 'initialized', 0, NULL, NULL, '{}', "
                        "'44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a', ?, "  # pragma: allowlist secret
                        "'cor-00000000-0000-4000-8000-000000000000', "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            config_id,
                            version_id,
                            config.strategy_id,
                            config.strategy_version,
                            config.config_hash,
                            config.config_schema_version,
                            config.model_dump_json(),
                            config.policy_version,
                            request_id,
                        ),
                        (
                            command_id,
                            config.strategy_id,
                            config.strategy_version,
                            mutation.model_dump_json(),
                            request_id,
                        ),
                        (
                            config_id,
                            request_id,
                        ),
                    ),
                    max_rows=3,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_config_mutation",
    )


def update_strategy_runtime_state_record(
    config_id: str,
    expected_state_version: int,
    evaluation_status: str,
    bars_processed: int,
    last_evidence_at: str | None,
    last_signal_id: str | None,
    local_state_json: str,
    local_state_hash: str,
    request_id: str,
    correlation_id: str,
) -> bool:
    """Optimistically update Strategy-local runtime state.

    Args:
        config_id: Configuration identifier.
        expected_state_version: Stale check state version.
        evaluation_status: New evaluation status string.
        bars_processed: Total bars processed count.
        last_evidence_at: ISO timestamp string for evidence.
        last_signal_id: Last emitted signal identifier.
        local_state_json: Serialized local state JSON.
        local_state_hash: SHA-256 local state digest.
        request_id: Tracing request identifier.
        correlation_id: Tracing correlation identifier.

    Returns:
        True if exactly one row was updated, False if optimistic check failed.
    """
    logger.info("Updating Strategy runtime state record")
    res = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "UPDATE strategy_state SET "
                        "state_version = state_version + 1, "
                        "evaluation_status = ?, "
                        "bars_processed = ?, "
                        "last_evidence_at = ?, "
                        "last_signal_id = ?, "
                        "local_state_json = ?, "
                        "local_state_hash = ?, "
                        "request_id = ?, "
                        "correlation_id = ?, "
                        "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') "
                        "WHERE config_id = ? AND state_version = ?",
                    ),
                    parameter_sets=(
                        (
                            evaluation_status,
                            bars_processed,
                            last_evidence_at,
                            last_signal_id,
                            local_state_json,
                            local_state_hash,
                            request_id,
                            correlation_id,
                            config_id,
                            expected_state_version,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_state_update",
    )
    return bool(res.affected_rows == 1)


def update_strategy_signal_publication_record(
    signal_id: str,
    expected_status: str,
    new_status: str,
    risk_submission_ref: str,
    request_id: str,
) -> bool:
    """Update Strategy signal publication status with risk submission reference.

    Args:
        signal_id: Unique signal identifier.
        expected_status: Expected current publication status.
        new_status: Target publication status.
        risk_submission_ref: Opaque risk submission reference string.
        request_id: Tracing request identifier.

    Returns:
        True if state transition succeeded.
    """
    logger.info("Updating Strategy signal publication status")
    res = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "UPDATE strategy_signals SET "
                        "publication_status = ?, "
                        "risk_submission_ref = ?, "
                        "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') "
                        "WHERE signal_id = ? AND publication_status = ?",
                    ),
                    parameter_sets=(
                        (
                            new_status,
                            risk_submission_ref,
                            signal_id,
                            expected_status,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_signal_publication_update",
    )
    return bool(res.affected_rows == 1)


def update_strategy_mutation_publication(
    mutation: StrategyMutationResult,
    command_id: str,
) -> None:
    """Update mutation publication state after audit event creation.

    Args:
        mutation: Published mutation result.
        command_id: Caller command identifier.
    """
    logger.info("Updating Strategy mutation publication record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "UPDATE strategy_mutations SET "
                        "publication_pending = 0, "
                        "published_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') "
                        "WHERE command_id = ?",
                    ),
                    parameter_sets=((command_id,),),
                    max_rows=1,
                ),
                request_id=mutation.request_id,
            )
        ),
        operation="data.execute_transaction.strategy_mutation_publication_update",
    )


__all__: list[str] = [
    "update_strategy_configuration_record",
    "update_strategy_mutation_publication",
    "update_strategy_runtime_state_record",
    "update_strategy_signal_publication_record",
]
