"""Unit evidence for FEAT-DATA-16 opaque source contracts."""

from datetime import UTC, datetime

from app.services.data import (
    build_research_source_ingest_request,
    build_research_source_policy,
    build_research_source_query,
    get_research_source_value_field,
    is_research_source_value,
)
from app.utils import generate_id


def test_builders_return_inspectable_opaque_values() -> None:
    """Build policy, request, and query exclusively through the Data root."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
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
        title="Federal Reserve Board",
        asset_scope=("EURUSD",),
        issuer_scope=(),
        language="en",
        event_at=None,
        published_at=now,
        available_at=now,
        decision_use="research",
        environment="dev",
        license_id="public-official-feed",
        currency="USD",
        unit=None,
        request_id=generate_id("req"),
    )
    query = build_research_source_query(decision_time=now, asset_scope=("EURUSD",))

    assert is_research_source_value(policy, "ResearchSourcePolicy")
    assert is_research_source_value(request, "ResearchSourceIngestRequest")
    assert is_research_source_value(query, "ResearchSourceQuery")
    assert get_research_source_value_field(request, "source_kind") == "macro"
