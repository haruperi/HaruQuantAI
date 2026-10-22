"""Persist financial instrument definitions and grouped specifications.

Description:
    Lists, adds, mass-edits, clones and deletes instruments through
    HostPersistence. Table columns live in the instruments table; contract
    size, pip size and swap settings live in grouped JSON columns.
    Private storage helpers pack flat fields into groups and unpack reads.
    Partial edits retain unrelated group members. InstrumentsCLI maps console
    arguments onto these calls.
Purpose:
    FEAT-DATAMGR-INSTRUMENTS: Authoritative financial instrument catalog.
Key Capabilities:
    - FR-DATAMGR-INSTR-LIST: Catalog [Instruments.instruments()] (INFO).
    - FR-DATAMGR-INSTR-ADD: Create [Instruments.add_instrument()] (INFO).
    - FR-DATAMGR-INSTR-MASS-EDIT: Edit [Instruments.mass_edit_instruments()] (INFO).
    - FR-DATAMGR-INSTR-CLONE: Copy [Instruments.clone_instrument()] (INFO).
    - FR-DATAMGR-INSTR-DELETE: Remove [Instruments.delete_instruments()] (INFO).
    - FR-DATAMGR-INSTR-REFRESH: Replace [Instruments.refresh_instruments()] (INFO).
Python API Usage:
    from app.workspace.data_manager.instruments import Instruments
    records = Instruments().instruments()
CLI Usage:
    uv run python -m app.workspace.data_manager.instruments
    uv run python -m app.cli instrument list
    uv run python -m app.cli instrument add instrument=EURUSD ticksize=0.00001
    uv run python -m app.cli instrument edit instrument=EURUSD swapLong=-2
    uv run python -m app.cli instrument delete instruments=EURUSD,GBPUSD
    uv run python -m app.cli instrument refresh EURUSD GBPUSD
"""

from __future__ import annotations

import asyncio
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.services.include.contracts import _COMMISSION_NOT_RETRIEVED

if TYPE_CHECKING:
    from app.services.include.trading import Trading

__all__ = ["Instruments", "InstrumentsCLI"]

logger = get_logger(__name__)
_TABLE = "datamgr_instruments"
_ROOT_AND_LEAF_PARTS = 2


