"""Manage persisted broker profiles and selected catalog imports.

Description:
    Combines configured profiles, stock membership and instrument/session
    definitions through public catalog services and host-owned persistence.
    Profile defaults remain separate from retrieved broker economics. Imports
    report confirmed records and failures instead of hiding partial completion.
Purpose:
    FEAT-DATAMGR-BROKER: Configured broker profiles and catalog assignment.
Key Capabilities:
    - FR-DATAMGR-BROKER-LIST: Profiles [Broker.brokers()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BROKER-ADD: Save defaults [Broker.add_broker()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BROKER-DELETE: Remove [Broker.delete_broker()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BROKER-STOCKS: Stock list [Broker.edit_stocks()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BROKER-IMPORT-INSTR: Import [Broker.import_instruments()] (INFO).
    - FR-DATAMGR-BROKER-IMPORT-SESS: Import [Broker.import_sessions()] (INFO).
Python API Usage:
    from app.workspace.data_manager.broker import Broker
    profiles = Broker().brokers()
CLI Usage:
    uv run python -m app.cli data brokers
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

from .instruments import Instruments
from .sessions import Sessions

__all__ = ["Broker", "BrokerCLI"]
logger = get_logger(__name__)
_ENTITY = "datamgr_broker_settings"
_LIMIT = 10000
_FILE_BYTES = 2000000
_MODELS = {"None", "Per trade", "Size based", "Percentage based", "Stockpicker"}
_CONTROL_START = 32
_CONTROL_DELETE = 127
_INSTRUMENT_MAP = {
    "name": "description",
    "type": "data_type",
    "pointValue": "point_value",
    "tickSize": "tick_size",
    "tickStep": "tick_step",
    "spread": "default_spread",
    "slippage": "default_slippage",
    "minDistance": "min_distance",
    "multiplier": "order_size_multiplier",
    "sizeStep": "order_size_step",
    "contractSize": "contract_size",
    "pipSize": "pip_size",
    "marginRate": "margin_rate",
    "decimals": "decimals",
    "minVolume": "min_volume",
    "maxVolume": "max_volume",
    "lotStep": "lot_step",
    "tickValue": "tick_value_in_money",
}


@dataclass(frozen=True)
class _Config:
    table: str = "datamgr_broker"
    stocks: str = "datamgr_broker_stock"


@contextmanager
def _operation(capability: str) -> Generator[dict[str, Any]]:
    fr_id = f"FR-DATAMGR-BROKER-{capability}"
    outcome: dict[str, Any] = {"fr_id": fr_id}
    try:
        yield outcome
    except TypeError as error:
        logger.warning("Broker request rejected", extra={"fr_id": fr_id})
        raise ValueError("Invalid broker field type.") from error
    except ValueError, LookupError, FileExistsError:
        logger.warning("Broker request rejected", extra={"fr_id": fr_id})
        raise
    except RuntimeError:
        logger.error("Broker storage failed", extra={"fr_id": fr_id})  # noqa: TRY400
        raise
    else:
        if outcome.pop("storage_failed", False):
            logger.error("Broker import stopped on storage failure", extra=outcome)
        elif outcome.get("failed_count", 0):
            logger.warning("Broker import completed with failed records", extra=outcome)
        else:
            logger.info("Broker operation completed", extra=outcome)


def _text(value: Any, label: str, maximum: int, *, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{label} must be text of at most {maximum} characters.")
    clean: str = value.strip()
    if required and not clean:
        raise ValueError(f"{label} is required.")
    if any(
        ord(char) < _CONTROL_START or ord(char) == _CONTROL_DELETE for char in clean
    ):
        raise ValueError(f"{label} contains control characters.")
    return clean


def _broker_timezone(value: Any) -> str:
    """Validate a configured clock label without converting its timestamps."""
    name = _text(value, "timezone", 100, required=True)
    if name != "EETUS":
        try:
            ZoneInfo(name)
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise ValueError(
                "Choose a valid broker timezone or clock label."
            ) from error
    return name


def _identifier(value: Any, *, default: bool = False) -> str:
    if default and value in ("-1", "0"):
        return "-1"
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[1-9]\d{0,18}", value)
        or int(value) >= 2**63
    ):
        raise ValueError("Broker ID must be a positive integer string.")
    return value


def _number(value: Any, maximum: float = 100000) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not 0 <= value <= maximum
        or not math.isfinite(value)
    ):
        raise ValueError(
            "Cost values must be finite nonnegative numbers within limits."
        )
    return float(value)


def _costs(spread: Any, commission: Any) -> dict[str, Any]:
    if not isinstance(spread, Mapping) or not isinstance(commission, Mapping):
        raise TypeError("Cost models must be objects.")
    if spread.get("model") == "inherit" and set(spread) == {"model"}:
        clean_spread: dict[str, Any] = {"model": "inherit"}
    elif spread.get("model") == "fixed" and set(spread) == {"model", "value"}:
        clean_spread = {"model": "fixed", "value": _number(spread["value"])}
    else:
        raise ValueError("Choose inherited or fixed spread.")
    if commission.get("model") == "inherit" and set(commission) == {"model"}:
        return {"spread_model": clean_spread, "commission_model": {"model": "inherit"}}
    return {"spread_model": clean_spread, "commission_model": _commission(commission)}


def _commission(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("Commission settings must be an object.")
    fields = {"model", "value", "unit", "min", "minUnit", "max", "maxUnit"}
    model = value.get("model")
    if not isinstance(model, str) or model not in _MODELS or set(value) != fields:
        raise ValueError("Choose a supported complete commission model.")
    clean = dict(value)
    clean["value"] = _number(
        value["value"], 100 if model == "Percentage based" else 100000
    )
    clean["min"], clean["max"] = _number(value["min"]), _number(value["max"])
    if value["unit"] not in ("share", "order", "equity") or any(
        value[key] not in ("money", "equity") for key in ("minUnit", "maxUnit")
    ):
        raise ValueError("Choose valid commission units.")
    if model == "None" and clean["value"] != 0:
        raise ValueError("No commission requires an explicit zero value.")
    if value["minUnit"] == value["maxUnit"] and 0 < clean["max"] < clean["min"]:
        raise ValueError("Commission maximum must not be below minimum.")
    return clean


def _json(value: str) -> Any:
    if len(value.encode("utf-8")) > _FILE_BYTES:
        raise ValueError("JSON file exceeds 2 MB.")
    try:
        return json.loads(value, parse_constant=_invalid_constant)
    except (ValueError, RecursionError) as error:
        raise ValueError("Select a valid bounded JSON file.") from error


def _invalid_constant(_value: str) -> None:
    raise ValueError("Nonfinite JSON number.")


class Broker:
    """Own broker defaults, stock membership and public catalog orchestration."""

    def __init__(self) -> None:
        self._config = _Config()
        self._instruments = Instruments()
        self._sessions = Sessions()

    def brokers(self) -> list[dict[str, Any]]:
        """List configured profiles with complete confirmed stocks and counts."""
        with _operation("LIST"):
            return self._profiles()

    def add_broker(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        """Create or edit a profile and its cost settings atomically."""
        with _operation("ADD"):
            if not isinstance(profile, Mapping):
                raise TypeError("Provide a broker profile object.")
            original = self._get(profile["id"]) if "id" in profile else None
            values = self._profile_values(profile, original)
            self._guard_edit(values, original)
            now = datetime.now(UTC).isoformat()
            columns = {
                "name": values["name"],
                "description": values["description"],
                "server_timezone": values["timezone"],
                "postfix": values["postfix"],
                "stockpicker_use": int(values["stockpicker_use"]),
                "mt_use": int(values["mt_use"]),
                "updated_at_utc": now,
            }
            operation: dict[str, Any] = {
                "op": "create",
                "table": self._config.table,
                "values": {**columns, "created_at_utc": now},
            }
            if original:
                operation.update(
                    op="update", key_columns={"id": int(original["id"])}, values=columns
                )
            settings = {"entity_type": _ENTITY, "entity_id": values["name"].casefold()}
            previous = {
                "entity_type": _ENTITY,
                "entity_id": original["name"].casefold()
                if original
                else settings["entity_id"],
            }
            old = HostPersistence.read_records("host_entities", previous, limit=1)
            if old and original is None:
                raise FileExistsError("Broker settings already exist for this name.")
            payload = json.dumps(
                {
                    "version": 1,
                    "spread_model": values["spread_model"],
                    "commission_model": values["commission_model"],
                },
                allow_nan=False,
            )
            operations = [operation]
            if old:
                operations.append(
                    {"op": "delete", "table": "host_entities", "key_columns": previous}
                )
            operations.append(
                {
                    "op": "create",
                    "table": "host_entities",
                    "values": {
                        **settings,
                        "scope": "datamanager",
                        "payload": payload,
                        "revision": old[0]["revision"] + 1 if old else 1,
                        "created_at_utc": old[0]["created_at_utc"] if old else now,
                        "updated_at_utc": now,
                    },
                }
            )
            HostPersistence.apply_batch(operations)
            return next(row for row in self._profiles({"name": values["name"]}))

    def edit_stocks(self, broker_id: str, symbols: Sequence[str]) -> dict[str, Any]:
        """Replace all stock membership, including an explicitly empty list."""
        with _operation("STOCKS"):
            profile = self._get(broker_id)
            if profile["is_system"] or not profile["stockpicker_use"]:
                raise ValueError("This broker cannot edit stock membership.")
            if not isinstance(symbols, (list, tuple)) or len(symbols) > _LIMIT:
                raise ValueError("Provide at most 10000 stock symbols.")
            unique: dict[str, str] = {}
            for raw in symbols:
                symbol = _text(raw, "Stock symbol", 128, required=True)
                if not re.fullmatch(r"[\w@.:$+/-]+", symbol, flags=re.ASCII):
                    raise ValueError("Invalid stock symbol.")
                unique.setdefault(symbol.casefold(), symbol)
            stocks = list(unique.values())
            operations = [
                {
                    "op": "delete",
                    "table": self._config.stocks,
                    "key_columns": {"ID": row["ID"]},
                }
                for row in HostPersistence.read_records(
                    self._config.stocks, {"BROKER_ID": int(broker_id)}, limit=0
                )
            ]
            operations.extend(
                {
                    "op": "create",
                    "table": self._config.stocks,
                    "values": {"BROKER_ID": int(broker_id), "TICKER": symbol},
                }
                for symbol in stocks
            )
            HostPersistence.apply_batch(operations)
            return {"broker_id": broker_id, "count": len(stocks), "stocks": stocks}

    def delete_broker(self, broker_ids: Sequence[str]) -> dict[str, Any]:
        """Remove unused custom profiles and owned settings atomically."""
        with _operation("DELETE"):
            if (
                not isinstance(broker_ids, (list, tuple))
                or not 0 < len(broker_ids) <= _LIMIT
            ):
                raise ValueError("Select between 1 and 10000 broker profiles.")
            identifiers = list(
                dict.fromkeys(_identifier(value) for value in broker_ids)
            )
            profiles = [self._get(identifier) for identifier in identifiers]
            if any(row["is_system"] for row in profiles):
                raise ValueError("System broker profiles cannot be deleted.")
            if any(
                row["total_instruments"] or row["total_sessions"] for row in profiles
            ):
                raise ValueError(
                    "Brokers with assigned instruments or sessions cannot be deleted."
                )
            references = {
                value for row in profiles for value in (row["id"], row["name"])
            }
            if any(
                str(row.get("broker")) in references
                for row in HostPersistence.read_records("datamgr_datasets", limit=0)
            ):
                raise ValueError("Brokers used by saved datasets cannot be deleted.")
            operations: list[dict[str, Any]] = []
            for row in profiles:
                operations.extend(
                    {
                        "op": "delete",
                        "table": self._config.stocks,
                        "key_columns": {"ID": stock["ID"]},
                    }
                    for stock in HostPersistence.read_records(
                        self._config.stocks, {"BROKER_ID": int(row["id"])}, limit=0
                    )
                )
                operations.extend(
                    [
                        {
                            "op": "delete",
                            "table": "host_entities",
                            "key_columns": {
                                "entity_type": _ENTITY,
                                "entity_id": row["name"].casefold(),
                            },
                        },
                        {
                            "op": "delete",
                            "table": self._config.table,
                            "key_columns": {"id": int(row["id"])},
                        },
                    ]
                )
            HostPersistence.apply_batch(operations)
            return {"deleted_ids": identifiers, "deleted_count": len(identifiers)}

    def import_instruments(
        self, broker_id: str, payload: Sequence[Mapping[str, Any]] | str
    ) -> dict[str, Any]:
        """Import selected definitions with explicit per-record outcomes."""
        with _operation("IMPORT-INSTR") as outcome:
            return self._import(broker_id, payload, "instruments", outcome)

    def import_sessions(
        self, broker_id: str, payload: Sequence[Mapping[str, Any]] | str
    ) -> dict[str, Any]:
        """Import selected full session schedules and holiday calendars."""
        with _operation("IMPORT-SESS") as outcome:
            return self._import(broker_id, payload, "sessions", outcome)

    def _profiles(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        rows = HostPersistence.read_records(self._config.table, filters, limit=0)
        if not rows:
            return []
        # A filtered lookup has one owner; listings aggregate each relation once.
        owner = {"broker_id": rows[0]["id"]} if filters else None
        stocks: dict[str, list[str]] = defaultdict(list)
        for stock in HostPersistence.read_records(
            self._config.stocks,
            {"BROKER_ID": rows[0]["id"]} if filters else None,
            limit=0,
        ):
            stocks[str(stock["BROKER_ID"])].append(stock["TICKER"])
        counts = {
            kind: Counter(
                str(record["broker_id"])
                for record in HostPersistence.read_records(
                    f"datamgr_{kind}", owner, limit=0
                )
            )
            for kind in ("instruments", "sessions")
        }
        settings_filter = {"entity_type": _ENTITY}
        if filters:
            settings_filter["entity_id"] = rows[0]["name"].casefold()
        settings = {
            row["entity_id"]: row["payload"]
            for row in HostPersistence.read_records(
                "host_entities", settings_filter, limit=0
            )
        }
        result = []
        for row in rows:
            identifier = str(row["id"])
            try:
                result.append(
                    {
                        **self._decode_profile(
                            row, settings.get(row["name"].casefold())
                        ),
                        "stocks": stocks[identifier],
                        "customized_stocks": len(stocks[identifier]),
                        "total_instruments": counts["instruments"][identifier],
                        "total_sessions": counts["sessions"][identifier],
                    }
                )
            except (ValueError, TypeError, ZoneInfoNotFoundError) as error:
                raise RuntimeError("Stored broker settings are invalid.") from error
        return sorted(result, key=lambda row: (row["name"].casefold(), int(row["id"])))

    def _decode_profile(
        self, row: Mapping[str, Any], payload: str | None
    ) -> dict[str, Any]:
        raw = (
            _json(payload)
            if payload is not None
            else {
                "version": 1,
                "spread_model": {"model": "inherit"},
                "commission_model": {"model": "inherit"},
            }
        )
        if (
            not isinstance(raw, dict)
            or type(raw.get("version")) is not int
            or raw.get("version") != 1
            or set(raw) != {"version", "spread_model", "commission_model"}
        ):
            raise ValueError("Invalid stored broker settings version.")
        flags = {}
        for key in ("is_system", "stockpicker_use", "mt_use"):
            if type(row[key]) is not int or row[key] not in (0, 1):
                raise ValueError("Stored broker flag must be zero or one.")
            flags[key] = bool(row[key])
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "timezone": _broker_timezone(row["server_timezone"]),
            "postfix": row["postfix"],
            **flags,
            **_costs(raw["spread_model"], raw["commission_model"]),
        }

    def _get(self, identifier: Any) -> dict[str, Any]:
        rows = self._profiles({"id": int(_identifier(identifier))})
        if not rows:
            raise LookupError("Broker is no longer in the catalog.")
        return rows[0]

    def _profile_values(
        self, source: Mapping[str, Any], original: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        fields = {
            "id",
            "name",
            "description",
            "timezone",
            "postfix",
            "stockpicker_use",
            "mt_use",
            "spread_model",
            "commission_model",
        }
        if set(source) - fields:
            raise ValueError("Unknown or read-only broker fields.")
        values = {
            "name": "",
            "description": "",
            "timezone": "UTC",
            "postfix": "",
            "stockpicker_use": True,
            "mt_use": True,
            "spread_model": {"model": "inherit"},
            "commission_model": {"model": "inherit"},
            **(original or {}),
            **source,
        }
        for key, bound in (("name", 50), ("description", 250), ("postfix", 100)):
            values[key] = _text(values[key], key, bound, required=key == "name")
        values["timezone"] = _broker_timezone(values["timezone"])
        if any(type(values[key]) is not bool for key in ("stockpicker_use", "mt_use")):
            raise ValueError("Broker flags must be booleans.")
        values.update(_costs(values["spread_model"], values["commission_model"]))
        return values

    def _guard_edit(
        self, values: Mapping[str, Any], original: Mapping[str, Any] | None
    ) -> None:
        for row in HostPersistence.read_records(self._config.table, limit=0):
            if row["name"].casefold() == values["name"].casefold() and (
                original is None or str(row["id"]) != original["id"]
            ):
                raise FileExistsError("Broker name must be unique.")
        if original is None:
            return
        if original["is_system"]:
            raise ValueError("System broker profiles cannot be edited.")
        if original["stocks"] and not values["stockpicker_use"]:
            raise ValueError("A broker with stocks must remain stock-enabled.")
        if (original["total_instruments"] or original["total_sessions"]) and not values[
            "mt_use"
        ]:
            raise ValueError("A broker with assigned catalogs must remain enabled.")
        if values["timezone"] != original["timezone"] and any(
            str(row.get("broker")) in (original["id"], original["name"])
            for row in HostPersistence.read_records("datamgr_datasets", limit=0)
        ):
            raise ValueError("A broker used by saved data cannot change timezone.")

    def _document(
        self, payload: Sequence[Mapping[str, Any]] | str, kind: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        options: dict[str, Any] = {}
        raw: Any = _json(payload) if isinstance(payload, str) else payload
        if isinstance(raw, dict):
            allowed = {"version", "kind", kind, "options"}
            if kind == "instruments":
                allowed.add("brokers")
            if (
                set(raw) - allowed
                or type(raw.get("version")) is not int
                or raw.get("version") != 1
                or raw.get("kind") != kind
            ):
                raise ValueError("Unsupported catalog JSON envelope.")
            options = raw.get("options", {})
            raw = raw.get(kind)
        if not isinstance(raw, (list, tuple)) or not 0 < len(raw) <= _LIMIT:
            raise ValueError("Provide between 1 and 10000 catalog records.")
        if any(not isinstance(record, Mapping) for record in raw):
            raise ValueError("Every catalog record must be an object.")
        if not isinstance(options, dict) or set(options) - {
            "selected_names",
            "postfix",
            "conflict_policy",
            "use_profile_costs",
        }:
            raise ValueError("Invalid import options.")
        if options.get("conflict_policy", "error") not in ("error", "overwrite"):
            raise ValueError("Choose error or explicit overwrite for conflicts.")
        if type(options.get("use_profile_costs", False)) is not bool:
            raise ValueError("Use profile costs must be boolean.")
        return [dict(record) for record in raw], options

    def _targets(
        self,
        profile: Mapping[str, Any],
        records: list[dict[str, Any]],
        options: Mapping[str, Any],
        kind: str,
    ) -> list[tuple[str, dict[str, Any], dict[str, Any] | None]]:
        field = "symbol" if kind == "instruments" else "name"
        names = [
            _text(record.get(field), field, 128, required=True) for record in records
        ]
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Duplicate source names in import.")
        selection = options.get("selected_names", names)
        if (
            not isinstance(selection, list)
            or not selection
            or any(not isinstance(name, str) for name in selection)
            or len(set(selection)) != len(selection)
            or set(selection) - set(names)
        ):
            raise ValueError("Choose existing unique records to import.")
        postfix = _text(options.get("postfix", profile["postfix"]), "postfix", 100)
        existing = (
            self._instruments.instruments()
            if kind == "instruments"
            else self._sessions.sessions()
        )
        by_name = {row[field].casefold(): row for row in existing}
        targets = []
        for name, record in zip(names, records, strict=True):
            if name not in selection:
                continue
            target = _text(name + postfix, field, 128, required=True)
            previous = by_name.get(target.casefold())
            if previous and str(previous["broker_id"]) not in (
                profile["id"],
                "0" if profile["id"] == "-1" else profile["id"],
            ):
                raise FileExistsError(
                    "A target belongs to another broker; choose another postfix."
                )
            if previous and options.get("conflict_policy", "error") != "overwrite":
                raise FileExistsError(
                    "Target records already exist; confirm overwrite."
                )
            if previous and previous[field] != target:
                raise FileExistsError(
                    "Overwrite requires the exact existing target spelling."
                )
            targets.append((target, record, previous))
        return targets

    def _import(
        self,
        broker_id: str,
        payload: Sequence[Mapping[str, Any]] | str,
        kind: str,
        outcome: dict[str, Any],
    ) -> dict[str, Any]:
        identifier = _identifier(broker_id, default=True)
        if identifier == "-1":
            profile = {
                "id": "-1",
                "name": "Default",
                "postfix": "",
                "timezone": "UTC",
                "spread_model": {"model": "inherit"},
                "commission_model": {"model": "inherit"},
            }
        else:
            profile = self._get(identifier)
            if profile["is_system"] or not profile["mt_use"]:
                raise ValueError("Choose an editable catalog-enabled broker.")

        records, options = self._document(payload, kind)
        targets = self._targets(profile, records, options, kind)
        result: dict[str, Any] = {
            "broker_id": profile["id"],
            "imported_count": 0,
            "created_count": 0,
            "updated_count": 0,
            "records": [],
            "failed": [],
            "unattempted": [],
        }
        for index, (name, raw, previous) in enumerate(targets):
            try:
                saved = self._save_import(
                    profile, raw, name, previous, options=options, kind=kind
                )
            except ValueError, TypeError, OverflowError, LookupError, FileExistsError:
                result["failed"].append(
                    {"name": name, "reason": "Record validation failed."}
                )
            except RuntimeError:
                result["failed"].append(
                    {"name": name, "reason": "Record storage unavailable."}
                )
                result["unattempted"] = [target[0] for target in targets[index + 1 :]]
                outcome["storage_failed"] = True
                break
            else:
                result["records"].append(saved)
                result["imported_count"] += 1
                result["updated_count" if previous else "created_count"] += 1
        outcome["failed_count"] = len(result["failed"])
        outcome["saved_count"] = result["imported_count"]
        return result

    def _save_import(
        self,
        profile: Mapping[str, Any],
        raw: dict[str, Any],
        name: str,
        previous: dict[str, Any] | None,
        *,
        options: Mapping[str, Any],
        kind: str,
    ) -> dict[str, Any]:
        if kind == "sessions":
            values = self._session_record(raw, profile)
            values.update(name=name, broker_id=int(profile["id"]))
            if previous:
                values["id"] = previous["id"]
            return self._sessions.session_template(values)
        values = self._instrument_record(raw)
        numeric_fields = set(_INSTRUMENT_MAP.values()) - {"description", "data_type"}
        for field in numeric_fields:
            if field not in values or (
                field in ("contract_size", "pip_size") and values[field] is None
            ):
                continue
            number = values[field]
            if type(number) not in (int, float) or not math.isfinite(number):
                raise ValueError("Instrument quantities must be finite numbers.")
        values.update(symbol=name, broker_id=int(profile["id"]))
        if options.get("use_profile_costs", False):
            if profile["spread_model"]["model"] == "fixed":
                values["default_spread"] = profile["spread_model"]["value"]
            if profile["commission_model"]["model"] != "inherit":
                values["commissions"] = json.dumps(
                    {"version": 1, "settings": profile["commission_model"]}
                )
        if previous:
            return dict(
                self._instruments.mass_edit_instruments([previous["id"]], values)[
                    "instruments"
                ][0]
            )
        return self._instruments.add_instrument(values)

    def _instrument_record(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        if "tickSize" not in raw:
            return {
                key: value
                for key, value in raw.items()
                if key not in ("id", "created_at_utc", "updated_at_utc")
            }
        allowed = set(_INSTRUMENT_MAP) | {
            "id",
            "symbol",
            "broker",
            "brokerName",
            "timezone",
            "commission",
            "swap",
        }
        if set(raw) - allowed:
            raise ValueError("Unknown instrument file fields.")
        values = {
            _INSTRUMENT_MAP[key]: value
            for key, value in raw.items()
            if key in _INSTRUMENT_MAP
        }
        if "commission" in raw:
            values["commissions"] = json.dumps(
                {"version": 1, "settings": _commission(raw["commission"])}
            )
        if "swap" in raw:
            values["swap_settings"] = raw["swap"]
        return values

    def _session_record(
        self, raw: Mapping[str, Any], profile: Mapping[str, Any]
    ) -> dict[str, Any]:
        values = {
            key: value
            for key, value in raw.items()
            if key not in ("id", "broker", "brokerName", "normalizationWarnings")
        }
        if "elements" in values:
            elements = values.pop("elements")
            if not isinstance(elements, list):
                raise ValueError("Session elements must be a list.")
            windows = []
            for element in elements:
                if not isinstance(element, Mapping) or set(element) - {
                    "dayFrom",
                    "dayTo",
                    "timeFrom",
                    "timeTo",
                    "eod",
                    "sessionType",
                    "dayOfWeek",
                }:
                    raise ValueError("Invalid session element.")
                windows.append(
                    {
                        "day_from": element.get("dayFrom"),
                        "day_to": element.get("dayTo"),
                        "start_time": element.get("timeFrom"),
                        "end_time": element.get("timeTo"),
                        "eod": element.get("eod"),
                        "session_type": element.get("sessionType", "Regular"),
                        **(
                            {"day_of_week": element["dayOfWeek"]}
                            if "dayOfWeek" in element
                            else {}
                        ),
                    }
                )
            values["windows"] = windows
            if "isDefault" in values:
                values["is_default"] = values.pop("isDefault")
        values.setdefault("timezone", profile["timezone"])
        return values


class BrokerCLI:
    """Headless CLI formatter and dispatcher for Broker Profile operations."""

    @staticmethod
    def _res(act: str, ren: str, **kw: Any) -> dict[str, Any]:
        return {"command": "brokerprofile", "action": act, "rendered": ren, **kw}

    @staticmethod
    def format_brokers_table(
        rows: Sequence[Mapping[str, Any]], csv: bool = False
    ) -> str:
        """Format broker profiles into ASCII table or CSV format."""
        if csv:
            keys = "name,server,account,path,symbols"
            kl = keys.split(",")
            lines = [keys] + [
                ",".join(
                    str(len(r.get("stocks", [])) if k == "symbols" else r.get(k, ""))
                    for k in kl
                )
                for r in rows
            ]
            return "\n".join(lines)
        cols = [
            ("Name", "name", 15),
            ("Server", "server", 20),
            ("Account", "account", 12),
            ("Symbols", "symbols", 8),
            ("Path", "path", 30),
        ]
        hdr = "| " + " | ".join(f"{h:<{w}}" for h, _, w in cols) + " |"
        sep = "|-" + "-|-".join("-" * w for _, _, w in cols) + "-|"
        lines = [f"=== Broker Profiles ({len(rows)} items) ===", hdr, sep]
        for r in rows:
            sym_len = len(r.get("stocks", []))
            row_map = {**r, "symbols": sym_len}
            lines.append(
                "| "
                + " | ".join(str(row_map.get(k, ""))[:w].ljust(w) for _, k, w in cols)
                + " |"
            )
        return "\n".join(lines)

    @classmethod
    def dispatch(cls, args: Sequence[str], service: Broker) -> dict[str, Any]:
        """Dispatch headless brokerprofile commands."""
        params = dict(a.split("=", 1) for a in args if "=" in a)
        action = params.pop("action", None)
        if action is None:
            pos = [a for a in args if "=" not in a]
            action = pos[0].lower() if pos else "list"
        action = action.lower()

        if action == "list":
            rows = service.brokers()
            csv_m = params.get("csv", "false").lower() == "true"
            return cls._res(
                action,
                cls.format_brokers_table(rows, csv=csv_m),
                count=len(rows),
                profiles=rows,
            )
        if action == "add":
            return cls._handle_add(params, service)
        if action == "delete":
            return cls._handle_delete(params, service)
        if action == "importstocks":
            return cls._handle_import_stocks(params, service)
        if action == "exportstocks":
            return cls._handle_export_stocks(params, service)
        if action in ("update", "updateall"):
            rows = service.brokers()
            return cls._res(
                action,
                f"Updated {len(rows)} broker profile(s).",
                count=len(rows),
                updated=rows,
            )
        raise ValueError(f"Unsupported brokerprofile action: '{action}'")

    @classmethod
    def _handle_add(cls, p: dict[str, str], s: Broker) -> dict[str, Any]:
        name = p.get("name") or p.get("broker")
        if not name:
            raise ValueError("Parameter 'broker' or 'name' is required for action=add.")
        profile_data = {
            "name": name,
            "description": p.get("description", ""),
            "timezone": p.get("timezone", "UTC"),
            "postfix": p.get("postfix", ""),
            "spread_model": {"model": "inherit"},
            "commission_model": {"model": "inherit"},
        }
        profile = s.add_broker(profile_data)
        return cls._res("add", f"Added broker profile '{name}'.", profile=profile)

    @classmethod
    def _handle_delete(cls, p: dict[str, str], s: Broker) -> dict[str, Any]:
        name = p.get("name") or p.get("broker") or p.get("brokers") or p.get("id")
        if not name:
            raise ValueError(
                "Parameter 'broker' or 'name' is required for action=delete."
            )
        brokers = s.brokers()
        target_ids: list[str] = []
        for item in name.split(","):
            item_clean = item.strip()
            matched = [
                b
                for b in brokers
                if str(b.get("id")) == item_clean
                or b.get("name", "").lower() == item_clean.lower()
            ]
            if matched:
                target_ids.append(str(matched[0]["id"]))
            elif item_clean.isdigit():
                target_ids.append(item_clean)
        if target_ids:
            s.delete_broker(target_ids)
        return cls._res("delete", f"Deleted broker profile '{name}'.", name=name)

    @classmethod
    def _handle_import_stocks(cls, p: dict[str, str], s: Broker) -> dict[str, Any]:
        name = p.get("name") or p.get("broker")
        if not name:
            raise ValueError(
                "Parameter 'broker' or 'name' is required for action=importstocks."
            )
        brokers = s.brokers()
        matched = [
            b
            for b in brokers
            if str(b.get("id")) == name or b.get("name", "").lower() == name.lower()
        ]
        b_id = str(matched[0]["id"]) if matched else name
        fp = p.get("filepath") or p.get("file")
        symbols: list[str] = []
        if fp and (path := Path(fp)).exists():
            symbols = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        elif "symbols" in p:
            symbols = [x.strip() for x in p["symbols"].split(",") if x.strip()]
        res = s.edit_stocks(b_id, symbols)
        return cls._res(
            "importstocks",
            f"Imported {len(symbols)} stock(s) to '{name}'.",
            result=res,
            count=len(symbols),
        )

    @classmethod
    def _handle_export_stocks(cls, p: dict[str, str], s: Broker) -> dict[str, Any]:
        name = p.get("name") or p.get("broker")
        if not name:
            raise ValueError(
                "Parameter 'broker' or 'name' is required for action=exportstocks."
            )
        rows = [b for b in s.brokers() if b.get("name", "").lower() == name.lower()]
        if not rows:
            raise LookupError(f"Broker profile '{name}' not found.")
        stocks = rows[0].get("stocks", [])
        fp = p.get("filepath") or p.get("file")
        if fp:
            Path(fp).write_text("\n".join(stocks), encoding="utf-8")
        return cls._res(
            "exportstocks",
            f"Exported {len(stocks)} stock(s) for '{name}'.",
            count=len(stocks),
            stocks=stocks,
        )
