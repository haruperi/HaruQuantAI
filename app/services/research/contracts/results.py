"""Immutable result contracts for the Research domain."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Literal

import pandas as pd

from app.utils import SecurityError, ValidationError, logger

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_WARNING_SEVERITIES = frozenset({"info", "warning", "error"})
_MAX_WARNING_LENGTH = 500
_MAX_WARNING_DETAILS = 32
_MAX_SCORE = 100.0


def _invalid(detail: str) -> None:
    """Raise a redacted Research result-validation failure.

    Args:
        detail: Uppercase symbolic failure detail.

    Raises:
        ValidationError: Always.
    """
    logger.error("Rejecting Research result: %s", detail)
    raise ValidationError("RES_INPUT_INVALID", detail)


def _text(value: str, detail: str) -> str:
    """Validate one non-empty trimmed result string.

    Args:
        value: Candidate string.
        detail: Symbolic error detail.

    Returns:
        The validated string.
    """
    logger.debug("Validating Research result text")
    if not value or value != value.strip():
        _invalid(detail)
    return value


def _hash(value: str, detail: str) -> str:
    """Validate a lowercase SHA-256 string.

    Args:
        value: Candidate digest.
        detail: Symbolic error detail.

    Returns:
        The validated digest.
    """
    logger.debug("Validating Research result hash")
    if _SHA256.fullmatch(value) is None:
        _invalid(detail)
    return value


def _freeze(value: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
    """Freeze one result mapping against mutation.

    Args:
        value: Mapping to copy.

    Returns:
        Immutable shallow mapping.
    """
    logger.debug("Freezing Research result mapping")
    return MappingProxyType(dict(value))


def _schema(value: str) -> None:
    """Validate an internal result schema version.

    Args:
        value: Candidate schema version.

    Raises:
        ValidationError: If the version is not v1.
    """
    logger.debug("Validating Research result schema version")
    if value != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "SCHEMA_VERSION_NOT_V1")


def _is_true(value: object) -> bool:
    """Check a runtime literal-true contract value.

    Args:
        value: Candidate runtime value.

    Returns:
        Whether the value is exactly true.
    """
    logger.debug("Validating Research advisory-only literal")
    return value is True


@dataclass(frozen=True, slots=True)
class ResearchWarning:
    """Bounded structured Research caveat."""

    code: str
    message: str
    severity: str
    field_path: str | None = None
    details: Mapping[str, JSONValue] | None = None

    def __post_init__(self) -> None:
        """Validate and freeze warning evidence.

        Raises:
            ValidationError: If warning vocabulary or bounds are invalid.
        """
        logger.debug("Validating Research warning")
        _text(self.code, "INVALID_WARNING_CODE")
        _text(self.message, "INVALID_WARNING_MESSAGE")
        if (
            len(self.message) > _MAX_WARNING_LENGTH
            or self.severity not in _WARNING_SEVERITIES
        ):
            _invalid("INVALID_WARNING")
        if self.field_path is not None:
            _text(self.field_path, "INVALID_WARNING_PATH")
        if self.details is not None:
            if len(self.details) > _MAX_WARNING_DETAILS:
                _invalid("WARNING_DETAILS_TOO_LARGE")
            object.__setattr__(self, "details", _freeze(self.details))


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Fatal issues, warnings, checks, and explicit cleaning actions."""

    fatal_issues: tuple[Mapping[str, JSONValue], ...]
    warnings: tuple[ResearchWarning, ...]
    checks: tuple[str, ...]
    cleaning_actions: tuple[Mapping[str, JSONValue], ...]

    def __post_init__(self) -> None:
        """Validate quality evidence and freeze its mappings.

        Raises:
            ValidationError: If evidence is malformed.
        """
        logger.debug("Validating Research data-quality report")
        if any("code" not in issue for issue in self.fatal_issues):
            _invalid("FATAL_ISSUE_CODE_MISSING")
        if any(not check for check in self.checks):
            _invalid("INVALID_QUALITY_CHECK")
        object.__setattr__(
            self, "fatal_issues", tuple(_freeze(item) for item in self.fatal_issues)
        )
        object.__setattr__(
            self,
            "cleaning_actions",
            tuple(_freeze(item) for item in self.cleaning_actions),
        )


