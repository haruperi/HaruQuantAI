"""Data Manager baskets (stock groups) catalog service.

Python API Usage:
    ```python
    from app.workspace.data_manager.baskets import Baskets

    baskets_svc = Baskets()
    baskets = baskets_svc.list()
    created = baskets_svc.add("My stocks", description="Watchlist")
    members = baskets_svc.edit_stocks("My stocks", "AAPL;01.01.2020")
    exported = baskets_svc.save("groups.json", "My stocks")
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.baskets
    ```
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import time
import uuid
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import IO

    from app.host.jobs import JobContext, JobManager

from app.host.logging import get_logger
from app.host.persistence import HostPersistence, RecordFilter
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

__all__ = [
    "BasketInfo",
    "BasketStockItem",
    "Baskets",
]

logger = get_logger(__name__)
persistence = HostPersistence()

BASKETS_CATALOG_FR = "FR-DATAMGR-BASKETS-CATALOG"
DESC_PARTS_MIN_LEN: int = 3


def _ms_to_date(ms: int) -> str:
    """Convert millisecond timestamp to DD.MM.YYYY string."""
    if ms in (0, -1):
        return "-"
    try:
        dt = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=ms)
        return dt.strftime("%d.%m.%Y")
    except OverflowError, OSError, ValueError:
        return "-"


@dataclass(slots=True)
class BasketStockItem:
    """Constituent stock membership in a basket."""

    id: int = 0
    ticker: str = ""
    basket_id: int = 0
    date_from: int = 0
    date_to: int = -1

    def to_dict(self) -> dict[str, Any]:
        """Serialize BasketStockItem to a dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> BasketStockItem:
        """Construct BasketStockItem from datamgr_stock table row."""
        raw_date_to = row.get("DATE_TO")
        if raw_date_to is None:
            raw_date_to = row.get("date_to")
        date_to = int(raw_date_to) if raw_date_to is not None else -1
        return cls(
            id=int(row.get("ID") or row.get("id") or 0),
            ticker=str(row.get("TICKER") or row.get("ticker") or ""),
            basket_id=int(row.get("BASKET_ID") or row.get("basket_id") or 0),
            date_from=int(row.get("DATE_FROM") or row.get("date_from") or 0),
            date_to=date_to,
        )


