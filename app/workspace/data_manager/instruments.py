"""Persist financial instrument definitions and independent specifications.

Description:
    Lists and validates instrument metadata through HostPersistence. Adds,
    clones and selected-field edits commit relational rows and specification
    extensions atomically. Legacy missing economics remain unspecified.
Purpose:
    FEAT-DATAMGR-INSTRUMENTS: Authoritative financial instrument catalog.
Key Capabilities:
    - FR-DATAMGR-INSTR-LIST: Catalog [Instruments.instruments()] (INFO).
    - FR-DATAMGR-INSTR-ADD: Create [Instruments.add_instrument()] (INFO).
    - FR-DATAMGR-INSTR-MASS-EDIT: Edit [Instruments.mass_edit_instruments()] (INFO).
    - FR-DATAMGR-INSTR-CLONE: Copy [Instruments.clone_instrument()] (INFO).
Python API Usage:
    from app.workspace.data_manager.instruments import Instruments
    records = Instruments().instruments()
CLI Usage:
    uv run python -m app.workspace.data_manager.instruments
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

__all__ = ["Instruments"]

logger = get_logger(__name__)
_DEFAULTS: dict[str, Any] = {
    "connection": "",
    "broker_id": -1,
    "description": "",
    "tick_size": 0.00001,
    "tick_step": 0.00001,
    "tick_value_in_money": 10.0,
    "point_value": 100000.0,
    "decimals": 5,
    "default_spread": 0.0001,
    "default_slippage": 0.0,
    "min_volume": 0.01,
    "max_volume": 100.0,
    "lot_step": 0.01,
    "margin_rate": 0.05,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "swap_3day_day": 3,
    "commissions": "0.0",
    "data_type": "Forex",
    "alias": "",
    "exchange": "",
    "country": "",
    "sector": "",
    "min_distance": 0.0,
    "order_size_multiplier": 1.0,
    "order_size_step": 0.0,
    "cot": None,
}
_TEXT_LIMIT = 8000
_FILTER_LIMIT = 256
_ID_DIGITS = 19
_EXTENSIONS = frozenset({"contract_size", "pip_size", "swap_settings"})
_POSITIVE = frozenset({"tick_size", "tick_step", "point_value", "lot_step"})
_NONNEGATIVE = frozenset(
    {
        "tick_value_in_money",
        "default_spread",
        "default_slippage",
        "min_volume",
        "max_volume",
        "margin_rate",
        "min_distance",
        "order_size_step",
    }
)
_DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


@dataclass(frozen=True)
class _Config:
    table: str = "datamgr_instruments"
    extension_type: str = "datamgr_instrument_specs"


@contextmanager
def _operation(fr_id: str) -> Iterator[None]:
    try:
        yield
    except ValueError, LookupError, FileExistsError:
        logger.warning("Instrument request rejected", extra={"fr_id": fr_id})
        raise
    except RuntimeError:
        logger.error("Instrument persistence failed", extra={"fr_id": fr_id})  # noqa: TRY400 - sanitized boundary
        raise
    else:
        logger.info("Instrument operation completed", extra={"fr_id": fr_id})


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")  # noqa: TRY004
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be a finite number.") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def _symbol(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9_@.:$]{1,128}", value
    ):
        raise ValueError("Symbol requires 1-128 letters, numbers or _ @ . : $.")
    return value


def _swap(value: Any) -> dict[str, Any]:
    keys = {"use", "type", "long", "short", "tripleSwapOn", "rolloutHour"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError("Invalid swap settings.")
    if type(value["use"]) is not bool or value["type"] not in (
        "money",
        "points",
        "percent",
    ):
        raise ValueError("Invalid swap settings.")
    if value["tripleSwapOn"] not in _DAYS or not isinstance(value["rolloutHour"], str):
        raise ValueError("Invalid swap schedule.")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value["rolloutHour"]):
        raise ValueError("Invalid swap rollout hour.")
    _number(value["long"], "swap long")
    _number(value["short"], "swap short")
    return dict(value)


def _commissions(value: Any) -> None:
    if not isinstance(value, str) or len(value) > _TEXT_LIMIT:
        raise ValueError("Invalid commissions.")
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid commissions.") from error
    if isinstance(parsed, (int, float)):
        _number(parsed, "commissions")
        return
    if not isinstance(parsed, dict) or set(parsed) != {"version", "settings"}:
        raise ValueError("Invalid commission format.")
    _commission_settings(parsed)


def _commission_settings(parsed: dict[str, Any]) -> None:
    settings = parsed["settings"]
    if parsed["version"] != 1 or not isinstance(settings, dict):
        raise ValueError("Invalid commission version.")
    if set(settings) != {"model", "value", "unit", "min", "minUnit", "max", "maxUnit"}:
        raise ValueError("Invalid commission settings.")
    if settings["model"] not in (
        "None",
        "Per trade",
        "Size based",
        "Percentage based",
        "Stockpicker",
    ):
        raise ValueError("Invalid commission model.")
    for key in ("value", "min", "max"):
        if _number(settings[key], f"commission {key}") < 0:
            raise ValueError("Commission values must be nonnegative.")
    for key in ("unit", "minUnit", "maxUnit"):
        if settings[key] not in ("share", "order", "equity", "money"):
            raise ValueError("Invalid commission unit.")


class Instruments:
    """Own authoritative instrument records and specification extensions."""

    def __init__(self) -> None:
        self._config = _Config()

    def instruments(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List all configured rows with optional explicit catalog filters."""
        with _operation("FR-DATAMGR-INSTR-LIST"):
            query = self._filters(filters)
            search = query.pop("search", "").casefold()
            extensions = self._extension_records()
            rows = HostPersistence.read_records(self._config.table, query, limit=0)
            result = [
                self._project(row, extensions.get(row["symbol"], {})) for row in rows
            ]
            return sorted(
                (
                    row
                    for row in result
                    if search in (row["symbol"] + " " + row["description"]).casefold()
                ),
                key=lambda row: (row["symbol"].casefold(), row["id"]),
            )

    def add_instrument(self, instrument: Mapping[str, Any]) -> dict[str, Any]:
        """Create an instrument and its independent specification atomically."""
        with _operation("FR-DATAMGR-INSTR-ADD"):
            self._input(instrument, create=True)
            symbol = _symbol(instrument.get("symbol"))
            self._unique(symbol)
            values = {**_DEFAULTS, **instrument, "symbol": symbol}
            self._validate(values)
            for key in ("contract_size", "pip_size"):
                if values.get(key) is None:
                    raise ValueError(f"{key} is required for a new instrument.")
            return self._create(values)

    def mass_edit_instruments(
        self, instrument_ids: Sequence[str], updates: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Commit only supplied mutable fields for all selected instruments."""
        with _operation("FR-DATAMGR-INSTR-MASS-EDIT"):
            if (
                not isinstance(instrument_ids, Sequence)
                or isinstance(instrument_ids, (str, bytes))
                or not instrument_ids
            ):
                raise ValueError("Select at least one instrument ID.")
            self._input(updates, create=False)
            if not updates:
                raise ValueError("Select at least one field for change.")
            rows = [
                self._get(identifier) for identifier in dict.fromkeys(instrument_ids)
            ]
            operations: list[dict[str, Any]] = []
            for row in rows:
                merged = {**row, **updates}
                if "swap_settings" not in updates and row["swap_settings"] is not None:
                    swap = dict(row["swap_settings"])
                    for scalar, key in (("swap_long", "long"), ("swap_short", "short")):
                        if scalar in updates:
                            swap[key] = updates[scalar]
                    if "swap_3day_day" in updates:
                        self._integer(updates["swap_3day_day"], "swap_3day_day", 0, 6)
                        swap["tripleSwapOn"] = _DAYS[updates["swap_3day_day"]]
                    merged["swap_settings"] = swap
                self._validate(merged)
                changed = self._columns(updates)
                changed["updated_at_utc"] = datetime.now(UTC).isoformat()
                operations.append(
                    {
                        "op": "update",
                        "table": self._config.table,
                        "key_columns": {"id": int(row["id"])},
                        "values": changed,
                    }
                )
                if _EXTENSIONS.intersection(updates) or {
                    "swap_long",
                    "swap_short",
                    "swap_3day_day",
                }.intersection(updates):
                    operations.append(self._extension_op(merged))
            self._commit(operations)
            result = [self._get(row["id"]) for row in rows]
            return {"updated_count": len(rows), "instruments": result}

    def clone_instrument(self, source_id: str, new_symbol: str) -> dict[str, Any]:
        """Copy all persisted specification fields under a new identity."""
        with _operation("FR-DATAMGR-INSTR-CLONE"):
            source = self._get(source_id)
            self._unique(_symbol(new_symbol))
            values = {key: source[key] for key in _DEFAULTS}
            values.update({key: source[key] for key in _EXTENSIONS})
            values["symbol"] = new_symbol
            return self._create(values)

    def _filters(self, filters: Mapping[str, Any] | None) -> dict[str, Any]:
        if filters is None:
            return {}
        if not isinstance(filters, Mapping) or set(filters) - {
            "search",
            "broker_id",
            "connection",
            "data_type",
        }:
            raise ValueError("Unsupported instrument filters.")
        result = dict(filters)
        if "broker_id" in result:
            value = result["broker_id"]
            if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
                result["broker_id"] = int(value)
            self._integer(result["broker_id"], "broker_id", -1, 2**63 - 1)
        for key in set(result) - {"broker_id"}:
            if not isinstance(result[key], str) or len(result[key]) > _FILTER_LIMIT:
                raise ValueError(f"Invalid filter {key}.")
        return result

    def _input(self, values: Any, *, create: bool) -> None:
        allowed = set(_DEFAULTS) | _EXTENSIONS | ({"symbol"} if create else set())
        if not isinstance(values, Mapping) or set(values) - allowed:
            raise ValueError("Unknown or immutable instrument fields.")
        if "swap_settings" in values and {
            "swap_long",
            "swap_short",
            "swap_3day_day",
        }.intersection(values):
            raise ValueError(
                "Supply full swap settings or scalar swap fields, not both."
            )

    def _integer(self, value: Any, key: str, low: int, high: int) -> None:
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{key} must be an integer from {low} to {high}.")

    def _validate(self, values: Mapping[str, Any]) -> None:
        self._validate_numbers(values)
        self._integer(values["decimals"], "decimals", 0, 12)
        self._integer(values["swap_3day_day"], "swap_3day_day", 0, 6)
        self._integer(values["broker_id"], "broker_id", -1, 2**63 - 1)
        broker = values["broker_id"]
        if broker not in (-1, 0) and not HostPersistence.read_records(
            "datamgr_broker", {"id": broker}, limit=1
        ):
            raise ValueError("Choose a configured broker ID.")
        for key, default in _DEFAULTS.items():
            if isinstance(default, str) and (
                not isinstance(values[key], str) or len(values[key]) > _TEXT_LIMIT
            ):
                raise ValueError(f"{key} must be text of at most 8000 characters.")
        if not values["data_type"].strip():
            raise ValueError("Data type is required.")
        if values["cot"] is not None and not isinstance(values["cot"], str):
            raise ValueError("cot must be text or null.")
        _commissions(values["commissions"])
        if values.get("swap_settings") is not None:
            _swap(values["swap_settings"])

    def _validate_numbers(self, values: Mapping[str, Any]) -> None:
        for key in (
            _POSITIVE
            | _NONNEGATIVE
            | {"swap_long", "swap_short", "order_size_multiplier"}
        ):
            number = _number(values[key], key)
            if (key in _POSITIVE and number <= 0) or (
                key in _NONNEGATIVE and number < 0
            ):
                raise ValueError(f"{key} is outside its allowed range.")
        if (
            values["order_size_multiplier"] < 1
            or values["max_volume"] < values["min_volume"]
        ):
            raise ValueError("Invalid order multiplier or volume bounds.")
        for key in ("contract_size", "pip_size"):
            if values.get(key) is not None and _number(values[key], key) <= 0:
                raise ValueError(f"{key} must be positive.")

    def _extension_records(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for record in HostPersistence.read_entity(self._config.extension_type, limit=0):
            try:
                payload = json.loads(record["payload"])
                self._validate_extension(payload)
            except (ValueError, TypeError) as error:
                raise RuntimeError(
                    "Stored instrument specification is invalid."
                ) from error
            result[record["entity_id"]] = payload
        return result

    def _validate_extension(self, payload: Any) -> None:
        if (
            not isinstance(payload, dict)
            or payload.pop("version", None) != 1
            or set(payload) - _EXTENSIONS
        ):
            raise ValueError("Invalid specification payload.")
        for key in ("contract_size", "pip_size"):
            if payload.get(key) is not None and _number(payload[key], key) <= 0:
                raise ValueError("Invalid specification size.")
        if payload.get("swap_settings") is not None:
            _swap(payload["swap_settings"])

    def _project(
        self, row: Mapping[str, Any], extension: Mapping[str, Any]
    ) -> dict[str, Any]:
        return {
            **row,
            "id": str(row["id"]),
            "point_size": 10.0 ** -int(row["decimals"]),
            **{key: extension.get(key) for key in _EXTENSIONS},
        }

    def _get(self, identifier: Any) -> dict[str, Any]:
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[1-9]\d*", identifier)
            or len(identifier) > _ID_DIGITS
            or int(identifier) > 2**63 - 1
        ):
            raise ValueError("Instrument ID must be a positive integer string.")
        rows = HostPersistence.read_records(
            self._config.table, {"id": int(identifier)}, limit=1
        )
        if not rows:
            raise LookupError("Instrument is no longer in the catalog.")
        return self._project(
            rows[0], self._extension_records().get(rows[0]["symbol"], {})
        )

    def _unique(self, symbol: str) -> None:
        if any(
            row["symbol"].casefold() == symbol.casefold()
            for row in HostPersistence.read_records(self._config.table, limit=0)
        ):
            raise FileExistsError("An instrument with this symbol already exists.")

    def _columns(self, values: Mapping[str, Any]) -> dict[str, Any]:
        result = {
            key: value
            for key, value in values.items()
            if key in _DEFAULTS or key == "symbol"
        }
        if values.get("swap_settings") is not None:
            swap = _swap(values["swap_settings"])
            result.update(
                swap_long=swap["long"],
                swap_short=swap["short"],
                swap_3day_day=_DAYS.index(swap["tripleSwapOn"]),
            )
        return result

    def _extension_op(self, values: Mapping[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        existing = HostPersistence.read_entity(
            self._config.extension_type, str(values["symbol"])
        )
        previous = existing[0] if existing else {}
        return {
            "op": "upsert",
            "table": "host_entities",
            "key_columns": {
                "entity_id": values["symbol"],
                "entity_type": self._config.extension_type,
            },
            "values": {
                "entity_id": values["symbol"],
                "entity_type": self._config.extension_type,
                "scope": "global",
                "revision": int(previous.get("revision", 0)) + 1,
                "created_at_utc": previous.get("created_at_utc", now),
                "updated_at_utc": now,
                "payload": json.dumps(
                    {"version": 1, **{key: values.get(key) for key in _EXTENSIONS}},
                    allow_nan=False,
                ),
            },
        }

    def _commit(self, operations: Sequence[Mapping[str, Any]]) -> None:
        try:
            HostPersistence.apply_batch(operations)
        except RuntimeError as error:
            raise RuntimeError("Instrument changes could not be saved.") from error

    def _create(self, values: Mapping[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        columns = {
            **self._columns(values),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        self._commit(
            [
                {"op": "create", "table": self._config.table, "values": columns},
                self._extension_op(values),
            ]
        )
        row = HostPersistence.read_records(
            self._config.table, {"symbol": values["symbol"]}, limit=1
        )[0]
        return self._project(row, {key: values.get(key) for key in _EXTENSIONS})


if __name__ == "__main__":
    logger.info("Configured instruments: %s", Instruments().instruments())
