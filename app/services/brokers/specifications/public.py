"""Public function surface for the provider specification feature.

All operations are standalone functions; contract classes remain internal and
are created, read, and parsed through opaque values.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.services.brokers.specifications.build import (
    build_provider_specification_snapshot as _build,
)
from app.services.brokers.specifications.build import (
    dump_provider_specification_snapshot as _dump,
)
from app.services.brokers.specifications.build import (
    parse_provider_specification_snapshot as _parse,
)
from app.services.brokers.specifications.build import (
    verify_provider_specification_snapshot as _verify,
)

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts.protocols import BrokerAdapter
    from app.services.brokers.canonical_contracts.responses import StandardResponse
    from app.services.brokers.specifications.contracts import (
        ProviderSpecificationSnapshot,
    )


def build_provider_specification_snapshot(**kwargs: object) -> object:
    """Build one typed current provider specification snapshot.

    Args:
        **kwargs: Raw ``symbol_info`` record plus the explicit connection
            identity fields accepted by the internal builder.

    Returns:
        The validated immutable opaque snapshot.

    Raises:
        ValueError: If any required field is missing or invalid.
    """
    return _build(
        kwargs.pop("symbol_info"),
        **kwargs,  # type: ignore[arg-type]
    )


def parse_provider_specification_snapshot(value: Mapping[str, object]) -> object:
    """Parse one canonical snapshot mapping back into the typed contract.

    Args:
        value: JSON-safe mapping produced by ``dump_provider_specification_snapshot``.

    Returns:
        The validated immutable opaque snapshot with a verified checksum.

    Raises:
        ValueError: If the mapping is not a canonical snapshot.
    """
    return _parse(value)


def dump_provider_specification_snapshot(snapshot: object) -> dict[str, object]:
    """Return the canonical JSON-safe mapping of one snapshot.

    Args:
        snapshot: Opaque snapshot value.

    Returns:
        Deterministic JSON-safe field mapping including the checksum.
    """
    return _dump(snapshot)  # type: ignore[arg-type]


def get_provider_specification_snapshot_field(
    snapshot: object,
    field: str,
) -> object:
    """Read one named snapshot field.

    Args:
        snapshot: Opaque snapshot value.
        field: Canonical field name.

    Returns:
        The field value (JSON-safe scalar or nested block mapping).

    Raises:
        ValueError: If the field name is not part of the schema.
    """
    dumped = _dump(snapshot)  # type: ignore[arg-type]
    if field not in dumped:
        message = "unknown snapshot field: " + field
        raise ValueError(message)
    return dumped[field]


def verify_provider_specification_snapshot(snapshot: object) -> bool:
    """Recompute and compare the snapshot checksum.

    Args:
        snapshot: Opaque snapshot value.

    Returns:
        True when the stored checksum matches the canonical material.
    """
    return _verify(snapshot)  # type: ignore[arg-type]


async def get_broker_provider_specification(
    adapter: BrokerAdapter, symbol: str
) -> StandardResponse[ProviderSpecificationSnapshot]:
    """Read one current provider specification snapshot through the adapter.

    Args:
        adapter: Broker adapter instance.
        symbol: Exact provider-native symbol string.

    Returns:
        The canonical adapter response carrying the snapshot.
    """
    return await adapter.get_provider_specification(symbol)


__all__ = [
    "build_provider_specification_snapshot",
    "dump_provider_specification_snapshot",
    "get_broker_provider_specification",
    "get_provider_specification_snapshot_field",
    "parse_provider_specification_snapshot",
    "verify_provider_specification_snapshot",
]
