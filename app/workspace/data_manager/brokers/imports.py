"""Broker symbol/session transfers reuse existing domain validators and persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree as ET

from fastapi import APIRouter, Request

from app.core.host.transport import TransportError
from app.host.response import ErrorCode
from app.include.contracts import TradingSession
from app.include.market_storage import safe_component
from app.workspace.data_manager.data.storage import require_data
from app.workspace.data_manager.sessions._helpers import _editable as session_editable
from app.workspace.data_manager.sessions._helpers import _row as session_row
from app.workspace.data_manager.symbols._helpers import (
    _apply_field_updates,
    _build_row_dict,
)
from app.workspace.data_manager.symbols.http import symbol_to_ui, symbol_updates

_MAX_DOCUMENT = 2_000_000
_MAX_RECORDS = 10000


def _xml_symbol(node: Any) -> Any:
    """Read typed symbol XML fields without duplicating symbol validation."""

    def scalar(key: str, value: str) -> Any:
        if key in {
            "symbol",
            "name",
            "broker",
            "brokerName",
            "timezone",
            "type",
            "tripleSwapOn",
            "rolloutHour",
            "model",
            "unit",
            "minUnit",
            "maxUnit",
        }:
            return value
        try:
            return json.loads(value)
        except ValueError:
            return value

    result = {key: scalar(key, value) for key, value in node.attrib.items()}
    for child in node:
        result[child.tag] = (
            _xml_symbol(child)
            if child.attrib or len(child)
            else scalar(child.tag, child.text or "")
        )
    return result


def _xml_records(content: str, kind: str) -> dict[str, Any]:
    """Normalize the bounded supported XML schema after rejecting DTD/entities."""
    if "<!DOCTYPE" in content.upper() or "<!ENTITY" in content.upper():
        raise ValueError("XML entities and DTDs are not allowed")
    root = ET.fromstring(content)  # noqa: S314 - bounded input rejects DTD and entities above
    if root.tag.lower() != kind or root.get("version", "1") != "1":
        raise ValueError("Expected a version 1 Symbols or Sessions XML document")
    items = []
    for element in root:
        if element.tag.lower() not in {"symbol", "session", "record"}:
            raise ValueError("Unknown XML record element")
        if element.text and element.text.strip().startswith("{"):
            items.append(json.loads(element.text))
        elif kind == "sessions":
            items.append(
                {
                    "name": element.get("name", ""),
                    "broker": element.get("broker", "-1"),
                    "brokerName": "Default",
                    "timezone": element.get("timezone", "UTC"),
                    "elements": [
                        {
                            "dayFrom": child.get("startDay", "Mon"),
                            "dayTo": child.get("endDay", "Mon"),
                            "timeFrom": child.get("startTime", "00:00"),
                            "timeTo": child.get("endTime", "23:59"),
                            "eod": child.get("seoc") == "Yes",
                            "sessionType": child.get("type", "Regular"),
                        }
                        for child in element
                        if child.tag == "SessionElement"
                    ],
                    "holidays": [
                        {
                            "date_str": child.get("date", ""),
                            "description": child.get("description", ""),
                        }
                        for child in element
                        if child.tag == "Holiday"
                    ],
                }
            )
        else:
            items.append(_xml_symbol(element))
    return {"version": 1, "kind": kind, kind: items, "brokers": []}


def parse_broker_records(content: str, kind: str) -> dict[str, Any]:
    """Normalize JSON or versioned XML records without guessing a vendor schema."""
    if (
        not isinstance(content, str)
        or not 0 < len(content.encode()) <= _MAX_DOCUMENT
        or kind not in {"symbols", "sessions"}
    ):
        raise ValueError("Choose a symbols/sessions file up to 2 MB")
    if content.lstrip().startswith("<"):
        payload = _xml_records(content, kind)
    else:
        payload = json.loads(content)
    if (
        not isinstance(payload, dict)
        or payload.get("version") != 1
        or payload.get("kind") != kind
        or not isinstance(payload.get(kind), list)
        or not 1 <= len(payload[kind]) <= _MAX_RECORDS
    ):
        raise ValueError("Invalid versioned catalog document")
    return payload


def _import_record(
    gateway: Any,
    kind: str,
    source: dict[str, Any],
    target: str,
    *,
    broker_id: int,
    options: dict[str, Any],
    profile: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    """Validate and commit one record within its own conflict-safe transaction."""
    table = "datamgr_symbols" if kind == "symbols" else "datamgr_sessions"
    policy = options.get("conflict_policy", "error")
    if kind == "symbols":
        safe_component(target)
    with gateway.transaction() as tx:
        existing = require_data(
            tx.read_records(table, filters={"name": target}, limit=1)
        )["records"]
        if existing and policy != "overwrite":
            raise ValueError("Definition already exists")
        if existing and int(existing[0].get("broker_id", -1)) != broker_id:
            raise ValueError("Existing definition belongs to another broker")
        values = {**source, "broker_id": broker_id}
        if kind == "symbols":
            fields = symbol_updates(values)
            if options.get("use_profile_costs") and profile:
                spread = json.loads(
                    profile.get("spread_model_json") or '{"model":"inherit"}'
                )
                commission = json.loads(
                    profile.get("commission_model_json") or '{"model":"inherit"}'
                )
                if spread.get("model") == "fixed":
                    fields["default_spread"] = spread["value"]
                if commission.get("model") != "inherit":
                    fields.update(
                        symbol_updates(
                            {
                                "commissions": json.dumps(
                                    {"version": 1, "settings": commission}
                                )
                            }
                        )
                    )
            now = datetime.now(UTC).isoformat()
            row = (
                _apply_field_updates(existing[0], fields, now)
                if existing
                else _build_row_dict(target, now, **fields)
            )
        else:
            fields = {
                key: value
                for key, value in values.items()
                if key
                in {
                    "description",
                    "timezone",
                    "windows",
                    "holidays",
                    "is_default",
                    "broker_id",
                }
            }
            row = session_row(
                {
                    **(session_editable(existing[0]) if existing else {}),
                    **fields,
                    "name": target,
                }
            )
        saved = require_data(
            tx.update_record(table, row, filters={"name": target})
            if existing
            else tx.create_records(table, row)
        )["records"][0]
    return saved, bool(existing)


def import_broker_records(
    gateway: Any, kind: str, broker_id: str, body: dict[str, Any]
) -> dict[str, Any]:
    """Commit each selected record atomically and report only confirmed identities."""
    if kind not in {"symbols", "sessions"}:
        raise ValueError("Choose symbols or sessions")
    identifier = int(broker_id)
    profile = None
    if identifier != -1:
        profiles = require_data(
            gateway.read_records("datamgr_broker", filters={"id": identifier}, limit=1)
        )["records"]
        if (
            not profiles
            or profiles[0].get("is_system")
            or not profiles[0].get("mt_use")
            or not profiles[0].get("enabled", 1)
        ):
            raise ValueError(
                "Choose an enabled custom broker with symbol/session settings"
            )
        profile = profiles[0]
    options = body.get("options") or {}
    selected = options.get("selected_names", [])
    records = body.get(kind)
    if (
        not isinstance(records, list)
        or not isinstance(selected, list)
        or not selected
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Choose distinct records to import")
    field = "symbol" if kind == "symbols" else "name"
    sources = {
        row[field]: row
        for row in records
        if isinstance(row, dict) and isinstance(row.get(field), str)
    }
    if any(name not in sources for name in selected):
        raise ValueError("Selected record is missing from file")
    postfix = options.get("postfix", "")
    policy = options.get("conflict_policy", "error")
    if not isinstance(postfix, str) or policy not in {"error", "overwrite"}:
        raise ValueError("Invalid import options")
    result: dict[str, Any] = {
        "broker_id": broker_id,
        "records": [],
        "failed": [],
        "unattempted": [],
        "created_count": 0,
        "updated_count": 0,
    }
    for name in selected:
        target = name + postfix
        try:
            saved, existing = _import_record(
                gateway,
                kind,
                sources[name],
                target,
                broker_id=identifier,
                options=options,
                profile=profile,
            )
            result["records"].append(
                symbol_to_ui(saved)
                if kind == "symbols"
                else {
                    **TradingSession.from_dict(saved).to_dict(),
                    "id": str(saved["id"]),
                }
            )
            result["updated_count" if existing else "created_count"] += 1
        except (ValueError, TypeError, KeyError, RuntimeError) as error:
            result["failed"].append({"name": target, "reason": str(error)})
    result["imported_count"] = len(result["records"])
    return result


def register_broker_import_routes(router: APIRouter) -> None:
    """Install the preview and import contracts already expected by the browser."""

    @router.post("/brokers/import-preview")
    def preview(body: dict[str, Any]) -> dict[str, Any]:
        try:
            return {
                "success": True,
                "data": parse_broker_records(
                    body.get("content", ""), body.get("kind", "")
                ),
            }
        except (ValueError, TypeError, ET.ParseError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error

    @router.post("/brokers/{broker_id}/import-{kind}")
    def import_records(
        broker_id: str, kind: str, request: Request, body: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            return {
                "success": True,
                "data": import_broker_records(
                    request.app.state.persistence, kind, broker_id, body
                ),
            }
        except (ValueError, TypeError, KeyError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error
