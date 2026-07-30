"""FEAT-RES-13: produce bounded intelligence from an official live source."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_settings,
    build_research_source_policy,
    build_research_source_query,
    data_settings_context,
    normalize_research_provider_payload,
    persist_research_provider_records,
    project_research_source_evidence,
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


def main() -> None:
    """Pass genuine Treasury data through provider-neutral Research evidence."""
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
            documents = persist_research_provider_records(
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

    print("Actual Data-owned provider evidence supplied to Research:")
    for document in documents:
        print(project_research_source_evidence(document))
    print("Official source-backed fundamental evidence:")
    print(project_intelligence_evidence(fundamental))
    print("Deterministic sentiment evidence with explicit missingness:")
    print(project_intelligence_evidence(sentiment))
    print(
        "Issuer model applicability for sovereign bonds:",
        assess_intelligence_applicability("sovereign_bond", model="issuer").status,
    )


if __name__ == "__main__":
    main()
