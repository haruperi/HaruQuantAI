"""Exact approved Strategy reference resolution."""

from __future__ import annotations

from app.services.data.contracts import DataError
from app.services.data.persistence import execute_transaction
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.strategy.contracts.enums import StrategyLifecycleStatus
from app.services.strategy.contracts.manifest import StrategyManifest
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.contracts.policy import (
    StrategyValidationPolicy,  # noqa: TC001
)
from app.services.strategy.contracts.references import (
    StrategyRef,
    ValidatedStrategyRef,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.migrations import _ensure_strategy_storage
from app.utils import logger


def validate_strategy_ref(
    ref: StrategyRef,
    policy: StrategyValidationPolicy,
) -> StrategyOutcome[ValidatedStrategyRef]:
    """Resolve and validate exactly one approved immutable strategy version.

    Args:
        ref: Caller-supplied version reference.
        policy: Explicit current validation policy.

    Returns:
        One validated exact reference or a deterministic failure.
    """
    logger.info("Validating Strategy reference for %s", ref.strategy_id)
    try:
        _ensure_strategy_storage(ref.request_id)
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "SELECT manifest_json, lifecycle_status, policy_json, "
                        "record_hash, request_id, correlation_id FROM "
                        "strategy_versions WHERE strategy_id = ? ORDER BY "
                        "strategy_version",
                    ),
                    parameter_sets=((ref.strategy_id,),),
                    max_rows=1_000,
                ),
                request_id=ref.request_id,
            )
        )
    except DataError:
        logger.error("Strategy reference persistence read failed")
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "strategy registry read failed",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    matches: list[ValidatedStrategyRef] = []
    for row in result.rows:
        manifest = StrategyManifest.model_validate_json(str(row["manifest_json"]))
        if not _version_matches(manifest.strategy_version, ref):
            continue
        validated = _validate_record(
            manifest,
            StrategyLifecycleStatus(str(row["lifecycle_status"])),
            str(row["record_hash"]),
            ref,
            policy,
        )
        if validated.status == "success" and validated.data is not None:
            matches.append(validated.data)
        elif validated.status == "error":
            return validated
    if len(matches) != 1:
        code = (
            StrategyErrorCode.NOT_FOUND
            if not result.rows
            else StrategyErrorCode.VERSION_CONSTRAINT_UNSATISFIABLE
        )
        return failure(
            code,
            "strategy reference did not resolve to exactly one approved version",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    return success(matches[0])


def _version_matches(version: str, ref: StrategyRef) -> bool:
    """Return whether one stored version matches a caller selector.

    Args:
        version: Stored exact version.
        ref: Caller selector.

    Returns:
        Whether the version matches.
    """
    logger.debug("Matching Strategy version constraint")
    if ref.exact_version is not None:
        return version == ref.exact_version
    constraint = ref.version_constraint or ""
    if constraint == "*":
        return True
    if constraint.startswith("=="):
        return version == constraint[2:]
    return version == constraint


def _validate_record(
    manifest: StrategyManifest,
    lifecycle: StrategyLifecycleStatus,
    record_hash: str,
    ref: StrategyRef,
    policy: StrategyValidationPolicy,
) -> StrategyOutcome[ValidatedStrategyRef]:
    """Validate one resolved registry record.

    Args:
        manifest: Stored immutable manifest.
        lifecycle: Stored lifecycle state.
        record_hash: Stored registry hash.
        ref: Caller reference.
        policy: Current validation policy.

    Returns:
        A validated reference or deterministic error.
    """
    logger.debug("Validating resolved Strategy registry record")
    if lifecycle is not StrategyLifecycleStatus.APPROVED:
        return failure(
            StrategyErrorCode.LIFECYCLE_NOT_APPROVED,
            "strategy lifecycle is not approved",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    if ref.environment not in manifest.permitted_environments:
        return failure(
            StrategyErrorCode.ENVIRONMENT_NOT_PERMITTED,
            "strategy is not permitted in the requested environment",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    if not any(
        manifest.module_path == root or manifest.module_path.startswith(f"{root}.")
        for root in policy.approved_module_roots
    ):
        return failure(
            StrategyErrorCode.UNAPPROVED_MODULE,
            "strategy module is outside approved roots",
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    return success(
        ValidatedStrategyRef(
            manifest=manifest,
            lifecycle_status=lifecycle,
            environment=ref.environment,
            policy_version=policy.policy_version,
            validation_policy=policy,
            registry_record_hash=record_hash,
            request_id=ref.request_id,
            correlation_id=ref.correlation_id,
        )
    )


__all__ = ["validate_strategy_ref"]
