"""Secret-safe support for genuine non-production Brokers usage programs."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_id,
    get_broker_value_field,
    resolve_provider_connection_config,
)
from app.utils import load_broker_provider_settings

_NON_PRODUCTION_ENVIRONMENTS = frozenset({"demo", "testnet", "sandbox"})


class UsageEvidenceError(RuntimeError):
    """Report one bounded usage-evidence failure without sensitive values."""


def config(broker_id: str | object) -> object:
    """Build one genuine enabled non-production provider configuration."""
    raw_id = (
        get_broker_value_field(broker_id, "value")
        if not isinstance(broker_id, str)
        else broker_id
    )
    try:
        return resolve_provider_connection_config(
            get_broker_id(str(raw_id)),
            settings=load_broker_provider_settings(),
        )
    except ValueError as error:
        raise UsageEvidenceError(str(error)) from error


def create_real_adapter(broker_id: str | object) -> object:
    """Create one genuine disconnected adapter through the public registry."""
    cfg = config(broker_id)
    created = create_broker_adapter(get_broker_id(str(broker_id)), cfg)
    require_success(f"{broker_id} adapter construction", created)
    adapter = get_broker_value_field(created, "data")
    if adapter is None:
        raise UsageEvidenceError(f"{broker_id} adapter construction returned no data")
    return adapter


@asynccontextmanager
async def real_session(broker_id: str) -> AsyncIterator[object]:
    """Open, verify, and deterministically close one genuine provider session."""
    adapter = create_real_adapter(broker_id)
    try:
        connected = await connect_broker(adapter)
        require_success(f"{broker_id} connect", connected)
        yield adapter
    finally:
        disconnected = await disconnect_broker(adapter)
        require_success(f"{broker_id} disconnect", disconnected)


def require_success(
    label: str,
    result: object,
) -> object:
    """Require and display one canonical successful broker result."""
    if get_broker_value_field(result, "status") != "success":
        error = get_broker_value_field(result, "error")
        code = (
            "NO_ERROR_CODE" if error is None else get_broker_value_field(error, "code")
        )
        raise UsageEvidenceError(f"{label} failed with {code}")
    show(label, result)
    return result


def require_error(
    label: str,
    result: object,
    *expected: str,
) -> object:
    """Require and display one exact canonical fail-closed broker result."""
    expected_codes = set(expected)
    error = get_broker_value_field(result, "error")
    if error is None or get_broker_value_field(error, "code") not in expected_codes:
        actual = (
            get_broker_value_field(result, "status")
            if error is None
            else get_broker_value_field(error, "code")
        )
        wanted = ", ".join(expected)
        raise UsageEvidenceError(f"{label} returned {actual}; expected {wanted}")
    show(label, result)
    return result


def show(label: str, result: object) -> None:
    """Print a bounded canonical result including its substantive payload."""
    detail = ""
    error = get_broker_value_field(result, "error")
    if error is not None:
        detail = f" {get_broker_value_field(error, 'code')}"
    metadata = get_broker_value_field(result, "metadata")
    extensions = get_broker_value_field(metadata, "extensions")
    operation = extensions.get("operation", "unknown")
    data = get_broker_value_field(result, "data")
    rendered = "<none>" if data is None else repr(data)[:500]
    print(
        label,
        get_broker_value_field(result, "status"),
        str(operation) + detail,
        "data=" + rendered,
    )


def show_value(
    label: str,
    result: object,
    value: object,
) -> None:
    """Print one bounded mapped provider value alongside result metadata."""
    require_success(label, result)
    print(f"{label} value", value)
