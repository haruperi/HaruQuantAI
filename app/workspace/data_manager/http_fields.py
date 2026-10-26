"""Pure browser symbol field mapping shared by the Data Manager adapter."""

from __future__ import annotations

import json
import math
from typing import Any

from app.host.response import ErrorCode
from app.host.transport import TransportError

DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


def _json(value: Any) -> dict[str, Any]:
    return json.loads(value) if isinstance(value, str) else value or {}


def symbol_to_ui(row: dict[str, Any]) -> dict[str, Any]:
    """Translate the persisted nested specification into existing browser fields."""
    price, volume, spread, swap, margin, trade = (
        _json(row.get(key))
        for key in ("price", "volume", "spread", "swap", "margin", "trade")
    )
    rollover = str(swap.get("rollover3days", "Wednesday")).upper()
    return {
        "id": str(row["id"]),
        "symbol": row["name"],
        "description": row.get("description") or "",
        "broker_id": row.get("broker_id") or 0,
        "data_type": row.get("data_type") or "",
        "point_value": price.get("point_value")
        if price.get("point_value") is not None
        else price.get("contract_size", 100000),
        "tick_size": price.get("tick_size", 0.0001),
        "tick_step": price.get("tick_step", 0.00001),
        "contract_size": price.get("contract_size", 100000),
        "pip_size": price.get("pip_size")
        if price.get("pip_size") is not None
        else price.get("tick_size", 0.0001),
        "margin_rate": margin.get("rate", 0),
        "decimals": price.get("digits", 5),
        "tick_value_in_money": price.get("tick_value", 0),
        "min_volume": volume.get("min", 0.01),
        "max_volume": volume.get("max", 100),
        "lot_step": volume.get("step", 0.01),
        "default_spread": spread.get("default", 0),
        "default_slippage": spread.get("slippage", 0),
        "min_distance": trade.get("min_distance", 0),
        "order_size_multiplier": volume.get("min", 0.01),
        "order_size_step": volume.get("step", 0.01),
        "commissions": trade.get("commission_settings")
        or str(row.get("commission") or 0),
        "swap_long": swap.get("long", 0),
        "swap_short": swap.get("short", 0),
        "swap_3day_day": DAYS.index(rollover) if rollover in DAYS else 3,
        "swap_settings": swap.get("settings"),
    }


def symbol_updates(values: dict[str, Any]) -> dict[str, Any]:
    """Validate browser field values before invoking the symbol service."""
    numeric = {
        "broker_id",
        "point_value",
        "contract_size",
        "tick_size",
        "pip_size",
        "tick_step",
        "decimals",
        "tick_value_in_money",
        "min_volume",
        "max_volume",
        "lot_step",
        "margin_rate",
        "default_spread",
        "default_slippage",
        "min_distance",
        "order_size_multiplier",
        "order_size_step",
    }
    for key in numeric & values.keys():
        value = values[key]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise TransportError(ErrorCode.VALIDATION, f"Invalid numeric field: {key}")
    try:
        return _map_updates(values)
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise TransportError(
            ErrorCode.VALIDATION, "Invalid symbol field values"
        ) from error


def _map_updates(values: dict[str, Any]) -> dict[str, Any]:
    """Map explicitly supplied browser fields to service fields."""
    direct = {
        "description",
        "data_type",
        "broker_id",
        "default_spread",
        "min_distance",
        "order_size_multiplier",
        "order_size_step",
    }
    result = {key: value for key, value in values.items() if key in direct}
    nested = {
        "price": {
            "point_value": "point_value",
            "contract_size": "contract_size",
            "tick_size": "tick_size",
            "pip_size": "pip_size",
            "tick_step": "tick_step",
            "decimals": "digits",
            "tick_value_in_money": "tick_value",
        },
        "volume": {"min_volume": "min", "max_volume": "max", "lot_step": "step"},
        "margin": {"margin_rate": "rate"},
        "spread": {"default_slippage": "slippage"},
    }
    for section, keys in nested.items():
        data = {
            target: values[source]
            for source, target in keys.items()
            if source in values and values[source] is not None
        }
        if data:
            result[section] = data
    if "commissions" in values:
        commission = json.loads(values["commissions"])
        result["commission"] = float(
            commission
            if isinstance(commission, (float, int))
            else commission["settings"]["value"]
        )
        result["trade"] = {"commission_settings": values["commissions"]}
    if "swap_settings" in values:
        swap = values["swap_settings"]
        result["swap"] = {
            "settings": swap,
            "long": swap["long"] if swap["use"] else 0,
            "short": swap["short"] if swap["use"] else 0,
            "mode": swap["type"],
            "rollover3days": swap["tripleSwapOn"].capitalize(),
        }
    return result
