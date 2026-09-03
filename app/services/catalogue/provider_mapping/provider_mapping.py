"""Provider and Broker Mapping domain logic and capability implementation.

Purpose:
    Map external broker and data provider symbols, identifiers, and feed tickers
    to canonical instruments with time-bounded validity and overlap protection.

Key capabilities:
    * Register and manage broker-specific symbol mappings with effective
      half-open intervals.
    * Map external provider identifiers to canonical instruments preserving raw
      symbols.
    * Resolve canonical instrument identity and version for provider symbols
      as of a timestamp.
    * Enforce non-overlapping mapping interval constraints across
      provider/broker pairs.
    * Publish typed domain events upon mapping creation, update, and deletion.
    * Provide async map_providers implementing MapProvidersCapability.

Python API usage:
    from app.services.catalogue.provider_mapping.provider_mapping import (
        ProviderMappingService,
    )
    from app.contracts.catalogue.models import (
        MapProvidersRequest,
        ProviderRef,
    )

    service = ProviderMappingService()
    result = await service.map_providers(
        MapProvidersRequest(
            request_id="018f0000-0000-7000-8000-000000000001",
            capability_snapshot_id="018f0000-0000-7000-8000-000000000002",
            operation="RESOLVE",
            provider=ProviderRef(
                provider_id="018f0000-0000-7000-8000-000000000003",
                provider_name="FeedA",
            ),
            provider_symbol="EURUSD.raw",
            as_of="2026-06-01T00:00:00.000000Z",
        )
    )

CLI usage:
    uv run python -m app.services.catalogue.provider_mapping.provider_mapping
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from typing import TYPE_CHECKING, override

from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    ProviderSymbolMappingChanged,
    ProviderSymbolMappingDeleted,
)
from app.contracts.catalogue.models import (
    BrokerRef,
    InstrumentRef,
    MapProvidersRequest,
    MapProvidersSuccess,
    ProviderRef,
    ProviderSymbolMapping,
)
from app.contracts.catalogue.ports import MapProvidersCapability
from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
)
from app.services.catalogue.provider_mapping.config import ProviderMappingConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus


def _half_open_intervals_overlap(
    start_a: str,
    end_a: str | None,
    start_b: str,
    end_b: str | None,
) -> bool:
    """Report whether two half-open UTC intervals share at least one instant.

    Args:
        start_a: Inclusive start of the first interval.
        end_a: Exclusive end of the first interval, or None when unbounded.
        start_b: Inclusive start of the second interval.
        end_b: Exclusive end of the second interval, or None when unbounded.

    Returns:
        True when the intervals intersect, False when they are disjoint.
    """
    return (end_a is None or start_b < end_a) and (end_b is None or start_a < end_b)


class ProviderMappingService(MapProvidersCapability):
    """Map broker and provider identities to canonical instruments."""

    def __init__(
        self,
        config: ProviderMappingConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the provider mapping service with configuration.

        Args:
            config: Optional configuration dataclass.
            event_bus: Optional kernel event bus for domain event publishing.
        """
        self._config = config or ProviderMappingConfig()
        self._event_bus = event_bus
        self._mem_uri: str | None = None
        if self._config.database_path is not None:
            self._conn = sqlite3.connect(
                str(self._config.database_path), check_same_thread=False
            )
        else:
            self._mem_uri = f"file:mem_map_{id(self)}?mode=memory&cache=shared"
            self._conn = sqlite3.connect(
                self._mem_uri, uri=True, check_same_thread=False
            )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection.

        Returns:
            Configured SQLite database connection.
        """
        return self._conn

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if hasattr(self, "_conn"):
            with contextlib.suppress(sqlite3.Error):
                self._conn.close()

    def __del__(self) -> None:
        """Ensure SQLite connection is closed on garbage collection."""
        self.close()

    def _init_db(self) -> None:
        """Initialize database schema if auto_migrate is enabled."""
        if not self._config.auto_migrate:
            return
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_symbol_mappings (
                    mapping_id TEXT PRIMARY KEY,
                    instrument_id TEXT NOT NULL,
                    instrument_version INTEGER NOT NULL,
                    provider_id TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    broker_id TEXT,
                    broker_name TEXT,
                    provider_symbol TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_to TEXT,
                    content_hash TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    @override
    async def map_providers(
        self,
        request: MapProvidersRequest,
    ) -> MapProvidersSuccess | CatalogueFailure:
        """Map provider and broker identities to canonical instruments.

        Args:
            request: Operation-discriminated provider mapping request.

        Returns:
            The resolved or persisted provider symbol mappings on success,
            otherwise a structured catalogue failure.
        """
        match request.operation:
            case "RESOLVE":
                return self._handle_resolve(request)
            case "UPSERT":
                return await self._handle_upsert(request)
            case "DELETE":
                return await self._handle_delete(request)

    def _handle_resolve(
        self,
        request: MapProvidersRequest,
    ) -> MapProvidersSuccess | CatalogueFailure:
        """Handle RESOLVE operation for provider mappings.

        Args:
            request: Validated RESOLVE request.

        Returns:
            MapProvidersSuccess containing resolved mappings or CatalogueFailure.

        Raises:
            ValueError: If provider, provider_symbol, or as_of is None.
        """
        if request.provider is None:
            msg = "provider is required for RESOLVE"
            raise ValueError(msg)
        if request.provider_symbol is None:
            msg = "provider_symbol is required for RESOLVE"
            raise ValueError(msg)
        if request.as_of is None:
            msg = "as_of is required for RESOLVE"
            raise ValueError(msg)

        provider_id_str = str(request.provider.provider_id)
        provider_symbol = request.provider_symbol
        as_of = request.as_of
        broker_id_str = (
            str(request.broker.broker_id) if request.broker is not None else None
        )

        with self._get_connection() as conn:
            if broker_id_str is not None:
                cursor = conn.execute(
                    """
                    SELECT raw_json, broker_id FROM provider_symbol_mappings
                    WHERE provider_id = ?
                      AND provider_symbol = ?
                      AND (broker_id = ? OR broker_id IS NULL)
                      AND effective_from <= ?
                      AND (effective_to IS NULL OR ? < effective_to)
                      AND is_deleted = 0
                    ORDER BY (CASE WHEN broker_id = ? THEN 1 ELSE 0 END) DESC,
                             effective_from DESC
                    """,
                    (
                        provider_id_str,
                        provider_symbol,
                        broker_id_str,
                        as_of,
                        as_of,
                        broker_id_str,
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT raw_json, broker_id FROM provider_symbol_mappings
                    WHERE provider_id = ?
                      AND provider_symbol = ?
                      AND effective_from <= ?
                      AND (effective_to IS NULL OR ? < effective_to)
                      AND is_deleted = 0
                    ORDER BY effective_from DESC
                    """,
                    (
                        provider_id_str,
                        provider_symbol,
                        as_of,
                        as_of,
                    ),
                )
            rows = cursor.fetchall()

            if not rows:
                return CatalogueFailure(
                    request_id=request.request_id,
                    code="CATALOGUE_NOT_FOUND",
                    problem=ProblemDetails(
                        type="urn:error:catalogue:not-found",
                        title="Mapping Not Found",
                        status=404,
                        code="CATALOGUE_NOT_FOUND",
                        detail=(
                            f"No active mapping found for provider {provider_id_str} "
                            f"symbol '{provider_symbol}' as of {as_of}"
                        ),
                        request_id=request.request_id,
                    ),
                    conflicting_refs=(),
                )

            mappings: list[ProviderSymbolMapping] = []
            for row in rows:
                mapping_data = json.loads(row["raw_json"])
                mappings.append(ProviderSymbolMapping.model_validate(mapping_data))

            return MapProvidersSuccess(
                request_id=request.request_id,
                mappings=tuple(mappings),
            )

    async def _handle_upsert(
        self,
        request: MapProvidersRequest,
    ) -> MapProvidersSuccess | CatalogueFailure:
        """Handle UPSERT operation for provider mappings.

        Args:
            request: Validated UPSERT request.

        Returns:
            MapProvidersSuccess on success or CatalogueFailure on overlap.

        Raises:
            ValueError: If mapping is None.
        """
        if request.mapping is None:
            msg = "mapping is required for UPSERT"
            raise ValueError(msg)
        mapping = request.mapping
        mapping_id_str = str(mapping.mapping_id)
        provider_id_str = str(mapping.provider.provider_id)
        broker_id_str = (
            str(mapping.broker.broker_id) if mapping.broker is not None else None
        )

        with self._get_connection() as conn:
            # Check existing mapping with same mapping_id
            cursor = conn.execute(
                """
                SELECT content_hash FROM provider_symbol_mappings
                WHERE mapping_id = ?
                """,
                (mapping_id_str,),
            )
            existing = cursor.fetchone()
            if (
                existing is not None
                and existing["content_hash"] == mapping.content_hash
            ):
                return MapProvidersSuccess(
                    request_id=request.request_id,
                    mappings=(mapping,),
                )

            # Check overlap against other active mappings for the same
            # provider, broker, and symbol.
            if broker_id_str is not None:
                cursor = conn.execute(
                    """
                    SELECT mapping_id, effective_from, effective_to
                    FROM provider_symbol_mappings
                    WHERE provider_id = ?
                      AND provider_symbol = ?
                      AND broker_id = ?
                      AND mapping_id != ?
                      AND is_deleted = 0
                    """,
                    (
                        provider_id_str,
                        mapping.provider_symbol,
                        broker_id_str,
                        mapping_id_str,
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT mapping_id, effective_from, effective_to
                    FROM provider_symbol_mappings
                    WHERE provider_id = ?
                      AND provider_symbol = ?
                      AND broker_id IS NULL
                      AND mapping_id != ?
                      AND is_deleted = 0
                    """,
                    (
                        provider_id_str,
                        mapping.provider_symbol,
                        mapping_id_str,
                    ),
                )
            rows = cursor.fetchall()

            for row in rows:
                if _half_open_intervals_overlap(
                    row["effective_from"],
                    row["effective_to"],
                    mapping.effective_from,
                    mapping.effective_to,
                ):
                    return CatalogueFailure(
                        request_id=request.request_id,
                        code="CATALOGUE_MAPPING_OVERLAP",
                        problem=ProblemDetails(
                            type="urn:error:catalogue:mapping-overlap",
                            title="Mapping Overlap",
                            status=409,
                            code="CATALOGUE_MAPPING_OVERLAP",
                            detail=(
                                f"Mapping interval overlaps with existing mapping "
                                f"{row['mapping_id']} for provider {provider_id_str} "
                                f"symbol '{mapping.provider_symbol}'"
                            ),
                            request_id=request.request_id,
                        ),
                        conflicting_refs=(mapping.mapping_id, Uuid7(row["mapping_id"])),
                    )

            conn.execute(
                """
                INSERT OR REPLACE INTO provider_symbol_mappings
                (mapping_id, instrument_id, instrument_version, provider_id,
                 provider_name, broker_id, broker_name, provider_symbol,
                 effective_from, effective_to, content_hash, raw_json, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    mapping_id_str,
                    str(mapping.instrument.instrument_id),
                    mapping.instrument_version,
                    provider_id_str,
                    mapping.provider.provider_name,
                    broker_id_str,
                    mapping.broker.broker_name if mapping.broker is not None else None,
                    mapping.provider_symbol,
                    mapping.effective_from,
                    mapping.effective_to,
                    mapping.content_hash,
                    json.dumps(mapping.model_dump(mode="json")),
                ),
            )
            conn.commit()

        if self._event_bus is not None:
            event = ProviderSymbolMappingChanged(
                mapping_id=mapping.mapping_id,
                instrument=mapping.instrument,
                instrument_version=mapping.instrument_version,
                provider=mapping.provider,
                broker=mapping.broker,
                provider_symbol=mapping.provider_symbol,
                content_hash=mapping.content_hash,
            )
            await self._event_bus.publish(event)

        return MapProvidersSuccess(
            request_id=request.request_id,
            mappings=(mapping,),
        )

    async def _handle_delete(
        self,
        request: MapProvidersRequest,
    ) -> MapProvidersSuccess | CatalogueFailure:
        """Handle DELETE operation for provider mappings.

        Args:
            request: Validated DELETE request.

        Returns:
            MapProvidersSuccess on success or CatalogueFailure if not found.

        Raises:
            ValueError: If mapping is None.
        """
        if request.mapping is None:
            msg = "mapping is required for DELETE"
            raise ValueError(msg)
        mapping = request.mapping
        mapping_id_str = str(mapping.mapping_id)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT raw_json, content_hash FROM provider_symbol_mappings
                WHERE mapping_id = ? AND is_deleted = 0
                """,
                (mapping_id_str,),
            )
            row = cursor.fetchone()
            if row is None:
                return CatalogueFailure(
                    request_id=request.request_id,
                    code="CATALOGUE_NOT_FOUND",
                    problem=ProblemDetails(
                        type="urn:error:catalogue:not-found",
                        title="Mapping Not Found",
                        status=404,
                        code="CATALOGUE_NOT_FOUND",
                        detail=f"Mapping {mapping_id_str} was not found",
                        request_id=request.request_id,
                    ),
                    conflicting_refs=(mapping.mapping_id,),
                )

            prior_content_hash = row["content_hash"]

            conn.execute(
                """
                UPDATE provider_symbol_mappings
                SET is_deleted = 1
                WHERE mapping_id = ?
                """,
                (mapping_id_str,),
            )
            conn.commit()

        if self._event_bus is not None:
            event = ProviderSymbolMappingDeleted(
                mapping_id=mapping.mapping_id,
                instrument=mapping.instrument,
                instrument_version=mapping.instrument_version,
                provider=mapping.provider,
                broker=mapping.broker,
                provider_symbol=mapping.provider_symbol,
                prior_content_hash=prior_content_hash,
            )
            await self._event_bus.publish(event)

        return MapProvidersSuccess(
            request_id=request.request_id,
            mappings=(),
            deleted=True,
        )


async def fr_cat_map_broker_symbols(
    service: ProviderMappingService,
    request: MapProvidersRequest,
) -> MapProvidersSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-MAP_BROKER_SYMBOLS.

    Args:
        service: Bound provider mapping service instance.
        request: Provider mapping request.

    Returns:
        Operation result or failure.
    """
    return await service.map_providers(request)


async def fr_cat_map_provider_identities(
    service: ProviderMappingService,
    request: MapProvidersRequest,
) -> MapProvidersSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-MAP_PROVIDER_IDENTITIES.

    Args:
        service: Bound provider mapping service instance.
        request: Provider mapping request.

    Returns:
        Operation result or failure.
    """
    return await service.map_providers(request)


async def main() -> None:
    """Executable usage demonstration for FEAT-CAT-MAP_PROVIDERS.

    Raises:
        TypeError: If scenario response type does not match expectations.
        ValueError: If returned error code does not match expectations.
    """
    service = ProviderMappingService()
    req_id = "00000000-0000-7000-8000-000000000001"
    snap_id = "00000000-0000-7000-8000-000000000002"
    inst_id = "00000000-0000-7000-8000-000000000010"
    prov_id = "00000000-0000-7000-8000-000000000030"
    broker_a_id = "00000000-0000-7000-8000-000000000040"
    broker_b_id = "00000000-0000-7000-8000-000000000041"
    mapping_a_id = "00000000-0000-7000-8000-000000000050"
    mapping_b_id = "00000000-0000-7000-8000-000000000051"

    print("=== SCENARIO: FR-CAT-MAP_BROKER_SYMBOLS ===")
    provider_ref = ProviderRef(provider_id=prov_id, provider_name="MetaTrader5")
    broker_a_ref = BrokerRef(broker_id=broker_a_id, broker_name="BrokerAlpha")
    broker_b_ref = BrokerRef(broker_id=broker_b_id, broker_name="BrokerBeta")
    inst_ref = InstrumentRef(instrument_id=inst_id)

    # Broker A maps canonical EURUSD to EURUSD.raw
    map_a = ProviderSymbolMapping(
        mapping_id=mapping_a_id,
        instrument=inst_ref,
        instrument_version=1,
        provider=provider_ref,
        broker=broker_a_ref,
        provider_symbol="EURUSD.raw",
        effective_from="2026-01-01T00:00:00.000000Z",
        content_hash="a" * 64,
    )
    upsert_a = MapProvidersRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT",
        mapping=map_a,
    )
    res_a = await fr_cat_map_broker_symbols(service, upsert_a)
    if not isinstance(res_a, MapProvidersSuccess):
        msg = f"Failed scenario 1A: {res_a}"
        raise TypeError(msg)
    print(
        f"Registered mapping for BrokerAlpha: {res_a.mappings[0].provider_symbol} "
        f"-> instrument {res_a.mappings[0].instrument.instrument_id}"
    )

    # Broker B maps same EURUSD to EURUSD_pro without conflict
    map_b = ProviderSymbolMapping(
        mapping_id=mapping_b_id,
        instrument=inst_ref,
        instrument_version=1,
        provider=provider_ref,
        broker=broker_b_ref,
        provider_symbol="EURUSD_pro",
        effective_from="2026-01-01T00:00:00.000000Z",
        content_hash="b" * 64,
    )
    upsert_b = MapProvidersRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT",
        mapping=map_b,
    )
    res_b = await fr_cat_map_broker_symbols(service, upsert_b)
    if not isinstance(res_b, MapProvidersSuccess):
        msg = f"Failed scenario 1B: {res_b}"
        raise TypeError(msg)
    print(
        f"Registered mapping for BrokerBeta: {res_b.mappings[0].provider_symbol} "
        f"-> instrument {res_b.mappings[0].instrument.instrument_id}"
    )

    print("\n=== SCENARIO: FR-CAT-MAP_PROVIDER_IDENTITIES ===")
    resolve_req = MapProvidersRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="RESOLVE",
        provider=provider_ref,
        broker=broker_a_ref,
        provider_symbol="EURUSD.raw",
        as_of="2026-06-01T00:00:00.000000Z",
    )
    resolve_res = await fr_cat_map_provider_identities(service, resolve_req)
    if not isinstance(resolve_res, MapProvidersSuccess):
        msg = f"Failed scenario 2 resolve: {resolve_res}"
        raise TypeError(msg)
    resolved_mapping = resolve_res.mappings[0]
    print(
        f"Resolved provider symbol 'EURUSD.raw' to instrument "
        f"{resolved_mapping.instrument.instrument_id} "
        f"v{resolved_mapping.instrument_version}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