@dataclass(frozen=True, slots=True)
class PreparedDataset:
    """Detached prepared frame with quality and reproducibility evidence."""

    data: pd.DataFrame
    schema_version: str
    quality: DataQualityReport
    dataset_hash: str
    configuration_hash: str
    source_references: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and detach the prepared frame.

        Raises:
            ValidationError: If schema, frame, hashes, or provenance are invalid.
        """
        logger.debug("Validating prepared Research dataset")
        _schema(self.schema_version)
        if not isinstance(self.data, pd.DataFrame) or self.data.empty:
            _invalid("INVALID_PREPARED_FRAME")
        _hash(self.dataset_hash, "INVALID_DATASET_HASH")
        _hash(self.configuration_hash, "INVALID_CONFIGURATION_HASH")
        if not self.source_references or any(
            not item for item in self.source_references
        ):
            _invalid("INVALID_SOURCE_REFERENCES")
        object.__setattr__(self, "data", self.data.copy(deep=True))


@dataclass(frozen=True, slots=True)
class LeakageReport:
    """Evidence-based suspected lookahead report."""

    suspected_columns: tuple[str, ...]
    severity: str
    evidence: Mapping[str, JSONValue]
    recommendation: str
    allowed_forward_columns: tuple[str, ...]
    target_column: str | None
    source_references: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and freeze leakage evidence.

        Raises:
            ValidationError: If severity or evidence is invalid.
        """
        logger.debug("Validating Research leakage report")
        if self.severity not in {"none", "low", "medium", "high"}:
            _invalid("INVALID_LEAKAGE_SEVERITY")
        if self.suspected_columns and not self.evidence:
            _invalid("LEAKAGE_EVIDENCE_MISSING")
        _text(self.recommendation, "INVALID_LEAKAGE_RECOMMENDATION")
        object.__setattr__(self, "evidence", _freeze(self.evidence))


