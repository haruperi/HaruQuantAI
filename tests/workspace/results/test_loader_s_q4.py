"""Unit tests for LoaderSQ4Service."""

from __future__ import annotations

import io
import zipfile

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.loader_s_q4 import LoaderSQ4Service


class TestLoaderSQ4Service:
    """Test suite for LoaderSQ4Service."""

    def test_golden_fixture_sqx_roundtrip(self) -> None:
        """Verify round-tripping a serialized .sqx strategy archive with 3 trades."""
        xml_data = (
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<Strategy formatVersion="SQ4" name="GoldenSQ4" symbol="GBPUSD" timeframe="H1">\n'
            b"  <Settings>\n"
            b'    <Param name="StopLoss" value="50"/>\n'
            b"  </Settings>\n"
            b"  <Results>\n"
            b"    <Trades>\n"
            b'      <Trade ticket="1" direction="BUY" profit_loss="100.0"/>\n'
            b'      <Trade ticket="2" direction="SELL" profit_loss="-40.0"/>\n'
            b'      <Trade ticket="3" direction="BUY" profit_loss="150.0"/>\n'
            b"    </Trades>\n"
            b"  </Results>\n"
            b"</Strategy>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("GoldenSQ4.xml", xml_data)

        archive = LoaderSQ4Service.load_bytes("GoldenSQ4.sqx", buf.getvalue())
        assert archive.format_version == "SQ4"
        assert archive.strategy_name == "GoldenSQ4"
        assert archive.symbol == "GBPUSD"
        assert archive.timeframe == "H1"
        assert archive.trade_count == 3
        assert archive.parameters["StopLoss"] == "50"

    def test_zip_slip_traversal_rejection(self) -> None:
        """Verify Zip Slip path traversal entries are detected and rejected."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.xml", b"<Strategy/>")

        with pytest.raises(DomainError) as exc_info:
            LoaderSQ4Service.load_bytes("malicious.sqx", buf.getvalue())
        assert exc_info.value.code == "RESULTS_SQ4_UNSAFE_ARCHIVE_ENTRY"

        buf2 = io.BytesIO()
        with zipfile.ZipFile(buf2, "w") as zf:
            zf.writestr("/root/evil.xml", b"<Strategy/>")

        with pytest.raises(DomainError) as exc_info2:
            LoaderSQ4Service.load_bytes("malicious2.sqx", buf2.getvalue())
        assert exc_info2.value.code == "RESULTS_SQ4_UNSAFE_ARCHIVE_ENTRY"

    def test_malformed_archive_rejection(self) -> None:
        """Verify malformed archive payload raises DomainError."""
        with pytest.raises(DomainError) as exc_info:
            LoaderSQ4Service.load_bytes("bad.sqx", b"")
        assert exc_info.value.code == "RESULTS_SQ4_MALFORMED_ARCHIVE"

        with pytest.raises(DomainError) as exc_info:
            LoaderSQ4Service.load_bytes("bad.sqx", b"Not valid xml or zip")
        assert exc_info.value.code == "RESULTS_SQ4_MALFORMED_ARCHIVE"
