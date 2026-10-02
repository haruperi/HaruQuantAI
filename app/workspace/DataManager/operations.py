# ruff: noqa: PLR2004 -- binary format constants and explicit bounds.
"""Retained Data Manager operations through explicit custody.

Description:
    Inspects and exports real retained rows and manages definitions without
    resolving operational paths or loading a concrete acquisition plugin.
Purpose:
    FEAT-DM-ACTIONS: Producer-independent Data Manager workflows.
Key Capabilities:
    - FR-DM-BROKER-TIME-EXPORT:
      Preserve original export times; export logs identify dataset and row count.
    - FR-DM-EXPORT: Actual source rows and standard export bytes; logs row counts.
    - FR-DM-CLONE: Explicit timestamp transformation; logs publication.
    - FR-DM-DEFINITIONS: Durable definition transfer; logs accepted records.
Python API Usage:
    result = execute(market, "actions.export_to_csv", request)
CLI Usage:
    uv run pytest tests/workspace/DataManager --no-cov
"""

from __future__ import annotations

import base64
import io
import json
import math
import re
import struct
import zipfile
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]

from app.host.capabilities import MarketAccess, SettingsAccess
from app.host.logging import get_logger
from app.workspace.DataManager.actions import TIMEFRAME_MINUTES, source_view
from app.workspace.DataManager.catalogs import Instrument, catalog_operation

logger = get_logger(__name__)


def inventory_presentation(
    market: MarketAccess, settings: SettingsAccess | None
) -> list[dict[str, Any]]:
    """Project authoritative broker names without changing durable definitions."""
    rows = [
        dict(row) for row in market.inventory() if row["source"] != "ExternalIndicator"
    ]
    brokers = (
        catalog_operation(settings, market, "catalogs.get", {"kind": "brokers"})[
            "state"
        ]["brokers"]
        if settings
        else list(market.list_all_brokers())
    )
    names = {row["id"]: row["name"] for row in brokers}
    names.update(
        {
            row["databaseBrokerId"]: row["name"]
            for row in brokers
            if row.get("databaseBrokerId")
        }
    )
    names["-1"] = "Default"
    for row in rows:
        stored = str(row.get("brokerName") or "")
        row["brokerName"] = names.get(
            row["broker"],
            stored
            if stored and stored != row["broker"] and not stored.lstrip("-").isdigit()
            else "Unknown broker",
        )
    logger.info("Projected dataset inventory names: rows=%d", len(rows))
    return rows


def resolve(market: MarketAccess, values: dict[str, Any]) -> dict[str, Any]:
    """Resolve an exact dataset ID or reject ambiguous symbol selections."""
    dataset_id = values.get("dataset_id")
    if dataset_id:
        return market.retained_source(str(dataset_id))
    rows = [row for row in market.inventory() if row["symbol"] == values.get("symbol")]
    if len(rows) != 1:
        raise ValueError("Select an exact dataset identity")
    return market.retained_source(str(rows[0]["id"]))


