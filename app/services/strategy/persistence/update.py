"""Update operations for Strategy-owned database records."""

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
    from app.services.strategy.contracts.outcomes import StrategyMutationResult
    from app.services.strategy.contracts.references import ValidatedStrategyConfig

logger = get_logger(__name__)


def update_strategy_configuration_record(
    config: ValidatedStrategyConfig,
    mutation: StrategyMutationResult,
    command_id: str,
    request_id: str,
) -> None:
    """Atomically record an immutable configuration update and mutation.

    The operation uses inserts because Strategy updates are immutable new versions;
    its domain effect is an update to the configured Strategy state.

    Args:
        config: Validated immutable Strategy configuration.
        mutation: Initial mutation publication record.
        command_id: Stable caller idempotency identifier.
        request_id: Request trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Updating immutable Strategy configuration persistence state")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_configs (strategy_id, "
                        "strategy_version, config_hash, config_json, "
                        "policy_version, request_id) VALUES (?, ?, ?, ?, ?, ?)",
                        "INSERT INTO strategy_mutations (command_id, mutation_json, "
                        "publication_pending) VALUES (?, ?, 1)",
                    ),
                    parameter_sets=(
                        (
                            config.strategy_id,
                            config.strategy_version,
                            config.config_hash,
                            config.model_dump_json(),
                            config.policy_version,
                            request_id,
                        ),
                        (command_id, mutation.model_dump_json()),
                    ),
                    max_rows=2,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_parameter_mutation",
    )


def update_strategy_mutation_publication(
    mutation: StrategyMutationResult, command_id: str
) -> None:
    """Mark one committed Strategy mutation's audit evidence as published.

    Args:
        mutation: Mutation containing the committed audit-event reference.
        command_id: Stable caller idempotency identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Updating Strategy mutation publication persistence state")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "UPDATE strategy_mutations SET mutation_json = ?, "
                        "publication_pending = 0 WHERE command_id = ?",
                    ),
                    parameter_sets=((mutation.model_dump_json(), command_id),),
                    max_rows=1,
                ),
                request_id=mutation.request_id,
            )
        ),
        operation="data.execute_transaction.strategy_mutation_publication",
    )


__all__ = [
    "update_strategy_configuration_record",
    "update_strategy_mutation_publication",
]
