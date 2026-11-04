"""S15 executable donor evidence and full chart/metadata integration contracts.

Reference capture: Java 26.0.2.1, 2026-11-04. chart_vectors.jsonl executes the
unchanged recovered ChartDef, DataInfo, InstrumentInfo, BarTypeFactory, TimeBar,
Fx/FuturesTimeBar, IntradayBar and SessionElement classes. Temporary dependencies
provide in-memory catalog/instrument/session lookups, JDOM attribute containers,
SLF4J, XMLUtil's recovered numeric recovery, and UTC SQTime operations. Calendar
execution methods outside S15 throw if called. Harness/build files are removed
through TemporaryDirectory after capture. The 365 outputs include 338 comparison
pairs, 16 chart states/cache identities, two dataset states and nine XML numeric
forms. No Python application code generated expected outputs.

XML is compared by attributes and child structure, with numeric equality for
Double fields rather than Java/Python float spelling. Explicit timezone and
injected lookups are approved Python adaptations; aggregation/calendar engines
retain their later-slice responsibilities. Ownership: app/core/data/charts.py
and instruments.py; DataInfo remains in contracts.py. The original 67 timeframe/
JVM-string outputs are in vectors.jsonl and covered by test_timeframes.py.
"""

from __future__ import annotations

import base64
import json
import logging
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, fromstring

import pytest
from app.core.data.charts import ChartDef
from app.core.data.contracts import DataInfo, SessionWindow
from app.core.data.instruments import InstrumentInfo
from app.core.host.logging import shutdown_logging
from app.core.lib.errors import DomainError
from pydantic import TypeAdapter

