"""Thread-safe registry for registering and lazy resolving data sources."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.services.data.contracts.errors import DataError
from app.services.data.sources.protocol import MarketDataSource
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts.sources import (
        SourceDescriptor,
        SourceIdentity,
        SourceIdentityRequest,
    )

type SourceFactory = Callable[[], MarketDataSource]

_lock = threading.RLock()
_registry: dict[str, tuple[SourceDescriptor, SourceFactory]] = {}
_instances: dict[str, MarketDataSource] = {}
_identities: dict[str, tuple[SourceIdentity, ...]] = {}


def register_source(
    descriptor: SourceDescriptor,
    factory: SourceFactory,
    identities: tuple[SourceIdentity, ...] = (),
) -> None:
    """Register a data source descriptor and lazy factory atomically.

    Args:
        descriptor: Capability and readiness declaration.
        factory: Lazy callable returning the source instance.
        identities: Explicit canonical/friendly/provider identity mappings.

    Raises:
        DataError: If the source_id is already registered.
    """
    logger.info("Registering source %s", descriptor.source_id)
    if any(identity.source_id != descriptor.source_id for identity in identities):
        raise DataError("INVALID_INPUT", safe_details={"field": "identities"})
    with _lock:
        if descriptor.source_id in _registry:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": f"Source {descriptor.source_id} is already registered"
                },
            )
        _registry[descriptor.source_id] = (descriptor, factory)
        _identities[descriptor.source_id] = identities


def resolve_source(source_id: str) -> MarketDataSource:
    """Lazily resolve and instantiate a registered source.

    Args:
        source_id: Identifier of the source.

    Returns:
        Instantiated MarketDataSource implementation.

    Raises:
        DataError: If the source is not registered.
    """
    logger.info("Resolving source instance for %s", source_id)
    with _lock:
        if source_id in _instances:
            return _instances[source_id]
        if source_id not in _registry:
            raise DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"field": "source_id"},
            )
        _, factory = _registry[source_id]
        instance = factory()
        _instances[source_id] = instance
        return instance


def get_source_descriptor(source_id: str) -> SourceDescriptor:
    """Get the descriptor for a registered source.

    Args:
        source_id: Identifier of the source.

    Returns:
        The descriptor of the source.

    Raises:
        DataError: If the source is not registered.
    """
    logger.info("Retrieving descriptor for source %s", source_id)
    with _lock:
        if source_id not in _registry:
            raise DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"field": "source_id"},
            )
        return _registry[source_id][0]


def update_source_descriptor_readiness(
    source_id: str, readiness: str
) -> SourceDescriptor:
    """Update the readiness level of a registered source.

    Args:
        source_id: Identifier of the source.
        readiness: Target readiness level.

    Returns:
        The updated descriptor.
    """
    logger.info(
        "Updating descriptor readiness for source %s to %s", source_id, readiness
    )
    with _lock:
        if source_id not in _registry:
            raise DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"field": "source_id"},
            )
        desc, factory = _registry[source_id]
        updated = desc.model_copy(update={"readiness": readiness})
        _registry[source_id] = (updated, factory)
        return updated


def list_registered_sources() -> tuple[SourceDescriptor, ...]:
    """List descriptors for all currently registered sources.

    Returns:
        A tuple of registered source descriptors.
    """
    logger.info("Listing all registered source descriptors")
    with _lock:
        return tuple(desc for desc, _ in _registry.values())


def resolve_source_identity(request: SourceIdentityRequest) -> SourceIdentity:
    """Resolve one explicit identity mapping without assuming symbol equality.

    Args:
        request: Source and caller identity to resolve.

    Returns:
        The single matching versioned source identity.

    Raises:
        DataError: If no mapping or more than one mapping matches.
    """
    logger.info("Resolving identity for source %s", request.source_id)
    normalized = request.identity.casefold()
    with _lock:
        candidates = tuple(
            identity
            for identity in _identities.get(request.source_id, ())
            if normalized
            in {
                identity.canonical_symbol.casefold(),
                identity.friendly_name.casefold(),
                identity.provider_symbol.casefold(),
            }
        )
    if len(candidates) != 1:
        raise DataError(
            "MISSING_ASSET_METADATA",
            safe_details={"field": "source_identity"},
            request_id=request.request_id,
        )
    identity = candidates[0]
    if identity.request_id == request.request_id:
        return identity
    return identity.model_copy(update={"request_id": request.request_id})


def _reset_registry() -> None:
    """Private reset helper to reset registry state between test suites."""
    logger.debug("Running DATA function: _reset_registry")
    with _lock:
        _registry.clear()
        _instances.clear()
        _identities.clear()


__all__ = [
    "get_source_descriptor",
    "list_registered_sources",
    "register_source",
    "resolve_source",
    "resolve_source_identity",
    "update_source_descriptor_readiness",
]