_VERSION = 2
_COMMISSION_VERSION = 2
_COMMISSION_MAX_RULES = 256
_COMMISSION_MAX_TIERS = 1024
_GROUPS = (
    "swap",
    "margin",
    "volume",
    "spread",
    "trade",
    "price",
    "contract",
    "option",
    "sessions",
    "commissions",
    "order_size",
    "symbol_state",
    "specification_meta",
)
_SCALARS = (
    "id",
    "symbol",
    "connection",
    "broker_id",
    "description",
    "data_type",
    "alias",
    "exchange",
    "country",
    "sector",
    "cot",
    "created_at_utc",
    "updated_at_utc",
)
_BOOLEANS = {"spread_float", "margin_hedged_use_leg", "custom", "select", "visible"}
_DAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
_FIELDS: dict[str, dict[str, str]] = {
    "swap": {"swap_long": "long", "swap_short": "short", "swap_settings": "settings"},
    "margin": {
        "margin_initial": "initial",
        "margin_maintenance": "maintenance",
        "margin_hedged": "hedged",
        "margin_rate": "configured_rate",
        "margin_hedged_use_leg": "hedged_use_leg",
        "margin_long": "long",
        "margin_short": "short",
        "margin_limit": "limit",
        "margin_stop": "stop",
        "margin_stop_limit": "stop_limit",
    },
    "volume": {
        "min_volume": "min",
        "max_volume": "max",
        "lot_step": "step",
        "volume_limit": "limit",
        "volume": "current",
        "volumehigh": "high",
        "volumelow": "low",
        "volume_real": "real",
        "volumehigh_real": "real_high",
        "volumelow_real": "real_low",
    },
    "spread": {
        "spread": "points",
        "spread_float": "floating",
        "default_spread": "default",
        "default_slippage": "slippage",
    },
    "trade": {
        "trade_stops_level": "stops_level",
        "trade_freeze_level": "freeze_level",
        "min_distance": "min_distance",
    },
    "price": {
        "decimals": "digits",
        "tick_size": "tick_size",
        "tick_step": "tick_step",
        "point": "point",
        "tick_value_in_money": "tick_value",
        "trade_tick_value_profit": "tick_value_profit",
        "trade_tick_value_loss": "tick_value_loss",
        "bid": "bid",
        "ask": "ask",
        "last": "last",
        "bidhigh": "bid_high",
        "bidlow": "bid_low",
        "askhigh": "ask_high",
        "asklow": "ask_low",
        "lasthigh": "last_high",
        "lastlow": "last_low",
        "time": "time",
        "ticks_bookdepth": "book_depth",
        "price_change": "change",
        "price_volatility": "volatility",
        "price_sensitivity": "sensitivity",
    },
    "contract": {
        "contract_size": "size",
        "point_value": "point_value",
        "pip_size": "pip_size",
        "currency_base": "currency_base",
        "currency_profit": "currency_profit",
        "currency_margin": "currency_margin",
        "trade_accrued_interest": "accrued_interest",
        "trade_face_value": "face_value",
        "trade_liquidity_rate": "liquidity_rate",
        "basis": "basis",
        "formula": "formula",
        "isin": "isin",
        "page": "page",
        "bank": "bank",
        "category": "category",
        "path": "path",
        "start_time": "start_time",
        "expiration_time": "expiration_time",
    },
    "option": {
        "option_strike": "strike",
        "price_theoretical": "theoretical",
        **{
            f"price_greeks_{g}": g
            for g in ("delta", "theta", "gamma", "vega", "rho", "omega")
        },
    },
    "order_size": {"order_size_multiplier": "multiplier", "order_size_step": "step"},
    "symbol_state": {"custom": "custom", "select": "selected", "visible": "visible"},
}
_ENUMS: dict[str, tuple[str, str, dict[int, str]]] = {
    "swap_mode": (
        "swap",
        "mode",
        dict(
            enumerate(
                (
                    "Disabled",
                    "Points",
                    "Symbol currency",
                    "Margin currency",
                    "Account currency",
                    "Interest current",
                    "Interest open",
                    "Reopen current",
                    "Reopen bid",
                )
            )
        ),
    ),
    "chart_mode": ("price", "chart_mode", {0: "Bid", 1: "Last"}),
    "trade_mode": (
        "trade",
        "mode",
        dict(
            enumerate(
                ("Disabled", "Long only", "Short only", "Close only", "Full access")
            )
        ),
    ),
    "trade_exemode": (
        "trade",
        "execution",
        dict(enumerate(("Request", "Instant", "Market", "Exchange"))),
    ),
    "trade_calc_mode": (
        "trade",
        "calculation",
        {
            0: "Forex",
            1: "Forex no leverage",
            2: "Futures",
            3: "CFD",
            4: "CFD index",
            5: "CFD leverage",
            32: "Exchange stocks",
            33: "Exchange futures",
            34: "Exchange futures FORTS",
            35: "Exchange bonds",
            36: "Exchange stocks MOEX",
            37: "Exchange bonds MOEX",
            64: "Collateral",
        },
    ),
    "order_gtc_mode": (
        "trade",
        "gtc",
        {0: "Good till cancelled", 1: "Daily", 2: "Daily excluding stops"},
    ),
    "option_mode": ("option", "style", {0: "European", 1: "American"}),
    "option_right": ("option", "right", {0: "Call", 1: "Put"}),
    "swap_3day_day": ("swap", "day3x", dict(enumerate(_DAYS))),
}
_FLAGS = {
    "filling_mode": (
        "filling",
        {1: "Fill or Kill", 2: "Immediate or Cancel", 4: "Book or Cancel"},
    ),
    "expiration_mode": (
        "expiration",
        {1: "Good till cancelled", 2: "Day", 4: "Specified", 8: "Specified day"},
    ),
    "order_mode": (
        "orders",
        {
            1: "Market",
            2: "Limit",
            4: "Stop",
            8: "Stop limit",
            16: "Stop Loss",
            32: "Take Profit",
            64: "Close By",
        },
    ),
    "trade_fill_flags": (
        "fill_policies",
        {1: "Fill or Kill", 2: "Immediate or Cancel", 4: "Return", 8: "Book or Cancel"},
    ),
    "trade_time_flags": (
        "time_policies",
        {1: "Good till cancelled", 2: "Day", 4: "Specified", 8: "Specified day"},
    ),
}
# These are the pre-task public flat columns/defaults, plus the three former
# extension fields. Storage groups never become a second public API.
_OMITTED = {
    "spread",
    "margin_long",
    "margin_short",
    "margin_limit",
    "margin_stop",
    "margin_stop_limit",
    "point",
    "path",
    "swap_rollover3days",
    "trade_fill_flags",
    "trade_time_flags",
}
_TEXT = {
    "basis",
    "category",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "bank",
    "formula",
    "isin",
    "page",
}
_STATS = (
    "deals",
    "buy_orders",
    "sell_orders",
    "volume",
    "turnover",
    "interest",
    "buy_orders_volume",
    "sell_orders_volume",
    "open",
    "close",
    "aw",
    "price_settlement",
    "price_limit_min",
    "price_limit_max",
)
_FLAT_DEFAULTS: dict[str, Any] = {
    **{
        old: "" if old in _TEXT else 0
        for mapping in _FIELDS.values()
        for old in mapping
        if old not in _OMITTED
    },
    **dict.fromkeys(_ENUMS, 0),
    **{old: 0 for old in _FLAGS if old not in _OMITTED},
    **{f"session_{key}": 0 for key in _STATS},
    "symbol": "",
    "connection": "",
    "broker_id": 0,
    "description": "",
    "data_type": "Forex",
    "alias": "",
    "exchange": "",
    "country": "",
    "sector": "",
    "cot": None,
    "created_at_utc": "",
    "updated_at_utc": "",
    "tick_size": 0.00001,
    "tick_step": 0.00001,
    "tick_value_in_money": 10.0,
    "point_value": 100000.0,
    "decimals": 5,
    "default_spread": 0.0001,
    "min_volume": 0.01,
    "max_volume": 100.0,
    "lot_step": 0.01,
    "margin_rate": 0.05,
    "swap_3day_day": 3,
    "commissions": _COMMISSION_NOT_RETRIEVED,
    "order_size_multiplier": 1.0,
    "contract_size": None,
    "pip_size": None,
    "swap_settings": None,
}


