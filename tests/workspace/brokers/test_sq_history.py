"""Fixture-backed SQ archive range and provider-failure regressions."""

import io
import struct
import zipfile
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.core.data.contracts import BridgeError
from app.workspace.brokers.codecs import SQ_MAGIC_HEADER_V42
from app.workspace.brokers.sq_equity import SQEquityClient
from app.workspace.brokers.sq_futures import SQFuturesClient


def archive(*dates: str) -> bytes:
    """Build valid independent SQ anchor bars inside a ZIP fixture."""
    payload = SQ_MAGIC_HEADER_V42
    for date in dates:
        stamp = int(datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp() * 1000)
        payload += b"\xbb\xbb\xbb" + struct.pack(
            ">Q5q", stamp, 1_100_000, 1_100_010, 1_099_990, 1_100_000, 100_000
        )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as zipped:
        zipped.writestr("history.dat", payload)
    return output.getvalue()


@pytest.mark.parametrize("client_type", [SQEquityClient, SQFuturesClient])
def test_archive_dates_are_verified_before_request_filtering(
    tmp_path, monkeypatch, caplog, client_type
):
    client = client_type(data_dir=tmp_path)
    monkeypatch.setattr(
        client,
        "_http_get",
        lambda url: SimpleNamespace(
            status_code=200, content=archive("2024-01-02", "2024-05-15")
        ),
    )
    try:
        with caplog.at_level("WARNING"), pytest.raises(BridgeError) as caught:
            client.get_bars(
                "@ES",
                "D1",
                date_from=datetime(2026, 1, 1, tzinfo=UTC),
                date_to=datetime(2026, 2, 1, tzinfo=UTC),
            )
        assert caught.value.code == "NO_DATA"
        assert "2024-01-02 through 2024-05-15" in str(caught.value)
        assert "2026-01-01" in str(caught.value)
        assert "Inspected CDN archives (data01.zip)" in str(caught.value)
        assert "FR-BROKER-SQ-ARCHIVE-AVAILABILITY" in caplog.text
        with caplog.at_level("INFO"):
            frame = client.get_bars(
                "@ES",
                "D1",
                date_from=datetime(2024, 5, 15, tzinfo=UTC),
                date_to=datetime(2024, 5, 15, tzinfo=UTC),
            )
        assert len(frame) == 1
        assert "returned 1 matching rows" in caplog.text
    finally:
        client.disconnect()


def test_both_archives_and_count_preserve_matching_history(tmp_path, monkeypatch):
    client = SQFuturesClient(data_dir=tmp_path)
    calls = []

    def get(url):
        calls.append(url)
        return SimpleNamespace(
            status_code=200,
            content=archive("2018-01-02" if "data00" in url else "2024-05-15"),
        )

    monkeypatch.setattr(client, "_http_get", get)
    try:
        rows = client._fetch_cdn_bars(
            "@ES", count=1, date_from=datetime(2018, 1, 1, tzinfo=UTC)
        )
        assert len(calls) == 2 and len(rows) == 1
        assert rows[0]["time"] == int(datetime(2024, 5, 15, tzinfo=UTC).timestamp())
    finally:
        client.disconnect()


@pytest.mark.parametrize("case", ["empty", "http", "corrupt"])
def test_unknown_coverage_is_not_invented_or_provider_errors_hidden(
    tmp_path, monkeypatch, case
):
    client = SQFuturesClient(data_dir=tmp_path)
    content = archive() if case == "empty" else b"not a zip"
    monkeypatch.setattr(
        client,
        "_http_get",
        lambda url: SimpleNamespace(
            status_code=503 if case == "http" else 200, content=content
        ),
    )
    try:
        if case == "corrupt":
            with pytest.raises(zipfile.BadZipFile):
                client._fetch_cdn_bars("@ES")
        else:
            with pytest.raises(BridgeError) as caught:
                client._fetch_cdn_bars("@ES")
            assert caught.value.code == (
                "DOWNLOAD_ERROR" if case == "http" else "NO_DATA"
            )
            if case == "empty":
                assert "availability could not be verified" in str(caught.value)
    finally:
        client.disconnect()
