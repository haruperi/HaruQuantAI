"""Deterministic provider parsing evidence for FEAT-DATA-16."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.data import (
    get_research_source_value_field,
    normalize_research_provider_payload,
)

_FIXTURES = Path(__file__).parents[1] / "fixtures" / "research_sources"
_CASES = (
    ("sec-edgar", "sec_submissions.json", "regulatory_filing"),
    ("sec-edgar", "sec_companyfacts.json", "fundamental_facts"),
    ("sec-edgar-filing-index", "sec_filing_index.json", "filing_document"),
    ("bls", "bls.json", "macro_observations"),
    ("bea", "bea.json", "macro_observations"),
    ("eia", "eia.json", "energy_observations"),
    ("treasury-fiscal-data", "treasury.json", "fiscal_observations"),
    ("cftc-cot", "cftc_cot.json", "positioning_report"),
    ("gdelt", "gdelt.json", "news_headline"),
    ("usda-nass", "usda_nass.json", "agricultural_observations"),
)


@pytest.mark.parametrize(("provider", "fixture", "kind"), _CASES)
def test_provider_fixture_normalizes_real_record_shape(
    provider: str,
    fixture: str,
    kind: str,
) -> None:
    """Normalize bounded checked-in provider evidence."""
    records = normalize_research_provider_payload(
        provider,
        (_FIXTURES / fixture).read_bytes(),
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert records
    assert records[0]["document_kind"] == kind
    assert len(str(records[0]["content_sha256"])) == 64


def test_provider_normalization_fails_closed() -> None:
    """Reject unknown providers, malformed payloads, and empty results."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(Exception, match="INVALID_INPUT"):
        normalize_research_provider_payload("unknown", b"{}", observed_at=now)
    with pytest.raises(Exception, match="INVALID_INPUT"):
        normalize_research_provider_payload("bls", b"{}", observed_at=now)
    with pytest.raises(Exception, match="LIMIT_EXCEEDED"):
        normalize_research_provider_payload("bls", b"", observed_at=now)


def test_root_inspector_rejects_mapping_private_fields() -> None:
    """Keep normalized mappings detached from opaque contract inspection."""
    with pytest.raises(ValueError, match="does not expose"):
        get_research_source_value_field({}, "_private")


def test_sec_and_gdelt_conservative_edge_cases() -> None:
    """Exercise malformed, filtered, and fallback provider records."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    sec = normalize_research_provider_payload(
        "sec-edgar",
        (
            b'{"filings":{"recent":{"accessionNumber":["skip","keep"],'
            b'"form":["S-1","8-K"],"primaryDocument":["s1.htm","eightk.htm"],'
            b'"acceptanceDateTime":["bad","bad"]}}}'
        ),
        observed_at=now,
    )
    assert len(sec) == 1
    assert sec[0]["available_at"] == now.isoformat()

    gdelt = normalize_research_provider_payload(
        "gdelt",
        (
            b'{"articles":[{"title":"","url":"https://example.test"},'
            b'{"title":"Official update","url":"https://sec.gov/update",'
            b'"seendate":"invalid"}]}'
        ),
        observed_at=now,
    )
    assert len(gdelt) == 1
    assert gdelt[0]["available_at"] == now.isoformat()

    for provider, payload in (
        ("sec-edgar", b"not-json"),
        ("sec-edgar", b'{"filings":{},"facts":{}}'),
        ("gdelt", b"not-json"),
    ):
        with pytest.raises(Exception, match=r"INVALID_INPUT|EMPTY_RESULT"):
            normalize_research_provider_payload(
                provider,
                payload,
                observed_at=now,
            )


def test_sec_filing_index_classifies_exhibits_and_transcripts() -> None:
    """Classify bounded SEC filing documents without retrieving document bodies."""
    records = normalize_research_provider_payload(
        "sec-edgar-filing-index",
        (_FIXTURES / "sec_filing_index.json").read_bytes(),
        observed_at=datetime(2026, 7, 30, tzinfo=UTC),
    )

    assert tuple(record["document_kind"] for record in records) == (
        "filing_document",
        "official_statement_exhibit",
        "transcript",
    )
    assert all(
        str(record["canonical_locator"]).startswith("https://www.sec.gov/Archives/")
        for record in records
    )
