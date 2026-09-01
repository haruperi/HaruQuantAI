"""Read operations for Strategy-owned database records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.strategy.contracts.responses import unwrap_data_response

logger = get_logger(__name__)


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    max_rows: int,
    request_id: str,
    operation: str,
) -> tuple[Mapping[str, Any], ...]:
    """Execute one bounded Strategy read and return normalized rows.

    Args:
        statement: Parameterized SQL read statement.
        parameters: Bound statement parameters.
        max_rows: Maximum accepted result rows.
        request_id: Request trace identifier.
        operation: Safe dependency-operation label.

    Returns:
        Ordered normalized database rows.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    result = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(statement,),
                    parameter_sets=(parameters,),
                    max_rows=max_rows,
                ),
                request_id=request_id,
            )
        ),
        operation=operation,
    )
    return tuple(result.rows)


def read_strategy_definitions(
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read stable Strategy definitions.

    Args:
        request_id: Tracing request identifier.
        strategy_id: Optional exact strategy identifier.

    Returns:
        Tuple of matching definition row mappings.
    """
    if strategy_id:
        return _read_rows(
            "SELECT * FROM strategy_definitions WHERE strategy_id = ?",
            (strategy_id,),
            max_rows=1,
            request_id=request_id,
            operation="data.execute_transaction.strategy_definition_lookup",
        )
    return _read_rows(
        "SELECT * FROM strategy_definitions ORDER BY strategy_id ASC",
        (),
        max_rows=1000,
        request_id=request_id,
        operation="data.execute_transaction.strategy_definitions_list",
    )


def read_strategy_versions(
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read strategy versions.

    Args:
        request_id: Tracing request identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching version row mappings.
    """
    if strategy_id:
        return _read_rows(
            "SELECT * FROM strategy_versions WHERE strategy_id = ? "
            "ORDER BY strategy_version ASC",
            (strategy_id,),
            max_rows=500,
            request_id=request_id,
            operation="data.execute_transaction.strategy_versions_filtered_list",
        )
    return _read_rows(
        "SELECT * FROM strategy_versions "
        "ORDER BY strategy_id ASC, strategy_version ASC",
        (),
        max_rows=1000,
        request_id=request_id,
        operation="data.execute_transaction.strategy_versions_list",
    )


def read_strategy_manifest_record(
    strategy_id: str,
    strategy_version: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read manifest JSON for one exact Strategy version.

    Args:
        strategy_id: Exact Strategy identifier.
        strategy_version: Exact version string.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching manifest rows.
    """
    return _read_rows(
        "SELECT manifest_json FROM strategy_versions WHERE strategy_id = ? "
        "AND strategy_version = ?",
        (strategy_id, strategy_version),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_manifest_lookup",
    )


def read_strategy_policy_record(
    strategy_id: str,
    strategy_version: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read policy JSON for one exact Strategy version.

    Args:
        strategy_id: Exact Strategy identifier.
        strategy_version: Exact version string.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching policy rows.
    """
    return _read_rows(
        "SELECT policy_json FROM strategy_versions WHERE strategy_id = ? "
        "AND strategy_version = ?",
        (strategy_id, strategy_version),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_policy_lookup",
    )


def read_strategy_configs(
    strategy_id: str,
    strategy_version: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read strategy configs for an exact version.

    Args:
        strategy_id: Strategy identifier.
        strategy_version: Version string.
        request_id: Tracing request identifier.

    Returns:
        Tuple of matching config row mappings.
    """
    return _read_rows(
        "SELECT * FROM strategy_configs WHERE strategy_id = ? "
        "AND strategy_version = ? ORDER BY created_at DESC",
        (strategy_id, strategy_version),
        max_rows=500,
        request_id=request_id,
        operation="data.execute_transaction.strategy_configs_list",
    )


def read_strategy_config_record(
    config_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read one strategy config by config_id.

    Args:
        config_id: Immutable config identifier.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching config rows.
    """
    return _read_rows(
        "SELECT * FROM strategy_configs WHERE config_id = ?",
        (config_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_config_lookup",
    )


def read_strategy_state_record(
    config_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read current Strategy-local runtime state for one configuration.

    Args:
        config_id: Immutable config identifier.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching state rows.
    """
    return _read_rows(
        "SELECT * FROM strategy_state WHERE config_id = ?",
        (config_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_state_lookup",
    )


def read_strategy_checkpoint_record(
    checkpoint_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read one Strategy checkpoint by checkpoint_id.

    Args:
        checkpoint_id: Checkpoint record identifier.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching checkpoint rows.
    """
    return _read_rows(
        "SELECT * FROM strategy_checkpoints WHERE checkpoint_id = ?",
        (checkpoint_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_checkpoint_lookup",
    )


def read_strategy_checkpoints(
    config_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read all Strategy checkpoints for a configuration, newest first.

    Args:
        config_id: Configuration identifier.
        request_id: Tracing request identifier.

    Returns:
        Tuple of matching checkpoint row mappings.
    """
    return _read_rows(
        "SELECT * FROM strategy_checkpoints WHERE config_id = ? ORDER BY sequence DESC",
        (config_id,),
        max_rows=500,
        request_id=request_id,
        operation="data.execute_transaction.strategy_checkpoints_list",
    )


def read_strategy_signals(
    config_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read persisted Strategy signals for one configuration.

    Args:
        config_id: Configuration identifier.
        request_id: Tracing request identifier.

    Returns:
        Tuple of matching signal row mappings.
    """
    return _read_rows(
        "SELECT * FROM strategy_signals WHERE config_id = ? ORDER BY sequence ASC",
        (config_id,),
        max_rows=1000,
        request_id=request_id,
        operation="data.execute_transaction.strategy_signals_list",
    )


def read_strategy_mutation_record(
    command_id: str,
    request_id: str,
) -> tuple[Mapping[str, Any], ...]:
    """Read one Strategy mutation by command_id.

    Args:
        command_id: Command identifier.
        request_id: Tracing request identifier.

    Returns:
        Zero or one matching mutation rows.
    """
    return _read_rows(
        "SELECT mutation_json FROM strategy_mutations WHERE command_id = ?",
        (command_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_mutation_lookup",
    )


def read_strategy_profiles(
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read versioned Strategy profiles.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching profile row mappings.
    """
    if strategy_id:
        return _read_rows(
            "SELECT * FROM strategy_profiles WHERE strategy_id = ? "
            "ORDER BY strategy_id ASC",
            (strategy_id,),
            max_rows=10,
            request_id=request_id,
            operation="data.execute_transaction.strategy_profiles_list",
        )
    return _read_rows(
        "SELECT * FROM strategy_profiles ORDER BY strategy_id ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_profiles_all",
    )


def read_strategy_playbooks(
    request_id: str,
    playbook_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read versioned Strategy playbooks.

    Args:
        request_id: Request trace identifier.
        playbook_id: Optional exact playbook identifier filter.

    Returns:
        Tuple of matching playbook row mappings.
    """
    if playbook_id:
        return _read_rows(
            "SELECT * FROM strategy_playbooks WHERE playbook_id = ? "
            "ORDER BY playbook_version ASC",
            (playbook_id,),
            max_rows=10,
            request_id=request_id,
            operation="data.execute_transaction.strategy_playbooks_by_id",
        )
    return _read_rows(
        "SELECT * FROM strategy_playbooks ORDER BY playbook_id ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_playbooks_all",
    )


def read_strategy_setup_evaluations(
    request_id: str,
    playbook_ref: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read append-only Strategy setup evaluation evidence.

    Args:
        request_id: Request trace identifier.
        playbook_ref: Optional playbook reference filter.

    Returns:
        Tuple of matching evaluation row mappings.
    """
    if playbook_ref:
        return _read_rows(
            "SELECT * FROM strategy_setup_evaluations WHERE playbook_ref = ? "
            "ORDER BY created_at ASC",
            (playbook_ref,),
            max_rows=100,
            request_id=request_id,
            operation="data.execute_transaction.strategy_setup_evaluations_by_playbook",
        )
    return _read_rows(
        "SELECT * FROM strategy_setup_evaluations ORDER BY created_at ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_setup_evaluations_all",
    )


def read_strategy_plans(
    request_id: str,
    plan_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read canonical Strategy trade plans.

    Args:
        request_id: Request trace identifier.
        plan_id: Optional exact plan identifier filter.

    Returns:
        Tuple of matching plan row mappings.
    """
    if plan_id:
        return _read_rows(
            "SELECT * FROM strategy_plans WHERE plan_id = ? ORDER BY plan_version ASC",
            (plan_id,),
            max_rows=10,
            request_id=request_id,
            operation="data.execute_transaction.strategy_plans_by_id",
        )
    return _read_rows(
        "SELECT * FROM strategy_plans ORDER BY plan_id ASC, plan_version ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_plans_all",
    )


def read_strategy_automation_policies(
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read versioned Strategy automation policies.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching policy row mappings.
    """
    if strategy_id:
        return _read_rows(
            "SELECT * FROM strategy_automation_policy WHERE strategy_id = ? "
            "ORDER BY policy_version ASC",
            (strategy_id,),
            max_rows=10,
            request_id=request_id,
            operation="data.execute_transaction.strategy_automation_policy_by_id",
        )
    return _read_rows(
        "SELECT * FROM strategy_automation_policy ORDER BY strategy_id ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_automation_policy_all",
    )


def read_strategy_lifecycle(
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Read append-only Strategy lifecycle decisions.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching lifecycle decision row mappings.
    """
    if strategy_id:
        return _read_rows(
            "SELECT * FROM strategy_lifecycle WHERE strategy_id = ? "
            "ORDER BY created_at ASC",
            (strategy_id,),
            max_rows=100,
            request_id=request_id,
            operation="data.execute_transaction.strategy_lifecycle_by_strategy",
        )
    return _read_rows(
        "SELECT * FROM strategy_lifecycle ORDER BY created_at ASC",
        (),
        max_rows=100,
        request_id=request_id,
        operation="data.execute_transaction.strategy_lifecycle_all",
    )


__all__: list[str] = [
    "read_strategy_automation_policies",
    "read_strategy_checkpoint_record",
    "read_strategy_checkpoints",
    "read_strategy_config_record",
    "read_strategy_configs",
    "read_strategy_definitions",
    "read_strategy_lifecycle",
    "read_strategy_manifest_record",
    "read_strategy_mutation_record",
    "read_strategy_plans",
    "read_strategy_playbooks",
    "read_strategy_policy_record",
    "read_strategy_profiles",
    "read_strategy_setup_evaluations",
    "read_strategy_signals",
    "read_strategy_state_record",
    "read_strategy_versions",
]
