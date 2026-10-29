"""Data models, helpers, and serialization for Data Manager baskets."""

from __future__ import annotations

import csv
import hashlib
import io
import tempfile
import time
import uuid
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO, Any, cast

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence, RecordFilter
from app.core.lib.responses import ErrorCode

logger = get_logger(__name__)
persistence = HostPersistence()

BASKETS_CATALOG_FR = "FR-DATAMGR-BASKETS-CATALOG"
DESC_PARTS_MIN_LEN: int = 3

type BasketTargets = str | int | Sequence[str | int]
_MAX_NAME = 50
_MAX_DESCRIPTION = 250
_MAX_TIMESTAMP = 253402300799999
_MIN_TIMESTAMP = -62135596800000
_DAY_MS = 86400000
_CSV_COLUMNS = 3

__all__ = [
    "BASKETS_CATALOG_FR",
    "DESC_PARTS_MIN_LEN",
    "BasketInfo",
    "BasketStockItem",
    "BasketTargets",
    "_BasketError",
    "_atomic_text",
    "_clear_memberships",
    "_csv_date",
    "_custom",
    "_date",
    "_description",
    "_download_one",
    "_error_code",
    "_group_row",
    "_json_groups",
    "_lookup",
    "_membership_rows",
    "_ms_to_date",
    "_normalize_stocks",
    "_read_all",
    "_records",
    "_replace_memberships",
    "_stock_row",
    "_targets",
    "_unique",
    "logger",
    "persistence",
]


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


MAX_BASKET_DESC_LEN: int = 22
BASKET_DESC_TRUNCATE_LEN: int = 20
MAX_READY_LEN: int = 13
READY_TRUNCATE_LEN: int = 11


def _get(item: Any, key: str, default: Any = "") -> Any:
    from collections.abc import Mapping

    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def format_basket_table(
    baskets: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format ASCII table of stock groups / baskets catalog entries."""
    from collections.abc import Mapping

    items: Sequence[Any]
    if (
        isinstance(baskets, Mapping)
        and "data" in baskets
        and isinstance(baskets["data"], Sequence)
    ):
        items = cast("Any", baskets["data"])
    elif isinstance(baskets, Sequence):
        items = baskets
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Stock Groups / Baskets Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<32} | {cnt:<12} | {desc:<22} | {syms:>17} "
        "| {down:>12} | {ready:<13} | {d_from:<10} | {d_to:<10} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (32, 12, 22, 17, 12, 13, 10, 10)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            cnt="Count",
            desc="Description",
            syms="Number of symbols",
            down="Downloaded",
            ready="Ready to use?",
            d_from="Date from",
            d_to="Date to",
        )
    )
    lines.append(divider)
    for item in items:
        name = str(_get(item, "name", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_BASKET_DESC_LEN:
            desc = desc[:BASKET_DESC_TRUNCATE_LEN] + ".."
        active = _get(item, "active_count", 0)
        total = _get(item, "stocks_count", 0)
        if total == 0:
            total = _get(item, "total_count", 0)
        cnt_str = f"{active} / {total}"
        syms = _get(item, "symbols_count", 0)
        down = _get(item, "downloaded_count", 0)
        down_str = f"{down} / {total}"
        ready_val = _get(item, "ready", False)
        if isinstance(ready_val, str):
            ready_str = (
                ready_val
                if len(ready_val) <= MAX_READY_LEN
                else ready_val[:READY_TRUNCATE_LEN].rstrip() + ".."
            )
        else:
            ready_str = "Yes" if ready_val else "No"
        d_from = str(_get(item, "date_from", "-"))
        d_to = str(_get(item, "date_to", "-"))
        lines.append(
            header_fmt.format(
                name=name,
                cnt=cnt_str,
                desc=desc,
                syms=syms,
                down=down_str,
                ready=ready_str,
                d_from=d_from,
                d_to=d_to,
            )
        )
    return "\n".join(lines)


class BasketsCLI:
    """Table formatters for the Data Manager catalog."""

    format_basket_table = staticmethod(format_basket_table)
