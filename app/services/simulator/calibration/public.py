"""Function-only API for governed empirical calibration."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.simulator.calibration import execution, spread
from app.services.simulator.calibration.contracts import (
    _CalibrationArtifact,
    _PartitionBundle,
    freeze_mapping,
)
from app.services.simulator.calibration.partition import partition
from app.services.simulator.calibration.validate import validate

logger = get_logger(__name__)


def _minimum_samples(policy: Mapping[str, object]) -> int:
    """Return a strictly positive integer sample requirement."""
    value = policy.get("minimum_samples")
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("minimum_samples must be a positive integer")
    return value


def partition_calibration_evidence(
    evidence: Sequence[Mapping[str, object]],
    *,
    evaluation_start: datetime,
    source_identity: str,
    retrospective: bool = False,
) -> object:
    """Partition eligible evidence before any fit function can observe it."""
    logger.info("Partitioning point-in-time eligible Simulation calibration evidence")
    return partition(
        evidence,
        evaluation_start=evaluation_start,
        source_identity=source_identity,
        retrospective=retrospective,
    )


def _artifact_material(artifact: _CalibrationArtifact) -> dict[str, object]:
    """Return canonical JSON-safe artifact material excluding its checksum."""
    return {
        "schema_id": artifact.schema_id,
        "artifact_id": artifact.artifact_id,
        "broker": artifact.broker,
        "server": artifact.server,
        "account_digest": artifact.account_digest,
        "environment": artifact.environment,
        "symbol": artifact.symbol,
        "source_identity": artifact.source_identity,
        "source_available_at": artifact.source_available_at.isoformat(),
        "ingested_at": artifact.ingested_at.isoformat(),
        "calibrated_at": artifact.calibrated_at.isoformat(),
        "training_start": artifact.training_start.isoformat(),
        "training_end": artifact.training_end.isoformat(),
        "effective_from": artifact.effective_from.isoformat(),
        "effective_to": artifact.effective_to.isoformat(),
        "retrospective": artifact.retrospective,
        "partition_hashes": dict(artifact.partition_hashes),
        "selection_rule": artifact.selection_rule,
        "component": artifact.component,
        "regime": artifact.regime,
        "sample_count": artifact.sample_count,
        "minimum_samples": artifact.minimum_samples,
        "minimum_coverage": str(artifact.minimum_coverage),
        "observed_coverage": str(artifact.observed_coverage),
        "parameters": dict(artifact.parameters),
        "applicability": dict(artifact.applicability),
        "exclusions": artifact.exclusions,
        "threshold_metric": artifact.threshold_metric,
        "threshold_unit": artifact.threshold_unit,
        "threshold_test": artifact.threshold_test,
        "threshold_tolerance": str(artifact.threshold_tolerance),
        "confidence": str(artifact.confidence),
        "economic_error_budget": str(artifact.economic_error_budget),
        "valid_until": artifact.valid_until.isoformat(),
        "estimator_version": artifact.estimator_version,
    }


def _build_artifact(  # noqa: C901
    bundle: _PartitionBundle,
    *,
    component: str,
    parameters: Mapping[str, str],
    exclusions: tuple[str, ...],
    identity: Mapping[str, object],
    policy: Mapping[str, object],
) -> _CalibrationArtifact:
    """Build and checksum one immutable artifact from predeclared inputs."""
    if not isinstance(bundle, _PartitionBundle):
        raise TypeError("partition must be a calibration partition bundle")
    records = tuple(
        record for record in bundle.calibration.records if record.component == component
    )
    if not records and component != "execution_components":
        raise ValueError("calibration partition omits requested component")
    training_records = (
        bundle.calibration.records if component == "execution_components" else records
    )
    identity_fields = ("broker", "server", "account_digest", "environment", "symbol")
    if any(
        str(getattr(record, name)) != str(identity[name])
        for record in bundle.calibration.records
        for name in identity_fields
    ) or any(
        record.source_checksum != str(identity["source_identity"])
        for record in bundle.calibration.records
    ):
        raise ValueError("artifact identity cannot relabel calibration evidence")
    retrospective = bool(policy.get("retrospective", False))
    if retrospective != bundle.retrospective:
        raise ValueError(
            "artifact retrospective label must match partition eligibility"
        )
    artifact_exclusions = exclusions
    if retrospective:
        artifact_exclusions = (*artifact_exclusions, "retrospective:exploratory_only")
    fields: dict[str, Any] = {
        "schema_id": "simulator.calibration.v1",
        "artifact_id": str(identity["artifact_id"]),
        "broker": str(identity["broker"]),
        "server": str(identity["server"]),
        "account_digest": str(identity["account_digest"]),
        "environment": str(identity["environment"]),
        "symbol": str(identity["symbol"]),
        "source_identity": str(identity["source_identity"]),
        "source_available_at": identity["source_available_at"],
        "ingested_at": identity["ingested_at"],
        "calibrated_at": identity["calibrated_at"],
        "training_start": min(record.economic_at for record in training_records),
        "training_end": max(record.economic_at for record in training_records),
        "effective_from": policy["effective_from"],
        "effective_to": policy["effective_to"],
        "retrospective": retrospective,
        "partition_hashes": freeze_mapping(
            {
                "calibration": bundle.calibration.checksum,
                "validation": bundle.validation.checksum,
                "certification": bundle.certification.checksum,
            }
        ),
        "selection_rule": bundle.selection_rule,
        "component": component,
        "regime": str(policy.get("regime", "scheduled_metadata_only")),
        "sample_count": len(training_records),
        "minimum_samples": _minimum_samples(policy),
        "minimum_coverage": Decimal(str(policy["minimum_coverage"])),
        "observed_coverage": Decimal(str(policy["observed_coverage"])),
        "parameters": freeze_mapping(parameters),
        "applicability": freeze_mapping(
            {
                "environment": str(identity["environment"]),
                "symbol": str(identity["symbol"]),
                "source_identity": str(identity["source_identity"]),
                "canonical_eligible": "false" if retrospective else "true",
            }
        ),
        "exclusions": artifact_exclusions,
        "threshold_metric": str(policy["threshold_metric"]),
        "threshold_unit": str(policy["threshold_unit"]),
        "threshold_test": str(policy["threshold_test"]),
        "threshold_tolerance": Decimal(str(policy["threshold_tolerance"])),
        "confidence": Decimal(str(policy["confidence"])),
        "economic_error_budget": Decimal(str(policy["economic_error_budget"])),
        "valid_until": policy["valid_until"],
        "estimator_version": "stdlib-empirical-v1",
        "checksum": "",
    }
    artifact = _CalibrationArtifact(**fields)
    if artifact.environment not in {"demo", "live"}:
        raise ValueError("calibration environment must be demo or live")
    if artifact.training_end > artifact.source_available_at or (
        not artifact.retrospective and artifact.training_end > artifact.effective_from
    ):
        raise ValueError("training evidence is not prospectively eligible")
    if (
        not artifact.retrospective
        and artifact.source_available_at > artifact.effective_from
    ):
        raise ValueError("source availability is after the prospective effective start")
    if (
        artifact.effective_to <= artifact.effective_from
        or artifact.valid_until > artifact.effective_to
    ):
        raise ValueError("calibration validity interval is invalid")
    if artifact.minimum_samples < 1 or artifact.sample_count < artifact.minimum_samples:
        raise ValueError("calibration minimum sample requirement is not met")
    if any(
        value < 0 or value > 1
        for value in (
            artifact.minimum_coverage,
            artifact.observed_coverage,
            artifact.confidence,
        )
    ):
        raise ValueError("coverage and confidence must be in [0, 1]")
    if artifact.observed_coverage < artifact.minimum_coverage:
        raise ValueError("calibration coverage is insufficient")
    checksum = canonical_digest(_artifact_material(artifact))
    return replace(artifact, checksum=checksum)


def fit_spread_calibration(
    partitions: object, *, identity: Mapping[str, object], policy: Mapping[str, object]
) -> object:
    """Fit a provider-M1 lower-bound spread artifact from calibration bytes only."""
    bundle = cast("_PartitionBundle", partitions)
    parameters = spread.fit(
        bundle.calibration.records, minimum_samples=_minimum_samples(policy)
    )
    return _build_artifact(
        bundle,
        component="spread",
        parameters=parameters,
        exclusions=(),
        identity=identity,
        policy=policy,
    )


def fit_execution_calibration(
    partitions: object,
    *,
    components: tuple[str, ...],
    identity: Mapping[str, object],
    policy: Mapping[str, object],
) -> object:
    """Fit only execution components supported by sufficient trace evidence."""
    bundle = cast("_PartitionBundle", partitions)
    parameters, exclusions = execution.fit(
        bundle.calibration.records,
        components=components,
        minimum_samples=_minimum_samples(policy),
    )
    return _build_artifact(
        bundle,
        component="execution_components",
        parameters=parameters,
        exclusions=exclusions,
        identity=identity,
        policy=policy,
    )


def validate_calibration_artifact(
    artifact: object, partitions: object, *, evaluated_at: datetime
) -> Mapping[str, object]:
    """Validate against validation evidence without exposing certification bytes."""
    if not isinstance(artifact, _CalibrationArtifact) or not isinstance(
        partitions, _PartitionBundle
    ):
        raise TypeError("artifact and partitions have invalid calibration types")
    logger.info("Validating Simulation calibration against locked validation evidence")
    return validate(artifact, partitions.validation, evaluated_at=evaluated_at)


def get_calibration_applicability(artifact: object) -> Mapping[str, object]:
    """Return applicability, exclusions, scope, and validity evidence."""
    if not isinstance(artifact, _CalibrationArtifact):
        raise TypeError("artifact has invalid calibration type")
    return {
        "applicability": dict(artifact.applicability),
        "exclusions": artifact.exclusions,
        "effective_from": artifact.effective_from,
        "effective_to": artifact.effective_to,
        "valid_until": artifact.valid_until,
        "retrospective": artifact.retrospective,
    }


def dump_calibration_artifact(artifact: object) -> dict[str, object]:
    """Serialize a verified artifact into canonical JSON-safe material."""
    if not isinstance(artifact, _CalibrationArtifact):
        raise TypeError("artifact has invalid calibration type")
    material = _artifact_material(artifact)
    if canonical_digest(material) != artifact.checksum:
        raise ValueError("calibration artifact checksum mismatch")
    material["checksum"] = artifact.checksum
    return material


def load_calibration_artifact(value: Mapping[str, object]) -> object:
    """Load and checksum-verify one serialized calibration artifact."""
    fields = dict(value)
    checksum = str(fields.pop("checksum", ""))
    for name in (
        "source_available_at",
        "ingested_at",
        "calibrated_at",
        "training_start",
        "training_end",
        "effective_from",
        "effective_to",
        "valid_until",
    ):
        fields[name] = datetime.fromisoformat(str(fields[name]))
    for name in (
        "minimum_coverage",
        "observed_coverage",
        "threshold_tolerance",
        "confidence",
        "economic_error_budget",
    ):
        fields[name] = Decimal(str(fields[name]))
    fields["partition_hashes"] = freeze_mapping(fields["partition_hashes"])  # type: ignore[arg-type]
    fields["parameters"] = freeze_mapping(fields["parameters"])  # type: ignore[arg-type]
    fields["applicability"] = freeze_mapping(fields["applicability"])  # type: ignore[arg-type]
    exclusions = fields["exclusions"]
    if not isinstance(exclusions, (list, tuple)):
        raise TypeError("calibration exclusions must be a sequence")
    fields["exclusions"] = tuple(str(item) for item in exclusions)
    artifact = _CalibrationArtifact(**fields, checksum=checksum)  # type: ignore[arg-type]
    if canonical_digest(_artifact_material(artifact)) != checksum:
        raise ValueError("calibration artifact checksum mismatch")
    return artifact


__all__ = [
    "dump_calibration_artifact",
    "fit_execution_calibration",
    "fit_spread_calibration",
    "get_calibration_applicability",
    "load_calibration_artifact",
    "partition_calibration_evidence",
    "validate_calibration_artifact",
]