def _commission_document(value: str) -> dict[str, Any] | None:
    parsed = json.loads(value)
    if not isinstance(parsed, dict) or parsed.get("version") != _COMMISSION_VERSION:
        return parsed if isinstance(parsed, dict) else None
    source_known = parsed.get("source") == "mt5" or (
        parsed.get("source") == "unknown" and parsed.get("status") == "not_retrieved"
    )
    if not source_known or parsed.get("status") not in (
        "available",
        "not_retrieved",
        "unavailable",
    ):
        raise ValueError("Invalid broker commission status.")
    _validate_commission_settings(parsed.get("settings"))
    rules = parsed.get("rules")
    if parsed["status"] != "available":
        if rules is not None:
            raise ValueError("Unavailable commissions cannot contain rules.")
        return parsed
    if not isinstance(rules, list) or len(rules) > _COMMISSION_MAX_RULES:
        raise ValueError("Invalid broker commission rules.")
    total = 0
    for rule in rules:
        tiers = _commission_tiers(rule)
        total += len(tiers)
        if total > _COMMISSION_MAX_TIERS:
            raise ValueError("Commission tier count exceeds limit.")
        for tier in tiers:
            _validate_commission_tier(tier)
    return parsed


def _validate_commission_settings(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict) or not isinstance(value.get("model"), str):
        raise TypeError("Invalid configured commission model.")
    rate = value.get("value")
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
    ):
        raise ValueError("Invalid configured commission value.")


