"""Unit tests for LoaderSQ3Service."""

from __future__ import annotations

import io
import zipfile

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.loader_s_q3 import (
    LoaderSQ3Service,
)


class TestLoaderSQ3Service:
    """Test suite for LoaderSQ3Service."""

    def test_load_sq3_xml_direct(self) -> None:
        """Verify parsing raw SQ3 XML string."""
        xml_data = (
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<Strategy formatVersion="SQ3" name="MyStrat" symbol="EURUSD" timeframe="H1">\n'
            b"  <Parameters>\n"
            b'    <Param name="StopLoss" value="50"/>\n'
            b"  </Parameters>\n"
            b"  <Trades>\n"
            b'    <Trade ticket="1" direction="BUY" profit_loss="120.0"/>\n'
            b'    <Trade ticket="2" direction="SELL" profit_loss="-30.0"/>\n'
            b"  </Trades>\n"
            b"</Strategy>"
        )
        archive = LoaderSQ3Service.load_bytes("MyStrat.str", xml_data)
        assert archive.format_version == "SQ3"
        assert archive.strategy_name == "MyStrat"
        assert archive.symbol == "EURUSD"
        assert archive.timeframe == "H1"
        assert archive.trade_count == 2
        assert archive.parameters["StopLoss"] == "50"
        assert archive.trades[0]["profit_loss"] == 120.0

        d = archive.to_dict()
        assert d["strategy_name"] == "MyStrat"

    def test_load_sq3_from_zip(self) -> None:
        """Verify parsing SQ3 strategy from a ZIP archive."""
        xml_data = (
            b'<Strategy formatVersion="SQ3" name="ZipStrat" symbol="GBPUSD" timeframe="M15">\n'
            b"  <Trades>\n"
            b'    <Trade ticket="10" direction="BUY" profit_loss="50.0"/>\n'
            b"  </Trades>\n"
            b"</Strategy>"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("strategy.xml", xml_data)

        archive = LoaderSQ3Service.load_bytes("ZipStrat.str", buf.getvalue())
        assert archive.strategy_name == "ZipStrat"
        assert archive.symbol == "GBPUSD"
        assert archive.timeframe == "M15"
        assert archive.trade_count == 1

    def test_empty_or_malformed_payload(self) -> None:
        """Verify DomainError on empty or invalid payload."""
        with pytest.raises(DomainError) as exc_info:
            LoaderSQ3Service.load_bytes("empty.str", b"")
        assert exc_info.value.code == "RESULTS_SQ3_MALFORMED_ARCHIVE"

        with pytest.raises(DomainError) as exc_info:
            LoaderSQ3Service.load_bytes("corrupt.str", b"Not an XML < < <<")
        assert exc_info.value.code == "RESULTS_SQ3_MALFORMED_ARCHIVE"
