"""Opt-in genuine-provider verification for FEAT-DATA-16."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from urllib.parse import urlsplit

import pytest
from app.services.data import (
    build_verified_research_source,
    get_research_source_value_field,
    normalize_research_provider_payload,
    retrieve_research_provider_payload,
)


@pytest.mark.skipif(
    os.getenv("HARU_RESEARCH_LIVE_PROVIDER") is None,
    reason="Set HARU_RESEARCH_LIVE_PROVIDER and companion variables to opt in.",
)
def test_configured_live_provider_is_real_and_repeatable() -> None:
    """Retrieve, validate, normalize, and hash one configured official record."""
    provider = os.environ["HARU_RESEARCH_LIVE_PROVIDER"]
    url = os.environ["HARU_RESEARCH_LIVE_URL"]
    expected_host = os.environ["HARU_RESEARCH_LIVE_HOST"]
    user_agent = os.environ["HARU_RESEARCH_LIVE_USER_AGENT"]
    now = datetime.now(UTC)

    assert (urlsplit(url).hostname or "").lower() == expected_host
    payload = retrieve_research_provider_payload(
        provider,
        url,
        allowed_hosts=(expected_host,),
        user_agent=user_agent,
        rate_limit=1,
        now=now,
    )
    first = normalize_research_provider_payload(
        provider,
        payload,
        observed_at=now,
    )
    second = normalize_research_provider_payload(
        provider,
        payload,
        observed_at=now,
    )
    assert first == second
    assert first[0]["external_id"]
    assert first[0]["published_at"]

    manifest = build_verified_research_source(
        provider,
        now,
        str(first[0]["external_id"]),
        str(first[0]["parser_version"]),
        hashlib.sha256(payload).hexdigest(),
        ("dev", "research"),
        os.getenv("HARU_RESEARCH_LIVE_LICENSE", "public-official-data"),
    )
    assert get_research_source_value_field(manifest, "fixture_sha256") == (
        hashlib.sha256(payload).hexdigest()
    )
