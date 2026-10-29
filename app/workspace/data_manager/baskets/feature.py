"""Data Manager baskets (stock groups) catalog core service."""

from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.jobs.manager import JobContext, JobManager

from app.core.host.persistence import HostPersistence
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

from ._helpers import (
    BASKETS_CATALOG_FR,
    BasketInfo,
    BasketStockItem,
    BasketTargets,
    _atomic_text,
    _BasketError,
    _clear_memberships,
    _csv_date,
    _custom,
    _description,
    _download_one,
    _error_code,
    _group_row,
    _json_groups,
    _lookup,
    _membership_rows,
    _normalize_stocks,
    _read_all,
    _records,
    _replace_memberships,
    _targets,
    _unique,
    logger,
    persistence,
)

__all__ = ["Baskets"]


class Baskets:
    """Service providing baskets and stock groups catalog presentation."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        jobs: JobManager | None = None,
        logs: Any = None,
    ) -> None:
        pkg = sys.modules.get(__package__ or "")
        gw = getattr(pkg, "persistence", persistence) if pkg else persistence
        self.gateway = gateway if gateway is not None else gw
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
