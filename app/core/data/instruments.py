"""Donor InstrumentInfo metadata embedded in chart and dataset contracts.

Description:
    Owns datalib/InstrumentInfo.java fields, getXML/setFromXML and clone.
    Broker SymbolInfo remains its separate existing broker contract. This value
    object adds no economics engine or manager; S16 consumers reuse this owner.
    Shared XMLUtil numeric/attribute helpers serve only the three metadata schemas
    here, DataInfo and ChartDef, avoiding circular runtime type references.
Purpose:
    FEAT-DATA-CHART-METADATA: Complete nested donor chart metadata custody.
Key Capabilities:
    - FR-data-instrument-xml: DEBUG records nested XML and numeric recovery;
      tests verify defaults, attributes, recovery, and log records.
    - FR-data-instrument-clone: DEBUG records detached metadata cloning;
      tests verify all donor fields, including minDistance and order sizing.
Python API Usage:
    InstrumentInfo.from_xml(element).clone()
CLI Usage:
    uv run pytest tests/core/data/test_chart_contracts.py --no-cov
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, fields, replace
from typing import Any
from xml.etree.ElementTree import Element

from app.core.host.logging import get_logger

logger = get_logger(__name__)
_XML_FIELDS = {
    "connection": "connection",
    "instrument": "instrument",
    "description": "description",
    "tickSize": "tick_size",
    "tickStep": "tick_step",
    "minDistance": "min_distance",
    "tickValueInMoney": "tick_value_in_money",
    "filename": "filename",
    "dateFrom": "date_from",
    "dateTo": "date_to",
    "rows": "rows",
    "totalDays": "total_days",
    "defaultSpread": "default_spread",
    "defaultSlippage": "default_slippage",
    "decimals": "decimals",
    "timeframe": "timeframe",
    "commissions": "commissions",
    "pointValue": "point_value",
    "dataType": "data_type",
    "recognizedFromOrders": "recognized_from_orders",
    "alias": "alias",
    "exchange": "exchange",
    "country": "country",
    "sector": "sector",
    "swap": "swap",
    "orderSizeMultiplier": "order_size_multiplier",
    "orderSizeStep": "order_size_step",
    "broker": "broker",
}


def _scalar_xml(tag: str, values: dict[str, Any], names: dict[str, str]) -> Element:
    """Map XMLUtil.trySetAttr for the three donor metadata contracts only."""
    attributes: dict[str, str] = {}
    for xml_name, field_name in names.items():
        value = values[field_name]
        if value is None:
            continue
        if isinstance(value, bool):
            text = str(value).lower()
        elif isinstance(value, float) and not math.isfinite(value):
            text = (
                "NaN"
                if math.isnan(value)
                else ("Infinity" if value > 0 else "-Infinity")
            )
        else:
            text = str(value)
        attributes[xml_name] = text
    logger.debug("FR-data-contract-xml: encoded donor metadata")
    return Element(tag, attributes)


def _xml_number(raw: str | None, default: float, bits: int) -> int | float:
    """Parse XMLUtil's Java integer/Double lexical forms before caller recovery."""
    if raw is None:
        raise ValueError("Missing number")
    if isinstance(default, int):
        if not re.fullmatch(r"[+-]?\d+", raw) or any(
            ord(c) > (1 << 16) - 1 for c in raw
        ):
            raise ValueError("Invalid Java integer")
        number = int(raw)
        if not -(1 << (bits - 1)) <= number < (1 << (bits - 1)):
            raise ValueError("Integer overflow")
        return number
    text = raw.strip("".join(chr(code) for code in range(33)))
    if text.lstrip("+-") in ("NaN", "Infinity"):
        return float(text)
    pattern = (
        r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|"
        r"0[xX](?:[0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?|\.[0-9a-fA-F]+)"
        r"[pP][+-]?[0-9]+)[fFdD]?"
    )
    if not re.fullmatch(pattern, text):
        raise ValueError("Invalid Java double")
    text = text.rstrip("fFdD")
    if "x" not in text.lower():
        return float(text)
    try:
        return float.fromhex(text)
    except OverflowError:
        return -math.inf if text.startswith("-") else math.inf