@dataclass(slots=True)
class BasketInfo:
    """Basket (stock group) catalog record definition."""

    id: int = 0
    name: str = ""
    system: bool = False
    description: str = ""
    stocks_count: int = 0
    active_count: int = 0
    symbols_count: int = 0
    downloaded_count: int = 0
    ready: bool = False
    date_from: str = "-"
    date_to: str = "-"
    stocks: list[BasketStockItem] = field(default_factory=list[BasketStockItem])

    def to_dict(self) -> dict[str, Any]:
        """Serialize BasketInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_group_row(
        cls,
        row: Mapping[str, Any],
        stocks: list[BasketStockItem] | None = None,
        downloaded_symbols: set[str] | None = None,
    ) -> BasketInfo:
        """Construct BasketInfo from datamgr_stock_group row and constituent stocks."""
        desc = str(row.get("description") or row.get("DESC") or "")
        stock_list = stocks if stocks is not None else []
        stocks_count = len(stock_list)

        now_ms = int(time.time() * 1000)
        active_count = sum(
            1
            for s in stock_list
            if s.date_from <= now_ms and (s.date_to == -1 or s.date_to >= now_ms)
        )

        downloaded_set = (
            downloaded_symbols if downloaded_symbols is not None else set[str]()
        )
        downloaded_count = sum(
            1
            for s in stock_list
            if (
                s.ticker.upper().split(".")[0] in downloaded_set
                or s.ticker.upper() in downloaded_set
            )
        )
        symbols_count = downloaded_count

        ready = stocks_count > 0 and downloaded_count >= stocks_count

        valid_from = [s.date_from for s in stock_list if s.date_from != 0]
        date_from = _ms_to_date(min(valid_from)) if valid_from else "-"

        valid_to = [s.date_to for s in stock_list if s.date_to > 0]
        date_to = _ms_to_date(max(valid_to)) if valid_to else "-"

        if (date_from == "-" or date_to == "-") and ";" in desc:
            parts = [p.strip() for p in desc.split(";")]
            if len(parts) >= DESC_PARTS_MIN_LEN:
                if date_from == "-" and parts[1]:
                    date_from = parts[1]
                if date_to == "-" and parts[2]:
                    date_to = parts[2]

        return cls(
            id=int(row.get("ID") or row.get("id") or 0),
            name=str(row.get("NAME") or row.get("name") or ""),
            system=bool(row.get("SYSTEM") or row.get("system") or 0),
            description=desc,
            stocks_count=stocks_count,
            active_count=active_count,
            symbols_count=symbols_count,
            downloaded_count=downloaded_count,
            ready=ready,
            date_from=date_from,
            date_to=date_to,
            stocks=stock_list,
        )


type BasketTargets = str | int | Sequence[str | int]
_MAX_NAME = 50
_MAX_DESCRIPTION = 250
_MAX_TIMESTAMP = 253402300799999
_MIN_TIMESTAMP = -62135596800000
_DAY_MS = 86400000
_CSV_COLUMNS = 3


class _BasketError(ValueError):
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.VALIDATION,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _error_code(error: Exception) -> ErrorCode:
    if isinstance(error, _BasketError):
        return error.code
    return ErrorCode.INTERNAL


def _records(response: dict[str, Any]) -> list[dict[str, Any]]:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise _BasketError(
            response.get("message") or "Basket storage failed",
            ErrorCode(error.get("code", "internal")),
        )
    return cast("list[dict[str, Any]]", response["data"]["records"])


def _read_all(
    gateway: HostPersistence, table: str, filters: Mapping[str, Any] | None = None
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        response = gateway.read_records(
            table, filters=filters, limit=1000, offset=offset
        )
        rows.extend(_records(response))
        offset = response["data"]["pagination"].get("next_offset")
    return rows


def _targets(targets: BasketTargets) -> list[str | int]:
    values: list[object] = (
        [targets] if isinstance(targets, (str, int)) else list(targets)
    )
    result: list[str | int] = []
    for raw in values:
        value = raw
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise _BasketError("Choose a group name or positive integer ID")
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise _BasketError("Group name is required")
        elif value <= 0:
            raise _BasketError("Group ID must be positive")
        if value not in result:
            result.append(value)
    if not result:
        raise _BasketError("Select at least one group")
    return result


def _lookup(gateway: HostPersistence, target: str | int) -> dict[str, Any]:
    target = _targets(target)[0]
    rows = _records(
        gateway.read_records(
            "datamgr_stock_group",
            filters={"ID" if isinstance(target, int) else "NAME": target},
            limit=2,
        )
    )
    if not rows:
        raise _BasketError(f"Group '{target}' not found", ErrorCode.NOT_FOUND)
    if len(rows) != 1:
        raise _BasketError(
            "Group name is ambiguous; use its integer ID", ErrorCode.CONFLICT
        )
    return rows[0]


def _custom(group: Mapping[str, Any]) -> None:
    if group["SYSTEM"]:
        raise _BasketError("System stock groups cannot be changed")


def _description(group: Mapping[str, Any]) -> str:
    return str(group.get("description") or group.get("DESC") or "")


def _group_row(name: Any, description: Any, system: Any) -> dict[str, Any]:
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > _MAX_NAME:
        raise _BasketError("Group name must contain 1-50 characters")
    if not isinstance(description, str) or len(description) > _MAX_DESCRIPTION:
        raise _BasketError("Group description must contain at most 250 characters")
    if not isinstance(system, bool):
        raise _BasketError("system must be a boolean")
    return {
        "NAME": name.strip(),
        "SYSTEM": int(system),
        "DESC": description,
        "description": description,
    }


def _unique(gateway: HostPersistence, name: str, excluding: int = 0) -> None:
    if any(
        row["ID"] != excluding and row["NAME"].casefold() == name.casefold()
        for row in _read_all(gateway, "datamgr_stock_group")
    ):
        raise _BasketError(f"Group '{name}' already exists", ErrorCode.CONFLICT)


def _date(value: Any, *, end: bool = False) -> int:
    if isinstance(value, str):
        value = value.strip()
    if value is None or value == "":
        return -1 if end else 0
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            value = int(text)
        else:
            try:
                fmt = "%d.%m.%Y" if "." in text else "%Y-%m-%d"
                parsed = datetime.strptime(text, fmt).replace(tzinfo=UTC)
                if parsed.strftime(fmt) != text:
                    raise ValueError("Non-canonical date")  # noqa: TRY301
                value = int(
                    (parsed - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds() * 1000
                )
            except (ValueError, OverflowError, OSError) as error:
                raise _BasketError(
                    "Dates must use DD.MM.YYYY, YYYY-MM-DD or Unix milliseconds"
                ) from error
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not _MIN_TIMESTAMP <= value <= _MAX_TIMESTAMP
    ):
        raise _BasketError(
            "Membership timestamps must be integers within the supported date range"
        )
    if value == -1 and not end:
        raise _BasketError("Only date_to may use -1 for ongoing membership")
    return int(value)


def _csv_date(value: Any, *, end: bool = False) -> str:
    timestamp = _date(value, end=end)
    if timestamp == -1 or (timestamp == 0 and not end):
        return ""
    if timestamp % _DAY_MS:
        return str(timestamp)
    return (
        datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=timestamp)
    ).strftime("%d.%m.%Y")


def _stock_row(item: Mapping[str, Any] | BasketStockItem) -> dict[str, Any]:
    values = item.to_dict() if isinstance(item, BasketStockItem) else dict(item)
    unknown = values.keys() - {"id", "basket_id", "ticker", "date_from", "date_to"}
    if unknown:
        raise _BasketError(f"Unknown membership fields: {', '.join(sorted(unknown))}")
    ticker = values.get("ticker")
    if (
        not isinstance(ticker, str)
        or not ticker.strip()
        or len(ticker.strip()) > _MAX_NAME
        or any(c in ticker for c in "\r\n;")
    ):
        raise _BasketError("Ticker must contain 1-50 characters without delimiters")
    start = _date(values.get("date_from"))
    end = _date(values.get("date_to"), end=True)
    if end != -1 and end < start:
        raise _BasketError("Membership end precedes its start")
    return {"TICKER": ticker.strip(), "DATE_FROM": start, "DATE_TO": end}


def _normalize_stocks(
    stocks: str | Sequence[Mapping[str, Any] | BasketStockItem],
) -> list[dict[str, Any]]:
    items: list[object] = []
    if isinstance(stocks, str):
        try:
            for fields in csv.reader(io.StringIO(stocks), delimiter=";", strict=True):
                if not fields or not any(field.strip() for field in fields):
                    continue
                if len(fields) > _CSV_COLUMNS:
                    raise _BasketError("Stock CSV requires ticker;date_from;date_to")
                padded = fields + [""] * (_CSV_COLUMNS - len(fields))
                items.append(
                    {"ticker": padded[0], "date_from": padded[1], "date_to": padded[2]}
                )
        except csv.Error as error:
            raise _BasketError("Invalid stock CSV") from error
    else:
        items = list(stocks)
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for item in items:
        if not isinstance(item, (Mapping, BasketStockItem)):
            raise _BasketError("Each membership must be an object")
        row = _stock_row(cast("Mapping[str, Any] | BasketStockItem", item))
        key = (row["TICKER"].casefold(), row["DATE_FROM"], row["DATE_TO"])
        if key in seen:
            raise _BasketError("Duplicate stock membership interval")
        seen.add(key)
        result.append(row)
    return result


def _membership_rows(gateway: HostPersistence, basket_id: int) -> list[dict[str, Any]]:
    return _read_all(gateway, "datamgr_stock", {"BASKET_ID": basket_id})


def _clear_memberships(gateway: HostPersistence, basket_id: int) -> None:
    while True:
        rows = _records(
            gateway.read_records(
                "datamgr_stock", filters={"BASKET_ID": basket_id}, limit=1000
            )
        )
        if not rows:
            return
        _records(
            gateway.delete_record(
                "datamgr_stock",
                filters=[RecordFilter("ID", "in", [r["ID"] for r in rows])],
            )
        )


def _replace_memberships(
    gateway: HostPersistence, basket_id: int, rows: list[dict[str, Any]]
) -> list[BasketStockItem]:
    _clear_memberships(gateway, basket_id)
    result: list[BasketStockItem] = []
    for start in range(0, len(rows), 1000):
        records = _records(
            gateway.create_records(
                "datamgr_stock",
                [{**r, "BASKET_ID": basket_id} for r in rows[start : start + 1000]],
            )
        )
        result.extend(BasketStockItem.from_row(r) for r in records)
    return result


@contextmanager
def _atomic_text(target: Path) -> Generator[IO[str]]:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            yield stream.file
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _json_groups(data: object) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    if not isinstance(data, list):
        raise _BasketError("Baskets JSON must be an array of group objects")
    result: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for item in cast("list[object]", data):
        if not isinstance(item, dict):
            raise _BasketError("Each group must be an object")
        values = cast("dict[str, Any]", item)
        if values.keys() - {"id", "name", "description", "system", "stocks"}:
            raise _BasketError("Unknown group fields in JSON")
        stocks = values.get("stocks", [])
        if not isinstance(stocks, list):
            raise _BasketError("stocks must be a membership array")
        row = _group_row(
            values.get("name"),
            values.get("description", ""),
            values.get("system", False),
        )
        result.append((row, _normalize_stocks(cast("list[Mapping[str, Any]]", stocks))))
    return result


def _download_one(
    gateway: HostPersistence, client: Any, ticker: str, folder: Path
) -> dict[str, Any]:
    frame = client.get_bars(ticker, "D1", count=100000)
    if (
        frame.empty
        or getattr(frame.index, "inferred_type", "") != "datetime64"
        or frame.index.hasnans
        or not {"Open", "High", "Low", "Close"}.issubset(frame.columns)
    ):
        raise _BasketError(
            f"No valid D1 bars returned for {ticker}", ErrorCode.UNAVAILABLE
        )
    frame = frame.sort_index()
    frame.index = (
        frame.index.tz_localize("UTC")
        if frame.index.tz is None
        else frame.index.tz_convert("UTC")
    )
    if frame.index.has_duplicates:
        frame = frame[~frame.index.duplicated(keep="last")]
    digest = hashlib.sha256(ticker.encode("utf-8")).hexdigest()[:24]
    target = folder / f"{digest}-{uuid.uuid4().hex}.parquet"
    now = datetime.now(UTC).isoformat()
    row: dict[str, Any] = {
        "id": f"basket-sq-equity-{digest}",
        "source": "sq-equity",
        "symbol": ticker,
        "underlying": ticker,
        "timeframe": "D1",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Stock",
        "date_from": frame.index.min().isoformat(),
        "date_to": frame.index.max().isoformat(),
        "bars": len(frame),
        "path": str(target.resolve()),
        "updated_at": now,
    }
    try:
        frame.to_parquet(target)
        with gateway.transaction() as tx:
            existing = _records(
                tx.read_records("datamgr_datasets", filters={"id": row["id"]}, limit=1)
            )
            if existing:
                _records(
                    tx.update_record("datamgr_datasets", row, filters={"id": row["id"]})
                )
            else:
                _records(
                    tx.create_records("datamgr_datasets", {**row, "created_at": now})
                )
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {
        "ticker": ticker,
        "dataset_id": row["id"],
        "bars": len(frame),
        "path": str(target.resolve()),
    }


class Baskets:
    """Service providing baskets and stock groups catalog presentation."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        jobs: JobManager | None = None,
        logs: Any = None,
    ) -> None:
        self.gateway = gateway if gateway is not None else persistence
        self.jobs = jobs
        self.logs = logs

    def _read_stock_groups(self) -> list[dict[str, Any]]:
        return _read_all(self.gateway, "datamgr_stock_group")

    def _read_stocks(self) -> list[dict[str, Any]]:
        return _read_all(self.gateway, "datamgr_stock")

    def _read_downloaded_symbols(self) -> set[str]:
        downloaded: set[str] = set()
        offset: int | None = 0
        while offset is not None:
            response = self.gateway.read_records(
                "datamgr_datasets", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data: dict[str, Any] = response["data"]
            records: list[dict[str, Any]] = data["records"]
            for record in records:
                symbol = str(record.get("symbol") or record.get("SYMBOL") or "").strip()
                if symbol and int(record.get("bars") or record.get("BARS") or 0) > 0:
                    downloaded.update((symbol.upper(), symbol.upper().split(".")[0]))
            offset = data["pagination"].get("next_offset")
        return downloaded

    def _run(self, operation: str, action: Callable[[], Any]) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            data = action()
            return StandardResponse.success(
                message=f"Completed baskets.{operation}",
                data=data,
                metadata=ResponseMetadata(
                    operation=f"baskets.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            return StandardResponse.failure(
                message=str(error),
                metadata=ResponseMetadata(
                    operation=f"baskets.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=_error_code(error),
                    message=str(error),
                    details=error.details if isinstance(error, _BasketError) else {},
                ),
            )

    def add(
        self, name: str = "", *, description: str = "", system: bool = False
    ) -> dict[str, Any]:
        """Create a uniquely named group; memberships are edited separately."""

        def action() -> BasketInfo:
            row = _group_row(name, description, system)
            with self.gateway.transaction() as tx:
                _unique(tx, row["NAME"])
                created = _records(tx.create_records("datamgr_stock_group", row))[0]
            return BasketInfo.from_group_row(created)

        return self._run("add", action)

    def edit(
        self,
        baskets: BasketTargets,
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Atomically edit group metadata; renaming requires a single group."""

        def action() -> list[BasketInfo]:
            targets = _targets(baskets)
            changes = {**(updates or {}), **kwargs}
            if not changes or changes.keys() - {"name", "description"}:
                raise _BasketError("Supply name and/or description to edit")
            if "name" in changes and len(targets) != 1:
                raise _BasketError("Rename requires exactly one group")
            result: list[BasketInfo] = []
            with self.gateway.transaction() as tx:
                for target in targets:
                    group = _lookup(tx, target)
                    _custom(group)
                    row = _group_row(
                        changes.get("name", group["NAME"]),
                        changes.get("description", _description(group)),
                        False,
                    )
                    _unique(tx, row["NAME"], group["ID"])
                    records = _records(
                        tx.update_record(
                            "datamgr_stock_group", row, filters={"ID": group["ID"]}
                        )
                    )
                    stocks = [
                        BasketStockItem.from_row(r)
                        for r in _membership_rows(tx, group["ID"])
                    ]
                    result.append(BasketInfo.from_group_row(records[0], stocks))
            return result

        return self._run("edit", action)

    def delete(self, baskets: BasketTargets) -> dict[str, Any]:
        """Delete groups and memberships atomically, keeping downloaded market data."""

        def action() -> list[BasketInfo]:
            result: list[BasketInfo] = []
            with self.gateway.transaction() as tx:
                for target in _targets(baskets):
                    group = _lookup(tx, target)
                    _custom(group)
                    stocks = [
                        BasketStockItem.from_row(r)
                        for r in _membership_rows(tx, group["ID"])
                    ]
                    _clear_memberships(tx, group["ID"])
                    _records(
                        tx.delete_record(
                            "datamgr_stock_group", filters={"ID": group["ID"]}
                        )
                    )
                    result.append(BasketInfo.from_group_row(group, stocks))
            return result

        return self._run("delete", action)

    def list_stocks(self, basket: str | int) -> dict[str, Any]:
        """Read all historical memberships for one named group or integer ID."""

        def action() -> list[BasketStockItem]:
            with self.gateway.transaction() as tx:
                group = _lookup(tx, basket)
                return [
                    BasketStockItem.from_row(r)
                    for r in _membership_rows(tx, group["ID"])
                ]

        return self._run("list_stocks", action)

    def edit_stocks(
        self,
        basket: str | int,
        stocks: str | Sequence[Mapping[str, Any] | BasketStockItem],
    ) -> dict[str, Any]:
        """Replace memberships using structured records or semicolon-separated text."""

        def action() -> list[BasketStockItem]:
            rows = _normalize_stocks(stocks)
            with self.gateway.transaction() as tx:
                group = _lookup(tx, basket)
                _custom(group)
                return _replace_memberships(tx, group["ID"], rows)

        return self._run("edit_stocks", action)

    def import_stocks(self, basket: str | int, csv_path: str | Path) -> dict[str, Any]:
        """Atomically replace memberships from UTF-8 ticker;from;to CSV (no header)."""

        def action() -> list[BasketStockItem]:
            rows = _normalize_stocks(Path(csv_path).read_text(encoding="utf-8-sig"))
            with self.gateway.transaction() as tx:
                group = _lookup(tx, basket)
                _custom(group)
                return _replace_memberships(tx, group["ID"], rows)

        return self._run("import_stocks", action)

    def export_stocks(self, basket: str | int, csv_path: str | Path) -> dict[str, Any]:
        """Export full membership history as semicolon-separated UTF-8 CSV."""

        def action() -> dict[str, Any]:
            with self.gateway.transaction() as tx:
                group = _lookup(tx, basket)
                rows = _membership_rows(tx, group["ID"])
            with _atomic_text(Path(csv_path)) as stream:
                writer = csv.writer(stream, delimiter=";", lineterminator="\n")
                for row in rows:
                    writer.writerow(
                        (
                            row["TICKER"],
                            _csv_date(row["DATE_FROM"]),
                            _csv_date(row.get("DATE_TO"), end=True),
                        )
                    )
            return {"path": str(csv_path), "count": len(rows)}

        return self._run("export_stocks", action)

    def save(
        self, json_path: str | Path, baskets: BasketTargets | None = None
    ) -> dict[str, Any]:
        """Export all or selected groups, including their full membership histories."""

        def action() -> dict[str, Any]:
            with self.gateway.transaction() as tx:
                groups = (
                    _read_all(tx, "datamgr_stock_group")
                    if baskets is None
                    else [_lookup(tx, target) for target in _targets(baskets)]
                )
                data = [
                    {
                        "name": g["NAME"],
                        "description": _description(g),
                        "system": bool(g["SYSTEM"]),
                        "stocks": [
                            {
                                "ticker": r["TICKER"],
                                "date_from": r["DATE_FROM"],
                                "date_to": r.get("DATE_TO")
                                if r.get("DATE_TO") is not None
                                else -1,
                            }
                            for r in _membership_rows(tx, g["ID"])
                        ],
                    }
                    for g in groups
                ]
            with _atomic_text(Path(json_path)) as stream:
                json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
                stream.write("\n")
            return {"path": str(json_path), "count": len(data)}

        return self._run("save", action)

    def load(self, json_path: str | Path) -> dict[str, Any]:
        """Atomically import a JSON group array, rejecting existing names."""

        def action() -> list[BasketInfo]:
            try:
                parsed: object = json.loads(
                    Path(json_path).read_text(encoding="utf-8-sig")
                )
            except (json.JSONDecodeError, UnicodeError) as error:
                raise _BasketError("Invalid baskets JSON") from error
            definitions = _json_groups(parsed)
            result: list[BasketInfo] = []
            with self.gateway.transaction() as tx:
                for group, stocks in definitions:
                    _unique(tx, group["NAME"])
                    created = _records(tx.create_records("datamgr_stock_group", group))[
                        0
                    ]
                    members = _replace_memberships(tx, created["ID"], stocks)
                    result.append(BasketInfo.from_group_row(created, members))
            return result

        return self._run("load", action)

    def update_data(
        self,
        baskets: BasketTargets,
        *,
        client: Any = None,
        data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Download D1 SQ equity bars and register datasets, optionally as a job.

        Without a job manager this blocks until all unique constituent tickers finish.
        An injected client must provide get_bars(symbol, timeframe, count=...).
        """

        def action() -> Any:
            with self.gateway.transaction() as tx:
                tickers = list(
                    dict.fromkeys(
                        r["TICKER"]
                        for target in _targets(baskets)
                        for r in _membership_rows(tx, _lookup(tx, target)["ID"])
                    )
                )
            if not tickers:
                raise _BasketError("Selected groups contain no stocks")
            folder = (
                Path(data_dir)
                if data_dir is not None
                else Path(__file__).resolve().parents[3] / "data" / "baskets"
            )
            if self.jobs is not None:
                return self.jobs.submit_job(
                    self._run_update_job,
                    tickers,
                    client,
                    folder,
                    owner="data-manager",
                    kind="baskets.update_data",
                    executor_kind="thread",
                    pass_context=True,
                )
            return self._download_data(tickers, client, folder)

        return self._run("update_data", action)

    def _run_update_job(
        self, context: JobContext, tickers: list[str], client: Any, folder: Path
    ) -> dict[str, Any]:
        from app.workspace.data_manager.logs import run_logged_task

        return run_logged_task(
            self.logs,
            context,
            lambda tracked: self._download_data(
                tickers, client, folder, context=tracked
            ),
        )

    def _download_data(
        self,
        tickers: list[str],
        client: Any,
        folder: Path,
        *,
        context: JobContext | None = None,
    ) -> dict[str, Any]:
        from app.workspace.brokers.sq_equity import SQEquityClient

        owned = client is None
        provider = SQEquityClient(data_dir=folder) if owned else client
        completed: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []
        try:
            folder.mkdir(parents=True, exist_ok=True)
            for index, ticker in enumerate(tickers):
                if context is not None:
                    context.wait_if_paused()
                try:
                    completed.append(
                        _download_one(self.gateway, provider, ticker, folder)
                    )
                except (
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                    OSError,
                ) as error:
                    logger.warning(
                        "Basket data update failed for %s: %s",
                        ticker,
                        type(error).__name__,
                    )
                    failed.append({"ticker": ticker, "error": str(error)})
                if context is not None:
                    context.report_progress((index + 1) * 100 / len(tickers), ticker)
        finally:
            if owned:
                provider.session.close()
        result = {
            "completed": completed,
            "failed": failed,
            "updated_count": len(completed),
        }
        if failed:
            raise _BasketError(
                "Some basket data updates failed", ErrorCode.UNAVAILABLE, result
            )
        return result

    def list(self, *, include_stocks: bool = True) -> dict[str, Any]:
        """Retrieve basket catalog items wrapped in StandardResponse.

        Args:
            include_stocks: Whether to query and populate constituent stock items.
        """
        start = time.perf_counter()
        try:
            group_rows = self._read_stock_groups()
            downloaded_symbols = self._read_downloaded_symbols()

            stocks_by_basket: dict[int, list[BasketStockItem]] = defaultdict(list)
            if include_stocks:
                stock_rows = self._read_stocks()
                for sr in stock_rows:
                    item = BasketStockItem.from_row(sr)
                    stocks_by_basket[item.basket_id].append(item)

            baskets = [
                BasketInfo.from_group_row(
                    gr,
                    stocks=stocks_by_basket.get(int(gr.get("ID") or gr.get("id") or 0)),
                    downloaded_symbols=downloaded_symbols,
                )
                for gr in group_rows
            ]

            logger.debug(
                "%s: Retrieved %d basket catalog items",
                BASKETS_CATALOG_FR,
                len(baskets),
                extra={"fr_id": BASKETS_CATALOG_FR, "count": len(baskets)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(baskets)} basket catalog items",
                metadata=ResponseMetadata(
                    operation="baskets.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=baskets,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list baskets", BASKETS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve baskets",
                metadata=ResponseMetadata(
                    operation="baskets.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing baskets",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_basket_table

    baskets_svc = Baskets()
    catalog_response = baskets_svc.list()
    if catalog_response["success"]:
        print(format_basket_table(catalog_response))
    else:
        print(f"Failed: {catalog_response['message']}")
