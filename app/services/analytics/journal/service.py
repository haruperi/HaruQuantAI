"""Immutable, hash-addressed player trade journal."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from app.services.analytics.contracts import AnalyticsValidationError

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

    Returns:
        Canonical immutable journal evidence.

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
    prior = _JOURNAL.setdefault(entry_id, result)
    if prior != result:
        raise AnalyticsValidationError("journal entry is immutable")
    return dict(prior)


def read_journal_entry(entry_id: str) -> Mapping[str, object] | None:
    """Read one immutable journal entry.

    Returns:
        The entry or ``None`` when absent.
    """
    value = _JOURNAL.get(entry_id)
    return None if value is None else dict(value)