@dataclass(frozen=True, slots=True)
class TimeSplitResult:
    """Chronological train, validation, and test partitions."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    boundaries: Mapping[str, datetime]
    split_hash: str

    def __post_init__(self) -> None:
        """Validate non-overlapping chronological partitions.

        Raises:
            ValidationError: If partitions or boundaries overlap.
        """
        logger.debug("Validating Research time split")
        if self.train.empty or self.validation.empty or self.test.empty:
            _invalid("EMPTY_TIME_PARTITION")
        indexes = (self.train.index, self.validation.index, self.test.index)
        if any(not isinstance(index, pd.DatetimeIndex) for index in indexes):
            _invalid("TIME_INDEX_REQUIRED")
        if not (
            self.train.index.max() < self.validation.index.min() < self.test.index.min()
        ):
            _invalid("OVERLAPPING_TIME_PARTITIONS")
        if any(
            value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
            for value in self.boundaries.values()
        ):
            _invalid("NON_UTC_BOUNDARY")
        _hash(self.split_hash, "INVALID_SPLIT_HASH")
        object.__setattr__(self, "boundaries", MappingProxyType(dict(self.boundaries)))
        object.__setattr__(self, "train", self.train.copy(deep=True))
        object.__setattr__(self, "validation", self.validation.copy(deep=True))
        object.__setattr__(self, "test", self.test.copy(deep=True))


@dataclass(frozen=True, slots=True)
class CoreMetricProfile:
    """Seven-family metric evidence with reproducibility metadata."""

    schema_version: str
    metrics: Mapping[str, JSONValue]
    quality: DataQualityReport
    dataset_hash: str
    configuration_hash: str
    warnings: tuple[ResearchWarning, ...]

    def __post_init__(self) -> None:
        """Validate metric families, units, sample sizes, and hashes.

        Raises:
            ValidationError: If metric evidence is incomplete.
        """
        logger.debug("Validating Research core metric profile")
        _schema(self.schema_version)
        expected = {
            "returns",
            "roc",
            "candles",
            "ranges",
            "volatility",
            "spread",
            "activity",
        }
        if set(self.metrics) != expected:
            _invalid("INVALID_METRIC_FAMILIES")
        if any(
            not isinstance(value, Mapping)
            or "unit" not in value
            or "sample_size" not in value
            for value in self.metrics.values()
        ):
            _invalid("METRIC_METADATA_MISSING")
        _hash(self.dataset_hash, "INVALID_DATASET_HASH")
        _hash(self.configuration_hash, "INVALID_CONFIGURATION_HASH")
        object.__setattr__(self, "metrics", _freeze(self.metrics))


@dataclass(frozen=True, slots=True)
class EdgeResult:
    """Advisory result for one deterministic edge study."""

    schema_version: str
    study: str
    statistics: Mapping[str, JSONValue]
    null_evidence: Mapping[str, JSONValue]
    classification: str
    seed: int
    warnings: tuple[ResearchWarning, ...]
    advisory_only: Literal[True]

    def __post_init__(self) -> None:
        """Validate edge evidence and advisory status.

        Raises:
            ValidationError: If the result is contradictory or malformed.
        """
        logger.debug("Validating Research edge result")
        _schema(self.schema_version)
        _text(self.study, "INVALID_STUDY_NAME")
        if self.classification not in {"confirmed", "contradicted", "inconclusive"}:
            _invalid("INVALID_EDGE_CLASSIFICATION")
        if self.seed < 0 or not _is_true(self.advisory_only):
            _invalid("INVALID_EDGE_METADATA")
        object.__setattr__(self, "statistics", _freeze(self.statistics))
        object.__setattr__(self, "null_evidence", _freeze(self.null_evidence))


@dataclass(frozen=True, slots=True)
class MarketStructureProfile:
    """Canonical market-structure profile and advisory fit."""

    schema_version: str
    structure: Mapping[str, JSONValue]
    score: float
    verdict: str
    strategy_fit: Mapping[str, JSONValue]
    warnings: tuple[ResearchWarning, ...]

    def __post_init__(self) -> None:
        """Validate canonical score and profile evidence.

        Raises:
            ValidationError: If score or verdict is invalid.
        """
        logger.debug("Validating Research market-structure profile")
        _schema(self.schema_version)
        if not 0.0 <= self.score <= _MAX_SCORE or self.verdict not in {
            "trending",
            "ranging",
            "mixed",
        }:
            _invalid("INVALID_STRUCTURE_SCORE")
        object.__setattr__(self, "structure", _freeze(self.structure))
        object.__setattr__(self, "strategy_fit", _freeze(self.strategy_fit))


@dataclass(frozen=True, slots=True)
class MarketStructureQualityReport:
    """Bounded market-structure stability, validation, and calibration evidence."""

    schema_version: str
    stability: Mapping[str, JSONValue]
    robustness: Mapping[str, JSONValue]
    calibration: Mapping[str, JSONValue]
    duration_ms: float
    warnings: tuple[ResearchWarning, ...]

    def __post_init__(self) -> None:
        """Validate market-structure quality evidence.

        Raises:
            ValidationError: If duration or evidence is invalid.
        """
        logger.debug("Validating Research market-structure quality report")
        _schema(self.schema_version)
        if self.duration_ms < 0:
            _invalid("INVALID_DURATION")
        for name in ("stability", "robustness", "calibration"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class UnsupervisedResearchResult:
    """Seeded PCA, clustering, and descriptive insight evidence."""

    schema_version: str
    preprocessing: Mapping[str, JSONValue]
    pca: Mapping[str, JSONValue]
    clusters: Mapping[str, JSONValue]
    insights: Mapping[str, JSONValue]
    seed: int
    warnings: tuple[ResearchWarning, ...]
    advisory_only: Literal[True]

    def __post_init__(self) -> None:
        """Validate modeling metadata and advisory status.

        Raises:
            ValidationError: If metadata is invalid.
        """
        logger.debug("Validating Research unsupervised result")
        _schema(self.schema_version)
        if self.seed < 0 or not _is_true(self.advisory_only):
            _invalid("INVALID_MODEL_METADATA")
        for name in ("preprocessing", "pca", "clusters", "insights"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class ResearchScorecard:
    """Advisory evidence-readiness scorecard."""

    schema_version: str
    score_rows: tuple[Mapping[str, JSONValue], ...]
    final_score: float
    readiness: str
    reasons: tuple[str, ...]
    warnings: tuple[ResearchWarning, ...]
    advisory_only: Literal[True]

    def __post_init__(self) -> None:
        """Validate score rows and readiness semantics.

        Raises:
            ValidationError: If score or readiness is invalid.
        """
        logger.debug("Validating Research scorecard")
        _schema(self.schema_version)
        if not 0.0 <= self.final_score <= _MAX_SCORE:
            _invalid("INVALID_FINAL_SCORE")
        if self.readiness not in {"BLOCKED", "REVIEW_READY", "INSUFFICIENT_EVIDENCE"}:
            _invalid("INVALID_READINESS")
        if not self.reasons or not _is_true(self.advisory_only):
            _invalid("READINESS_REASONS_REQUIRED")
        object.__setattr__(
            self, "score_rows", tuple(_freeze(row) for row in self.score_rows)
        )


@dataclass(frozen=True, slots=True)
class ResearchProfileSnapshot:
    """Versioned normalized snapshot of approved Research stages."""

    schema_version: str
    stages: Mapping[str, JSONValue]
    scorecard: ResearchScorecard
    dataset_hash: str
    configuration_hash: str
    generated_at: datetime
    warnings: tuple[ResearchWarning, ...]
    advisory_only: Literal[True]

    def __post_init__(self) -> None:
        """Validate snapshot versions, hashes, and UTC metadata.

        Raises:
            ValidationError: If required stage metadata is missing.
        """
        logger.debug("Validating Research profile snapshot")
        _schema(self.schema_version)
        if not self.stages or any(
            not isinstance(value, Mapping) or "schema_version" not in value
            for value in self.stages.values()
        ):
            _invalid("UNVERSIONED_SNAPSHOT_STAGE")
        _hash(self.dataset_hash, "INVALID_DATASET_HASH")
        _hash(self.configuration_hash, "INVALID_CONFIGURATION_HASH")
        if (
            self.generated_at.tzinfo is None
            or self.generated_at.utcoffset() != UTC.utcoffset(self.generated_at)
        ):
            _invalid("SNAPSHOT_TIME_NOT_UTC")
        if not _is_true(self.advisory_only):
            _invalid("SNAPSHOT_NOT_ADVISORY")
        object.__setattr__(self, "stages", _freeze(self.stages))


@dataclass(frozen=True, slots=True)
class ResearchReport:
    """Registered immutable advisory Research report contract version 1."""

    contract_version: Literal["v1"]
    schema_id: Literal["research.report.v1"]
    report_id: str
    hypothesis: str
    evidence: Mapping[str, JSONValue]
    seeds: Mapping[str, int]
    configuration_hash: str
    dataset_hash: str
    source_references: tuple[str, ...]
    warnings: tuple[ResearchWarning, ...]
    generated_at: datetime
    dependency_versions: Mapping[str, str]
    duration_ms: float
    advisory_only: Literal[True]

    def __post_init__(self) -> None:
        """Validate the registered contract and leakage publication gate.

        Raises:
            SecurityError: If evidence contains a high-severity leakage report.
            ValidationError: If contract metadata is malformed.
        """
        logger.debug("Validating ResearchReport v1")
        if self.contract_version != "v1" or self.schema_id != "research.report.v1":
            raise ValidationError("RES_VERSION_INCOMPATIBLE", "REPORT_VERSION_NOT_V1")
        _text(self.report_id, "INVALID_REPORT_ID")
        _text(self.hypothesis, "INVALID_HYPOTHESIS")
        _hash(self.configuration_hash, "INVALID_CONFIGURATION_HASH")
        _hash(self.dataset_hash, "INVALID_DATASET_HASH")
        if (
            self.generated_at.tzinfo is None
            or self.generated_at.utcoffset() != UTC.utcoffset(self.generated_at)
        ):
            _invalid("REPORT_TIME_NOT_UTC")
        if self.duration_ms < 0 or not _is_true(self.advisory_only):
            _invalid("INVALID_REPORT_METADATA")
        leakage = self.evidence.get("leakage")
        if isinstance(leakage, Mapping) and leakage.get("severity") == "high":
            raise SecurityError("RES_LEAKAGE_DETECTED", "PUBLICATION_BLOCKED")
        object.__setattr__(self, "evidence", _freeze(self.evidence))
        object.__setattr__(self, "seeds", MappingProxyType(dict(self.seeds)))
        object.__setattr__(
            self,
            "dependency_versions",
            MappingProxyType(dict(self.dependency_versions)),
        )


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Safe relative reference to one persisted Research artifact."""

    relative_path: Path
    format: str
    size_bytes: int
    sha256: str
    atomic: bool
    schema_version: str
    audit_event_id: str

    def __post_init__(self) -> None:
        """Validate safe artifact reference metadata.

        Raises:
            ValidationError: If the path or metadata is invalid.
        """
        logger.debug("Validating Research artifact reference")
        if self.relative_path.is_absolute() or ".." in self.relative_path.parts:
            _invalid("UNSAFE_ARTIFACT_REFERENCE")
        if self.format not in {"json", "markdown"} or self.size_bytes < 0:
            _invalid("INVALID_ARTIFACT_REFERENCE")
        _hash(self.sha256, "INVALID_ARTIFACT_HASH")
        _schema(self.schema_version)
        _text(self.audit_event_id, "INVALID_AUDIT_EVENT_ID")


__all__ = (
    "ArtifactReference",
    "CoreMetricProfile",
    "DataQualityReport",
    "EdgeResult",
    "LeakageReport",
    "MarketStructureProfile",
    "MarketStructureQualityReport",
    "PreparedDataset",
    "ResearchProfileSnapshot",
    "ResearchReport",
    "ResearchScorecard",
    "ResearchWarning",
    "TimeSplitResult",
    "UnsupervisedResearchResult",
)
