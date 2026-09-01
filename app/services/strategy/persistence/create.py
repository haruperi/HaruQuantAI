"""Create operations for Strategy-owned database records."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.strategy.contracts.responses import unwrap_data_response

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


def create_strategy_profile_record(
    *,
    profile_id: str,
    strategy_id: str,
    strategy_version: str,
    profile_json: str,
    expectancy_profile_ref: str | None,
    expectancy_exact_version: str | None,
    record_hash: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Persist one versioned Strategy profile record.

    Args:
        profile_id: Stable profile identifier.
        strategy_id: Owning strategy identifier.
        strategy_version: Exact strategy version.
        profile_json: JSON serialized StrategyProfile v1.
        expectancy_profile_ref: Optional exact expectancy profile reference.
        expectancy_exact_version: Optional exact expectancy version.
        record_hash: Canonical profile-record digest.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy profile persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_profiles (profile_id, "
                        "strategy_id, strategy_version, profile_json, "
                        "expectancy_profile_ref, expectancy_exact_version, record_hash, "
                        "request_id, correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            profile_id,
                            strategy_id,
                            strategy_version,
                            profile_json,
                            expectancy_profile_ref,
                            expectancy_exact_version,
                            record_hash,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_profile_create",
    )


def create_strategy_playbook_record(
    *,
    playbook_id: str,
    playbook_version: int,
    strategy_profile_ref: str,
    playbook_json: str,
    record_hash: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Persist one versioned Strategy playbook record.

    Args:
        playbook_id: Stable playbook identifier.
        playbook_version: Positive playbook version.
        strategy_profile_ref: Referenced strategy profile.
        playbook_json: JSON serialized StrategyPlaybook v1.
        record_hash: Canonical playbook-record digest.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy playbook persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_playbooks (playbook_id, "
                        "playbook_version, strategy_profile_ref, playbook_json, "
                        "record_hash, request_id, correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            playbook_id,
                            playbook_version,
                            strategy_profile_ref,
                            playbook_json,
                            record_hash,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_playbook_create",
    )


def create_strategy_setup_evaluation_record(
    *,
    evaluation_id: str,
    playbook_ref: str,
    outcome: str,
    source_snapshot_json: str,
    reason_code_json: str,
    record_hash: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Append one Strategy setup evaluation evidence record.

    Args:
        evaluation_id: Evaluation evidence identifier.
        playbook_ref: Evaluated playbook reference.
        outcome: Deterministic setup-evaluation outcome.
        source_snapshot_json: JSON serialized source snapshot references.
        reason_code_json: JSON serialized reason codes.
        record_hash: Canonical evaluation-record digest.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy setup evaluation persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT INTO strategy_setup_evaluations (evaluation_id, "
                        "playbook_ref, outcome, source_snapshot_json, reason_code_json, "
                        "record_hash, request_id, correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            evaluation_id,
                            playbook_ref,
                            outcome,
                            source_snapshot_json,
                            reason_code_json,
                            record_hash,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_setup_evaluation_create",
    )


def create_strategy_plan_record(
    *,
    plan_id: str,
    plan_version: int,
    status: str,
    strategy_id: str,
    strategy_version: str,
    plan_json: str,
    parent_plan_id: str | None,
    record_hash: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Persist one canonical Strategy trade plan record.

    Args:
        plan_id: Stable plan identifier.
        plan_version: Positive plan version.
        status: Plan lifecycle status.
        strategy_id: Owning strategy identifier.
        strategy_version: Exact strategy version.
        plan_json: JSON serialized TradePlan v1.
        parent_plan_id: Optional parent plan for amendments.
        record_hash: Canonical plan-record digest.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy trade plan persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_plans (plan_id, plan_version, "
                        "status, strategy_id, strategy_version, plan_json, parent_plan_id, "
                        "record_hash, request_id, correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            plan_id,
                            plan_version,
                            status,
                            strategy_id,
                            strategy_version,
                            plan_json,
                            parent_plan_id,
                            record_hash,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_plan_create",
    )


def create_strategy_automation_policy_record(
    *,
    policy_id: str,
    strategy_id: str,
    strategy_version: str,
    policy_version: int,
    mode: str,
    policy_json: str,
    record_hash: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Persist one versioned Strategy automation policy record.

    Args:
        policy_id: Stable policy identifier.
        strategy_id: Owning strategy identifier.
        strategy_version: Exact strategy version.
        policy_version: Positive policy version.
        mode: Effective automation mode.
        policy_json: JSON serialized policy body.
        record_hash: Canonical policy-record digest.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy automation policy persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT OR IGNORE INTO strategy_automation_policy (policy_id, "
                        "strategy_id, strategy_version, policy_version, mode, policy_json, "
                        "record_hash, request_id, correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            policy_id,
                            strategy_id,
                            strategy_version,
                            policy_version,
                            mode,
                            policy_json,
                            record_hash,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_automation_policy_create",
    )


def create_strategy_lifecycle_record(
    *,
    strategy_id: str,
    strategy_version: str,
    from_status: str,
    to_status: str,
    reason: str,
    decision_json: str,
    request_id: str,
    correlation_id: str,
) -> None:
    """Append one Strategy lifecycle decision record.

    Args:
        strategy_id: Owning strategy identifier.
        strategy_version: Exact strategy version.
        from_status: Source lifecycle status.
        to_status: Target lifecycle status.
        reason: Governance reason.
        decision_json: JSON serialized lifecycle decision.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    logger.info("Creating Strategy lifecycle persistence record")
    unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "INSERT INTO strategy_lifecycle (strategy_id, strategy_version, "
                        "from_status, to_status, reason, decision_json, request_id, "
                        "correlation_id, created_at) VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                    ),
                    parameter_sets=(
                        (
                            strategy_id,
                            strategy_version,
                            from_status,
                            to_status,
                            reason,
                            decision_json,
                            request_id,
                            correlation_id,
                        ),
                    ),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="data.execute_transaction.strategy_lifecycle_create",
    )


__all__: list[str] = [
    "create_strategy_automation_policy_record",
    "create_strategy_checkpoint_record",
    "create_strategy_lifecycle_record",
    "create_strategy_plan_record",
    "create_strategy_playbook_record",
    "create_strategy_profile_record",
    "create_strategy_setup_evaluation_record",
    "create_strategy_signal_records",
    "create_strategy_version_record",
]
