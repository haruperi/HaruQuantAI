"""Deterministic non-mutating authority-to-projection comparison."""

from collections.abc import Mapping
from hashlib import sha256
from types import MappingProxyType
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts.models import JsonValue
from app.services.trading.reconciliation.snapshots import AuthoritySnapshot
from app.services.trading.state import TradingProjection
from app.utils import canonical_json, logger, to_json_safe

type DiscrepancyClass = Literal[
    "missing_internal",
    "missing_authority",
    "mismatched",
    "stale_authority",
]


class ReconciliationReport(BaseModel):
    """Immutable deterministic discrepancy report that never claims resolution.

    Attributes:
        discrepancy_classes: Ordered finite discrepancy categories.
        severity: Highest factual reconciliation severity.
        evidence_refs: Exact authority and projection evidence references.
        unresolved: Whether any discrepancy remains unresolved.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.reconciliation_report.v1"] = (
        "trading.reconciliation_report.v1"
    )
    report_id: str
    discrepancy_classes: tuple[DiscrepancyClass, ...]
    missing_internal_ids: tuple[str, ...]
    missing_authority_ids: tuple[str, ...]
    mismatched_ids: tuple[str, ...]
    stale_authority: bool
    severity: Literal["none", "warning", "critical"]
    evidence_refs: Mapping[str, JsonValue]
    unresolved: bool

    @field_validator("report_id")
    @classmethod
    def _validate_report_id(cls, value: str) -> str:
        """Validate deterministic report identity text.

        Args:
            value: Candidate report identifier.

        Returns:
            Validated report identifier.

        Raises:
            ValueError: If identity is blank or untrimmed.
        """
        logger.debug("Validating ReconciliationReport identity")
        if not value or value != value.strip():
            raise ValueError("report_id must be non-empty and trimmed")
        return value

    @field_validator(
        "discrepancy_classes",
        "missing_internal_ids",
        "missing_authority_ids",
        "mismatched_ids",
    )
    @classmethod
    def _validate_ordered_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate ordered unique discrepancy evidence.

        Args:
            value: Candidate discrepancy values.

        Returns:
            Validated discrepancy values.

        Raises:
            ValueError: If values are blank, duplicated, or unsorted.
        """
        logger.debug("Validating ReconciliationReport discrepancy values")
        if any(not item or item != item.strip() for item in value):
            raise ValueError("discrepancy values must be non-empty and trimmed")
        if len(set(value)) != len(value) or value != tuple(sorted(value)):
            raise ValueError("discrepancy values must be unique and sorted")
        return value

    @field_validator("evidence_refs", mode="before")
    @classmethod
    def _validate_evidence(
        cls,
        value: Mapping[str, object],
    ) -> Mapping[str, JsonValue]:
        """Validate immutable JSON-safe evidence references.

        Args:
            value: Candidate evidence references.

        Returns:
            Immutable JSON-safe evidence references.

        Raises:
            TypeError: If references are not a JSON-safe mapping.
        """
        logger.debug("Validating ReconciliationReport evidence references")
        safe = to_json_safe(value)
        if not isinstance(safe, dict) or not safe:
            raise TypeError("reconciliation evidence must be a non-empty mapping")
        return MappingProxyType(safe)

    @model_validator(mode="after")
    def _validate_status(self) -> Self:
        """Prevent false resolved or severity claims.

        Returns:
            Validated report.

        Raises:
            ValueError: If status conflicts with discrepancy evidence.
        """
        logger.debug("Validating ReconciliationReport unresolved status")
        has_discrepancy = bool(self.discrepancy_classes)
        if self.unresolved != has_discrepancy:
            raise ValueError("unresolved status must match discrepancy evidence")
        expected_severity = (
            "critical"
            if self.missing_internal_ids or self.mismatched_ids
            else "warning"
            if has_discrepancy
            else "none"
        )
        if self.severity != expected_severity:
            raise ValueError("severity conflicts with discrepancy evidence")
        return self


def _scoped_facts(
    orders: Mapping[str, JsonValue],
    positions: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Prefix authority identifiers to preserve record class.

    Args:
        orders: Order facts keyed by authority identifier.
        positions: Position facts keyed by authority identifier.

    Returns:
        Combined class-preserving fact mapping.
    """
    logger.debug("Scoping reconciliation order and position facts")
    return {
        **{f"order:{key}": value for key, value in orders.items()},
        **{f"position:{key}": value for key, value in positions.items()},
    }


def compare_authority_state(
    authority: AuthoritySnapshot,
    internal: TradingProjection,
) -> ReconciliationReport:
    """Compare authority truth with one exact Trading projection.

    Args:
        authority: Normalized route-authority evidence.
        internal: Trading-owned projection for the same scope.

    Returns:
        Deterministic non-mutating reconciliation report.

    Raises:
        ValueError: If authority and projection scopes are incompatible.
    """
    logger.info(
        "Comparing Trading projection version %s with authority", internal.version
    )
    if (
        authority.route != internal.route
        or authority.authority_id != internal.authority_id
        or authority.account_id != internal.tenant_id
    ):
        raise ValueError("authority and Trading projection scopes differ")
    authority_facts = _scoped_facts(authority.orders, authority.positions)
    internal_facts = _scoped_facts(internal.orders, internal.positions)
    authority_ids = set(authority_facts)
    internal_ids = set(internal_facts)
    missing_internal = tuple(sorted(authority_ids - internal_ids))
    missing_authority = tuple(sorted(internal_ids - authority_ids))
    mismatched = tuple(
        sorted(
            identity
            for identity in authority_ids & internal_ids
            if canonical_json(authority_facts[identity])
            != canonical_json(internal_facts[identity])
        )
    )
    stale_authority = authority.observed_at < internal.updated_at
    classes = tuple(
        sorted(
            category
            for category, present in (
                ("missing_internal", bool(missing_internal)),
                ("missing_authority", bool(missing_authority)),
                ("mismatched", bool(mismatched)),
                ("stale_authority", stale_authority),
            )
            if present
        )
    )
    severity: Literal["none", "warning", "critical"] = (
        "critical"
        if missing_internal or mismatched
        else "warning"
        if classes
        else "none"
    )
    evidence: dict[str, JsonValue] = {
        "authority_source_id": authority.source_id,
        "authority_observed_at": authority.observed_at.isoformat(),
        "authority_expires_at": authority.expires_at.isoformat(),
        "projection_version": internal.version,
        "projection_updated_at": internal.updated_at.isoformat(),
    }
    digest = sha256(
        canonical_json({"classes": classes, **evidence}).encode()
    ).hexdigest()
    return ReconciliationReport(
        report_id=f"trd-reconciliation-{digest}",
        discrepancy_classes=classes,  # type: ignore[arg-type]
        missing_internal_ids=missing_internal,
        missing_authority_ids=missing_authority,
        mismatched_ids=mismatched,
        stale_authority=stale_authority,
        severity=severity,
        evidence_refs=evidence,
        unresolved=bool(classes),
    )


__all__ = ["ReconciliationReport", "compare_authority_state"]
