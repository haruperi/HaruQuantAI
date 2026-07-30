"""Integration evidence for FEAT-DATA-16 persistence and point-in-time reads."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Self

import pytest
from app.services.data import (
    assess_research_source_eligibility,
    build_data_settings,
    build_research_source_ingest_request,
    build_research_source_policy,
    build_research_source_query,
    data_settings_context,
    get_research_source_value_field,
    ingest_research_source,
    project_research_source_evidence,
    query_research_sources,
    run_data_migrations,
)
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings for research-source persistence."""
    return build_data_settings(
        database_url="sqlite:///data.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _policy() -> object:
    """Build the official-source policy used by focused tests."""
    return build_research_source_policy(
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


def _request(
    now: datetime,
    *,
    source_url: str = "https://www.federalreserve.gov/feeds/press_all.xml",
    external_id: str = "press-all",
    title: str = "Federal Reserve Board",
    max_bytes: int = 262_144,
) -> object:
    """Build one bounded official-source request."""
    return build_research_source_ingest_request(
        source_url=source_url,
        source_id="federal-reserve",
        source_kind="macro",
        external_id=external_id,
        title=title,
        asset_scope=("EURUSD",),
        issuer_scope=("Federal Reserve",),
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
        max_bytes=max_bytes,
    )


def _feed(item_id: str, title: str = "Federal Reserve Board") -> bytes:
    """Return deterministic XML standing in for retrieved official bytes."""
    return (
        b"<rss><channel><item><title>"
        + title.encode()
        + b"</title><guid>https://example.test/"
        + item_id.encode()
        + b"</guid><pubDate>Thu, 01 Jan 2026 23:00:00 GMT</pubDate>"
        b"</item></channel></rss>"
    )


def test_ingest_is_idempotent_and_query_is_point_in_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persist verified bytes once and exclude them before availability."""
    now = datetime(2026, 1, 2, tzinfo=UTC)
    monkeypatch.setattr(
        "app.services.data.research_sources.ingestion._fetch",
        lambda _request: _feed("release-1"),
    )
    settings = _settings(tmp_path)
    policy = _policy()
    request = _request(now)

    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        first = ingest_research_source(request, policy=policy, now=now)
        second = ingest_research_source(request, policy=policy, now=now)
        before = query_research_sources(
            build_research_source_query(decision_time=now - timedelta(seconds=1))
        )
        at_time = query_research_sources(build_research_source_query(decision_time=now))

    assert get_research_source_value_field(first, "document_id") == (
        get_research_source_value_field(second, "document_id")
    )
    assert get_research_source_value_field(before, "records") == ()
    assert len(get_research_source_value_field(at_time, "records")) == 1


def test_ingest_fetch_and_metadata_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover bounded transport, metadata, content, and non-feed behavior."""
    now = datetime(2026, 1, 2, tzinfo=UTC)
    settings = _settings(tmp_path)
    policy = _policy()

    class _Response:
        """Minimal context-managed HTTP response."""

        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return self._payload

    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion.urlopen",
            lambda *_args, **_kwargs: _Response(
                b"Federal Reserve Board official statement"
            ),
        )
        document = ingest_research_source(
            _request(
                now,
                source_url="https://www.federalreserve.gov/statement.txt",
            ),
            policy=policy,
            now=now,
        )
        assert get_research_source_value_field(document, "external_id") == "press-all"

        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion.urlopen",
            lambda *_args, **_kwargs: _Response(b"0123456789"),
        )
        with pytest.raises(Exception, match="LIMIT_EXCEEDED"):
            ingest_research_source(
                _request(
                    now,
                    source_url="https://www.federalreserve.gov/statement.txt",
                    max_bytes=5,
                ),
                policy=policy,
                now=now,
            )

        def _unavailable(*_args: object, **_kwargs: object) -> Any:
            raise OSError("offline")

        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion.urlopen",
            _unavailable,
        )
        with pytest.raises(Exception, match="SOURCE_UNAVAILABLE"):
            ingest_research_source(_request(now), policy=policy, now=now)

        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion._fetch",
            lambda _request: b"<rss></rss>",
        )
        with pytest.raises(Exception, match="EMPTY_RESULT"):
            ingest_research_source(_request(now), policy=policy, now=now)

        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion._fetch",
            lambda _request: (
                b"<rss><channel><item><title>Another publisher</title>"
                b"</item></channel></rss>"
            ),
        )
        with pytest.raises(Exception, match="INVALID_INPUT"):
            ingest_research_source(_request(now), policy=policy, now=now)

        monkeypatch.setattr(
            "app.services.data.research_sources.ingestion._fetch",
            lambda _request: (
                b"<rss><channel><item><title>Federal Reserve Board</title>"
                b"</item></channel></rss>"
            ),
        )
        with pytest.raises(Exception, match="INVALID_INPUT"):
            ingest_research_source(_request(now), policy=policy, now=now)


def test_query_filters_pagination_projection_and_eligibility(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise every decision-time filter and explicit ineligibility reason."""
    now = datetime(2026, 1, 2, tzinfo=UTC)
    payloads = iter((_feed("release-1"), _feed("release-2")))
    monkeypatch.setattr(
        "app.services.data.research_sources.ingestion._fetch",
        lambda _request: next(payloads),
    )
    with data_settings_context(_settings(tmp_path)):
        run_data_migrations(generate_id("req"))
        first = ingest_research_source(_request(now), policy=_policy(), now=now)
        ingest_research_source(
            _request(now, external_id="different-request-id"),
            policy=_policy(),
            now=now,
        )
        for filters in (
            {"source_kinds": ("filing",)},
            {"source_ids": ("another-source",)},
            {"asset_scope": ("GBPUSD",)},
            {"issuer_scope": ("Another Issuer",)},
            {"language": "fr"},
        ):
            page = query_research_sources(
                build_research_source_query(decision_time=now, **filters)
            )
            assert get_research_source_value_field(page, "records") == ()

        page_one = query_research_sources(
            build_research_source_query(decision_time=now, limit=1)
        )
        assert get_research_source_value_field(page_one, "next_cursor") == "1"
        page_two = query_research_sources(
            build_research_source_query(decision_time=now, limit=1, cursor="1")
        )
        assert len(get_research_source_value_field(page_two, "records")) == 1

    projection = project_research_source_evidence(first)
    assert projection["title"] == "Federal Reserve Board"
    with pytest.raises(Exception, match="INVALID_INPUT"):
        project_research_source_evidence(object())

    unsafe = replace(
        first,
        available_at=now + timedelta(seconds=1),
        retrieved_at=now + timedelta(seconds=1),
        trust_status="unverified",
        manipulation_status="suspected",
        injection_status="unsafe",
        retention_until=now - timedelta(seconds=1),
    )
    decision = assess_research_source_eligibility(unsafe, decision_time=now)
    assert get_research_source_value_field(decision, "reasons") == (
        "NOT_YET_AVAILABLE",
        "TRUST_NOT_VERIFIED",
        "MANIPULATION_UNRESOLVED",
        "INJECTION_UNSAFE",
        "RETENTION_EXPIRED",
    )