def _xml_values(
    element: Element,
    names: dict[str, str],
    defaults: dict[str, Any],
    fallbacks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map XMLUtil recovery/defaults, logging rejected attributes without values.

    Existing DataInfo host string fields use empty strings for absent nullable
    Java strings; ChartDef/InstrumentInfo represent null directly. These local
    helpers serve only the three explicit metadata schemas, not a framework.
    """
    values: dict[str, Any] = {}
    wide = {
        "history_from",
        "history_to",
        "loaded_history_from",
        "backload_number",
        "date_from",
        "date_to",
        "file_hash",
    }
    for xml_name, field_name in names.items():
        raw, default = element.get(xml_name), defaults[field_name]
        if isinstance(default, bool):
            values[field_name] = raw is not None and raw.lower() == "true"
        elif isinstance(default, (int, float)):
            fallback = (fallbacks or {}).get(
                field_name, -1 if isinstance(default, int) else -1.0
            )
            try:
                values[field_name] = _xml_number(
                    raw, default, 64 if field_name in wide else 32
                )
            except ValueError:
                logger.debug("FR-data-contract-xml: numeric recovery for %s", xml_name)
                values[field_name] = fallback
        else:
            values[field_name] = raw if raw is not None else default
    logger.debug("FR-data-contract-xml: decoded donor metadata")
    return values


@dataclass
class InstrumentInfo:
    """Canonical donor metadata; interned Java strings need no Python adaptation."""

    connection: str | None = None
    instrument: str | None = None
    broker: int = -1
    description: str | None = None
    tick_size: float = 0.0
    tick_step: float = 0.0
    tick_value_in_money: float = 0.0
    filename: str | None = None
    date_from: int = 0
    date_to: int = 0
    rows: int = 0
    total_days: int = 0
    default_spread: float = 0.0
    default_slippage: float = 0.0
    min_distance: float = 0.0
    decimals: int = 0
    timeframe: str | None = None
    point_value: float = 0.0
    data_type: int = 0
    recognized_from_orders: bool = False
    alias: str | None = None
    exchange: str | None = None
    country: str | None = None
    sector: str | None = None
    commissions: str | None = None
    swap: str | None = None
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0

    def to_xml(self) -> Element:
        """Match getXML, including literal null commissions/swap attributes."""
        values = asdict(self)
        for field_name in ("commissions", "swap"):
            if values[field_name] is None:
                values[field_name] = "null"
        logger.debug("FR-data-instrument-xml: serializing InstrumentInfo")
        return _scalar_xml("InstrumentInfo", values, _XML_FIELDS)

    @classmethod
    def from_xml(cls, element: Element) -> InstrumentInfo:
        """Match setFromXML's per-field defaults and numeric recovery."""
        if element.tag != "InstrumentInfo":
            raise ValueError("Expected InstrumentInfo XML")
        fallbacks = {
            "min_distance": 0.0,
            "default_slippage": 0.0,
            "order_size_multiplier": 1.0,
            "order_size_step": 0.0,
            "broker": -1,
        }
        logger.debug("FR-data-instrument-xml: parsing InstrumentInfo")
        return cls(**_xml_values(element, _XML_FIELDS, asdict(cls()), fallbacks))

    def clone(self) -> InstrumentInfo:
        """Match the donor's complete independent scalar copy."""
        logger.debug("FR-data-instrument-clone: cloned InstrumentInfo")
        return replace(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> InstrumentInfo:
        """Restore the Python JSON representation without a second field owner."""
        logger.debug("FR-data-instrument-xml: restoring metadata dictionary")
        return cls(
            **{
                field.name: values[field.name]
                for field in fields(cls)
                if field.name in values
            }
        )
