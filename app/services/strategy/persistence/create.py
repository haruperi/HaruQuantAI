"""Create operations for Strategy-owned database records."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.strategy.contracts.responses import unwrap_data_response
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.strategy.checkpoints.models import StrategyCheckpoint
    from app.services.strategy.contracts.outcomes import StrategyMutationResult
    from app.services.strategy.contracts.policy import StrategyValidationPolicy
    from app.services.strategy.contracts.requests import StrategyRegistrationRequest

logger = get_logger(__name__)


def create_strategy_version_record(
    request: StrategyRegistrationRequest,
    policy: StrategyValidationPolicy,
    record_hash: str,
    mutation: StrategyMutationResult,
) -> None:
    """Atomically create immutable Strategy definition, version, and mutation records.

    Args:
        request: Validated Strategy registration command.
        policy: Policy recorded with the immutable version.
        record_hash: Canonical registry-record digest.
        mutation: Initial mutation publication record.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating immutable Strategy version persistence records")
    version_id = f"{request.manifest.strategy_id}@{request.manifest.strategy_version}"
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_definitions (strategy_id, "
                        "evaluator_key, strategy_code, display_name, strategy_class, "
                        "owner_ref, description, lifecycle_status, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, 'trend', ?, 'Registered Strategy definition', 'active', "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                        "INSERT INTO strategy_versions (version_id, strategy_id, "
                        "strategy_version, module_path, manifest_json, lifecycle_status, "
                        "policy_json, source_hash, artifact_hash, dependency_hash, "
                        "record_hash, request_id, correlation_id, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                        "INSERT INTO strategy_mutations (command_id, mutation_type, "
                        "strategy_id, strategy_version, mutation_json, publication_pending, "
                        "request_id, correlation_id, created_at) VALUES "
                        "(?, 'REGISTER_VERSION', ?, ?, ?, 1, ?, ?, "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            request.manifest.strategy_id,
                            request.manifest.strategy_id,
                            request.manifest.strategy_id,
                            request.manifest.strategy_id,
                            request.manifest.owner_ref,
                        ),
                        (
                            version_id,
                            request.manifest.strategy_id,
                            request.manifest.strategy_version,
                            request.manifest.module_path,
                            request.manifest.model_dump_json(),
                            request.lifecycle_status.value,
                            policy.model_dump_json(),
                            request.manifest.source_hash,
                            request.manifest.artifact_hash,
                            request.manifest.dependency_hash,
                            record_hash,
                            request.request_id,
                            request.correlation_id,
                        ),
                        (
                            request.command_id,
                            request.manifest.strategy_id,
                            request.manifest.strategy_version,
                            mutation.model_dump_json(),
                            request.request_id,
                            request.correlation_id,
                        ),
                    ),
                    max_rows=3,
                ),
                request_id=request.request_id,
            )
        ),
        operation="data.execute_transaction.strategy_registry_mutation",
    )


def create_strategy_checkpoint_record(checkpoint: StrategyCheckpoint) -> None:
    """Create one immutable Strategy checkpoint record if it is absent.

    Args:
        checkpoint: Validated, redacted, and bounded checkpoint.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating immutable Strategy checkpoint persistence record")
    config_id = getattr(
        checkpoint,
        "config_id",
        f"{checkpoint.strategy_id}@{checkpoint.strategy_version}#{checkpoint.config_hash}",
    )
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_checkpoints "
                        "(checkpoint_id, config_id, state_version, sequence, "
                        "checkpoint_json, checksum, authorization_ref, request_id, "
                        "correlation_id, created_at) "
                        "VALUES (?, ?, 0, 0, ?, ?, ?, ?, "
                        "'cor-00000000-0000-4000-8000-000000000000', "
                        "strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            checkpoint.checkpoint_id,
                            config_id,
                            checkpoint.model_dump_json(),
                            checkpoint.state_checksum,
                            checkpoint.authorization_ref,
                            checkpoint.request_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=checkpoint.request_id,
            )
        ),
        operation="data.execute_transaction.strategy_checkpoint_create",
    )


def create_strategy_signal_records(
    records: tuple[Mapping[str, Any], ...],
    request_id: str,
) -> None:
    """Atomically persist genuine evaluator Strategy signal output records.

    Args:
        records: Bounded sequence of signal record mappings.
        request_id: Tracing request identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    if not records:
        return
    logger.info("Creating durable Strategy signal persistence records")
    statements = tuple(
        "INSERT OR IGNORE INTO strategy_signals (signal_id, config_id, strategy_id, "
        "strategy_version, sequence, symbol, signal_name, side, active, "
        "signal_timestamp, signal_json, lineage_json, facts_json, intent_id, "
        "publication_status, risk_submission_ref, request_id, correlation_id, "
        "created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        for _ in records
    )
    parameter_sets = tuple(
        (
            rec["signal_id"],
            rec["config_id"],
            rec["strategy_id"],
            rec["strategy_version"],
            rec["sequence"],
            rec["symbol"],
            rec["signal_name"],
            rec.get("side"),
            1 if rec.get("active") else 0,
            rec["signal_timestamp"],
            rec["signal_json"],
            rec.get("lineage_json", "{}"),
            rec.get("facts_json", "{}"),
            rec.get("intent_id"),
            rec.get("publication_status", "generated"),
            rec.get("risk_submission_ref"),
            rec["request_id"],
            rec["correlation_id"],
            rec["created_at"],
            rec["updated_at"],
        )
        for rec in records
    )
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=statements,
                    parameter_sets=parameter_sets,
                    max_rows=len(records),
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_signal_create",
    )


__all__: list[str] = [
    "create_strategy_checkpoint_record",
    "create_strategy_signal_records",
    "create_strategy_version_record",
]
