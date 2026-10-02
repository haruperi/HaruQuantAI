# ruff: noqa: N815 -- established presentation fields and bounded schemas.
"""Durable Data Manager configuration catalogs.

Description:
    Validates instrument, broker, session and stock-group documents and stores
    explicit revisions through host settings custody. No browser state is seeded.
Purpose:
    FEAT-DM-CATALOGS: Persisted Data Manager configuration workflows.
Key Capabilities:
    - FR-DM-BROKER-CLOCK-POLICY: Explicit database association and policy edits;
      logs operation and accepted revisions.
    - FR-DM-CATALOG-SCHEMA: Typed immutable metadata; logs validation failures.
    - FR-DM-CATALOG-PERSIST: Explicit revision checks; logs committed revisions.
Python API Usage:
    result = catalog_operation(settings, market, "catalogs.get", {"kind": "brokers"})
CLI Usage:
    uv run pytest tests/workspace/DataManager/test_catalogs.py --no-cov
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import Field, model_validator

from app.host.capabilities import MarketAccess, SettingsAccess
from app.host.contracts import ClockPolicy, Document
from app.host.logging import get_logger

logger = get_logger(__name__)
Day = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class Commission(Document):
    """Instrument commission metadata."""

    model: Literal["None", "Per trade", "Size based", "Percentage based", "Stockpicker"]
    value: float = Field(allow_inf_nan=False)
    unit: str
    min: float = Field(allow_inf_nan=False)
    minUnit: str
    max: float = Field(allow_inf_nan=False)
    maxUnit: str


class Swap(Document):
    """Instrument rollover metadata."""

    use: bool
    type: Literal["money", "points", "percent"]
    long: float = Field(allow_inf_nan=False)
    short: float = Field(allow_inf_nan=False)
    tripleSwapOn: str
    rolloutHour: str


class Instrument(Document):
    """One immutable configured instrument."""

    symbol: str = Field(min_length=1, max_length=128)
    name: str = Field(max_length=250)
    type: Literal["Stock", "Futures", "Forex", "CFD"]
    broker: str
    brokerName: str
    pointValue: float = Field(gt=0, allow_inf_nan=False)
    tickSize: float = Field(gt=0, allow_inf_nan=False)
    tickStep: float = Field(gt=0, allow_inf_nan=False)
    spread: float = Field(ge=0, allow_inf_nan=False)
    slippage: float = Field(ge=0, allow_inf_nan=False)
    minDistance: float = Field(ge=0, allow_inf_nan=False)
    multiplier: float = Field(gt=0, allow_inf_nan=False)
    sizeStep: float = Field(gt=0, allow_inf_nan=False)
    timezone: str
    commission: Commission
    swap: Swap


class SessionElement(Document):
    """One weekly session interval."""

    dayFrom: Day
    timeFrom: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    dayTo: Day
    timeTo: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    eod: bool

    @model_validator(mode="after")
    def times(self) -> SessionElement:
        """Reject reversed intervals on one day."""
        if self.dayFrom == self.dayTo and self.timeFrom > self.timeTo:
            raise ValueError("Session end precedes start")
        return self


class Session(Document):
    """Named broker-associated session definition."""

    name: str = Field(min_length=1, max_length=128)
    broker: str
    brokerName: str
    elements: tuple[SessionElement, ...] = Field(min_length=1, max_length=100)


class Membership(Document):
    """Stock-group membership with optional validity dates."""

    ticker: str = Field(min_length=1, max_length=128)
    date_from: str | None = Field(default=None, alias="from")
    to: str | None = None


class StockGroup(Document):
    """One stock group document."""

    id: str
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(max_length=1000)
    system: bool
    members: tuple[Membership, ...] = Field(max_length=10000)
    origin: Literal["file-import"] | None = None
    originName: str | None = None
    originFingerprint: str | None = None


class Broker(Document):
    """One explicit broker configuration."""

    id: str
    databaseBrokerId: str | None = Field(default=None, pattern=r"^[1-9][0-9]*$")
    name: str = Field(min_length=1, max_length=50)
    desc: str = Field(max_length=250)
    postfix: str = Field(max_length=100)
    timezone: str
    mtUse: bool
    stockPickerUse: bool
    system: bool
    stocks: tuple[str, ...] = Field(max_length=10000)
    instruments: tuple[str, ...] = Field(max_length=10000)


class InstrumentState(Document):
    """Explicit instrument catalog transfer."""

    instruments: tuple[Instrument, ...] = Field(default=(), max_length=10000)
    overrides: dict[str, Instrument] = Field(default_factory=dict, max_length=10000)
    removed: tuple[str, ...] = Field(default=(), max_length=10000)


class SessionState(Document):
    """Explicit session catalog transfer."""

    sessions: tuple[Session, ...] = Field(default=(), max_length=10000)
    overrides: dict[str, Session] = Field(default_factory=dict, max_length=10000)
    removed: tuple[str, ...] = Field(default=(), max_length=10000)


class GroupState(Document):
    """Explicit stock-group catalog transfer."""

    groups: tuple[StockGroup, ...] = Field(default=(), max_length=1000)


class BrokerState(Document):
    """Explicit broker catalog transfer."""

    brokers: tuple[Broker, ...] = Field(default=(), max_length=100)


class Request(Document):
    """Catalog identity, current revision and bounded metadata payload."""

    kind: Literal["instruments", "sessions", "groups", "brokers"]
    revision: int = Field(default=0, ge=0)
    state: dict[str, Any] | None = None


def catalog_operation(  # noqa: PLR0912, PLR0915, C901 -- cohesive source conversion or bounded operation dispatch.
    settings: SettingsAccess,
    market: MarketAccess,
    operation: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Validate and commit a catalog revision; reject stale concurrent writers."""
    request = Request.model_validate(values)
    models: dict[str, type[Document]] = {
        "instruments": InstrumentState,
        "sessions": SessionState,
        "groups": GroupState,
        "brokers": BrokerState,
    }
    model = models[request.kind]
    key = "catalog." + request.kind
    current = settings.get(key)
    if (
        current is None or not current.get("state", {}).get("brokers")
    ) and request.kind == "brokers":
        try:
            db_brokers = list(market.list_all_brokers())
            if db_brokers:
                current = {
                    "revision": 0,
                    "state": {"brokers": db_brokers},
                }
        except (PermissionError, ValueError, OSError) as error:
            logger.debug("Could not seed broker catalog from database: %s", error)
    if current is None:
        current = {
            "revision": 0,
            "state": model().model_dump(mode="json", by_alias=True, exclude_none=True),
        }
    if operation == "catalogs.get":
        logger.info(
            "Read Data Manager catalog: kind=%s revision=%d",
            request.kind,
            current["revision"],
        )
        return {**current, "schema": model.model_json_schema()}
    if operation != "catalogs.replace" or request.state is None:
        raise ValueError("Invalid catalog operation")
    if request.revision != current["revision"]:
        raise ValueError("Catalog changed; reload before saving")
    state = model.model_validate(request.state).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    rows = state.get(request.kind, [])
    if request.kind == "brokers":
        database_ids = {row["id"] for row in market.list_all_brokers()}
        previous_by_id = {row["id"]: row for row in current["state"]["brokers"]}
        associations = []
        for row in rows:
            associated = row.get("databaseBrokerId")
            previous = previous_by_id.get(row["id"], {}).get("databaseBrokerId")
            if previous and associated != previous:
                raise ValueError("Database broker association is immutable")
            if associated and associated not in database_ids:
                raise ValueError("Database broker association is unavailable")
            resolved = associated or (row["id"] if row["id"] in database_ids else None)
            if resolved:
                associations.append(resolved)
        if len(associations) != len(set(associations)):
            raise ValueError("Duplicate database broker association")
    names = [str(row.get("symbol", row.get("name", ""))).casefold() for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate catalog identities")
    if request.kind in ("instruments", "sessions"):
        for name, item in state["overrides"].items():
            if name != item.get("symbol", item.get("name")):
                raise ValueError("Override identity mismatch")
    if request.kind in ("instruments", "brokers"):
        retained = market.inventory()
        identity = "symbol" if request.kind == "instruments" else "id"
        present = {row[identity] for row in rows}
        previous = current["state"].get(request.kind, [])
        removed = {row[identity] for row in previous} - present
        reference = "instrument" if request.kind == "instruments" else "broker"
        if any(row[reference] in removed for row in retained):
            raise ValueError("Catalog record is referenced by retained data")
    result = {"revision": request.revision + 1, "state": state}
    settings.set(key, result)
    logger.info(
        "Committed Data Manager catalog: kind=%s revision=%d",
        request.kind,
        result["revision"],
    )
    return result


def broker_clock_operation(
    settings: SettingsAccess,
    market: MarketAccess,
    operation: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Resolve explicit catalog/database association and serve host policy custody."""
    broker_id = values.get("broker_id")
    if not isinstance(broker_id, str):
        raise TypeError("Select a broker profile")
    brokers = catalog_operation(settings, market, "catalogs.get", {"kind": "brokers"})[
        "state"
    ]["brokers"]
    selected = next((row for row in brokers if row["id"] == broker_id), None)
    if selected is None:
        raise ValueError("Broker profile unavailable")
    database_ids = {row["id"] for row in market.list_all_brokers()}
    database_id = selected.get("databaseBrokerId") or broker_id
    if database_id not in database_ids:
        raise ValueError(
            "Associate this profile with a database broker "
            "before editing its clock policy"
        )
    if operation == "broker_clock.replace":
        revision = values.get("expected_revision")
        if type(revision) is not int or revision < 0:
            raise ValueError("Invalid broker clock revision")
        result = market.replace_broker_clock_policy(
            database_id, revision, ClockPolicy.model_validate(values.get("policy"))
        )
    elif operation == "broker_clock.get":
        result = market.broker_clock_policy(database_id)
    else:
        raise ValueError("Unknown broker clock operation")
    logger.info("Broker clock operation: %s", operation)
    return {
        **result,
        "database_broker_id": database_id,
        "schema": ClockPolicy.model_json_schema(),
    }


def broker_operation(
    settings: SettingsAccess,
    market: MarketAccess,
    operation: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Query persisted instruments or propagate their broker associations to data."""
    catalog = catalog_operation(
        settings, market, "catalogs.get", {"kind": "instruments"}
    )["state"]
    instruments = {row["symbol"]: row for row in catalog["instruments"]}
    instruments.update(catalog["overrides"])
    for name in catalog["removed"]:
        instruments.pop(name, None)
    if operation == "actions.broker_data":
        query = str(values.get("query", "")).casefold()
        broker = values.get("broker_id")
        rows = [
            {
                **row,
                "description": row["name"],
                "dataType": row["type"],
                "decimals": max(
                    0,
                    -int(Decimal(str(row["tickSize"])).normalize().as_tuple().exponent),
                ),
            }
            for row in instruments.values()
            if (
                not query
                or query in row["symbol"].casefold()
                or query in row["name"].casefold()
            )
            and (not broker or broker == "-1" or row["broker"] == broker)
        ]
        logger.info("Read broker instruments: count=%d", len(rows))
        return {"query": query, "count": len(rows), "instruments": rows}
    profiles = values.get("profile_ids", [])
    symbols = values.get("symbols", [])
    if not isinstance(profiles, list) or not isinstance(symbols, list):
        raise TypeError("Invalid broker selection")
    brokers = catalog_operation(settings, market, "catalogs.get", {"kind": "brokers"})[
        "state"
    ]["brokers"]
    names = {row["id"]: row["name"] for row in brokers}
    names["-1"] = "Default"
    updates = []
    for dataset in market.inventory():
        item = instruments.get(dataset["instrument"])
        if (
            item
            and (not profiles or item["broker"] in profiles)
            and (not symbols or dataset["symbol"] in symbols)
        ):
            if item["broker"] not in names:
                raise ValueError("Instrument refers to an unavailable broker")
            updates.append((dataset["id"], item["broker"], names[item["broker"]]))
    for dataset_id, broker, name in updates:
        market.update_source_broker(dataset_id, broker, name)
    logger.info("Propagated broker metadata: datasets=%d", len(updates))
    return {
        "success": True,
        "updated": len(updates),
        "updatedDatasets": len(updates),
        "brokerProfiles": len({row[1] for row in updates}),
    }