def selected(market: MarketAccess, values: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve every selection before applying a management mutation."""
    names = values.get("dataset_ids", values.get("symbols", []))
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ValueError("Invalid dataset selection")
    if not names:
        return [
            row for row in market.inventory() if row["source"] != "ExternalIndicator"
        ]
    rows = []
    for name in dict.fromkeys(names):
        matches = [row for row in market.inventory() if row["id"] == name]
        rows.append(matches[0] if matches else resolve(market, {"symbol": name}))
    return rows


def shifted(index: pd.DatetimeIndex, timezone: str) -> pd.DatetimeIndex:
    """Transform to requested wall timestamps with explicit fixed or IANA zone."""
    if timezone in ("", "Original", "UTC"):
        return index
    match = re.fullmatch(r"(?:UTC)?([+-]?\d{1,2})(?:h)?", timezone)
    if match:
        hours = int(match[1])
        if abs(hours) > 23:
            raise ValueError("Timezone shift exceeds 23 hours")
        return index + pd.Timedelta(hours=hours)
    return index.tz_convert(ZoneInfo(timezone)).tz_localize(None).tz_localize("UTC")


def export_timezone(record: dict[str, Any], values: dict[str, Any]) -> str:
    """Require qualified conversion for original broker coordinates."""
    target = str(values.get("target_timezone") or "Original")
    if record["timezone"] == "Exchange/Broker" and target not in (
        "Original",
        "Exchange/Broker",
    ):
        raise ValueError("Broker-time conversion requires a verified historical policy")
    return "Original" if target == "Exchange/Broker" else target


def text_export(
    market: MarketAccess, operation: str, values: dict[str, Any]
) -> dict[str, Any]:
    """Export lossless prices and source volumes, with truthful column headers."""
    record = resolve(market, values)
    request = {**values, "dataset_id": record["id"]}
    target = export_timezone(record, values)
    _, frame, timeframe = source_view(market, request)
    frame.index = shifted(frame.index, target)
    mt5 = operation == "actions.export_to_mt5"
    if frame.empty:
        raise ValueError("No rows in the selected export range")
    output = pd.DataFrame(index=frame.index)
    output["<DATE>"] = frame.index.strftime("%Y.%m.%d")
    output["<TIME>"] = frame.index.strftime("%H:%M:%S.%f").str.slice(0, 12)
    ticks = "Bid" in frame
    columns = ("Bid", "Ask", "Volume") if ticks else tuple(frame.columns)
    for column in columns:
        output[f"<{column.upper()}>"] = frame[column].values
    if mt5 and ticks:
        if values.get("spread_mode", "real") == "fixed":
            digits = int(values.get("digits", 5))
            output["<ASK>"] = (
                output["<BID>"] + int(values.get("spread_points", 10)) / 10**digits
            )
        output["<LAST>"] = output["<BID>"]
        output["<FLAGS>"] = 6
        output = output[
            ["<DATE>", "<TIME>", "<BID>", "<ASK>", "<LAST>", "<VOLUME>", "<FLAGS>"]
        ]
    elif mt5:
        output["<TICKVOL>"] = output["<VOLUME>"]
        output["<VOL>"] = output["<VOLUME>"]
        output["<SPREAD>"] = int(values.get("spread_points", 10))
        output = output.drop(columns=["<VOLUME>"])
    if not mt5 and values.get("header") and values.get("include_header", True):
        header = str(values["header"]).split(",")
        if len(header) != len(output.columns):
            projected = [
                "<" + label.strip().strip("<>").upper() + ">" for label in header
            ]
            projected = [
                "<VOLUME>" if label == "<VOL>" else label for label in projected
            ]
            if len(set(projected)) == len(projected) and all(
                label in output.columns for label in projected
            ):
                output = output[projected]
        if len(header) != len(output.columns) or any(
            not label.strip() for label in header
        ):
            raise ValueError(
                "Provide one nonempty header label for each exported column"
            )
        output.columns = header
    content = output.to_csv(
        index=False,
        sep="\t" if mt5 else ",",
        header=bool(values.get("include_header", True)),
        lineterminator="\n",
    )
    logger.info("Exported retained rows: id=%s rows=%d", record["id"], len(frame))
    return {
        "success": True,
        "symbol": record["symbol"],
        "timeframe": timeframe,
        "kind": "ticks" if ticks else "m1",
        "records": len(frame),
        "contentLength": len(content),
        "content": content,
    }


def mt4_export(  # noqa: C901 -- two binary output formats.
    market: MarketAccess, values: dict[str, Any]
) -> dict[str, Any]:
    """Return binary HST files and actual tick FXT records in a downloadable ZIP."""
    record = resolve(market, values)
    target = str(values.get("mt4_symbol") or record["instrument"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,11}", target):
        raise ValueError("MT4 symbol requires 1-11 ASCII filename characters")
    digits, spread = int(values.get("digits", 5)), int(values.get("spread", 20))
    if not 0 <= digits <= 10 or not 0 <= spread <= 100000:
        raise ValueError("Invalid MT4 precision or spread")
    timeframes = (
        ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        if values.get("timeframe", "All") == "All"
        else [str(values["timeframe"])]
    )
    mode = values.get("export_mode", "All")
    if mode not in ("All", "hst", "fxt"):
        raise ValueError("Invalid MT4 export mode")
    buffer = io.BytesIO()
    names: list[str] = []
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if mode in ("All", "hst"):
            for timeframe in timeframes:
                _, bars, _ = source_view(
                    market,
                    {**values, "dataset_id": record["id"], "timeframe": timeframe},
                )
                bars.index = shifted(
                    bars.index, str(values.get("target_timezone") or "Original")
                )
                if bars.empty or "Open" not in bars:
                    raise ValueError("MT4 HST requires nonempty candle data")
                stream = io.BytesIO()
                stream.write(
                    struct.pack(
                        "<I64s12sIIII52s",
                        401,
                        b"(C)opyright 2003, MetaQuotes Software Corp.",
                        target.encode(),
                        TIMEFRAME_MINUTES[timeframe],
                        digits,
                        0,
                        0,
                        bytes(52),
                    )
                )
                for stamp, row in bars.iterrows():
                    stream.write(
                        struct.pack(
                            "<QddddQiQ",
                            int(stamp.timestamp()),
                            row["Open"],
                            row["High"],
                            row["Low"],
                            row["Close"],
                            int(row["Volume"]),
                            spread,
                            int(row["Volume"]),
                        )
                    )
                filename = f"{target}{TIMEFRAME_MINUTES[timeframe]}.hst"
                archive.writestr(filename, stream.getvalue())
                names.append(filename)
        if mode in ("All", "fxt"):
            _, ticks, _ = source_view(
                market,
                {
                    **values,
                    "dataset_id": record["id"],
                    "timeframe": record["timeframe"],
                },
            )
            if ticks.empty or "Bid" not in ticks:
                raise ValueError("MT4 tick model requires retained tick rows")
            ticks.index = shifted(
                ticks.index, str(values.get("target_timezone") or "Original")
            )
            stream = io.BytesIO()
            server = str(values.get("server_name", "MetaQuotes-Demo")).encode("ascii")[
                :127
            ]
            header = struct.pack(
                "<I64s128s16sIIIII",
                405,
                b"HaruQuantAI MT4 FXT Tick Model",
                server,
                target.encode(),
                1,
                0,
                len(ticks.index.floor("min").unique()),
                int(ticks.index[0].timestamp()),
                int(ticks.index[-1].timestamp()),
            )
            stream.write(header.ljust(728, b"\0"))
            for stamp, row in ticks.iterrows():
                seconds = int(stamp.timestamp())
                bid = float(row["Bid"])
                stream.write(
                    struct.pack(
                        "<QddddQii",
                        seconds - seconds % 60,
                        bid,
                        bid,
                        bid,
                        bid,
                        int(row["Volume"]),
                        seconds,
                        7,
                    )
                )
            filename = f"{target}1_0.fxt"
            archive.writestr(filename, stream.getvalue())
            names.append(filename)
    logger.info("Generated MT4 binary export: id=%s files=%d", record["id"], len(names))
    return {
        "success": True,
        "symbol": target,
        "files": names,
        "archive_base64": base64.b64encode(buffer.getvalue()).decode(),
    }


def edit_rows(  # noqa: C901, PLR0912 -- bounded source-type edit validation.
    market: MarketAccess, values: dict[str, Any]
) -> dict[str, Any]:
    """Apply timestamp-addressed edits to stored rows with optimistic revisions."""
    record = resolve(market, values)
    if record["timezone"] == "Exchange/Broker":
        raise ValueError(
            "Broker-time edits require source-specific record identification"
        )
    if values.get("timeframe", record["timeframe"]) != record["timeframe"]:
        raise ValueError("Edit the stored timeframe; aggregated views cannot be edited")
    revisions = values.get("expected_revisions")
    if not isinstance(revisions, dict) or any(
        not isinstance(key, str) or not isinstance(value, int)
        for key, value in revisions.items()
    ):
        raise ValueError("A complete revision map is required for editing")
    changes = values.get("changes")
    if not isinstance(changes, list) or not changes or len(changes) > 10000:
        raise ValueError("Select 1-10,000 stored row changes")
    table = market.read_source(str(record["id"]))
    frame = table.to_pandas().set_index("DateTime")
    if not frame.index.is_unique:
        raise ValueError(
            "Duplicate timestamps require source-specific row identification"
        )
    for change in changes:
        if not isinstance(change, dict) or set(change) - {
            "timestamp",
            "values",
            "delete",
        }:
            raise ValueError("Invalid row change")
        stamp = pd.to_datetime(change.get("timestamp"), utc=True)
        if stamp not in frame.index:
            raise ValueError("Edited timestamp no longer exists")
        if change.get("delete", False):
            frame = frame.drop(stamp)
            continue
        edits = change.get("values")
        if not isinstance(edits, dict) or not edits or set(edits) - set(frame.columns):
            raise ValueError("Invalid editable columns")
        for column, value in edits.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Edits require finite numeric values")
            edited_value = value
            dtype = frame[column].dtype
            if column in ("Bid", "Ask") and pd.api.types.is_integer_dtype(dtype):
                edited_value = round(value * 1_000_000)
            if pd.api.types.is_integer_dtype(dtype) and edited_value != int(
                edited_value
            ):
                raise ValueError("This source column requires an integer")
            frame.loc[stamp, column] = edited_value
        row = frame.loc[stamp]
        if "Volume" in row and row["Volume"] < 0:
            raise ValueError("Volume cannot be negative")
        if "Ask" in row and row["Ask"] < row["Bid"]:
            raise ValueError("Ask cannot be below bid")
        if "Open" in row and (
            row["High"] < max(row["Open"], row["Low"], row["Close"])
            or row["Low"] > min(row["Open"], row["Close"])
        ):
            raise ValueError("Invalid OHLC bounds")
    frame = frame.reset_index().sort_values("DateTime")
    partitions = {
        str(year): pa.Table.from_pandas(part, schema=table.schema, preserve_index=False)
        for year, part in frame.groupby(frame["DateTime"].dt.year)
    }
    market.replace_source(str(record["id"]), partitions, expected_revisions=revisions)
    logger.info("Saved stored data edits: id=%s changes=%d", record["id"], len(changes))
    return {
        "success": True,
        "symbol": record["symbol"],
        "changedRows": len(changes),
        "bars": len(frame),
    }


def validate_definition_batch(rows: list[dict[str, Any]]) -> None:
    """Reject malformed or internally conflicting metadata before any write."""
    identity_fields = (
        "source",
        "symbol",
        "underlying",
        "instrument",
        "timeframe",
        "timezone",
        "broker",
    )
    identities: dict[tuple[str, ...], str] = {}
    for row in rows:
        if any(
            not isinstance(row.get(key), str) or not 1 <= len(row[key]) <= 160
            for key in ("owner", *identity_fields)
        ):
            raise ValueError("Invalid definition identity")
        if not re.fullmatch(
            r"(?:plugin\.data_manager\.[a-z_]+|workspace\.data_manager)",
            row["owner"],
        ):
            raise ValueError("Invalid definition owner")
        if row["timezone"] == "Exchange/Broker":
            if (
                row["source"] != "MT5"
                or row["owner"] != "plugin.data_manager.meta_trader"
                or row.get("options", {}).get("timestamp_basis") != "broker_reported"
            ):
                raise ValueError("Invalid broker-time source definition")
        else:
            ZoneInfo(row["timezone"])
        if not isinstance(row.get("options", {}), dict):
            raise TypeError("Invalid provider options")
        encoded = json.dumps(row.get("options", {}), allow_nan=False, sort_keys=True)
        identity = tuple(row[key] for key in ("owner", *identity_fields))
        if identity in identities and identities[identity] != encoded:
            raise ValueError("Conflicting definition options")
        identities[identity] = encoded


def transfer_definitions(
    market: MarketAccess,
    operation: str,
    values: dict[str, Any],
    settings: SettingsAccess | None,
) -> dict[str, Any]:
    """Transfer validated definitions and durable configured instruments."""
    if operation == "actions.save":
        rows = [
            market.export_definition(str(row["id"])) for row in selected(market, values)
        ]
        instruments = []
        if settings is not None:
            state = catalog_operation(
                settings, market, "catalogs.get", {"kind": "instruments"}
            )["state"]
            configured = {row["symbol"]: row for row in state["instruments"]}
            configured.update(state["overrides"])
            names = {row["instrument"] for row in rows}
            instruments = [
                row
                for name, row in configured.items()
                if name not in state["removed"]
                and (
                    (not values.get("symbols") and not values.get("dataset_ids"))
                    or name in names
                )
            ]
        return {
            "success": True,
            "datasetsCount": len(rows),
            "instrumentsCount": len(instruments),
            "content": json.dumps(
                {"version": 1, "datasets": rows, "instruments": instruments},
                allow_nan=False,
            ),
        }
    if operation == "actions.load":
        rows = values.get("definitions", [])
        if (
            not isinstance(rows, list)
            or len(rows) > 10000
            or any(not isinstance(row, dict) for row in rows)
        ):
            raise ValueError("Invalid definition transfer")
        incoming = values.get("instruments", [])
        if not isinstance(incoming, list) or len(incoming) > 10000:
            raise ValueError("Invalid instrument transfer")
        instruments = [
            Instrument.model_validate(row).model_dump(mode="json") for row in incoming
        ]
        if instruments and settings is None:
            raise ValueError("Instrument catalog custody unavailable")
        validate_definition_batch(rows)
        ids = [market.import_definition(row) for row in rows]
        if instruments and settings is not None:
            catalog = catalog_operation(
                settings, market, "catalogs.get", {"kind": "instruments"}
            )
            state = catalog["state"]
            configured = {row["symbol"]: row for row in state["instruments"]}
            configured.update({row["symbol"]: row for row in instruments})
            state["instruments"] = list(configured.values())
            for row in instruments:
                state["overrides"].pop(row["symbol"], None)
            state["removed"] = [
                name
                for name in state["removed"]
                if name not in {row["symbol"] for row in instruments}
            ]
            catalog_operation(
                settings,
                market,
                "catalogs.replace",
                {
                    "kind": "instruments",
                    "revision": catalog["revision"],
                    "state": state,
                },
            )
        return {
            "success": True,
            "loadedDatasets": len(ids),
            "loadedInstruments": len(instruments),
            "dataset_ids": ids,
        }
    raise ValueError("Unknown definition transfer operation")


def execute(  # noqa: C901, PLR0912 -- workspace operation boundary.
    market: MarketAccess,
    operation: str,
    values: dict[str, Any],
    settings: SettingsAccess | None = None,
) -> dict[str, Any]:
    """Manage retained source resources with no arbitrary database/path overrides."""
    if any(
        key in values
        for key in ("db_path", "data_root", "output_path", "output_dir", "file_path")
    ):
        raise ValueError("Caller filesystem destinations are not accepted")
    logger.info("Executing retained Data Manager operation: %s", operation)
    if operation == "actions.save_data_changes":
        return edit_rows(market, values)
    if operation in ("actions.export_to_csv", "actions.export_to_mt5"):
        return text_export(market, operation, values)
    if operation == "actions.export_to_mt4":
        return mt4_export(market, values)
    if operation in ("actions.save", "actions.load"):
        return transfer_definitions(market, operation, values, settings)
    if operation == "actions.delete":
        if not values.get("symbols") and not values.get("dataset_ids"):
            raise ValueError("Select datasets to delete")
        rows = selected(market, values)
        mode = values.get("mode", "remove")
        if mode not in ("clear", "remove"):
            raise ValueError("Invalid deletion mode")
        for row in rows:
            market.remove_source(str(row["id"]), clear_only=mode == "clear")
        return {
            "success": True,
            "deletedCount": len(rows),
            "mode": mode,
            "deleted": [row["symbol"] for row in rows],
        }
    if operation == "actions.clone_to_timezone":
        record = resolve(market, values)
        if record["timezone"] == "Exchange/Broker":
            raise ValueError(
                "Broker-time conversion requires a verified historical policy"
            )
        if record["source"] == "Clone":
            raise ValueError("Cloned data cannot be cloned again")
        table = market.read_source(str(record["id"]))
        frame = table.to_pandas()
        shift = int(values.get("shift_hours", 0))
        timezone = str(values.get("timezone", f"UTC{shift:+d}"))
        frame["DateTime"] = shifted(pd.DatetimeIndex(frame["DateTime"]), timezone)
        if values.get("remove_weekends", False):
            frame = frame[frame["DateTime"].dt.dayofweek < 5]
        if frame.empty:
            raise ValueError("Clone contains no rows after filtering")
        postfix = (
            str(values.get("postfix", "_clone"))
            .replace("{timeframe}", str(record["timeframe"]))
            .replace("{cloneTime}", datetime.now(UTC).strftime("%Y%m%d%H%M%S"))
        )
        dataset_id = market.register_source(
            source="Clone",
            symbol=record["symbol"] + postfix,
            underlying=record["underlying"],
            instrument=record["instrument"],
            timeframe=record["timeframe"],
            timezone=timezone,
            broker=record["broker"],
            options={"source_data_id": record["id"], "shift_hours": shift},
        )
        for year, part in frame.groupby(frame["DateTime"].dt.year):
            market.publish_source(
                dataset_id,
                str(year),
                pa.Table.from_pandas(part, schema=table.schema, preserve_index=False),
            )
        return {
            "success": True,
            "sourceSymbol": record["symbol"],
            "clonedSymbol": record["symbol"] + postfix,
            "bars": len(frame),
            "shiftHours": shift,
            "timezone": timezone,
            "underlying": record["underlying"],
        }
    raise ValueError("Unknown retained Data Manager operation")