def _commission_tiers(rule: Any) -> list[Any]:
    if not isinstance(rule, dict) or any(
        not isinstance(rule.get(k), str)
        for k in ("currency", "range", "charge", "entry", "direction", "profit")
    ):
        raise ValueError("Invalid commission rule meanings.")
    tiers = rule.get("tiers")
    if not isinstance(tiers, list):
        raise TypeError("Invalid commission tiers.")
    return tiers


def _validate_commission_tier(tier: Any) -> None:
    if not isinstance(tier, dict) or any(
        not isinstance(tier.get(k), str)
        for k in ("mode", "volume_type", "currency", "effective_currency")
    ):
        raise ValueError("Invalid commission tier meanings.")
    for key in ("value", "min", "max", "from", "to"):
        value = tier.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("Invalid commission tier quantity.")


def _merge_commissions(current: str, incoming: str) -> str:
    previous = _commission_document(current)
    updated = _commission_document(incoming)
    if not updated:
        return incoming
    if (
        updated.get("version") == _COMMISSION_VERSION
        and "settings" not in updated
        and previous
        and "settings" in previous
    ):
        updated["settings"] = previous["settings"]
    elif (
        updated.get("version") == 1
        and previous
        and previous.get("version") == _COMMISSION_VERSION
    ):
        previous["settings"] = updated.get("settings")
        updated = previous
    else:
        return incoming
    return json.dumps(updated, allow_nan=False)


