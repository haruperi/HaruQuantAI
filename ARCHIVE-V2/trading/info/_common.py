"""Shared helpers for trading read-only info facades."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

from app.services.brokers import get_broker_module
from app.services.trading.contracts import JsonObject
from app.services.trading.security import redact_for_boundary
from app.utils.logger import logger

T = TypeVar("T")


def broker_call(name: str, *args: object, **kwargs: object) -> object:
    """Call a read-only broker information function.

    Args:
        name: Broker module function name.
        *args: Positional function arguments.
        **kwargs: Keyword function arguments.

    Returns:
        object: Broker response, or ``None`` when unavailable.
    """
    logger.info("Calling read-only broker info function {}.", name)
    broker = get_broker_module()
    func = getattr(broker, name, None)
    if not callable(func):
        logger.info("Broker info function {} is unavailable.", name)
        return None
    try:
        return func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Read-only broker info call {} failed: {}.", name, exc)
        return None


def first_or_none(value: object) -> object | None:
    """Return the first item from a broker collection.

    Args:
        value: Broker response value.

    Returns:
        object | None: First item when available.
    """
    logger.debug("Selecting first broker info item.")
    if isinstance(value, Iterable) and not isinstance(value, str | bytes | dict):
        return next(iter(value), None)
    return value


def iter_or_empty(value: object) -> tuple[object, ...]:
    """Return a type-narrowed tuple view of a broker collection.

    Args:
        value: Broker response value.

    Returns:
        tuple[object, ...]: Items when the value is iterable, else empty.
    """
    logger.debug("Coercing broker info response to an iterable tuple.")
    if isinstance(value, Iterable) and not isinstance(value, str | bytes | dict):
        return tuple(value)
    return ()


def safe_attr(
    data: object | None,
    name: str,
    default: T,
    caster: Callable[..., T],
) -> T:
    """Read and cast a broker attribute with a neutral fallback.

    Args:
        data: Broker data object.
        name: Attribute name.
        default: Neutral fallback.
        caster: Cast function.

    Returns:
        T: Cast attribute value or fallback.
    """
    logger.debug("Reading broker info attribute {}.", name)
    if data is None:
        return default
    try:
        return caster(getattr(data, name, default))
    except (TypeError, ValueError):
        logger.warning("Broker info attribute {} could not be cast.", name)
        return default


def redacted_info_payload(payload: JsonObject) -> JsonObject:
    """Redact an exported info payload.

    Args:
        payload: JSON-safe info payload.

    Returns:
        JsonObject: Redacted payload.
    """
    logger.info("Redacting trading info payload.")
    return redact_for_boundary(payload).payload
