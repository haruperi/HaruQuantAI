"""Deterministic Data-backed fundamental and sentiment evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from datetime import datetime

from app.composition.logging import get_logger
from app.services.data import (
    get_research_source_value_field,
    project_research_source_evidence,
    query_research_sources,
)
from app.services.research.contracts.errors import (
    ValidationError,
)
from app.services.research.intelligence.contracts import (
    FundamentalSourceEvidence,
    IntelligenceApplicability,
    SentimentSourceEvidence,
    evidence_hash,
)

logger = get_logger(__name__)

_POSITIVE = frozenset(
    {"growth", "improve", "increase", "strong", "gain", "expand", "recovery"}
)
_NEGATIVE = frozenset(
    {"decline", "decrease", "weak", "loss", "contract", "risk", "stress"}
)
_ISSUER_ASSET_CLASSES = frozenset({"equity", "corporate_bond", "fund"})
_MACRO_ASSET_CLASSES = frozenset(
    {"forex", "index", "commodity", "sovereign_bond", "equity"}
)


def _records(query: object) -> tuple[object, ...]:
    """Query Data and return opaque eligible source records.

    Args:
        query: Opaque Data research-source query.

    Returns:
        Eligible opaque Data source records.

    Raises:
        ValidationError: If Data returns an invalid page.
    """
    logger.info("Querying eligible Data research-source evidence")
    page = query_research_sources(query)  # type: ignore[arg-type]
    records = get_research_source_value_field(page, "records")
    if not isinstance(records, tuple):
        raise ValidationError("RES_INPUT_INVALID", "SOURCE_PAGE_INVALID")
    return records


def _string_tuple(value: object, *, field: str) -> tuple[str, ...]:
    """Return one validated string tuple from a Data projection.

    Args:
        value: Candidate projection value.
        field: Symbolic projection field.

    Returns:
        Validated tuple.

    Raises:
        ValidationError: If the projection value is malformed.
    """
    if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
        raise ValidationError("RES_INPUT_INVALID", field)
    return value


def _revision(value: object) -> int:
    """Return one validated positive revision.

    Args:
        value: Candidate projection value.

    Returns:
        Positive revision.

    Raises:
        ValidationError: If the revision is malformed.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError("RES_INPUT_INVALID", "SOURCE_REVISION_INVALID")
    return value


def assess_intelligence_applicability(
    asset_class: str,
    *,
    model: str,
) -> IntelligenceApplicability:
    """Return whether the requested evidence model applies to an asset class.

    Args:
        asset_class: Normalized instrument asset class.
        model: Issuer, macro, or sentiment model.

    Returns:
        Typed applicability evidence.

    Raises:
        ValidationError: If the model is unknown.
    """
    logger.info("Assessing Research intelligence applicability")
    normalized = asset_class.strip().lower()
    if model == "issuer":
        applicable = normalized in _ISSUER_ASSET_CLASSES
    elif model == "macro":
        applicable = normalized in _MACRO_ASSET_CLASSES
    elif model == "sentiment":
        applicable = bool(normalized)
    else:
        logger.warning("Rejecting unknown Research intelligence model")
        raise ValidationError("RES_INPUT_INVALID", "INTELLIGENCE_MODEL_UNKNOWN")
    return IntelligenceApplicability(
        status="applicable" if applicable else "not_applicable",
        asset_class=normalized,
        model=model,  # type: ignore[arg-type]
        reasons=() if applicable else ("MODEL_NOT_APPLICABLE_TO_ASSET_CLASS",),
    )


