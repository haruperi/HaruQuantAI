"""Function-only effective-dated calculation API."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from app.services.simulator.calculations.conformance import load, model_identity, run
from app.services.simulator.calculations.contracts import CalculationSpecification
from app.services.simulator.calculations.fx import convert
from app.services.simulator.calculations.margin import planned, total
from app.services.simulator.calculations.profit import calculate


def _specification(
    value: Mapping[str, object], as_of: datetime
) -> CalculationSpecification:
    """Select the unique revision covering an instant.

    Args:
        value: Data-provided revision or complete revision-set mapping.
        as_of: Aware-UTC selection instant.

    Returns:
        Validated effective specification.

    Raises:
        TypeError: If revision evidence is structurally invalid.
        ValueError: If coverage is absent, ambiguous, or unsupported.
    """
    candidates = value.get("revisions")
    revisions = tuple(candidates) if isinstance(candidates, (tuple, list)) else (value,)
    selected: list[Mapping[str, object]] = []
    for revision in revisions:
        if not isinstance(revision, Mapping):
            raise TypeError("provider revision must be a mapping")
        start = datetime.fromisoformat(str(revision["effective_from"]))
        end_value = revision.get("effective_to")
        end = datetime.fromisoformat(str(end_value)) if end_value is not None else None
        if start <= as_of and (end is None or as_of < end):
            selected.append(revision)
    if value.get("complete_coverage") is not True or len(selected) != 1:
        raise ValueError("provider specification coverage is not uniquely proven")
    revision = selected[0]
    payload = revision.get("payload")
    if not isinstance(payload, Mapping):
        raise TypeError("provider revision payload is missing")
    fields = dict(payload)
    fields.update(
        revision_id=revision["revision_id"],
        checksum=revision.get("snapshot_checksum", revision.get("checksum")),
        effective_from=datetime.fromisoformat(str(revision["effective_from"])),
        effective_to=(
            datetime.fromisoformat(str(revision["effective_to"]))
            if revision.get("effective_to") is not None
            else None
        ),
    )
    return CalculationSpecification(**fields)


def calculate_fx_profit(revision: Mapping[str, object], **fields: object) -> Decimal:
    """Calculate effective-dated FX profit.

    Args:
        revision: Data-provided effective revision evidence.
        **fields: Profit inputs including ``as_of``.

    Returns:
        Exact rounded account-currency profit.

    Raises:
        TypeError: If ``as_of`` is not a datetime.
    """
    as_of = fields.get("as_of")
    if not isinstance(as_of, datetime):
        raise TypeError("as_of must be datetime")
    return calculate(_specification(revision, as_of), **fields)  # type: ignore[arg-type]


def calculate_total_margin(revision: Mapping[str, object], **fields: object) -> Decimal:
    """Calculate effective-dated total margin.

    Args:
        revision: Data-provided effective revision evidence.
        **fields: Margin inputs including ``as_of``.

    Returns:
        Exact rounded total margin.

    Raises:
        TypeError: If ``as_of`` is not a datetime.
    """
    as_of = fields.get("as_of")
    if not isinstance(as_of, datetime):
        raise TypeError("as_of must be datetime")
    return total(_specification(revision, as_of), **fields)  # type: ignore[arg-type]


def calculate_planned_margin(
    revision: Mapping[str, object], **fields: object
) -> Decimal:
    """Calculate effective-dated incremental planned margin.

    Args:
        revision: Data-provided effective revision evidence.
        **fields: Margin inputs including ``as_of``.

    Returns:
        Exact non-negative planned margin.

    Raises:
        TypeError: If ``as_of`` is not a datetime.
    """
    as_of = fields.get("as_of")
    if not isinstance(as_of, datetime):
        raise TypeError("as_of must be datetime")
    return planned(_specification(revision, as_of), **fields)


def convert_account_currency(**fields: object) -> Decimal:
    """Convert one exact amount using supplied Data evidence.

    Args:
        **fields: Arguments accepted by the conversion engine.

    Returns:
        Rounded account-currency amount.
    """
    return convert(**fields)  # type: ignore[arg-type]


def load_calculation_conformance_artifact(value: Mapping[str, object]) -> object:
    """Load one checksummed offline artifact.

    Args:
        value: JSON-safe artifact mapping.

    Returns:
        Opaque validated artifact.
    """
    return load(value)


def run_offline_calculation_conformance(artifact: object) -> Mapping[str, object]:
    """Run exact offline differential checks.

    Args:
        artifact: Opaque value from the artifact loader.

    Returns:
        Exact mismatch verdict.

    Raises:
        TypeError: If artifact has the wrong internal type.
    """
    from app.services.simulator.calculations.contracts import CalculationArtifact

    if not isinstance(artifact, CalculationArtifact):
        raise TypeError("artifact must be a calculation conformance artifact")
    return run(artifact)


def get_supported_calculation_modes() -> tuple[str, ...]:
    """Return the exact admitted provider calculation modes.

    Returns:
        Ordered mode tuple.
    """
    return ("FOREX",)


def get_calculation_model_identity() -> Mapping[str, str]:
    """Return stable calculation model identity.

    Returns:
        Model identifier and checksum.
    """
    return model_identity()


__all__ = [
    "calculate_fx_profit",
    "calculate_planned_margin",
    "calculate_total_margin",
    "convert_account_currency",
    "get_calculation_model_identity",
    "get_supported_calculation_modes",
    "load_calculation_conformance_artifact",
    "run_offline_calculation_conformance",
]
