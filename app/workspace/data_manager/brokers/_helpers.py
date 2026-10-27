"""Helper functions, data models, and persistence adapters for Data Manager brokers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import ErrorCode

logger = get_logger(__name__)
persistence = HostPersistence()

BROKERS_CATALOG_FR = "FR-DATAMGR-BROKERS-CATALOG"

_FIELDS = {
    "name",
    "description",
    "is_system",
    "stockpicker_use",
    "mt_use",
    "server_timezone",
    "postfix",
    "enabled",
    "clock_policy",
    "clock_policy_revision",
}

__all__ = [
    "BROKERS_CATALOG_FR",
    "_FIELDS",
    "BrokerInfo",
    "_BrokerError",
    "_editable",
    "_error_code",
    "_lookup",
    "_names",
    "_parse_json_dict",
    "_policy_json",
    "_records",
    "_row",
    "logger",
    "persistence",
]


def _parse_json_dict(val: Any) -> dict[str, Any]:
    """Parse JSON string into dictionary or return empty dict."""
    if isinstance(val, dict):
        return cast("dict[str, Any]", val)
    if isinstance(val, str) and val.startswith(("{", "[")):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return cast("dict[str, Any]", parsed)
        except json.JSONDecodeError, TypeError:
            return {}
    return {}


@dataclass(slots=True)
class BrokerInfo:
    """Broker profile catalog record definition."""

    id: int = 0
    name: str = ""
    is_system: bool = False
    description: str = ""
    stockpicker_use: bool = False
    mt_use: bool = False
    server_timezone: str = "UTC"
    postfix: str = ""
    enabled: bool = True
    created_at_utc: str = ""
    updated_at_utc: str = ""
    clock_policy: dict[str, Any] = field(default_factory=dict[str, Any])
    clock_policy_revision: int = 0
    customized_stocks: int = 0
    customized_instruments: int = 0
    customized_sessions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize BrokerInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_row(
        cls,
        row: Mapping[str, Any],
        *,
        customized_stocks: int | None = None,
        customized_instruments: int | None = None,
        customized_sessions: int | None = None,
    ) -> BrokerInfo:
        """Construct BrokerInfo from a database row."""
        c_stocks = (
            customized_stocks
            if customized_stocks is not None
            else int(
                row.get("customized_stocks")
                or row.get("stocks_count")
                or len(row.get("stocks", []))
                or 0
            )
        )
        c_insts = (
            customized_instruments
            if customized_instruments is not None
            else int(
                row.get("customized_instruments") or row.get("total_instruments") or 0
            )
        )
        c_sess = (
            customized_sessions
            if customized_sessions is not None
            else int(row.get("customized_sessions") or row.get("total_sessions") or 0)
        )
        return cls(
            id=int(row.get("id", 0)),
            name=str(row.get("name", "")),
            is_system=bool(row.get("is_system", 0)),
            description=str(row.get("description", "")),
            stockpicker_use=bool(row.get("stockpicker_use", 0)),
            mt_use=bool(row.get("mt_use", 0)),
            server_timezone=str(row.get("server_timezone", "UTC")),
            postfix=str(row.get("postfix", "")),
            enabled=bool(row.get("enabled", 1)),
            created_at_utc=str(row.get("created_at_utc", "")),
            updated_at_utc=str(row.get("updated_at_utc", "")),
            clock_policy=_parse_json_dict(row.get("clock_policy_json", "{}")),
            clock_policy_revision=int(row.get("clock_policy_revision", 0)),
            customized_stocks=c_stocks,
            customized_instruments=c_insts,
            customized_sessions=c_sess,
        )


class _BrokerError(ValueError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.VALIDATION) -> None:
        super().__init__(message)
        self.code = code


def _error_code(error: Exception) -> ErrorCode:
    if isinstance(error, _BrokerError):
        return error.code
    return ErrorCode.INTERNAL


def _records(response: dict[str, Any]) -> list[dict[str, Any]]:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise _BrokerError(
            response.get("message") or "Broker storage failed",
            ErrorCode(error.get("code", "internal")),
        )
    return cast("list[dict[str, Any]]", response["data"]["records"])


def _names(names: str | Sequence[str]) -> list[str]:
    values: list[object] = [names] if isinstance(names, str) else list(names)
    if not values:
        raise _BrokerError("At least one non-empty broker name is required")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise _BrokerError("At least one non-empty broker name is required")
        normalized.append(value.strip())
    return list(dict.fromkeys(normalized))


def _policy_json(policy: Any) -> str:
    if not isinstance(policy, dict):
        raise _BrokerError("clock_policy must be an object")
    try:
        return json.dumps(policy, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise _BrokerError("clock_policy must contain valid JSON values") from error


def _row(values: Mapping[str, Any]) -> dict[str, Any]:
    unknown = values.keys() - _FIELDS
    if unknown:
        raise _BrokerError(f"Unknown broker fields: {', '.join(sorted(unknown))}")
    data = dict(values)
    for key, default in (
        ("name", ""),
        ("description", ""),
        ("server_timezone", "UTC"),
        ("postfix", ""),
    ):
        value = data.get(key, default)
        if not isinstance(value, str):
            raise _BrokerError(f"{key} must be a string")
        data[key] = value.strip() if key in {"name", "server_timezone"} else value
    if not data["name"]:
        raise _BrokerError("Broker name is required")
    try:
        if data["server_timezone"] != "EETUS":
            ZoneInfo(data["server_timezone"])
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise _BrokerError("Unknown broker timezone") from error
    for key in ("is_system", "stockpicker_use", "mt_use", "enabled"):
        value = data.get(key, key == "enabled")
        if not isinstance(value, bool):
            raise _BrokerError(f"{key} must be a boolean")
        data[key] = int(value)
    revision = data.get("clock_policy_revision", 0)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise _BrokerError("clock_policy_revision must be a non-negative integer")
    data["clock_policy_revision"] = revision
    data["clock_policy_json"] = _policy_json(data.pop("clock_policy", {}))
    return data


def _editable(row: Mapping[str, Any]) -> dict[str, Any]:
    values = BrokerInfo.from_row(row).to_dict()
    return {key: values[key] for key in _FIELDS}


def _lookup(gateway: HostPersistence, name: str) -> dict[str, Any]:
    rows = _records(
        gateway.read_records("datamgr_broker", filters={"name": name}, limit=1)
    )
    if not rows:
        raise _BrokerError(f"Broker '{name}' not found", ErrorCode.NOT_FOUND)
    return rows[0]


MAX_BROKER_DESC_LEN: int = 22
BROKER_DESC_TRUNCATE_LEN: int = 20


def _get(item: Any, key: str, default: Any = "") -> Any:
    from collections.abc import Mapping

    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def format_broker_table(
    brokers: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format ASCII table of broker profile catalog entries."""
    from collections.abc import Mapping

    items: Sequence[Any]
    if (
        isinstance(brokers, Mapping)
        and "data" in brokers
        and isinstance(brokers["data"], Sequence)
    ):
        items = cast("Any", brokers["data"])
    elif isinstance(brokers, Sequence):
        items = brokers
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Broker Profiles Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<26} | {desc:<22} | {pf:<14} | {tz:<16} "
        "| {stocks:>17} | {insts:>22} | {sess:>19} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (26, 22, 14, 16, 17, 22, 19)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            desc="Description",
            pf="Postfix",
            tz="Timezone",
            stocks="Customized stocks",
            insts="Customized instruments",
            sess="Customized sessions",
        )
    )
    lines.append(divider)
    for item in items:
        name = str(_get(item, "name", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_BROKER_DESC_LEN:
            desc = desc[:BROKER_DESC_TRUNCATE_LEN] + ".."
        pf = str(_get(item, "postfix", ""))
        tz = str(
            _get(item, "server_timezone", "") or _get(item, "timezone", "") or "UTC"
        )
        stocks = _get(item, "customized_stocks", 0)
        insts = _get(item, "customized_instruments", 0)
        if insts == 0:
            insts = _get(item, "total_instruments", 0)
        sess = _get(item, "customized_sessions", 0)
        if sess == 0:
            sess = _get(item, "total_sessions", 0)
        lines.append(
            header_fmt.format(
                name=name,
                desc=desc,
                pf=pf,
                tz=tz,
                stocks=stocks,
                insts=insts,
                sess=sess,
            )
        )
    return "\n".join(lines)


class BrokersCLI:
    """Table formatters for the Data Manager catalog."""

    format_broker_table = staticmethod(format_broker_table)
