"""Strategy operating-envelope candidate gate (feature).

Extends ``FEAT-OPT-03``/``FEAT-OPT-08``: filter optimization candidates so the search
optimizes only within an approved Strategy operating envelope. The envelope is owned by
Strategy (``feature`` → ``FEAT-STR-12``) and is consumed here only through its
documented public ``evaluate_operating_envelope`` boundary (shallow cross-domain import,
per AGENTS.md §1).

A candidate failing the envelope is **rejected** with a structured reason — never
scored zero and never silently retained. Missing point-in-time evidence returns
``RESTRICTED`` (the Strategy contract's own fail-closed behaviour), which this gate
treats as a rejection rather than an inferred pass (change-control rule 4).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from app.composition.logging import get_logger

logger = get_logger(__name__)

ENVELOPE_REJECTED_REASON = "operating_envelope_restricted"


def evaluate_candidate_envelope(
    candidate: Mapping[str, object],
    *,
    operating_envelope: Mapping[str, object],
    volatility: Decimal | None,
    spread: Decimal | None,
    liquidity: Decimal | None,
    regime: str | None,
    session: str | None,
    active_event_types: tuple[str, ...] | None,
) -> tuple[bool, str | None]:
    """Evaluate one candidate against the approved operating envelope.

    Args:
        candidate: Candidate executable-parameter mapping (carried for context; not
            mutated).
        operating_envelope: Validated ``strategy.operating_envelope.v1`` mapping.
        volatility: Point-in-time realized volatility evidence, or ``None`` if
            unavailable.
        spread: Point-in-time spread evidence, or ``None`` if unavailable.
        liquidity: Point-in-time liquidity evidence, or ``None`` if unavailable.
        regime: Point-in-time market regime, or ``None`` if unavailable.
        session: Point-in-time trading session, or ``None`` if unavailable.
        active_event_types: Point-in-time active economic event types, or ``None``.

    Returns:
        A two-tuple ``(permitted, reason)``. ``permitted`` is ``True`` only when the
        envelope evaluates to ``PERMITTED``. When ``False``, ``reason`` is
        ``operating_envelope_restricted``.
    """
    # Imported lazily to keep the optimization import surface free of cross-domain
    # dependencies at module load (NFR-OPT-007 import safety).
    from app.services.strategy import evaluate_operating_envelope

    candidate_hash = str(candidate.get("candidate_hash", "unknown"))
    logger.debug(
        "Evaluating candidate against operating envelope | candidate=%s",
        candidate_hash,
    )
    outcome = evaluate_operating_envelope(
        operating_envelope,
        volatility=volatility,
        spread=spread,
        liquidity=liquidity,
        regime=regime,
        session=session,
        active_event_types=active_event_types,
    )
    if outcome == "PERMITTED":
        return True, None
    return False, ENVELOPE_REJECTED_REASON


def filter_candidates_by_envelope(
    candidates: Mapping[str, Mapping[str, object]],
    *,
    operating_envelope: Mapping[str, object],
    point_in_time_evidence: Mapping[str, object],
) -> dict[str, dict[str, dict[str, object]]]:
    """Partition candidates into permitted and rejected by the operating envelope.

    Args:
        candidates: Mapping of candidate hash to executable-parameter mapping.
        operating_envelope: Validated ``strategy.operating_envelope.v1`` mapping.
        point_in_time_evidence: Mapping carrying ``volatility``, ``spread``,
            ``liquidity``, ``regime``, ``session``, and ``active_event_types``
            evidence. Any missing field fails closed to rejection.

    Returns:
        A mapping with ``permitted`` and ``rejected`` keys. ``permitted`` maps
        candidate hashes to their executable parameters; ``rejected`` maps candidate
        hashes to a structured rejection record carrying the reason. No candidate is
        silently dropped or re-scored.
    """
    volatility = _optional_decimal(point_in_time_evidence.get("volatility"))
    spread = _optional_decimal(point_in_time_evidence.get("spread"))
    liquidity = _optional_decimal(point_in_time_evidence.get("liquidity"))
    regime = _optional_str(point_in_time_evidence.get("regime"))
    session = _optional_str(point_in_time_evidence.get("session"))
    active = _optional_tuple(point_in_time_evidence.get("active_event_types"))
    permitted: dict[str, dict[str, object]] = {}
    rejected: dict[str, dict[str, object]] = {}
    for candidate_hash, parameters in candidates.items():
        permitted_flag, reason = evaluate_candidate_envelope(
            parameters,
            operating_envelope=operating_envelope,
            volatility=volatility,
            spread=spread,
            liquidity=liquidity,
            regime=regime,
            session=session,
            active_event_types=active,
        )
        if permitted_flag:
            permitted[candidate_hash] = dict(parameters)
        else:
            rejected[candidate_hash] = {
                "reason_code": reason or ENVELOPE_REJECTED_REASON,
                "executable_parameters": dict(parameters),
            }
    logger.info(
        "Operating-envelope gate applied | permitted=%d rejected=%d",
        len(permitted),
        len(rejected),
    )
    return {"permitted": permitted, "rejected": rejected}


def _optional_decimal(value: object) -> Decimal | None:
    """Coerce an optional evidence value to a finite Decimal.

    Args:
        value: Raw evidence value.

    Returns:
        Coerced Decimal, or ``None`` if the value is absent/invalid.
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except ArithmeticError, ValueError:
        return None


def _optional_str(value: object) -> str | None:
    """Coerce an optional evidence value to a non-empty string.

    Args:
        value: Raw evidence value.

    Returns:
        Coerced string, or ``None`` if absent.
    """
    if value is None:
        return None
    text = str(value)
    return text or None


def _optional_tuple(value: object) -> tuple[str, ...] | None:
    """Coerce an optional evidence value to a tuple of strings.

    Args:
        value: Raw evidence value.

    Returns:
        Tuple of strings, or ``None`` if absent.
    """
    if value is None:
        return None
    if isinstance(value, Mapping):
        return None
    if not isinstance(value, (list, tuple)):
        return None
    return tuple(str(item) for item in value)


def get_envelope_gate_contract_version() -> str:
    """Return the operating-envelope gate consumer version.

    Returns:
        The canonical ``v1`` version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "ENVELOPE_REJECTED_REASON",
    "evaluate_candidate_envelope",
    "filter_candidates_by_envelope",
    "get_envelope_gate_contract_version",
)
