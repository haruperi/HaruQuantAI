"""Symbol-scoped calendar-state derivation for FEAT-DATA-11.

`derive_calendar_state` is the Data-side bridge used by a caller's
``MarketContextProvider`` composition to populate
``MarketContextEvidence.calendar_state``: it resolves the symbol profile,
picks up the relevant events for the symbol at the supplied instant, and
returns the normalized state plus the two blackout-window provenance fields
that Risk's ``_calendar_result`` requires.

Keeping this in Data (rather than in Risk) preserves the existing boundary:
Data owns every provider/cross-provider identity mapping and the production of
`MarketContextEvidence`; Risk only consumes that evidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.profiling import (
    SymbolEventProfile,
    _get_symbol_event_profile_raw,
)
from app.services.data.economic_calendar.restriction import (
    CALENDAR_STATE_OPEN,
    CALENDAR_STATE_UNKNOWN,
    _evaluate_calendar_state_raw,
)

if TYPE_CHECKING:
    from app.services.data.evidence.market_context_contracts import (
        MarketContextEvidence,
    )

#: Default impact filter for symbol-scoped news restriction, matching the
#: Risk config ``blocked_calendar_states`` baseline (every release-state is
#: blocked by default). Callers may override per-governor profile.
DEFAULT_MINIMUM_IMPACT: EventImpact = EventImpact.HIGH


@dataclass(frozen=True, slots=True)
class CalendarStateResult:
    """Data-derived normalized calendar-state evidence for one symbol.

    Attributes:
        symbol: Queried symbol.
        calendar_state: Normalized state string. One of ``"event"``,
            ``"blackout_before"``, ``"blackout_after"``, ``"open"``, or
            ``"unknown"``.
        blackout_before_minutes: Minutes the requester expects Risk to block
            before the release.
        blackout_after_minutes: Minutes the requester expects Risk to block
            after the release.
        event_count: Number of relevant events considered for this state.
        evidence_ref: Optional opaque reference to the underlying event set
            (e.g. an upstream store query id).
    """

    symbol: str
    calendar_state: str
    blackout_before_minutes: int
    blackout_after_minutes: int
    event_count: int
    evidence_ref: str | None


def _relevant_events(
    events: Sequence[EconomicEvent], profile: SymbolEventProfile
) -> list[EconomicEvent]:
    """Return events whose currency or country intersects the profile.

    Args:
        events: The ``events`` argument.
        profile: The ``profile`` argument.

    Returns:
        The result produced by the operation.
    """
    relevant: list[EconomicEvent] = []
    for event in events:
        if event.currency is not None and event.currency in profile.currencies:
            relevant.append(event)
            continue
        if event.country is not None and event.country in profile.countries:
            relevant.append(event)
            continue
    return relevant


def _derive_calendar_state_raw(
    symbol: str,
    at: datetime,
    *,
    events: Sequence[EconomicEvent] | None,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
    evidence_ref: str | None = None,
) -> CalendarStateResult:
    """Derive one Risk-consumable calendar-state for ``symbol`` at ``at``.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        at: Timezone-aware UTC instant.
        events: Pre-fetched normalized events, or ``None`` when acquisition
            failed or was not attempted. An empty successful result is open.
        before_minutes: Requester blackout minutes before each release.
        after_minutes: Requester blackout minutes after each release.
        minimum_impact: Minimum impact (defaults to HIGH).
        evidence_ref: Optional opaque correlation reference for audit.

    Returns:
        Immutable calendar-state result ready to populate
        ``MarketContextEvidence``.

    Raises:
        DataError: If ``at`` is timezone-naive or ``symbol`` is unknown.
    """
    if at.tzinfo is None:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "at"})
    profile = _get_symbol_event_profile_raw(symbol)
    relevant = [] if events is None else _relevant_events(events, profile)
    if events is None:
        state = CALENDAR_STATE_UNKNOWN
    elif not relevant:
        state = CALENDAR_STATE_OPEN
    else:
        state = _evaluate_calendar_state_raw(
            relevant,
            at,
            before_minutes=before_minutes,
            after_minutes=after_minutes,
            minimum_impact=(
                minimum_impact if minimum_impact is not None else DEFAULT_MINIMUM_IMPACT
            ),
        )
    return CalendarStateResult(
        symbol=symbol,
        calendar_state=state,
        blackout_before_minutes=before_minutes,
        blackout_after_minutes=after_minutes,
        event_count=len(relevant),
        evidence_ref=evidence_ref,
    )


def derive_calendar_state(
    symbol: str,
    at: datetime,
    *,
    events: Sequence[EconomicEvent] | None,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
    evidence_ref: str | None = None,
) -> StandardResponse[CalendarStateResult]:
    """Derive one Risk-consumable calendar-state for ``symbol`` at ``at``.

    Args:
        symbol: Canonical tradable symbol (must have a registered profile).
        at: Timezone-aware UTC instant.
        events: Pre-fetched normalized events, or ``None`` when acquisition
            failed or was not attempted. An empty successful result is open.
            Callers are expected to constrain to the relevant window before
            calling (e.g. +/- one day is sufficient for the default 10-minute
            windows).
        before_minutes: Requester blackout minutes before each release.
        after_minutes: Requester blackout minutes after each release.
        minimum_impact: Minimum impact (defaults to HIGH).
        evidence_ref: Optional opaque correlation reference for audit.

    Returns:
        Standard response carrying the immutable calendar-state result ready
        to populate ``MarketContextEvidence``.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when ``at`` is timezone-naive or
            ``symbol`` is unknown.
    """
    return run_data_operation(
        operation="data.economic_calendar.derive_calendar_state",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _derive_calendar_state_raw(
            symbol,
            at,
            events=events,
            before_minutes=before_minutes,
            after_minutes=after_minutes,
            minimum_impact=minimum_impact,
            evidence_ref=evidence_ref,
        ),
    )


def _calendar_state_provenance_raw(
    result: CalendarStateResult,
) -> dict[str, str]:
    """Build the provenance fields Risk's ``_calendar_result`` requires.

    Risk's gate requires ``evidence.provenance["blackout_before_minutes"]``
    and ``["blackout_after_minutes"]`` to equal the configured integer
    minutes (as strings). This helper produces those two entries; callers
    may merge them into any wider provenance dict.

    Args:
        result: One calendar-state derivation result.

    Returns:
        ``{"blackout_before_minutes": str, "blackout_after_minutes": str}``.
    """
    return {
        "blackout_before_minutes": str(result.blackout_before_minutes),
        "blackout_after_minutes": str(result.blackout_after_minutes),
    }


def calendar_state_provenance(
    result: CalendarStateResult,
) -> StandardResponse[dict[str, str]]:
    """Build the provenance fields Risk's ``_calendar_result`` requires.

    Args:
        result: One calendar-state derivation result.

    Returns:
        Standard response carrying
        ``{"blackout_before_minutes": str, "blackout_after_minutes": str}``.
    """
    return run_data_operation(
        operation="data.economic_calendar.calendar_state_provenance",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _calendar_state_provenance_raw(result),
    )


def project_calendar_state(result: CalendarStateResult) -> dict[str, object]:
    """Return a detached projection of Risk-ready calendar-state evidence.

    Args:
        result: Internal calendar-state result.

    Returns:
        Public calendar state, windows, event count, and evidence reference.
    """
    return {
        "symbol": result.symbol,
        "calendar_state": result.calendar_state,
        "blackout_before_minutes": result.blackout_before_minutes,
        "blackout_after_minutes": result.blackout_after_minutes,
        "event_count": result.event_count,
        "evidence_ref": result.evidence_ref,
    }


def _populate_market_context_calendar_raw(
    evidence: MarketContextEvidence,
    *,
    events: Sequence[EconomicEvent] | None,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
    evidence_ref: str | None = None,
) -> MarketContextEvidence:
    """Return a copy of ``evidence`` with populated ``calendar_state``.

    Args:
        evidence: The ``evidence`` argument.
        events: The ``events`` argument.
        before_minutes: The ``before_minutes`` argument.
        after_minutes: The ``after_minutes`` argument.
        minimum_impact: The ``minimum_impact`` argument.
        evidence_ref: The ``evidence_ref`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the result cannot be derived for the supplied symbol.
    """
    derived = _derive_calendar_state_raw(
        evidence.symbol,
        evidence.as_of,
        events=events,
        before_minutes=before_minutes,
        after_minutes=after_minutes,
        minimum_impact=minimum_impact,
        evidence_ref=evidence_ref,
    )
    merged_provenance = dict(evidence.provenance)
    merged_provenance.update(_calendar_state_provenance_raw(derived))
    update: dict[str, object] = {
        "calendar_state": derived.calendar_state,
        "provenance": merged_provenance,
    }
    # Risk's gate treats ``"unknown"`` exactly like ``None`` (calendar evidence
    # is missing). Only when a real state is present should "calendar" leave
    # ``missing_fields``; "unknown" preserves the explicit-missing contract.
    if (
        derived.calendar_state != CALENDAR_STATE_UNKNOWN
        and "calendar" in evidence.missing_fields
    ):
        update["missing_fields"] = tuple(
            field for field in evidence.missing_fields if field != "calendar"
        )
    return evidence.model_copy(update=update)


def populate_market_context_calendar(
    evidence: MarketContextEvidence,
    *,
    events: Sequence[EconomicEvent] | None,
    before_minutes: int = 10,
    after_minutes: int = 10,
    minimum_impact: EventImpact | None = None,
    evidence_ref: str | None = None,
) -> StandardResponse[MarketContextEvidence]:
    """Return a copy of ``evidence`` with populated ``calendar_state``.

    This is the Data-side wiring used to satisfy Risk's existing calendar
    gate without modifying the `MarketContextProvider`/`get_market_context_evidence`
    contract. The caller (e.g. a production `MarketContextProvider` adapter or
    the live workflow) supplies an existing market-context evidence, plus the
    pre-fetched events relevant to its symbol window; this function derives
    the canonical state, records the two required provenance fields, and
    returns a new immutable evidence copy. The original ``provenance`` mapping
    is preserved with the two ``blackout_*`` entries merged (overwriting).

    Args:
        evidence: Existing market-context evidence whose symbol drives the
            derived state.
        events: Pre-fetched normalized events relevant to the symbol window.
        before_minutes: Risk-side blackout minutes before each release.
        after_minutes: Risk-side blackout minutes after each release.
        minimum_impact: Minimum impact to consider (defaults to HIGH).
        evidence_ref: Optional opaque correlation reference.

    Returns:
        Standard response carrying a new `MarketContextEvidence` with
        ``calendar_state`` populated (one of ``"event"``,
        ``"blackout_before"``, ``"blackout_after"``, ``"open"``, or
        ``"unknown"``) and provenance carrying
        ``blackout_before_minutes``/``blackout_after_minutes`` as strings.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when the result cannot be derived for
            the supplied symbol.
    """
    return run_data_operation(
        operation="data.economic_calendar.populate_market_context_calendar",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _populate_market_context_calendar_raw(
            evidence,
            events=events,
            before_minutes=before_minutes,
            after_minutes=after_minutes,
            minimum_impact=minimum_impact,
            evidence_ref=evidence_ref,
        ),
    )


__all__ = [
    "DEFAULT_MINIMUM_IMPACT",
    "CalendarStateResult",
    "calendar_state_provenance",
    "derive_calendar_state",
    "populate_market_context_calendar",
    "project_calendar_state",
]
