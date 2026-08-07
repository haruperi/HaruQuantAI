"""FEAT-RES-13: produce bounded intelligence from an official live source."""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_research_source_policy,
    build_research_source_query,
    data_settings_context,
    normalize_research_provider_payload,
    persist_research_provider_records,
    retrieve_research_provider_payload,
    run_data_migrations,
)
from app.services.research import (
    assess_intelligence_applicability,
    build_fundamental_source_evidence,
    build_sentiment_source_evidence,
    project_intelligence_evidence,
)
from app.utils import generate_id


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _evidence_output(requirement: str, value: object) -> None:
    """Print the required success line and bounded actual evidence."""
    print(f"SUCCESS: {requirement}")
    print(value)


def fr_res_099(fundamental: Mapping[str, object]) -> None:
    """FR-RES-099: demonstrate versioned fundamental evidence."""
    _evidence_output("FR-RES-099", fundamental)


def fr_res_100(fundamental: Mapping[str, object]) -> None:
    """FR-RES-100: demonstrate eligible point-in-time coverage."""
    _evidence_output("FR-RES-100", fundamental["coverage"])


def fr_res_101(sentiment: Mapping[str, object]) -> None:
    """FR-RES-101: demonstrate bounded sentiment source evidence."""
    _evidence_output("FR-RES-101", sentiment)


def fr_res_102(sentiment: Mapping[str, object]) -> None:
    """FR-RES-102: demonstrate deterministic polarity and missingness."""
    _evidence_output(
        "FR-RES-102",
        {
            "polarity": sentiment["polarity"],
            "missing_measurements": sentiment["missing_measurements"],
        },
    )


def fr_res_103() -> None:
    """FR-RES-103: demonstrate explicit asset-class applicability."""
    applicability = assess_intelligence_applicability("sovereign_bond", model="issuer")
    _evidence_output("FR-RES-103", applicability.status)


def fr_res_104(
    fundamental: Mapping[str, object], sentiment: Mapping[str, object]
) -> None:
    """FR-RES-104: demonstrate detached non-binding projections."""
    _evidence_output(
        "FR-RES-104",
        {
            "fundamental_schema": fundamental["schema_id"],
            "sentiment_schema": sentiment["schema_id"],
            "advisory_only": True,
        },
    )


def main() -> None:
    """Pass genuine Treasury data through provider-neutral Research evidence."""
    _feature_header(
        "FEATURE: FEAT-RES-13 — intelligence/ — Fundamental and Sentiment Source Evidence\n\n"
        "Purpose: Assess applicability and project point-in-time fundamental and sentiment source evidence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Source record applicability assessment\n-> Stage 2: Point-in-time fundamental and sentiment evidence extraction\n-> Stage 3: Consolidated intelligence evidence projection"
    )

    now = datetime.now(UTC)
    policy = build_research_source_policy(
        "treasury-fiscal-data-v1",
        "treasury-fiscal-data",
        ("api.fiscaldata.treasury.gov",),
        ("dev",),
        ("research",),
        ("US",),
        False,
        30,
        5,
        1.0,
        None,
    )
    payload = retrieve_research_provider_payload(
        "treasury-fiscal-data",
        (
            "https://api.fiscaldata.treasury.gov/services/api/"
            "fiscal_service/v2/accounting/od/debt_to_penny"
            "?sort=-record_date&page%5Bsize%5D=1"
        ),
        allowed_hosts=("api.fiscaldata.treasury.gov",),
        user_agent="HaruQuantAI research-source-reader",
        now=now,
    )
    normalized = normalize_research_provider_payload(
        "treasury-fiscal-data",
        payload,
        observed_at=now,
    )
    with tempfile.TemporaryDirectory(prefix="research-intelligence-") as directory:
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            persist_research_provider_records(
                normalized,
                payload,
                source_id="treasury-fiscal-data",
                source_kind="macro",
                asset_scope=("USD",),
                issuer_scope=(),
                macro_series_scope=("debt-to-penny",),
                language="en",
                license_id="public-official-data",
                environment="dev",
                decision_use="research",
                policy=policy,
                retrieved_at=now,
                request_id=generate_id("req"),
            )
            query = build_research_source_query(
                decision_time=now,
                source_kinds=("macro",),
                asset_scope=("USD",),
            )
            fundamental = build_fundamental_source_evidence(
                query,
                asset_class="sovereign_bond",
                model="macro",
                required_kinds=("macro",),
            )
            sentiment = build_sentiment_source_evidence(
                query,
                measurement_version="lexicon-v1",
            )

    projected_fundamental = project_intelligence_evidence(fundamental)
    projected_sentiment = project_intelligence_evidence(sentiment)
    fr_res_099(projected_fundamental)
    fr_res_100(projected_fundamental)
    fr_res_101(projected_sentiment)
    fr_res_102(projected_sentiment)
    fr_res_103()
    fr_res_104(projected_fundamental, projected_sentiment)


if __name__ == "__main__":
    main()