def build_fundamental_source_evidence(
    query: object,
    *,
    asset_class: str,
    model: str,
    required_kinds: tuple[str, ...],
) -> FundamentalSourceEvidence:
    """Build fundamental evidence from eligible Data-owned source records.

    Args:
        query: Opaque Data point-in-time query.
        asset_class: Instrument asset class.
        model: Fundamental applicability model.
        required_kinds: Source kinds required for coverage.

    Returns:
        Bounded fundamental source evidence.

    Raises:
        ValidationError: If the model or source coverage is ineligible.
    """
    logger.info("Building bounded fundamental source evidence")
    applicability = assess_intelligence_applicability(asset_class, model=model)
    if applicability.status != "applicable":
        logger.warning("Rejecting inapplicable fundamental evidence model")
        raise ValidationError("RES_INPUT_INVALID", "FUNDAMENTAL_MODEL_NOT_APPLICABLE")
    projections = tuple(
        project_research_source_evidence(item) for item in _records(query)
    )
    eligible = tuple(
        item
        for item in projections
        if str(item["source_kind"]) in {"filing", "statement", "transcript", "macro"}
    )
    coverage = Counter(str(item["source_kind"]) for item in eligible)
    missing = tuple(kind for kind in required_kinds if coverage[kind] == 0)
    if not eligible or missing:
        logger.warning("Rejecting insufficient fundamental source coverage")
        raise ValidationError("RES_INSUFFICIENT_DATA", "FUNDAMENTAL_COVERAGE_MISSING")
    references = tuple(str(item["document_id"]) for item in eligible)
    observed = min(
        datetime.fromisoformat(str(item["published_at"])) for item in eligible
    )
    available = max(
        datetime.fromisoformat(str(item["available_at"])) for item in eligible
    )
    asset_scope = tuple(
        sorted(
            {
                scope
                for item in eligible
                for scope in _string_tuple(
                    item["asset_scope"],
                    field="SOURCE_ASSET_SCOPE_INVALID",
                )
            }
        )
    )
    issuer_scope = tuple(
        sorted(
            {
                scope
                for item in eligible
                for scope in _string_tuple(
                    item["issuer_scope"],
                    field="SOURCE_ISSUER_SCOPE_INVALID",
                )
            }
        )
    )
    material = {
        "asset_scope": asset_scope,
        "issuer_scope": issuer_scope,
        "references": references,
        "coverage": dict(coverage),
        "available_by": available,
    }
    return FundamentalSourceEvidence(
        contract_version="v1",
        schema_id="research.fundamental_source_evidence.v1",
        asset_scope=asset_scope,
        issuer_scope=issuer_scope,
        document_references=references,
        source_kinds=tuple(sorted(coverage)),
        observed_from=observed,
        available_by=available,
        coverage=dict(coverage),
        revisions={
            str(item["document_id"]): _revision(item["revision"]) for item in eligible
        },
        currency_lineage={
            str(item["document_id"]): (
                None if item["currency"] is None else str(item["currency"])
            )
            for item in eligible
        },
        unit_lineage={
            str(item["document_id"]): None
            if item["unit"] is None
            else str(item["unit"])
            for item in eligible
        },
        quality={
            "trusted_records": len(eligible),
            "missing_required_kinds": missing,
        },
        canonical_hash=evidence_hash(material),
    )


def _polarity(title: str) -> float | None:
    """Return deterministic lexicon polarity or explicit missingness."""
    words = {word.strip(".,:;!?()[]").lower() for word in title.split()}
    positive = len(words & _POSITIVE)
    negative = len(words & _NEGATIVE)
    total = positive + negative
    return None if total == 0 else (positive - negative) / total


