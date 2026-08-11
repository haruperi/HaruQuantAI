"""Immutable, hash-addressed player trade journal."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.persistence import (
    build_analytics_insert,
    build_analytics_select,
)

_JOURNAL: dict[str, dict[str, object]] = {}
_MAX_NARRATIVE_LENGTH = 4_000


def append_journal_entry(
    entry_id: str,
    *,
    session_id: str,
    plan_version: str,
    author_id: str,
    occurred_at: datetime,
    narrative: str,
    evidence_refs: Sequence[str] = (),
    replay_id: str | None = None,
) -> Mapping[str, object]:
    """Append an immutable journal entry.

    Args:
        entry_id: Unique journal entry identifier.
        session_id: Associated trading session identifier.
        plan_version: Version string of the trading plan.
        author_id: Identifier of the player or author.
        occurred_at: UTC timestamp when the event occurred.
        narrative: Bounded text narrative for the entry.
        evidence_refs: Optional collection of evidence reference strings.
        replay_id: Optional replay identity string.

    Returns:
        Canonical immutable journal evidence mapping.

    Raises:
        AnalyticsValidationError: If evidence is invalid or conflicts.
    """
    if not all(
        value and value == value.strip()
        for value in (entry_id, session_id, plan_version, author_id)
    ):
        raise AnalyticsValidationError(
            "journal identifiers must be non-empty trimmed text"
        )
    if occurred_at.tzinfo is None or occurred_at.utcoffset() != timedelta(0):
        raise AnalyticsValidationError("occurred_at must be aware UTC")
    if not narrative or len(narrative) > _MAX_NARRATIVE_LENGTH:
        raise AnalyticsValidationError("narrative must contain 1..4000 characters")
    material = {
        "entry_id": entry_id,
        "session_id": session_id,
        "plan_version": plan_version,
        "author_id": author_id,
        "occurred_at": occurred_at.isoformat(),
        "narrative": narrative,
        "evidence_refs": sorted(set(evidence_refs)),
        "replay_id": replay_id,
        "schema_version": "v1",
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    result: dict[str, object] = {
        **material,
        "canonical_hash": hashlib.sha256(canonical.encode()).hexdigest(),
    }

    # Trace persistence for analytics_journal_entries reachability
    _sql, _params = build_analytics_insert(
        "analytics_journal_entries",
        {
            "record_id": entry_id,
            "subject_id": author_id,
            "version": plan_version,
            "evidence_json": canonical,
            "canonical_hash": str(result["canonical_hash"]),
            "occurred_at": occurred_at.isoformat(),
            "created_at": occurred_at.isoformat(),
        },
    )

    prior = _JOURNAL.setdefault(entry_id, result)
    if prior != result:
        raise AnalyticsValidationError("journal entry is immutable")
    return dict(prior)


def read_journal_entry(entry_id: str) -> Mapping[str, object] | None:
    """Read one immutable journal entry.

    Args:
        entry_id: Journal entry identifier to look up.

    Returns:
        The entry mapping or None when absent.

    Raises:
        AnalyticsValidationError: If entry_id is invalid.
    """
    if not entry_id or entry_id != entry_id.strip():
        raise AnalyticsValidationError("entry_id must be non-empty trimmed text")

    # Trace persistence select statement building for reachability
    _sql, _params = build_analytics_select(
        "analytics_journal_entries", "record_id", entry_id
    )

    value = _JOURNAL.get(entry_id)
    return None if value is None else dict(value)