def _validate_json(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Instrument quantities must be finite.")
    json.dumps(value, allow_nan=False)


def _group_legacy(data: Mapping[str, Any]) -> dict[str, Any]:
    """Pack flat column values without changing their public representation."""
    result: dict[str, Any] = {group: {} for group in _GROUPS}
    result.update({k: v for k, v in data.items() if k in _SCALARS})
    # New scalar defaults belong to the schema, not to guessed broker data.
    for key in _SCALARS:
        if key != "id" and key not in result:
            result[key] = _FLAT_DEFAULTS.get(key)
    consumed = set(_SCALARS)
    for group, fields in _FIELDS.items():
        for flat, member in fields.items():
            if flat in data:
                result[group][member] = (
                    bool(data[flat])
                    if flat in _BOOLEANS and data[flat] in (0, 1)
                    else data[flat]
                )
                consumed.add(flat)
    unknown = _store_modes(data, result, consumed)
    result["sessions"] = {
        k.removeprefix("session_"): v
        for k, v in data.items()
        if k.startswith("session_")
    }
    consumed.update(f"session_{key}" for key in result["sessions"])
    if "commissions" in data:
        document = _commission_document(data["commissions"])
        result["commissions"] = (
            document
            if document and document.get("version") == _COMMISSION_VERSION
            else {"value": data["commissions"]}
        )
        consumed.add("commissions")
    result["specification_meta"] = {
        "version": _VERSION,
        "unknown_values": unknown,
        "unmapped": {k: v for k, v in data.items() if k not in consumed},
    }
    _validate_json(result)
    return result


def _store_modes(
    data: Mapping[str, Any], result: dict[str, Any], consumed: set[str]
) -> dict[str, Any]:
    unknown: dict[str, Any] = {}
    for flat, (group, key, meanings) in _ENUMS.items():
        if flat in data:
            value = data[flat]
            result[group][key] = meanings.get(value)
            consumed.add(flat)
            if value not in meanings:
                unknown[flat] = value
    for flat, (key, meanings) in _FLAGS.items():
        if flat not in data:
            continue
        bits = data[flat]
        consumed.add(flat)
        if not isinstance(bits, int) or bits < 0 or bits & ~sum(meanings):
            result["trade"][key] = None
            unknown[flat] = bits
        else:
            result["trade"][key] = [
                label for bit, label in meanings.items() if bits & bit
            ]
    return unknown


def _encode(groups: Mapping[str, Any]) -> dict[str, Any]:
    result = {k: v for k, v in groups.items() if k in _SCALARS}
    for key in _GROUPS:
        value = groups[key]
        if not isinstance(value, dict):
            raise TypeError("Instrument storage groups must be objects.")
        _validate_json(value)
        result[key] = json.dumps(value, allow_nan=False)
    return result


def _decode(row: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for key in _GROUPS:
        value = result[key]
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict):
            raise TypeError("Instrument storage groups must be objects.")
        _validate_json(value)
        result[key] = value
    if result["specification_meta"].get("version") != _VERSION:
        raise ValueError("Unsupported instrument storage version.")
    return result


def _pack(flat: Mapping[str, Any], *, allow_unknown: bool = False) -> dict[str, Any]:
    invalid = set(flat) - set(_FLAT_DEFAULTS) - {"id"}
    if invalid and not allow_unknown:
        raise ValueError("Unsupported instrument fields: " + ", ".join(sorted(invalid)))
    for name, value in flat.items():
        if name == "swap_settings":
            if value is not None and not isinstance(value, dict):
                raise TypeError("Swap settings must be an object or null.")
        elif isinstance(value, (dict, list)):
            raise TypeError("Public instrument fields must retain their flat types.")
    if "commissions" in flat:
        _commission_document(flat["commissions"])
    return _encode(_group_legacy({**_FLAT_DEFAULTS, **flat}))


def _unpack(row: Mapping[str, Any]) -> dict[str, Any]:
    groups = _decode(row)
    flat = dict(_FLAT_DEFAULTS)
    flat.update({k: v for k, v in groups.items() if k in _SCALARS})
    for group, fields in _FIELDS.items():
        for name, member in fields.items():
            if member in groups[group]:
                flat[name] = (
                    int(groups[group][member])
                    if name in _BOOLEANS and isinstance(groups[group][member], bool)
                    else groups[group][member]
                )
    for name, (group, member, meanings) in _ENUMS.items():
        if member in groups[group] and groups[group][member] is not None:
            inverse = {label: code for code, label in meanings.items()}
            flat[name] = inverse[groups[group][member]]
    _unpack_flags(groups, flat)
    flat.update({f"session_{key}": value for key, value in groups["sessions"].items()})
    if "value" in groups["commissions"]:
        flat["commissions"] = groups["commissions"]["value"]
    elif groups["commissions"].get("version") == _COMMISSION_VERSION:
        flat["commissions"] = json.dumps(groups["commissions"], allow_nan=False)
    flat.update(groups["specification_meta"].get("unknown_values", {}))
    flat.update(groups["specification_meta"].get("unmapped", {}))
    if "id" in flat:
        flat["id"] = str(flat["id"])
    return flat


def _unpack_flags(groups: Mapping[str, Any], flat: dict[str, Any]) -> None:
    for name, (member, meanings) in _FLAGS.items():
        labels = groups["trade"].get(member)
        if labels is None:
            continue
        if not isinstance(labels, list):
            raise TypeError("Stored instrument flags must be text arrays.")
        inverse = {label: bit for bit, label in meanings.items()}
        flat[name] = sum(inverse[label] for label in labels)


def _normalize_data_type(path: str) -> str:
    """Extract intermediate category from MT5 symbol path, dropping root and leaf."""
    parts = [p for p in path.replace("/", "\\").split("\\") if p]
    if len(parts) > _ROOT_AND_LEAF_PARTS:
        return "\\".join(parts[1:-1])
    if len(parts) == _ROOT_AND_LEAF_PARTS:
        return parts[0]
    return path


def _filter_matches(actual: Any, expected: Any) -> bool:
    if isinstance(actual, (int, float)) and isinstance(expected, str):
        try:
            return Decimal(str(actual)) == Decimal(expected)
        except InvalidOperation:
            return False
    if isinstance(actual, str) and isinstance(expected, (int, float)):
        return actual == str(expected)
    return bool(actual == expected)


class Instruments:
    """Own authoritative instrument records and grouped specifications."""

    def instruments(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List the existing flat specification view of grouped database records."""
        rows = HostPersistence.read_records(_TABLE, limit=0)
        logger.info("Instruments listed", extra={"fr_id": "FR-DATAMGR-INSTR-LIST"})
        result = [_unpack(row) for row in rows]
        if filters:
            known = set(_FLAT_DEFAULTS) | {"id"}
            known.update(key for row in result for key in row)
            if set(filters) - known:
                raise ValueError("Unsupported instrument filter.")
            result = [
                row
                for row in result
                if all(
                    _filter_matches(int(row[k]) if k == "id" else row.get(k), v)
                    for k, v in filters.items()
                )
            ]
        return result

    def add_instrument(self, instrument: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and create one grouped specification."""
        return self._insert(instrument)

    def _insert(
        self, instrument: Mapping[str, Any], *, allow_unknown: bool = False
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        row = _pack(instrument, allow_unknown=allow_unknown)
        row.pop("id", None)
        row.update(created_at_utc=now, updated_at_utc=now)
        HostPersistence.create_record(_TABLE, row)
        logger.info("Instrument added", extra={"fr_id": "FR-DATAMGR-INSTR-ADD"})
        return self._by_symbol(str(row["symbol"]))

    def mass_edit_instruments(
        self, instrument_ids: Sequence[str], updates: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Apply existing flat field updates while retaining group siblings."""
        if set(updates) - set(_FLAT_DEFAULTS) or set(updates) & {
            "id",
            "created_at_utc",
        }:
            raise ValueError("Unsupported instrument edit fields.")
        rows = [self._get(identifier) for identifier in dict.fromkeys(instrument_ids)]
        operations = []
        for row in rows:
            merged = {**row, **updates}
            if "commissions" in updates:
                merged["commissions"] = _merge_commissions(
                    row["commissions"], updates["commissions"]
                )
            merged["updated_at_utc"] = datetime.now(UTC).isoformat()
            encoded = _pack(merged, allow_unknown=True)
            encoded.pop("id", None)
            operations.append(
                {
                    "op": "update",
                    "table": _TABLE,
                    "key_columns": {"id": int(row["id"])},
                    "values": encoded,
                }
            )
        HostPersistence.apply_batch(operations)
        logger.info("Instruments edited", extra={"fr_id": "FR-DATAMGR-INSTR-MASS-EDIT"})
        return {
            "updated_count": len(rows),
            "instruments": [self._get(r["id"]) for r in rows],
        }

    def clone_instrument(self, source_id: str, new_symbol: str) -> dict[str, Any]:
        """Copy all groups with a fresh identity."""
        source = self._get(source_id)
        source.pop("id")
        source["symbol"] = new_symbol
        result = self._insert(source, allow_unknown=True)
        logger.info("Instrument cloned", extra={"fr_id": "FR-DATAMGR-INSTR-CLONE"})
        return result

    def delete_instruments(self, instrument_ids: Sequence[str]) -> dict[str, Any]:
        """Delete selected records atomically."""
        rows = [self._get(identifier) for identifier in dict.fromkeys(instrument_ids)]
        HostPersistence.apply_batch(
            [
                {"op": "delete", "table": _TABLE, "key_columns": {"id": int(r["id"])}}
                for r in rows
            ]
        )
        logger.info("Instruments deleted", extra={"fr_id": "FR-DATAMGR-INSTR-DELETE"})
        return {"deleted_count": len(rows)}

    async def refresh_instruments(
        self, trading: Trading, symbols: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Replace all or selected instruments from existing MT5 snapshots."""
        symbol = trading.symbol
        if symbols is None:
            names = list(dict.fromkeys(await symbol.SymbolsGet()))
        else:
            names = list(dict.fromkeys(symbols))
            if not names:
                raise ValueError("Select at least one symbol to refresh.")
        if not names:
            raise RuntimeError("MetaTrader returned no symbols; catalog unchanged.")
        now = datetime.now(UTC).isoformat()
        previous = {r["symbol"]: r["commissions"] for r in self.instruments()}
        incoming = []
        for name in names:
            if not await symbol.Name(name):
                raise LookupError("A MetaTrader symbol is unavailable; unchanged.")
            await symbol.RefreshRates()
            info = await symbol.SymbolInfo()
            data = asdict(info)
            flat = {key: data[key] for key in _FLAT_DEFAULTS if key in data}
            flat.update(
                symbol=name,
                data_type=_normalize_data_type(info.path),
                default_spread=info.spread * info.point,
                created_at_utc=now,
                updated_at_utc=now,
                contract_size=info.trade_contract_size,
                pip_size=info.point * (10 if info.digits in (3, 5) else 1),
                swap_settings=None,
            )
            flat["commissions"] = _merge_commissions(
                previous.get(name, _COMMISSION_NOT_RETRIEVED), info.commissions
            )
            incoming.append(_pack(flat))
        scope = None if symbols is None else set(names)
        existing = [
            r for r in self.instruments() if scope is None or r["symbol"] in scope
        ]
        operations: list[dict[str, Any]] = [
            {"op": "delete", "table": _TABLE, "key_columns": {"id": int(row["id"])}}
            for row in existing
        ]
        operations.extend(
            {"op": "create", "table": _TABLE, "values": row} for row in incoming
        )
        HostPersistence.apply_batch(operations)
        logger.info(
            "Instruments refreshed", extra={"fr_id": "FR-DATAMGR-INSTR-REFRESH"}
        )
        return {"deleted_count": len(existing), "inserted_count": len(incoming)}

    def _get(self, identifier: str) -> dict[str, Any]:
        rows = HostPersistence.read_records(_TABLE, {"id": int(identifier)}, limit=1)
        if not rows:
            raise LookupError("Instrument is no longer in the catalog.")
        return _unpack(rows[0])

    def _by_symbol(self, symbol: str) -> dict[str, Any]:
        return _unpack(
            HostPersistence.read_records(_TABLE, {"symbol": symbol}, limit=1)[0]
        )


_CLI_PARAMS: dict[str, tuple[str, type]] = {
    "description": ("description", str),
    "pointvalue": ("point_value", float),
    "ticksize": ("tick_size", float),
    "tickstep": ("tick_step", float),
    "defaultspread": ("default_spread", float),
    "defaultslippage": ("default_slippage", float),
    "datatype": ("data_type", str),
    "broker": ("broker_id", int),
    "minDistance": ("min_distance", float),
    "orderSizeMultiplier": ("order_size_multiplier", float),
    "orderSizeStep": ("order_size_step", float),
    "swapLong": ("swap_long", float),
    "swapShort": ("swap_short", float),
}


_TABLE_COLUMNS = (
    ("Instrument", "symbol", 14),
    ("Description", "description", 24),
    ("Broker profile", "broker_id", 14),
    ("Point value", "point_value", 11),
    ("Pip/Tick size", "tick_size", 13),
    ("Pip/Tick step", "tick_step", 13),
    ("Default spread", "default_spread", 14),
    ("Default slippage", "default_slippage", 16),
    ("Commissions", "commissions", 11),
    ("Swap", "swap", 14),
    ("Data type", "data_type", 24),
    ("Order size mult.", "order_size_multiplier", 16),
    ("Order size step", "order_size_step", 15),
)


def _cell(row: Mapping[str, Any], key: str) -> str:
    if key == "broker_id":
        return "Default" if row.get(key) in (-1, 0, None) else f"Broker {row.get(key)}"
    if key == "swap":
        return f"{row.get('swap_long', 0.0)} / {row.get('swap_short', 0.0)}"
    if key == "commissions":
        value = str(row.get(key, ""))
        if value.startswith("{"):
            parsed = json.loads(value)
            if isinstance(parsed, dict) and "settings" in parsed:
                return str(parsed["settings"].get("model", value))
        return value
    value = row.get(key, "")
    return "" if value is None else str(value)


async def _refresh(
    service: Instruments,
    symbols: Sequence[str] | None,
    factory: Callable[[], Trading],
) -> dict[str, Any]:
    trading = factory()
    await trading.start()
    try:
        await trading.wait_connected(timeout=30.0)
        return await service.refresh_instruments(trading, symbols)
    finally:
        await trading.close()


_CLI_ACTIONS = frozenset({"list", "add", "edit", "delete", "refresh"})


def _parse_cli_args(
    args: Sequence[str],
) -> tuple[str, dict[str, str], dict[str, Any], list[str]]:
    params = dict(a.split("=", 1) for a in args if "=" in a)
    action = params.pop("action", None)
    if action is None:
        positional = [a for a in args if "=" not in a]
        action = (
            positional[0].lower()
            if positional and positional[0].lower() in _CLI_ACTIONS
            else "list"
        )
    else:
        action = action.lower()
    values = {
        col: cast(params[name])
        for name, (col, cast) in _CLI_PARAMS.items()
        if name in params
    }
    raw_symbols = [
        s.strip()
        for a in args
        if "=" not in a and a != action
        for s in a.split(",")
        if s.strip()
    ]
    if "instruments" in params:
        raw_symbols.extend(
            s.strip() for s in params["instruments"].split(",") if s.strip()
        )
    return action, params, values, list(dict.fromkeys(raw_symbols))


class InstrumentsCLI:
    """Map `key=value` console arguments onto Instruments operations."""

    @staticmethod
    def format_instruments_table(rows: Sequence[Mapping[str, Any]]) -> str:
        """Format instruments into an ASCII table with the UI columns."""
        lines = [f"=== Instruments ({len(rows)} items) ==="]
        header = "| " + " | ".join(f"{h:<{w}}" for h, _, w in _TABLE_COLUMNS) + " |"
        lines.append(header)
        lines.append("|-" + "-|-".join("-" * w for _, _, w in _TABLE_COLUMNS) + "-|")
        for row in rows:
            cells = [
                _cell(row, key)[: w - 2] + ".."
                if len(_cell(row, key)) > w
                else _cell(row, key)
                for _, key, w in _TABLE_COLUMNS
            ]
            lines.append(
                "| "
                + " | ".join(
                    f"{c:<{w}}"
                    for c, (_, _, w) in zip(cells, _TABLE_COLUMNS, strict=True)
                )
                + " |"
            )
        return "\n".join(lines)

    @staticmethod
    def dispatch(
        args: Sequence[str],
        service: Instruments,
        trading_factory: Callable[[], Trading] | None = None,
    ) -> dict[str, Any]:
        """Run the list/add/edit/delete/refresh action described by `args`."""
        action, params, values, symbols = _parse_cli_args(args)
        result: dict[str, Any] = {"command": "instrument", "action": action}
        if action == "list":
            rows = service.instruments()
            result.update(
                count=len(rows),
                instruments=rows,
                rendered=InstrumentsCLI.format_instruments_table(rows),
            )
        elif action == "add":
            result["instrument"] = service.add_instrument(
                {"symbol": params["instrument"], **values}
            )
        elif action == "edit":
            result.update(
                service.mass_edit_instruments(
                    [InstrumentsCLI._id(service, params["instrument"])], values
                )
            )
        elif action == "delete":
            del_symbols = params["instruments"].split(",")
            result.update(
                service.delete_instruments(
                    [InstrumentsCLI._id(service, s) for s in del_symbols]
                )
            )
        elif action == "refresh":
            from app.workspace.data_manager.routes import _metatrader_trading

            res = asyncio.run(
                _refresh(
                    service,
                    symbols or None,
                    trading_factory or _metatrader_trading,
                )
            )
            result.update(res)
            result["rendered"] = (
                f"Refreshed {res.get('inserted_count', 0)} "
                "instrument(s) "
                f"from MetaTrader 5 (deleted {res.get('deleted_count', 0)})."
            )
        else:
            raise ValueError(f"Unsupported instrument action: '{action}'")
        return result

    @staticmethod
    def _id(service: Instruments, symbol: str) -> str:
        rows = service.instruments({"symbol": symbol})
        if not rows:
            raise LookupError(f"Instrument '{symbol}' not found.")
        return str(rows[0]["id"])


if __name__ == "__main__":
    logger.info("Configured instruments: %s", Instruments().instruments())
