"""Verified-source manifest persistence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.services.data.persistence import (
    update_verified_research_source_record,
)

if TYPE_CHECKING:
    from app.services.data.research_sources.contracts import VerifiedResearchSource


def persist_verified_research_source(
    manifest: VerifiedResearchSource,
    *,
    request_id: str,
) -> VerifiedResearchSource:
    """Persist one immutable provider verification manifest."""
    update_verified_research_source_record(
        (
            manifest.source_id,
            manifest.parser_version,
            manifest.verified_at.isoformat(),
            manifest.external_record_id,
            manifest.fixture_sha256,
            json.dumps(manifest.environments),
            manifest.license_policy,
        ),
        request_id=request_id,
    )
    return manifest


__all__ = ("persist_verified_research_source",)