_FIXTURES = Path(__file__).parent / "fixtures/s15"
_VECTORS: list[dict[str, Any]] = [
    json.loads(line)
    for line in (_FIXTURES / "chart_vectors.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
_FLOAT_ATTRIBUTES = {
    "spread",
    "tickSize",
    "tickStep",
    "tickValueInMoney",
    "defaultSpread",
    "defaultSlippage",
    "minDistance",
    "pointValue",
    "orderSizeStep",
    "orderSizeMultiplier",
}


def _instrument() -> InstrumentInfo:
    return InstrumentInfo(
        connection="broker",
        instrument="Forex",
        tick_size=0.00001,
        tick_step=0.00001,
        tick_value_in_money=1.0,
        default_spread=2.5,
        order_size_step=0.01,
        broker=8,
        min_distance=7.0,
    )


def _info(kind: int = 2) -> DataInfo:
    return DataInfo(
        connection="broker",
        symbol="EURUSD",
        original_symbol="EURUSD.x",
        instrument="Forex",
        timeframe="M1",
        filename="bars.bin",
        timezone="UTC",
        u_symbol="EURUSD",
        u_symbol_name="Euro",
        id=9,
        source_data_id=3,
        broker_id=8,
        basket_id=7,
        rows=4,
        date_from=1000,
        date_to=2000,
        decimals=5,
        bar_time_type=kind,
        file_hash=123,
        source=1,
        remove_weekends=True,
        symbol_info=_instrument(),
    )


def _back(timeframe: str, kind: int = 2) -> ChartDef:
    return ChartDef.for_backtest(
        _info(kind),
        _instrument(),
        timeframe=timeframe,
        history_from=0,
        history_to=1709208000000,
        spread=2.5,
        session="London",
        timezone="UTC",
    )


def _assert_xml(actual: Element, expected: Element) -> None:
    assert actual.tag == expected.tag
    assert actual.attrib.keys() == expected.attrib.keys()
    for name, value in expected.attrib.items():
        if name in _FLOAT_ATTRIBUTES:
            first, second = float(actual.attrib[name]), float(value)
            assert math.isnan(first) if math.isnan(second) else first == second
        else:
            assert actual.attrib[name] == value
    assert len(actual) == len(expected)
    for first_child, second_child in zip(actual, expected, strict=True):
        _assert_xml(first_child, second_child)


def _expected(payload: str) -> Element:
    return fromstring(base64.b64decode(payload))


def _state(name: str) -> ChartDef:  # noqa: PLR0911 - independent donor scenarios
    if name == "default":
        return ChartDef()
    if name.startswith("session_"):
        return _back("H7")
    if name == "recovered":
        element = Element(
            "ChartDef",
            {
                "symbol": "EURUSD",
                "connectionName": "broker",
                "spread": "bad",
                "historyFrom": "1_0",
                "type": "garbage",
            },
        )
        return ChartDef.from_xml(element, timezone="UTC")
    if name == "live" or name.startswith("xml"):
        live = ChartDef.for_live(
            _info(),
            _instrument(),
            timeframe="H7",
            backload_type=3,
            backload_number=50,
            session="London",
        )
        if name == "live":
            return live
        element = live.to_xml()
        element.set("type", name[-1])
        return ChartDef.from_xml(element, timezone="UTC")
    back = _back("D2", 1)
    if name == "backtest":
        return back
    back.registered, back.real_spread, back.min_distance = True, True, 3.0
    if name == "clone_zero":
        return back.clone(history_from=0, history_to=-1)
    if name == "clone_range":
        return back.clone(history_from=1000, history_to=2000)
    if name == "clone_symbol":
        return back.clone(symbol="GBPUSD")
    return back.copy_for_backtest(
        _info(1),
        _instrument(),
        timezone="UTC",
        timeframe="H7" if name == "copy_tf" else None,
    )


@pytest.mark.parametrize(
    "vector",
    _VECTORS,
    ids=lambda v: str(v.get("case", v.get("input", v.get("target", "reference")))),
)
def test_recovered_java_contracts(vector: dict[str, Any]) -> None:
    if vector["kind"] == "compare":
        first, second = (
            _back(vector["target"], vector["bar_type"]),
            _back(vector["source"], vector["bar_type"]),
        )
        assert first.can_be_computed_from(second) == vector["compute"]
        assert first.is_smaller_than(second) == vector["smaller"]
    elif vector["kind"] == "chart":
        chart = _state(vector["case"])
        _assert_xml(chart.to_xml(), _expected(vector["xml"]))
        assert chart.connection_hash == vector["connection_hash"]
        assert chart.symbol_hash == vector["symbol_hash"]
        assert chart.get_spread() == vector["spread"]
        assert chart.min_distance == vector["min_distance"]
        if vector["instrument"] is not None:
            assert chart.instrument_info is not None
            _assert_xml(chart.instrument_info.to_xml(), _expected(vector["instrument"]))
        else:
            assert chart.instrument_info is None
        name = vector["case"]
        session_name = (
            "London"
            if name in ("session_none", "session_empty", "session_windows")
            else None
        )
        elements: list[SessionWindow] | None = None
        if name == "session_empty":
            elements = []
        elif name == "session_windows":
            elements = [
                SessionWindow(
                    day_from="Mon",
                    start_time="09:30",
                    day_to="Fri",
                    end_time="17:00",
                    eod=True,
                ),
                SessionWindow(
                    day_from="Sun", start_time="00:00", day_to="Sun", end_time="00:00"
                ),
            ]
        if vector["hash"] is not None:
            assert (
                chart.get_charts_hash(
                    session_name=session_name, session_elements=elements
                )
                == vector["hash"]
            )
    elif vector["kind"] == "data":
        info = _info()
        if vector["case"] == "clone":
            info = info.clone()
        _assert_xml(info.to_xml(), _expected(vector["xml"]))
        if "text" in vector:
            assert str(info) == vector["text"]
    else:
        instrument = InstrumentInfo.from_xml(
            Element("InstrumentInfo", {"tickSize": vector["input"]})
        )
        _assert_xml(instrument.to_xml(), _expected(vector["xml"]))


def test_java_strings_and_cross_process_identity() -> None:
    for line in (
        (_FIXTURES / "vectors.jsonl").read_text(encoding="utf-8-sig").splitlines()
    ):
        record = json.loads(line)
        if record["kind"] == "string":
            chart = ChartDef(record["input"], connection_name=record["input"])
            assert chart.symbol_hash == chart.connection_hash == record["value"]
    code = "from app.core.data.charts import ChartDef; import json; c=ChartDef('EURUSD',connection_name='broker'); print(json.dumps([c.connection_hash,c.symbol_hash]))"
    values = [
        subprocess.check_output(
            [sys.executable, "-c", code],
            text=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
            timeout=30,
        )
        for seed in ("1", "42")
    ]
    assert json.loads(values[0]) == json.loads(values[1])


def test_clone_detaches_every_nested_owner_and_preserves_cached_hashes() -> None:
    original = _back("H7")
    original.symbol = (
        "changed-without-rehash"  # Java setSymbol does not update its hash.
    )
    cloned = original.clone(history_from=0, history_to=0)
    assert cloned.symbol_hash == original.symbol_hash
    assert cloned.history_from == original.history_from
    assert cloned.data_info is not None and original.data_info is not None
    assert cloned.instrument_info is not None and original.instrument_info is not None
    assert (
        cloned.data_info.symbol_info is not None
        and original.data_info.symbol_info is not None
    )
    cloned.data_info.symbol_info.tick_size = 10.0
    cloned.instrument_info.min_distance = 99.0
    assert original.data_info.symbol_info.tick_size == 0.00001
    assert original.instrument_info.min_distance == 7.0
    assert cloned.data_info.id == 0 and cloned.data_info.source_data_id == 0
    assert cloned.clone(symbol="GBPUSD").symbol_hash == ChartDef("GBPUSD").symbol_hash


def test_nested_xml_and_dict_roundtrips() -> None:
    chart = _back("H7")
    restored = ChartDef.from_dict(chart.to_dict())
    assert restored == chart
    assert TypeAdapter(ChartDef).validate_python(chart.to_dict()) == chart
    assert TypeAdapter(DataInfo).validate_python(_info().to_dict()) == _info()
    parsed = ChartDef.from_xml(chart.to_xml(), timezone="UTC")
    assert parsed.data_info is not None and parsed.data_info.symbol_info is not None
    assert parsed.data_info.symbol_info.min_distance == 7.0
    assert (
        parsed.instrument_info is None
    )  # Donor setFromXML does not resolve this cache.
    assert DataInfo.from_dict(_info().to_dict()) == _info()
    assert _info().to_chart_def().data_info is not None
    assert DataInfo(connection="broker").source == 0
    assert DataInfo().date_from_str is None
    with pytest.raises(ValueError):
        DataInfo(id="source:EURUSD:M1", source="provider").to_xml()


def test_identity_guards_and_failures() -> None:
    chart = _back("H7")
    assert not chart.can_be_computed_from(ChartDef("different", "M1"))
    assert not chart.is_smaller_than(ChartDef("EURUSD", "D1", connection_name="other"))
    with pytest.raises(ValueError):
        ChartDef("EURUSD").get_charts_hash(session_name=None, session_elements=None)
    with pytest.raises(ValueError):
        ChartDef().copy_for_backtest(_info(), None, timezone="UTC")
    with pytest.raises(ValueError):
        ChartDef().timeframe_seconds()
    chart.data_info = DataInfo(bar_time_type=0)
    with pytest.raises(DomainError):
        chart.can_be_computed_from(chart)
    assert not ChartDef().is_symbol_recognized()
    assert ChartDef("").is_symbol_recognized()
    for element in (Element("Wrong"), Element("ChartDef")):
        with pytest.raises(ValueError):
            ChartDef.from_xml(element, timezone="UTC")
    with pytest.raises(ValueError):
        InstrumentInfo.from_xml(Element("Wrong"))
    with pytest.raises(ValueError):
        DataInfo.from_xml(Element("Wrong"))
    with pytest.raises(ValueError):
        chart.copy_for_backtest(DataInfo(symbol="other"), None, timezone="UTC")
    with pytest.raises(OverflowError):
        ChartDef.for_backtest(
            _info(),
            None,
            timeframe="M1",
            history_from=0,
            history_to=2**63 - 1,
            spread=0.0,
            session="No Session",
            timezone="UTC",
        )


def test_timezone_snapshot_changes_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        chart = ChartDef.for_backtest(
            _info(),
            _instrument(),
            timeframe="H1",
            history_from=0,
            history_to=1710064800000,
            spread=2.0,
            session="London",
            timezone="America/New_York",
        )
        assert chart.history_to == 1710129599999  # DST transition day, 2024-03-10.
        first = chart.get_charts_hash(session_name="London", session_elements=[])
        second = chart.get_charts_hash(
            session_name="London", session_elements=[SessionWindow()]
        )
        assert first != second
        chart.data_info.file_hash += 1  # type: ignore[union-attr]
        assert (
            chart.get_charts_hash(session_name="London", session_elements=[]) != first
        )
        chart.clone().to_xml()
        InstrumentInfo.from_xml(Element("InstrumentInfo")).clone()
        DataInfo.from_xml(Element("DataInfo"))
    shutdown_logging()
    for label in (
        "FR-data-chart-initialize",
        "FR-data-chart-identity",
        "FR-data-chart-clone",
        "FR-data-contract-xml",
        "FR-data-instrument-xml",
        "FR-data-instrument-clone",
    ):
        assert label in caplog.text
