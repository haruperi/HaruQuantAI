# ruff: noqa: DOC501, N812
"""BrokerAccountSnapshot v1 cross-domain contract transport.

The application Phase 0 reconciliation (``feature``) requires a
normalized account snapshot carrying broker-reported balance, equity, margin,
currency, permissions, and source timestamp. Open Decision ``OD-BRK-01`` records
that the existing ``AccountStateSnapshot`` model lives in Data
(``app/services/data/evidence/account_contracts.py``); the approved in-domain
direction (see Brokers README ``### application Phase 0 reconciliation``) is
to adopt a **distinct Brokers-owned name** rather than relocate the Data model.

This module therefore defines ``BrokerAccountSnapshot v1`` as a fresh
Brokers-owned contract. It does **not** import, alias, or mutate Data's
``AccountStateSnapshot``; the cross-domain relocation remains a pending item in
the Brokers README Open Decisions.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from app.services.brokers.contracts.enums import BrokerEnvironment, BrokerId
from app.utils import canonical_digest, to_json_safe
from app.utils import create_validation_error as ValidationError

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.account_snapshot.v1"

_PERMISSION_STATES = frozenset(
    {"FULL", "READ_ONLY", "CLOSE_ONLY", "NO_TRADING", "UNKNOWN"}
)
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "broker",
        "environment",
        "account_reference",
        "currency",
        "balance",
        "equity",
        "margin_used",
        "margin_free",
        "margin_level",
        "leverage",
        "permissions",
        "source_timestamp",
        "integrity_hash",
    }
)


def _require_text(value: object) -> str:
    """Validate non-empty text.

    Args:
        value: Candidate value.

    Returns:
        Validated text.

    Raises:
        ValidationError: If the value is not non-empty text.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    return value


def _require_optional_decimal(value: object) -> str | None:
    """Validate an optional finite decimal encoded as text.

    Args:
        value: Candidate value.

    Returns:
        Canonical decimal text, or ``None``.

    Raises:
        ValidationError: If the value is malformed.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID") from error
    if not parsed.is_finite():
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    return str(parsed)


def _require_timestamp(value: datetime) -> str:
    """Validate an aware UTC timestamp and return canonical text.

    Args:
        value: Candidate timestamp.

    Returns:
        Canonical ISO-8601 UTC text.

    Raises:
        ValidationError: If the timestamp is naive or non-UTC.
    """
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    return value.isoformat().replace("+00:00", "Z")


def build_broker_account_snapshot(
    *,
    broker: BrokerId | str,
    environment: BrokerEnvironment | str,
    account_reference: str | None,
    currency: str,
    balance: Decimal | float | str,
    equity: Decimal | float | str,
    margin_used: Decimal | float | str | None,
    margin_free: Decimal | float | str | None,
    margin_level: Decimal | float | str | None,
    leverage: str | None,
    permissions: str,
    source_timestamp: datetime,
) -> dict[str, object]:
    """Build and hash a redacted BrokerAccountSnapshot v1 mapping.

    Args:
        broker: Owning broker identifier.
        environment: Configured broker environment.
        account_reference: Optional broker account reference.
        currency: Account currency.
        balance: Broker-reported account balance.
        equity: Broker-reported account equity.
        margin_used: Broker-reported used margin.
        margin_free: Broker-reported free margin.
        margin_level: Broker-reported margin level percentage.
        leverage: Broker-reported leverage expression.
        permissions: Normalized permission verdict.
        source_timestamp: Aware UTC broker-reported timestamp.

    Returns:
        BrokerAccountSnapshot v1 mapping.

    Raises:
        ValidationError: If any field evidence is invalid.
    """
    broker_value = (
        broker if isinstance(broker, BrokerId) else BrokerId(_require_text(broker))
    )
    env_value = (
        environment
        if isinstance(environment, BrokerEnvironment)
        else BrokerEnvironment(_require_text(environment))
    )
    if account_reference is not None:
        _require_text(account_reference)
    if leverage is not None:
        _require_text(leverage)
    if permissions not in _PERMISSION_STATES:
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    snapshot: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "broker": broker_value.value,
        "environment": env_value.value,
        "account_reference": account_reference,
        "currency": _require_text(currency),
        "balance": _require_optional_decimal(balance),
        "equity": _require_optional_decimal(equity),
        "margin_used": _require_optional_decimal(margin_used),
        "margin_free": _require_optional_decimal(margin_free),
        "margin_level": _require_optional_decimal(margin_level),
        "leverage": leverage,
        "permissions": permissions,
        "source_timestamp": _require_timestamp(source_timestamp),
    }
    snapshot["integrity_hash"] = canonical_digest(snapshot)
    return snapshot


def parse_broker_account_snapshot(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a BrokerAccountSnapshot v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached account snapshot.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INTEGRITY_INVALID")
    source_timestamp_text = value.get("source_timestamp")
    if not isinstance(source_timestamp_text, str):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    account_reference = value.get("account_reference")
    leverage = value.get("leverage")
    if account_reference is not None and not isinstance(account_reference, str):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    if leverage is not None and not isinstance(leverage, str):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    rebuilt = build_broker_account_snapshot(
        broker=cast("str", value["broker"]),
        environment=cast("str", value["environment"]),
        account_reference=account_reference,
        currency=cast("str", value["currency"]),
        balance=cast("str", value["balance"]),
        equity=cast("str", value["equity"]),
        margin_used=cast("str", value["margin_used"]),
        margin_free=cast("str", value["margin_free"]),
        margin_level=cast("str", value["margin_level"]),
        leverage=leverage,
        permissions=cast("str", value["permissions"]),
        source_timestamp=datetime.fromisoformat(source_timestamp_text),
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("BROKER_ACCOUNT_SNAPSHOT_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_broker_account_snapshot",
    "parse_broker_account_snapshot",
]