def build_sentiment_source_evidence(
    query: object,
    *,
    measurement_version: str,
) -> SentimentSourceEvidence:
    """Build deterministic sentiment evidence from point-in-time records.

    Args:
        query: Opaque Data point-in-time query.
        measurement_version: Closed deterministic measurement version.

    Returns:
        Bounded sentiment source evidence.

    Raises:
        ValidationError: If the version or source coverage is ineligible.
    """
    logger.info("Building deterministic sentiment source evidence")
    if measurement_version != "lexicon-v1":
        logger.warning("Rejecting unsupported sentiment measurement version")
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "SENTIMENT_VERSION_UNKNOWN")
    projections = tuple(
        project_research_source_evidence(item) for item in _records(query)
    )
    eligible = tuple(
        item
        for item in projections
        if str(item["source_kind"]) in {"news", "social", "alternative", "macro"}
    )
    if not eligible:
        logger.warning("Rejecting insufficient sentiment source coverage")
        raise ValidationError("RES_INSUFFICIENT_DATA", "SENTIMENT_COVERAGE_MISSING")
    polarity = {
        str(item["document_id"]): _polarity(str(item["title"])) for item in eligible
    }
    measured = tuple(value for value in polarity.values() if value is not None)
    disagreement = any(value > 0 for value in measured) and any(
        value < 0 for value in measured
    )
    references = tuple(str(item["document_id"]) for item in eligible)
    available = max(
        datetime.fromisoformat(str(item["available_at"])) for item in eligible
    )
    coverage = Counter(str(item["source_id"]) for item in eligible)
    material = {
        "references": references,
        "measurement_version": measurement_version,
        "polarity": polarity,
        "coverage": dict(coverage),
        "available_by": available,
    }
    return SentimentSourceEvidence(
        contract_version="v1",
        schema_id="research.sentiment_source_evidence.v1",
        asset_scope=tuple(
            sorted(
                {
                    scope
                    for item in eligible
                    for scope in _string_tuple(
                        item["asset_scope"],
                        field="SOURCE_ASSET_SCOPE_INVALID",
                    )
                }
            )
        ),
        document_references=references,
        event_references=tuple(
            str(item["external_id"]) for item in eligible if item["external_id"]
        ),
        available_by=available,
        measurement_version=measurement_version,
        polarity=polarity,
        source_coverage=dict(coverage),
        disagreement=disagreement,
        missing_measurements=tuple(
            reference for reference, value in polarity.items() if value is None
        ),
        revisions={
            str(item["document_id"]): _revision(item["revision"]) for item in eligible
        },
        trust_evidence={
            str(item["document_id"]): str(item["trust_status"]) for item in eligible
        },
        manipulation_evidence={
            str(item["document_id"]): str(item["manipulation_status"])
            for item in eligible
        },
        injection_evidence={
            str(item["document_id"]): str(item["injection_status"]) for item in eligible
        },
        canonical_hash=evidence_hash(material),
    )


def project_intelligence_evidence(
    evidence: object,
    *,
    max_references: int = 50,
) -> Mapping[str, object]:
    """Project evidence without source payload or action fields.

    Args:
        evidence: Fundamental or sentiment evidence.
        max_references: Maximum references retained.

    Returns:
        Detached, bounded, advisory-only projection.

    Raises:
        ValidationError: If evidence has an unknown type.
    """
    logger.info("Projecting bounded Research intelligence evidence")
    if isinstance(evidence, FundamentalSourceEvidence):
        references = evidence.document_references
        return {
            "schema_id": evidence.schema_id,
            "asset_scope": evidence.asset_scope,
            "issuer_scope": evidence.issuer_scope,
            "document_references": references[:max_references],
            "coverage": dict(evidence.coverage),
            "quality": dict(evidence.quality),
            "canonical_hash": evidence.canonical_hash,
            "advisory_only": True,
        }
    if isinstance(evidence, SentimentSourceEvidence):
        references = evidence.document_references
        return {
            "schema_id": evidence.schema_id,
            "asset_scope": evidence.asset_scope,
            "document_references": references[:max_references],
            "polarity": dict(evidence.polarity),
            "disagreement": evidence.disagreement,
            "missing_measurements": evidence.missing_measurements,
            "canonical_hash": evidence.canonical_hash,
            "advisory_only": True,
        }
    logger.warning("Rejecting unknown Research intelligence evidence")
    raise ValidationError("RES_INPUT_INVALID", "INTELLIGENCE_EVIDENCE_UNKNOWN")


__all__ = (
    "assess_intelligence_applicability",
    "build_fundamental_source_evidence",
    "build_sentiment_source_evidence",
    "project_intelligence_evidence",
)
