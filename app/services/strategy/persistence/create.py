"""Create operations for Strategy-owned database records."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    """Atomically create an immutable Strategy version and mutation record.

    Args:
        request: Validated Strategy registration command.
        policy: Policy recorded with the immutable version.
        record_hash: Canonical registry-record digest.
        mutation: Initial mutation publication record.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating immutable Strategy version persistence records")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT INTO strategy_versions (strategy_id, "
                        "strategy_version, manifest_json, lifecycle_status, "
                        "policy_json, record_hash, request_id, correlation_id) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        "INSERT INTO strategy_mutations (command_id, "
                        "mutation_json, publication_pending) VALUES (?, ?, 1)",
                    ),
                    parameter_sets=(
                        (
                            request.manifest.strategy_id,
                            request.manifest.strategy_version,
                            request.manifest.model_dump_json(),
                            request.lifecycle_status.value,
                            policy.model_dump_json(),
                            record_hash,
                            request.request_id,
                            request.correlation_id,
                        ),
                        (request.command_id, mutation.model_dump_json()),
                    ),
                    max_rows=2,
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
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
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
                request_id=checkpoint.request_id,
            )
        ),
        operation="data.execute_transaction.strategy_checkpoint_write",
    )


__all__ = ["create_strategy_checkpoint_record", "create_strategy_version_record"]
