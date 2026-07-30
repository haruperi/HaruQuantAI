"""Verified-source manifest persistence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.services.data.persistence.contracts import StatementPlan, TransactionRequest
from app.services.data.persistence.transactions import _execute_transaction_raw

if TYPE_CHECKING:
    from app.services.data.research_sources.contracts import VerifiedResearchSource


def persist_verified_research_source(
    manifest: VerifiedResearchSource,
    *,
    request_id: str,
) -> VerifiedResearchSource:
    """Persist one immutable provider verification manifest."""
    _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    INSERT INTO data_verified_research_sources (
                        source_id, parser_version, verified_at, external_record_id,
                        fixture_sha256, environments_json, license_policy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (source_id, parser_version) DO UPDATE SET
                        verified_at = excluded.verified_at,
                        external_record_id = excluded.external_record_id,
                        fixture_sha256 = excluded.fixture_sha256,
                        environments_json = excluded.environments_json,
                        license_policy = excluded.license_policy
                    """.strip(),
                ),
                parameter_sets=(
                    (
                        manifest.source_id,
                        manifest.parser_version,
                        manifest.verified_at.isoformat(),
                        manifest.external_record_id,
                        manifest.fixture_sha256,
                        json.dumps(manifest.environments),
                        manifest.license_policy,
                    ),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    return manifest


__all__ = ("persist_verified_research_source",)
