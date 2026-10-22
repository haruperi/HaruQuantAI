"""Manage persisted stock baskets and historical symbol memberships.

Description:
    Lists existing host-owned groups, saves custom group metadata and replaces
    dated symbol memberships atomically. System groups remain read-only and
    configured membership periods remain separate from downloaded market data.
Purpose:
    FEAT-DATAMGR-BASKET: Persist stock baskets and watchlist symbol groupings.
Key Capabilities:
    - FR-DATAMGR-BASKET-LIST: list-groups [Basket.baskets()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BASKET-ADD: save-group [Basket.add_basket()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BASKET-EDIT: edit-members [Basket.edit_stocks()] (INFO/WARNING/ERROR).
    - FR-DATAMGR-BASKET-DELETE: remove [Basket.delete_basket()] (INFO/WARNING/ERROR).
    Every operation logs its FR outcome; tests verify logs without payloads.
Python API Usage:
    from app.workspace.data_manager.baskets import Basket
    groups = Basket().baskets()
CLI Usage:
    uv run python -m app.cli data baskets
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

__all__ = ["Basket"]
logger = get_logger(__name__)
_GROUP = "datamgr_stock_group"
_STOCK = "datamgr_stock"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_DAY_MS = 86400000
_CONTROL_START = 32
_CONTROL_DELETE = 127
_MEMBER_LIMIT = 50000
_GROUP_LIMIT = 1000
_MEMBER_TEXT_LIMIT = 74
_MEMBER_FIELDS = 3


@contextmanager
def _operation(name: str) -> Generator[None]:
    fr = {"fr_id": f"FR-DATAMGR-BASKET-{name}"}
    try:
        yield
    except ValueError, LookupError, FileExistsError:
        logger.warning("Basket request rejected", extra=fr)
        raise
    except RuntimeError:
        logger.error("Basket storage unavailable", extra=fr)  # noqa: TRY400
        raise
    else:
        logger.info("Basket operation completed", extra=fr)


def _text(value: Any, maximum: int, *, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"Provide text of at most {maximum} characters.")
    clean: str = value.strip()
    if (required and not clean) or any(
        ord(c) < _CONTROL_START or ord(c) == _CONTROL_DELETE for c in clean
    ):
        raise ValueError("Text is empty or contains control characters.")
    return clean


def _identifier(value: Any) -> int:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[1-9]\d{0,18}", value)
        or int(value) >= 2**63
    ):
        raise ValueError("Choose a positive numeric basket ID.")
    return int(value)


def _stored_date(value: Any) -> str | None:
    if value is None or value == -1:
        return None
    if type(value) is not int or value % _DAY_MS:
        raise ValueError("Stored membership date must be midnight UTC milliseconds.")
    try:
        return (_EPOCH + timedelta(milliseconds=value)).date().isoformat()
    except OverflowError as error:
        raise ValueError("Stored membership date is out of range.") from error


def _date_ms(value: str) -> int:
    if not value:
        return -1
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Membership dates must use YYYY-MM-DD.")
    parsed = date.fromisoformat(value)
    return (parsed - _EPOCH.date()).days * _DAY_MS


def _members(symbols: Sequence[str]) -> list[dict[str, Any]]:
    if not isinstance(symbols, (list, tuple)) or len(symbols) > _MEMBER_LIMIT:
        raise ValueError("Provide at most 50000 membership strings.")
    unique: dict[tuple[str, int, int], dict[str, Any]] = {}
    for raw in symbols:
        if not isinstance(raw, str) or len(raw) > _MEMBER_TEXT_LIMIT:
            raise ValueError("Provide ticker or ticker;date-from;date-to strings.")
        cells = raw.split(";")
        if len(cells) > _MEMBER_FIELDS:
            raise ValueError("Membership has too many fields.")
        symbol = _text(cells[0], 50, required=True)
        start, end = (_date_ms(value.strip()) for value in [*cells[1:], "", ""][:2])
        if start != -1 and end != -1 and start > end:
            raise ValueError("Membership end must not precede its start.")
        unique.setdefault(
            (symbol.casefold(), start, end),
            {
                "TICKER": symbol,
                "DATE_FROM": start,
                "DATE_TO": end,
            },
        )
    return list(unique.values())


class Basket:
    """Manage custom group metadata and dated constituent membership."""

    def baskets(self) -> list[dict[str, Any]]:
        """List all confirmed groups and complete membership history."""
        with _operation("LIST"):
            return self._records()

    def add_basket(self, basket: Mapping[str, Any]) -> dict[str, Any]:
        """Create or edit custom metadata while preserving member history."""
        with _operation("ADD"):
            if not isinstance(basket, Mapping) or set(basket) - {
                "id",
                "name",
                "description",
            }:
                raise ValueError("Provide only group identity, name and description.")
            original = self._get(basket["id"]) if "id" in basket else None
            if original and original["system"]:
                raise ValueError("System stock groups cannot be edited.")
            name = _text(
                basket.get("name", original["name"] if original else ""),
                50,
                required=True,
            )
            name = "[" + name.strip("[]") + "]"
            name = _text(name, 50, required=True)
            if not name.strip("[]").strip():
                raise ValueError("Group name is required.")
            description = _text(
                basket.get("description", original["description"] if original else ""),
                250,
            )
            rows = HostPersistence.read_records(_GROUP, limit=0)
            if any(
                row["NAME"].casefold() == name.casefold()
                and (not original or str(row["ID"]) != original["id"])
                for row in rows
            ):
                raise FileExistsError("Stock group name must be unique.")
            values = {"NAME": name, "DESC": description, "description": description}
            if original:
                HostPersistence.update_record(
                    _GROUP, {"ID": int(original["id"])}, values
                )
                identifier = original["id"]
            else:
                created = HostPersistence.create_record(_GROUP, {**values, "SYSTEM": 0})
                identifier = str(created["pk"]["ID"])
            return self._get(identifier)

    def edit_stocks(self, basket_id: str, symbols: Sequence[str]) -> dict[str, Any]:
        """Atomically replace dated member strings, including an empty selection."""
        with _operation("EDIT"):
            identifier = _identifier(basket_id)
            original = self._get(basket_id)
            if original["system"]:
                raise ValueError("System stock groups cannot be edited.")
            members = _members(symbols)
            operations = [
                {"op": "delete", "table": _STOCK, "key_columns": {"ID": row["ID"]}}
                for row in HostPersistence.read_records(
                    _STOCK, {"BASKET_ID": identifier}, limit=0
                )
            ]
            operations.extend(
                {
                    "op": "create",
                    "table": _STOCK,
                    "values": {**member, "BASKET_ID": identifier},
                }
                for member in members
            )
            HostPersistence.apply_batch(operations)
            return self._get(basket_id)

    def delete_basket(self, basket_ids: Sequence[str]) -> dict[str, Any]:
        """Delete selected custom groups and their dated memberships atomically."""
        with _operation("DELETE"):
            if (
                not isinstance(basket_ids, (list, tuple))
                or not 0 < len(basket_ids) <= _GROUP_LIMIT
            ):
                raise ValueError("Select between 1 and 1000 stock groups.")
            identifiers = list(
                dict.fromkeys(_identifier(value) for value in basket_ids)
            )
            groups = [self._get(str(identifier)) for identifier in identifiers]
            if any(group["system"] for group in groups):
                raise ValueError("System stock groups cannot be deleted.")
            operations: list[dict[str, Any]] = []
            for identifier in identifiers:
                operations.extend(
                    {"op": "delete", "table": _STOCK, "key_columns": {"ID": row["ID"]}}
                    for row in HostPersistence.read_records(
                        _STOCK, {"BASKET_ID": identifier}, limit=0
                    )
                )
                operations.append(
                    {"op": "delete", "table": _GROUP, "key_columns": {"ID": identifier}}
                )
            HostPersistence.apply_batch(operations)
            return {
                "deleted_ids": [str(value) for value in identifiers],
                "deleted_count": len(identifiers),
            }

    def _get(self, identifier: str) -> dict[str, Any]:
        rows = self._records({"ID": _identifier(identifier)})
        if not rows:
            raise LookupError("Stock group no longer exists.")
        return rows[0]

    def _records(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        groups = HostPersistence.read_records(_GROUP, filters, limit=0)
        members: dict[int, list[dict[str, Any]]] = defaultdict(list)
        stocks = HostPersistence.read_records(
            _STOCK, {"BASKET_ID": filters["ID"]} if filters else None, limit=0
        )
        try:
            for row in stocks:
                start, end = (
                    _stored_date(row["DATE_FROM"]),
                    _stored_date(row["DATE_TO"]),
                )
                if start and end and start > end:
                    raise RuntimeError("Stored membership dates are reversed.")
                members[row["BASKET_ID"]].append(
                    {
                        "symbol": _text(row["TICKER"], 50, required=True),
                        "date_from": start,
                        "date_to": end,
                    }
                )
            result = []
            for row in groups:
                if type(row["SYSTEM"]) is not int or row["SYSTEM"] not in (0, 1):
                    raise RuntimeError("Stored stock group system flag is invalid.")
                result.append(
                    {
                        "id": str(row["ID"]),
                        "name": _text(row["NAME"], 50, required=True),
                        "description": _text(
                            row["description"] or row["DESC"] or "", 250
                        ),
                        "system": bool(row["SYSTEM"]),
                        "items": members[row["ID"]],
                    }
                )
        except (ValueError, OverflowError, TypeError) as error:
            raise RuntimeError("Stored stock group data is invalid.") from error
        return sorted(result, key=lambda row: (row["name"].casefold(), int(row["id"])))
