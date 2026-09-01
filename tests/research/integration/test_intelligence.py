"""Integration evidence for FEAT-RES-13 Data-backed intelligence."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_research_source_ingest_request,
    build_research_source_policy,
    build_research_source_query,
    data_settings_context,
    ingest_research_source,
    run_data_migrations,
)
from app.services.research import (
    assess_intelligence_applicability,
    build_fundamental_source_evidence,
    build_sentiment_source_evidence,
    project_intelligence_evidence,
)


def test_intelligence_uses_persisted_eligible_source_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build bounded evidence from a real Data record, not injected Research data."""
    now = datetime(2026, 1, 2, tzinfo=UTC)
    monkeypatch.setitem(
        ingest_research_source.__globals__,
        "_fetch",
        lambda _request: (
            b"<rss><channel><item>"
            b"<title>Federal Reserve Board growth improves while risk declines</title>"
            b"<guid>https://example.test/release-1</guid>"
            b"<pubDate>Thu, 01 Jan 2026 23:00:00 GMT</pubDate>"
            b"</item></channel></rss>"
        ),
    )
    settings = build_data_settings(
        database_url="sqlite:///data.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    policy = build_research_source_policy(
        "fed-v1",
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
        external_id="press-all",
        title="Federal Reserve Board growth improves while risk declines",
        asset_scope=("EURUSD",),
        issuer_scope=(),
        language="en",
        event_at=None,
        published_at=now - timedelta(hours=1),
        available_at=now,
        decision_use="research",
        environment="dev",
        license_id="public-official-feed",
        currency="USD",
        unit=None,
        request_id=generate_id("req"),
    )

    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        ingest_research_source(request, policy=policy, now=now)
        query = build_research_source_query(
            decision_time=now,
            source_kinds=("macro",),
            asset_scope=("EURUSD",),
        )
        fundamental = build_fundamental_source_evidence(
            query,
            asset_class="forex",
            model="macro",
            required_kinds=("macro",),
        )
        sentiment = build_sentiment_source_evidence(
            query,
            measurement_version="lexicon-v1",
        )
        with pytest.raises(ValueError, match="FUNDAMENTAL_COVERAGE_MISSING"):
            build_fundamental_source_evidence(
                query,
                asset_class="forex",
                model="macro",
                required_kinds=("filing",),
            )
        with pytest.raises(ValueError, match="SENTIMENT_VERSION_UNKNOWN"):
            build_sentiment_source_evidence(
                query,
                measurement_version="model-v2",
            )

    fundamental_projection = project_intelligence_evidence(fundamental)
    sentiment_projection = project_intelligence_evidence(sentiment)
    assert fundamental_projection["coverage"] == {"macro": 1}
    assert sentiment_projection["polarity"]
    assert "source_payload" not in fundamental_projection
    assert fundamental_projection["advisory_only"] is True
    assert (
        assess_intelligence_applicability(
            "forex",
            model="issuer",
        ).status
        == "not_applicable"
    )
    assert (
        assess_intelligence_applicability(
            "equity",
            model="issuer",
        ).status
        == "applicable"
    )
    with pytest.raises(ValueError, match="INTELLIGENCE_MODEL_UNKNOWN"):
        assess_intelligence_applicability("equity", model="unknown")
    with pytest.raises(ValueError, match="INTELLIGENCE_EVIDENCE_UNKNOWN"):
        project_intelligence_evidence(object())
