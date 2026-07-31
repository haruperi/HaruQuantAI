"""FEAT-DATA-16: ingest and inspect genuine official research-source evidence."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_research_source_ingest_request,
    build_research_source_policy,
    build_research_source_query,
    build_verified_research_source,
    data_settings_context,
    get_research_source_value_field,
    ingest_research_source,
    normalize_research_provider_payload,
    persist_research_provider_records,
    persist_verified_research_source,
    project_research_source_evidence,
    project_research_source_observation,
    query_research_source_observations,
    query_research_sources,
    retrieve_research_provider_payload,
    run_data_migrations,
)
from app.utils import generate_id


def main() -> None:
    """Retrieve official Federal Reserve and Treasury evidence."""
    now = datetime.now(UTC)
    treasury_policy = build_research_source_policy(
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
    treasury_payload = retrieve_research_provider_payload(
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
    treasury_record = normalize_research_provider_payload(
        "treasury-fiscal-data",
        treasury_payload,
        observed_at=now,
    )[0]
    policy = build_research_source_policy(
        "federal-reserve-public-v1",
        "federal-reserve",
        ("www.federalreserve.gov",),
        ("dev",),
        ("research",),
        ("US",),
        False,
        30,
        10,
        60.0,
        None,
    )
    request = build_research_source_ingest_request(
        source_url="https://www.federalreserve.gov/feeds/press_all.xml",
        source_id="federal-reserve",
        source_kind="macro",
        external_id="official-press-release-feed",
        title="Federal Reserve Board",
        asset_scope=("EURUSD", "USD"),
        issuer_scope=(),
        language="en",
        event_at=None,
        published_at=now - timedelta(seconds=1),
        available_at=now,
        decision_use="research",
        environment="dev",
        license_id="public-official-feed",
        currency="USD",
        unit=None,
        request_id=generate_id("req"),
    )
    with tempfile.TemporaryDirectory(prefix="data-research-source-") as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            document = ingest_research_source(request, policy=policy, now=now)
            treasury_documents = persist_research_provider_records(
                (treasury_record,),
                treasury_payload,
                source_id="treasury-fiscal-data",
                source_kind="macro",
                asset_scope=("USD",),
                issuer_scope=(),
                macro_series_scope=("debt-to-penny",),
                language="en",
                license_id="public-official-data",
                environment="dev",
                decision_use="research",
                policy=treasury_policy,
                retrieved_at=now,
                request_id=generate_id("req"),
            )
            persist_verified_research_source(
                build_verified_research_source(
                    "treasury-fiscal-data",
                    now,
                    str(treasury_record["external_id"]),
                    str(treasury_record["parser_version"]),
                    hashlib.sha256(treasury_payload).hexdigest(),
                    ("dev", "research"),
                    "public-official-data",
                ),
                request_id=generate_id("req"),
            )
            page = query_research_sources(
                build_research_source_query(
                    decision_time=now,
                    source_kinds=("macro",),
                    asset_scope=("EURUSD",),
                )
            )
            point_in_time_observations = query_research_source_observations(
                now,
                source_id="treasury-fiscal-data",
                request_id=generate_id("req"),
            )
    print("Official source evidence:")
    print(project_research_source_evidence(document))
    print(
        "Decision-time records:",
        len(get_research_source_value_field(page, "records")),
    )
    print("Official Treasury source record:")
    print(
        {
            key: treasury_record[key]
            for key in (
                "title",
                "canonical_locator",
                "parser_version",
                "content_sha256",
            )
        }
    )
    print("Actual Treasury observations:")
    for observation in point_in_time_observations[:8]:
        print(project_research_source_observation(observation))
    print(
        "Persisted Treasury documents:",
        [project_research_source_evidence(value) for value in treasury_documents],
    )
    print("Persisted observation count:", len(point_in_time_observations))


if __name__ == "__main__":
    main()
