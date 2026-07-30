"""Unit evidence for FEAT-DATA-16 source policy enforcement."""

from datetime import UTC, datetime

import pytest
from app.services.data import (
    build_research_source_ingest_request,
    build_research_source_policy,
    validate_research_source_policy,
)
from app.utils import generate_id


def test_policy_rejects_undeclared_host() -> None:
    """Fail closed before any source socket is opened."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    request = build_research_source_ingest_request(
        source_url="https://example.org/research.xml",
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

    with pytest.raises(Exception, match="LICENSE_RESTRICTION"):
        validate_research_source_policy(request, policy, now=now)
