"""Create operations for Research-owned artifact metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    run_domain_migrations,
)
from app.services.research.contracts.errors import ValidationError
from app.services.research.migrations import build_research_migration_request

logger = get_logger(__name__)


def create_artifact_metadata(
    *,
    relative_path: str,
    format_name: str,
    size_bytes: int,
    sha256: str,
    atomic: bool,
    schema_version: str,
    audit_event_id: str,
    request_id: str,
    correlation_id: str,
) -> Mapping[str, object]:
    """Record one Research artifact manifest row through Data.

    Args:
        relative_path: Approved path relative to the Research artifact root.
        format_name: Serialized artifact format.
        size_bytes: Exact serialized byte count.
        sha256: Exact serialized content digest.
        atomic: Whether the file replacement was atomic.
        schema_version: Artifact schema version.
        audit_event_id: Authorizing audit event identifier.
        request_id: Request trace identifier.
        correlation_id: Cross-operation trace identifier.

    Returns:
        Detached normalized metadata row.

    Raises:
        ValidationError: If migration or insertion cannot be confirmed.
    """
    logger.info("Persisting Research artifact metadata")
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")
    statement = """INSERT INTO research_artifacts (
        relative_path, format, size_bytes, sha256, atomic, schema_version,
        audit_event_id, request_id, correlation_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(relative_path) DO UPDATE SET
        format = excluded.format,
        size_bytes = excluded.size_bytes,
        sha256 = excluded.sha256,
        atomic = excluded.atomic,
        schema_version = excluded.schema_version,
        audit_event_id = excluded.audit_event_id,
        request_id = excluded.request_id,
        correlation_id = excluded.correlation_id"""
    parameters = (
        relative_path,
        format_name,
        size_bytes,
        sha256,
        int(atomic),
        schema_version,
        audit_event_id,
        request_id,
        correlation_id,
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(cast("tuple[Any, ...]", parameters),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "METADATA_WRITE_FAILED")
    result = cast("Any", response.data)
    if result.affected_rows != 1:
        raise ValidationError("RES_PERSISTENCE_FAILED", "METADATA_CONFLICT")
    return {
        "relative_path": relative_path,
        "format": format_name,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "atomic": atomic,
        "schema_version": schema_version,
        "audit_event_id": audit_event_id,
        "request_id": request_id,
        "correlation_id": correlation_id,
    }


def create_expectancy_profile(
    *,
    profile_id: str,
    exact_version: str,
    strategy_ref: str,
    hypothesis: str,
    match_keys_json: str,
    envelope_json: str,
    governance_state: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_by: str,
    evidence_ref: str,
    canonical_hash: str,
    request_id: str,
) -> Mapping[str, object]:
    """Record one approved-expectancy governance row through Data.

    Args:
        profile_id: Stable surrogate governance identity (OD-RES-01).
        exact_version: Version-exact identity referenced by Strategy/Risk.
        strategy_ref: Strategy identity covered by the profile.
        hypothesis: Tested question or declared research objective.
        match_keys_json: Canonical JSON exact-match keys (instruments/regimes/sessions).
        envelope_json: Canonical JSON operating envelope and sample evidence.
        governance_state: Lifecycle state of the profile.
        reviewer: Reviewer principal for the recorded decision.
        decision: Recorded governance decision label.
        reason: Recorded governance decision reason.
        superseded_by: Surrogate identity superseding this profile, if any.
        evidence_ref: Bounded evidence reference backing the profile.
        canonical_hash: Canonical SHA-256 of the profile material.
        request_id: Request trace identifier.

    Returns:
        Detached normalized governance row.

    Raises:
        ValidationError: If migration or insertion cannot be confirmed.
    """
    logger.info("Persisting Research expectancy profile %s", profile_id)
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")
    statement = """INSERT INTO research_expectancy_profiles (
        profile_id, exact_version, strategy_ref, hypothesis, match_keys_json,
        envelope_json, governance_state, reviewer, decision, reason,
        superseded_by, evidence_ref, canonical_hash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    parameters = (
        profile_id,
        exact_version,
        strategy_ref,
        hypothesis,
        match_keys_json,
        envelope_json,
        governance_state,
        reviewer,
        decision,
        reason,
        superseded_by,
        evidence_ref,
        canonical_hash,
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(cast("tuple[Any, ...]", parameters),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EXPECTANCY_WRITE_FAILED")
    result = cast("Any", response.data)
    if result.affected_rows != 1:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EXPECTANCY_CONFLICT")
    return {
        "profile_id": profile_id,
        "exact_version": exact_version,
        "strategy_ref": strategy_ref,
        "governance_state": governance_state,
        "canonical_hash": canonical_hash,
    }


def create_governed_evidence(
    *,
    table: str,
    identity_column: str,
    identity: str,
    evidence_json: str,
    canonical_hash: str,
    request_id: str,
) -> Mapping[str, object]:
    """Append one immutable Research evidence record.

    Args:
        table: Approved Research evidence table.
        identity_column: Approved identity column.
        identity: Profile or scenario identity.
        evidence_json: Canonical evidence JSON.
        canonical_hash: Canonical evidence digest.
        request_id: Request trace identifier.

    Returns:
        Detached persistence acknowledgement.

    Raises:
        ValidationError: If the target is unsupported or persistence fails.
    """
    targets = {
        ("research_performance_drift_evidence", "profile_id"),
        ("research_stress_scenario_evidence", "scenario_id"),
    }
    if (table, identity_column) not in targets:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EVIDENCE_TARGET_INVALID")
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")
    statement = (
        f"INSERT INTO {table} "  # noqa: S608 - table is closed above.
        f"({identity_column}, evidence_json, canonical_hash, request_id) "
        "VALUES (?, ?, ?, ?)"
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=((identity, evidence_json, canonical_hash, request_id),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EVIDENCE_WRITE_FAILED")
    if cast("Any", response.data).affected_rows != 1:
        raise ValidationError("RES_PERSISTENCE_FAILED", "EVIDENCE_CONFLICT")
    return {
        identity_column: identity,
        "canonical_hash": canonical_hash,
        "request_id": request_id,
    }


__all__ = (
    "create_artifact_metadata",
    "create_expectancy_profile",
    "create_governed_evidence",
)


def create_research_experiment_row(
    *,
    experiment_id: str,
    principal_id: str,
    name: str,
    hypothesis: str,
    notes: str,
    tags_json: str,
    created_at: str,
    request_id: str,
) -> None:
    """Insert one experiment ledger row through Data.

    Args:
        experiment_id: Stable experiment identity.
        principal_id: Owning authenticated principal.
        name: Human-readable experiment name.
        hypothesis: Explicit hypothesis under test.
        notes: Free-form notes, empty when absent.
        tags_json: Serialized tag list.
        created_at: ISO-8601 creation instant.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If migration or insertion cannot be confirmed.
    """
    logger.info("Persisting Research experiment row")
    _confirm_run_migration(request_id)
    statement = """INSERT INTO research_experiments (
        experiment_id, principal_id, name, hypothesis, notes, tags_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(experiment_id) DO UPDATE SET
        name = excluded.name,
        hypothesis = excluded.hypothesis,
        notes = excluded.notes,
        tags_json = excluded.tags_json"""
    _write(
        statement,
        (
            experiment_id,
            principal_id,
            name,
            hypothesis,
            notes,
            tags_json,
            created_at,
        ),
        request_id=request_id,
        detail="EXPERIMENT_WRITE_FAILED",
    )


def upsert_research_run_row(
    *,
    run_id: str,
    experiment_id: str,
    principal_id: str,
    batch_id: str,
    status: str,
    hypothesis: str,
    symbol: str,
    timeframe: str,
    preset: str,
    selected_stages_json: str,
    reason: str,
    force_rerun: bool,
    request_json: str,
    report_json: str,
    dataset_json: str,
    configuration_json: str,
    artifacts_json: str,
    error_json: str,
    created_at: str,
    started_at: str,
    completed_at: str,
    request_id: str,
) -> None:
    """Insert or advance one run ledger row through Data.

    Args:
        run_id: Stable run identity.
        experiment_id: Owning experiment identity.
        principal_id: Owning authenticated principal.
        batch_id: Owning batch identity, empty when absent.
        status: Current lifecycle status.
        hypothesis: Explicit hypothesis recorded on the run.
        symbol: Instrument the run analyzed.
        timeframe: Canonical timeframe key.
        preset: Server-owned preset identifier.
        selected_stages_json: Serialized stage selection.
        reason: Operator-supplied run reason, empty when absent.
        force_rerun: Whether the caller forced a fresh run.
        request_json: Serialized safe-request evidence.
        report_json: Serialized projected report, empty when absent.
        dataset_json: Serialized dataset evidence, empty when absent.
        configuration_json: Serialized effective configuration.
        artifacts_json: Serialized artifact references.
        error_json: Serialized terminal failure evidence.
        created_at: ISO-8601 queue instant.
        started_at: ISO-8601 start instant, empty when not started.
        completed_at: ISO-8601 terminal instant, empty when in flight.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If migration or the write cannot be confirmed.
    """
    logger.info("Persisting Research run row")
    _confirm_run_migration(request_id)
    statement = """INSERT INTO research_runs (
        run_id, experiment_id, principal_id, batch_id, status, hypothesis,
        symbol, timeframe, preset, selected_stages_json, reason, force_rerun,
        request_json, report_json, dataset_json, configuration_json,
        artifacts_json, error_json, created_at, started_at, completed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(run_id) DO UPDATE SET
        status = excluded.status,
        report_json = excluded.report_json,
        dataset_json = excluded.dataset_json,
        configuration_json = excluded.configuration_json,
        artifacts_json = excluded.artifacts_json,
        error_json = excluded.error_json,
        started_at = excluded.started_at,
        completed_at = excluded.completed_at"""
    _write(
        statement,
        (
            run_id,
            experiment_id,
            principal_id,
            batch_id,
            status,
            hypothesis,
            symbol,
            timeframe,
            preset,
            selected_stages_json,
            reason,
            int(force_rerun),
            request_json,
            report_json,
            dataset_json,
            configuration_json,
            artifacts_json,
            error_json,
            created_at,
            started_at,
            completed_at,
        ),
        request_id=request_id,
        detail="RUN_WRITE_FAILED",
    )


def create_research_run_batch_row(
    *,
    batch_id: str,
    experiment_id: str,
    principal_id: str,
    symbols_json: str,
    trigger: str,
    reason: str,
    request_json: str,
    rejections_json: str,
    created_at: str,
    request_id: str,
) -> None:
    """Insert or update one automation batch ledger row through Data.

    Args:
        batch_id: Stable batch identity.
        experiment_id: Owning experiment identity.
        principal_id: Owning authenticated principal.
        symbols_json: Serialized symbol universe.
        trigger: Batch trigger kind.
        reason: Operator-supplied reason, empty when absent.
        request_json: Serialized request evidence.
        rejections_json: Serialized rejection list.
        created_at: ISO-8601 creation instant.
        request_id: Request trace identifier.

    Raises:
        ValidationError: If migration or the write cannot be confirmed.
    """
    logger.info("Persisting Research batch row")
    _confirm_run_migration(request_id)
    statement = """INSERT INTO research_run_batches (
        batch_id, experiment_id, principal_id, symbols_json, trigger, reason,
        request_json, rejections_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(batch_id) DO UPDATE SET
        rejections_json = excluded.rejections_json"""
    _write(
        statement,
        (
            batch_id,
            experiment_id,
            principal_id,
            symbols_json,
            trigger,
            reason,
            request_json,
            rejections_json,
            created_at,
        ),
        request_id=request_id,
        detail="BATCH_WRITE_FAILED",
    )


def _confirm_run_migration(request_id: str) -> None:
    """Ensure the run-ledger migration is applied before any write.

    Args:
        request_id: Request trace identifier.

    Raises:
        ValidationError: If migration cannot be confirmed.
    """
    migration = run_domain_migrations(
        cast("Any", build_research_migration_request(request_id))
    )
    if migration.status != "success" or migration.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", "MIGRATION_FAILED")


def _write(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
    detail: str,
) -> None:
    """Execute one bounded ledger write through Data.

    Args:
        statement: Parameterized SQL write statement.
        parameters: Bound statement parameters.
        request_id: Request trace identifier.
        detail: Symbolic failure detail.

    Raises:
        ValidationError: If Data rejects the write.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(cast("tuple[Any, ...]", parameters),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValidationError("RES_PERSISTENCE_FAILED", detail)
