"""Durable execution-session registry operations."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.services.trading.persistence import (
    archive_execution_session_record,
    assign_simulation_session_identity_record,
    complete_simulation_session_configuration_record,
    create_execution_session_record,
    read_execution_session_events,
    read_execution_session_record,
    read_execution_session_records,
    set_default_execution_session_record,
    update_execution_session_record,
)
from app.services.trading.session_registry.contracts import _SessionRecord

logger = get_logger(__name__)
_SIM_USERNAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def _now() -> datetime:
    """Return the current aware UTC instant."""
    return datetime.now(UTC)


def create_execution_session(
    *,
    principal_id: str,
    environment_id: str,
    name: str,
    mode: str,
    provider: str,
    request_id: str,
    description: str = "",
    provider_account_ref: str | None = None,
    credential_ref: str | None = None,
    simulation_session_id: str | None = None,
    dataset_ref: str | None = None,
    dataset_revision: str | None = None,
    dataset_hash: str | None = None,
    sim_initial_balance: object | None = None,
    sim_leverage: int | None = None,
    sim_account_currency: str | None = None,
    simulation_username: str | None = None,
    auto_start: bool = True,
    metadata: Mapping[str, str] | None = None,
) -> object:
    """Create one durable stopped session without opening an authority.

    Returns:
        Created durable session projection payload.

    Raises:
        ValueError: If mode requirements or parameter validations fail.
    """
    if mode == "sim":
        if sim_initial_balance is None or sim_leverage is None:
            raise ValueError("SIM sessions require initial balance and leverage")
        if not all((dataset_ref, dataset_revision, dataset_hash)):
            raise ValueError("SIM sessions require verified dataset lineage")
        sim_account_currency = sim_account_currency or "USD"
    elif any(
        value is not None
        for value in (
            sim_initial_balance,
            sim_leverage,
            sim_account_currency,
            dataset_ref,
            dataset_revision,
            dataset_hash,
        )
    ):
        raise ValueError(
            "DEMO and LIVE account and dataset values are provider-authored"
        )
    now = _now()
    identity_material = (
        f"execution-session:{principal_id}:{environment_id}:{mode}:{request_id}:{name}"
    )
    session_id = derive_stable_id("id", identity_material)
    record = _SessionRecord(
        session_id=session_id,
        principal_id=principal_id,
        environment_id=environment_id,
        name=name,
        description=description,
        mode=mode,  # type: ignore[arg-type]
        provider=provider,
        provider_account_ref=provider_account_ref,
        credential_ref=credential_ref,
        simulation_session_id=simulation_session_id,
        dataset_ref=dataset_ref,
        dataset_revision=dataset_revision,
        dataset_hash=dataset_hash,
        sim_initial_balance=(
            None if sim_initial_balance is None else Decimal(str(sim_initial_balance))
        ),
        sim_leverage=sim_leverage,
        sim_account_currency=sim_account_currency,
        auto_start=auto_start,
        metadata=dict(metadata or {}),
        created_at=now,
        updated_at=now,
    )
    create_execution_session_record(record.model_dump(mode="json"), request_id)
    logger.info("Created Trading execution session %s", session_id)
    if mode == "sim" and simulation_username is not None:
        return assign_simulation_session_identity(
            session_id,
            expected_version=record.version,
            username=simulation_username,
            request_id=request_id,
        )
    return record


def assign_simulation_session_identity(
    session_id: str,
    *,
    expected_version: int,
    username: str,
    request_id: str,
) -> object:
    """Assign a concurrency-safe ``username_N`` identity to one SIM session.

    Returns:
        Updated durable session projection.

    Raises:
        ValueError: If username cannot form a SIM identity or session disappears.
    """
    safe_username = _SIM_USERNAME_PATTERN.sub("_", username.strip()).strip("_")
    if not safe_username:
        raise ValueError("authenticated username cannot form a SIM identity")
    assign_simulation_session_identity_record(
        session_id,
        expected_version=expected_version,
        username=safe_username,
        request_id=request_id,
    )
    result = get_execution_session(session_id)
    if result is None:
        raise ValueError("SIM session disappeared after identity allocation")
    return result


def complete_simulation_session_configuration(
    session_id: str,
    *,
    expected_version: int,
    username: str,
    account_name: str,
    dataset_ref: str,
    dataset_revision: str,
    dataset_hash: str,
    request_id: str,
) -> object:
    """Complete a stopped legacy SIM using authenticated and verified evidence.

    Returns:
        Updated durable session projection.

    Raises:
        ValueError: If identity evidence is absent or the atomic update fails.
    """
    safe_username = _SIM_USERNAME_PATTERN.sub("_", username.strip()).strip("_")
    if not safe_username or not account_name.strip():
        raise ValueError("SIM identity evidence is required")
    complete_simulation_session_configuration_record(
        session_id,
        expected_version=expected_version,
        username=safe_username,
        account_name=account_name.strip(),
        dataset_ref=dataset_ref,
        dataset_revision=dataset_revision,
        dataset_hash=dataset_hash,
        request_id=request_id,
    )
    result = get_execution_session(session_id)
    if result is None:
        raise ValueError("configured SIM session is unavailable")
    return result


def list_execution_sessions(
    *, principal_id: str, environment_id: str, mode: str | None = None
) -> tuple[object, ...]:
    """List non-archived sessions newest-first.

    Returns:
        Tuple of matching execution session objects.
    """
    return tuple(
        _SessionRecord.model_validate(item)
        for item in read_execution_session_records(principal_id, environment_id, mode)
    )


def get_execution_session(session_id: str) -> object | None:
    """Read one session by stable identity.

    Returns:
        Execution session object if found, otherwise None.
    """
    item = read_execution_session_record(session_id)
    return None if item is None else _SessionRecord.model_validate(item)


def update_execution_session_metadata(
    session_id: str,
    *,
    expected_version: int,
    name: str,
    description: str,
    auto_start: bool,
    metadata: Mapping[str, str],
    request_id: str,
) -> object:
    """Compare-and-swap editable non-authority session metadata.

    Returns:
        Updated durable session projection.

    Raises:
        ValueError: If atomic update fails or session disappears.
    """
    update_execution_session_record(
        session_id,
        expected_version=expected_version,
        changes={
            "name": name,
            "description": description,
            "auto_start": auto_start,
            "metadata": dict(metadata),
            "updated_at": _now().isoformat(),
        },
        event_type="metadata_updated",
        request_id=request_id,
    )
    result = get_execution_session(session_id)
    if result is None:
        raise ValueError("execution session disappeared after update")
    return result


def set_default_execution_session(
    session_id: str, *, expected_version: int, request_id: str
) -> object:
    """Select exactly one default session for its mode and scope.

    Returns:
        Default session projection payload.

    Raises:
        ValueError: If setting default session fails or session disappears.
    """
    set_default_execution_session_record(
        session_id, expected_version=expected_version, request_id=request_id
    )
    result = get_execution_session(session_id)
    if result is None:
        raise ValueError("default execution session is unavailable")
    return result


def archive_execution_session(
    session_id: str, *, expected_version: int, request_id: str
) -> object:
    """Archive a stopped, inactive session while retaining evidence.

    Returns:
        Archived session projection payload.

    Raises:
        ValueError: If archiving fails or session disappears.
    """
    archive_execution_session_record(
        session_id, expected_version=expected_version, request_id=request_id
    )
    result = get_execution_session(session_id)
    if result is None:
        raise ValueError("archived execution session is unavailable")
    return result


def get_execution_session_events(session_id: str) -> tuple[Mapping[str, Any], ...]:
    """Return bounded immutable lifecycle history newest-first."""
    return read_execution_session_events(session_id)


__all__ = [
    "archive_execution_session",
    "assign_simulation_session_identity",
    "complete_simulation_session_configuration",
    "create_execution_session",
    "get_execution_session",
    "get_execution_session_events",
    "list_execution_sessions",
    "set_default_execution_session",
    "update_execution_session_metadata",
]
