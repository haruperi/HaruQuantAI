"""Instrument Catalogue domain logic and capability implementation.

Purpose:
    Define, version, query, and protect canonical trading instruments, order
    constraints, and tick/lot specifications across financial asset classes.

Key capabilities:
    * Define canonical instruments with asset class, base/quote currencies, and
      tick sizing.
    * Maintain immutable, time-bounded instrument versions with effective
      intervals.
    * Enforce order constraints including min/max quantities, steps, and
      supported order types.
    * Protect referenced instrument versions against deletion or mutating
      removal.
    * Publish typed domain events upon instrument version creation and deletion.
    * Provide async catalog_instruments implementing
      CatalogInstrumentsCapability.

Python API usage:
    from app.services.catalogue.instrument_catalogue.instrument_catalogue import (
        InstrumentCatalogueService,
    )
    from app.contracts.catalogue.models import (
        CatalogInstrumentsRequest,
        InstrumentRef,
    )

    service = InstrumentCatalogueService()
    result = await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id="018f0000-0000-7000-8000-000000000001",
            capability_snapshot_id="018f0000-0000-7000-8000-000000000002",
            operation="GET",
            instrument_ref=InstrumentRef(
                instrument_id="018f0000-0000-7000-8000-000000000003"
            ),
        )
    )

CLI usage:
    uv run python -m \
        app.services.catalogue.instrument_catalogue.instrument_catalogue
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
from typing import TYPE_CHECKING, override

from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    InstrumentVersionCreated,
    InstrumentVersionDeleted,
)
from app.contracts.catalogue.models import (
    CatalogInstrumentsRequest,
    CatalogInstrumentsSuccess,
    InstrumentRef,
    InstrumentVersion,
    OrderConstraints,
)
from app.contracts.catalogue.ports import CatalogInstrumentsCapability
from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
)
from app.services.catalogue.instrument_catalogue.config import (
    InstrumentCatalogueConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus


class InstrumentCatalogueService(CatalogInstrumentsCapability):
    """Manage, version, retain, and protect canonical instruments."""

    def __init__(
        self,
        config: InstrumentCatalogueConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the instrument catalogue service with configuration.

        Args:
            config: Optional configuration dataclass.
            event_bus: Optional kernel event bus for domain event publishing.
        """
        self._config = config or InstrumentCatalogueConfig()
        self._event_bus = event_bus
        self._mem_uri: str | None = None
        if self._config.database_path is not None:
            self._conn = sqlite3.connect(
                str(self._config.database_path), check_same_thread=False
            )
        else:
            self._mem_uri = f"file:mem_{id(self)}?mode=memory&cache=shared"
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
                CREATE TABLE IF NOT EXISTS instruments (
                    instrument_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    latest_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS instrument_versions (
                    instrument_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    raw_json TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_to TEXT,
                    content_hash TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (instrument_id, version),
                    FOREIGN KEY (instrument_id) REFERENCES instruments (instrument_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS manifest_references (
                    reference_id TEXT PRIMARY KEY,
                    instrument_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    manifest_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record_manifest_reference(
        self,
        instrument_id: Uuid7,
        version: int,
        manifest_id: str,
        reference_id: str | None = None,
    ) -> None:
        """Record a committed manifest reference protecting an instrument version.

        Args:
            instrument_id: UUIDv7 identity of the referenced instrument.
            version: Version number referenced by the manifest.
            manifest_id: Identifier of the committed manifest.
            reference_id: Optional explicit reference UUID string.
        """
        ref_id = reference_id or str(instrument_id) + ":" + str(version)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO manifest_references
                (reference_id, instrument_id, version, manifest_id, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (ref_id, str(instrument_id), version, manifest_id),
            )
            conn.commit()

    def is_version_referenced(self, instrument_id: Uuid7, version: int) -> bool:
        """Check whether an instrument version is referenced by a manifest.

        Args:
            instrument_id: UUIDv7 identity of the instrument.
            version: Version number to check.

        Returns:
            True if referenced by at least one committed manifest, False otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM manifest_references
                WHERE instrument_id = ? AND version = ?
                """,
                (str(instrument_id), version),
            )
            row = cursor.fetchone()
            count = int(row[0]) if row is not None else 0
            return count > 0

    @override
    async def catalog_instruments(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Manage and query versioned canonical instruments.

        Args:
            request: Operation-discriminated instrument catalogue request.

        Returns:
            The matching instrument versions, page cursor, or deletion flag
            on success, otherwise a structured catalogue failure.
        """
        match request.operation:
            case "GET":
                return self._handle_get(request)
            case "LIST":
                return self._handle_list(request)
            case "UPSERT_VERSION":
                return await self._handle_upsert(request)
            case "DELETE_VERSION":
                return await self._handle_delete(request)

    def _handle_get(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Handle GET operation for instrument catalogue.

        Args:
            request: Validated GET request with instrument_ref.

        Returns:
            CatalogInstrumentsSuccess on success, or CatalogueFailure if not found.

        Raises:
            ValueError: If instrument_ref is None.
        """
        if request.instrument_ref is None:
            msg = "instrument_ref is required for GET"
            raise ValueError(msg)
        instrument_id_str = str(request.instrument_ref.instrument_id)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT raw_json FROM instrument_versions
                WHERE instrument_id = ? AND is_deleted = 0
                ORDER BY version DESC LIMIT 1
                """,
                (instrument_id_str,),
            )
            row = cursor.fetchone()
            if row is None:
                return CatalogueFailure(
                    request_id=request.request_id,
                    code="CATALOGUE_NOT_FOUND",
                    problem=ProblemDetails(
                        type="urn:error:catalogue:not-found",
                        title="Instrument Not Found",
                        status=404,
                        code="CATALOGUE_NOT_FOUND",
                        detail=f"Instrument {instrument_id_str} was not found",
                        request_id=request.request_id,
                    ),
                    conflicting_refs=(request.instrument_ref.instrument_id,),
                )
            version_data = json.loads(row["raw_json"])
            instrument = InstrumentVersion.model_validate(version_data)
            return CatalogInstrumentsSuccess(
                request_id=request.request_id,
                instruments=(instrument,),
            )

    def _handle_list(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess:
        """Handle LIST operation for instrument catalogue.

        Args:
            request: Validated LIST request with pagination options.

        Returns:
            CatalogInstrumentsSuccess containing latest active instrument versions.
        """
        limit = request.page_size
        cursor = request.page_cursor

        with self._get_connection() as conn:
            query = """
                SELECT v.raw_json, i.instrument_id
                FROM instruments i
                JOIN instrument_versions v
                  ON i.instrument_id = v.instrument_id
                 AND i.latest_version = v.version
                WHERE v.is_deleted = 0
            """
            params: list[object] = []
            if cursor:
                query += " AND i.instrument_id > ?"
                params.append(cursor)

            query += " ORDER BY i.instrument_id ASC LIMIT ?"
            params.append(limit + 1)

            rows = conn.execute(query, params).fetchall()

            instruments: list[InstrumentVersion] = []
            next_cursor: str | None = None

            if len(rows) > limit:
                next_cursor = str(rows[limit - 1]["instrument_id"])
                rows = rows[:limit]

            for row in rows:
                version_data = json.loads(row["raw_json"])
                instruments.append(InstrumentVersion.model_validate(version_data))

            return CatalogInstrumentsSuccess(
                request_id=request.request_id,
                instruments=tuple(instruments),
                next_cursor=next_cursor,
            )

    async def _handle_upsert(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Handle UPSERT_VERSION operation for instrument catalogue.

        Args:
            request: Validated UPSERT_VERSION request.

        Returns:
            CatalogInstrumentsSuccess on success, or CatalogueFailure on conflict.

        Raises:
            ValueError: If instrument_version is None.
        """
        if request.instrument_version is None:
            msg = "instrument_version is required for UPSERT_VERSION"
            raise ValueError(msg)
        version = request.instrument_version
        instrument_id_str = str(version.instrument_id)

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT latest_version FROM instruments WHERE instrument_id = ?",
                (instrument_id_str,),
            )
            row = cursor.fetchone()

            if row is None:
                failure = self._insert_initial_version(
                    conn, request, version, instrument_id_str
                )
            else:
                failure = self._insert_subsequent_version(
                    conn,
                    request,
                    version,
                    instrument_id_str,
                    int(row["latest_version"]),
                )

            if failure is not None:
                return failure

        if self._event_bus is not None:
            event = InstrumentVersionCreated(
                instrument=InstrumentRef(instrument_id=version.instrument_id),
                instrument_version=version.version,
                content_hash=version.content_hash,
            )
            await self._event_bus.publish(event)

        return CatalogInstrumentsSuccess(
            request_id=request.request_id,
            instruments=(version,),
        )

    def _insert_initial_version(
        self,
        conn: sqlite3.Connection,
        request: CatalogInstrumentsRequest,
        version: InstrumentVersion,
        instrument_id_str: str,
    ) -> CatalogueFailure | None:
        """Insert initial version 1 of a new instrument.

        Args:
            conn: Active SQLite connection.
            request: Validated catalogue request.
            version: InstrumentVersion to insert.
            instrument_id_str: String representation of instrument UUID.

        Returns:
            CatalogueFailure on version conflict, or None on success.
        """
        if request.expected_version is not None and request.expected_version != 1:
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:catalogue:version-conflict",
                    title="Version Conflict",
                    status=409,
                    code="CATALOGUE_VERSION_CONFLICT",
                    detail=(
                        f"Expected version {request.expected_version} "
                        "for new instrument"
                    ),
                    request_id=request.request_id,
                ),
                conflicting_refs=(version.instrument_id,),
            )
        if version.version != 1:
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:catalogue:version-conflict",
                    title="Version Conflict",
                    status=409,
                    code="CATALOGUE_VERSION_CONFLICT",
                    detail=f"Initial version must be 1, got {version.version}",
                    request_id=request.request_id,
                ),
                conflicting_refs=(version.instrument_id,),
            )

        conn.execute(
            """
            INSERT INTO instruments
            (instrument_id, symbol, latest_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                instrument_id_str,
                version.symbol,
                version.version,
                version.effective_from,
                version.effective_from,
            ),
        )
        conn.execute(
            """
            INSERT INTO instrument_versions
            (instrument_id, version, raw_json, effective_from, effective_to,
             content_hash, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                instrument_id_str,
                version.version,
                json.dumps(version.model_dump(mode="json")),
                version.effective_from,
                version.effective_to,
                version.content_hash,
            ),
        )
        conn.commit()
        return None

    def _insert_subsequent_version(
        self,
        conn: sqlite3.Connection,
        request: CatalogInstrumentsRequest,
        version: InstrumentVersion,
        instrument_id_str: str,
        latest_version: int,
    ) -> CatalogueFailure | None:
        """Insert subsequent version for an existing instrument.

        Args:
            conn: Active SQLite connection.
            request: Validated catalogue request.
            version: InstrumentVersion to append.
            instrument_id_str: String representation of instrument UUID.
            latest_version: Current latest version in storage.

        Returns:
            CatalogueFailure on conflict, or None on success.
        """
        if (
            request.expected_version is not None
            and request.expected_version != latest_version
        ):
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:catalogue:version-conflict",
                    title="Version Conflict",
                    status=409,
                    code="CATALOGUE_VERSION_CONFLICT",
                    detail=(
                        f"Expected version {request.expected_version} "
                        f"but latest version is {latest_version}"
                    ),
                    request_id=request.request_id,
                ),
                conflicting_refs=(version.instrument_id,),
            )

        # Check existing version
        cursor = conn.execute(
            """
            SELECT raw_json, content_hash FROM instrument_versions
            WHERE instrument_id = ? AND version = ?
            """,
            (instrument_id_str, version.version),
        )
        existing_ver = cursor.fetchone()
        if existing_ver is not None:
            if existing_ver["content_hash"] == version.content_hash:
                return None
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:catalogue:version-conflict",
                    title="Version Conflict",
                    status=409,
                    code="CATALOGUE_VERSION_CONFLICT",
                    detail=(f"Version {version.version} exists with different hash"),
                    request_id=request.request_id,
                ),
                conflicting_refs=(version.instrument_id,),
            )

        if version.version != latest_version + 1:
            return CatalogueFailure(
                request_id=request.request_id,
                code="CATALOGUE_VERSION_CONFLICT",
                problem=ProblemDetails(
                    type="urn:error:catalogue:version-conflict",
                    title="Version Conflict",
                    status=409,
                    code="CATALOGUE_VERSION_CONFLICT",
                    detail=(
                        f"Next version must be {latest_version + 1}, "
                        f"got {version.version}"
                    ),
                    request_id=request.request_id,
                ),
                conflicting_refs=(version.instrument_id,),
            )

        # Close open effective interval on previous version
        prior_cursor = conn.execute(
            """
            SELECT raw_json FROM instrument_versions
            WHERE instrument_id = ? AND version = ?
            """,
            (instrument_id_str, latest_version),
        )
        prior_row = prior_cursor.fetchone()
        if prior_row is not None:
            prior_data = json.loads(prior_row["raw_json"])
            if prior_data.get("effective_to") is None:
                prior_data["effective_to"] = version.effective_from
                conn.execute(
                    """
                    UPDATE instrument_versions
                    SET effective_to = ?, raw_json = ?
                    WHERE instrument_id = ? AND version = ?
                    """,
                    (
                        version.effective_from,
                        json.dumps(prior_data),
                        instrument_id_str,
                        latest_version,
                    ),
                )

        conn.execute(
            """
            INSERT INTO instrument_versions
            (instrument_id, version, raw_json, effective_from, effective_to,
             content_hash, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                instrument_id_str,
                version.version,
                json.dumps(version.model_dump(mode="json")),
                version.effective_from,
                version.effective_to,
                version.content_hash,
            ),
        )
        conn.execute(
            """
            UPDATE instruments
            SET latest_version = ?, symbol = ?, updated_at = ?
            WHERE instrument_id = ?
            """,
            (
                version.version,
                version.symbol,
                version.effective_from,
                instrument_id_str,
            ),
        )
        conn.commit()
        return None

    async def _handle_delete(
        self,
        request: CatalogInstrumentsRequest,
    ) -> CatalogInstrumentsSuccess | CatalogueFailure:
        """Handle DELETE_VERSION operation for instrument catalogue.

        Args:
            request: Validated DELETE_VERSION request with ref and expected_version.

        Returns:
            CatalogInstrumentsSuccess on success, or CatalogueFailure on conflict.

        Raises:
            ValueError: If instrument_ref or expected_version is None.
        """
        if request.instrument_ref is None:
            msg = "instrument_ref is required for DELETE_VERSION"
            raise ValueError(msg)
        if request.expected_version is None:
            msg = "expected_version is required for DELETE_VERSION"
            raise ValueError(msg)
        instrument_id_str = str(request.instrument_ref.instrument_id)
        expected_version = request.expected_version

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT raw_json, content_hash FROM instrument_versions
                WHERE instrument_id = ? AND version = ? AND is_deleted = 0
                """,
                (instrument_id_str, expected_version),
            )
            row = cursor.fetchone()
            if row is None:
                return CatalogueFailure(
                    request_id=request.request_id,
                    code="CATALOGUE_NOT_FOUND",
                    problem=ProblemDetails(
                        type="urn:error:catalogue:not-found",
                        title="Instrument Version Not Found",
                        status=404,
                        code="CATALOGUE_NOT_FOUND",
                        detail=(
                            f"Instrument {instrument_id_str} version "
                            f"{expected_version} not found"
                        ),
                        request_id=request.request_id,
                    ),
                    conflicting_refs=(request.instrument_ref.instrument_id,),
                )

            # Check if protected by a committed manifest reference
            if self.is_version_referenced(
                request.instrument_ref.instrument_id, expected_version
            ):
                return CatalogueFailure(
                    request_id=request.request_id,
                    code="CATALOGUE_REFERENCE_PROTECTED",
                    problem=ProblemDetails(
                        type="urn:error:catalogue:reference-protected",
                        title="Reference Protected",
                        status=409,
                        code="CATALOGUE_REFERENCE_PROTECTED",
                        detail=(
                            f"Cannot delete instrument {instrument_id_str} version "
                            f"{expected_version}: referenced by committed manifest"
                        ),
                        request_id=request.request_id,
                    ),
                    conflicting_refs=(request.instrument_ref.instrument_id,),
                )

            prior_content_hash = row["content_hash"]

            conn.execute(
                """
                UPDATE instrument_versions
                SET is_deleted = 1
                WHERE instrument_id = ? AND version = ?
                """,
                (instrument_id_str, expected_version),
            )
            conn.commit()

        if self._event_bus is not None:
            event = InstrumentVersionDeleted(
                instrument=InstrumentRef(
                    instrument_id=request.instrument_ref.instrument_id
                ),
                instrument_version=expected_version,
                prior_content_hash=prior_content_hash,
            )
            await self._event_bus.publish(event)

        return CatalogInstrumentsSuccess(
            request_id=request.request_id,
            instruments=(),
            deleted=True,
        )


async def fr_cat_define_instruments(
    service: InstrumentCatalogueService,
    request: CatalogInstrumentsRequest,
) -> CatalogInstrumentsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-DEFINE_INSTRUMENTS.

    Args:
        service: Bound instrument catalogue service instance.
        request: Instrument catalogue request.

    Returns:
        Operation result or failure.
    """
    return await service.catalog_instruments(request)


async def fr_cat_version_instruments(
    service: InstrumentCatalogueService,
    request: CatalogInstrumentsRequest,
) -> CatalogInstrumentsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-VERSION_INSTRUMENTS.

    Args:
        service: Bound instrument catalogue service instance.
        request: Instrument catalogue request.

    Returns:
        Operation result or failure.
    """
    return await service.catalog_instruments(request)


async def fr_cat_protect_referenced_versions(
    service: InstrumentCatalogueService,
    request: CatalogInstrumentsRequest,
) -> CatalogInstrumentsSuccess | CatalogueFailure:
    """Requirement implementation trace for FR-CAT-PROTECT_REFERENCED_VERSIONS.

    Args:
        service: Bound instrument catalogue service instance.
        request: Instrument catalogue request.

    Returns:
        Operation result or failure.
    """
    return await service.catalog_instruments(request)


async def main() -> None:
    """Executable usage demonstration for FEAT-CAT-CATALOG_INSTRUMENTS.

    Raises:
        TypeError: If scenario response type does not match expectations.
        ValueError: If returned error code does not match expectations.
    """
    service = InstrumentCatalogueService()
    req_id = "00000000-0000-7000-8000-000000000001"
    snap_id = "00000000-0000-7000-8000-000000000002"
    inst_id = "00000000-0000-7000-8000-000000000010"
    session_id = "00000000-0000-7000-8000-000000000020"

    print("=== SCENARIO: FR-CAT-DEFINE_INSTRUMENTS ===")
    v1 = InstrumentVersion(
        instrument_id=inst_id,
        version=1,
        symbol="EURUSD",
        display_name="Euro / US Dollar",
        asset_class="FOREX",
        base_currency="EUR",
        quote_currency="USD",
        settlement_currency="USD",
        point_value="100000",
        tick_size="0.00001",
        price_decimals=5,
        quantity_multiplier="1",
        order_constraints=OrderConstraints(
            min_quantity="0.01",
            max_quantity="100",
            quantity_step="0.01",
            min_order_distance="0.00005",
            supported_order_types=("MARKET", "LIMIT"),
            supported_time_in_force=("GTC", "IOC"),
        ),
        default_spread="0.00012",
        exchange="IDEALPRO",
        timezone="America/New_York",
        session_id=session_id,
        effective_from="2026-01-01T00:00:00.000000Z",
        content_hash="a" * 64,
    )
    upsert_req = CatalogInstrumentsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT_VERSION",
        instrument_version=v1,
    )
    res1 = await fr_cat_define_instruments(service, upsert_req)
    if not isinstance(res1, CatalogInstrumentsSuccess):
        msg = f"Failed scenario 1: {res1}"
        raise TypeError(msg)
    print(
        f"Created instrument version 1: {res1.instruments[0].symbol} "
        f"v{res1.instruments[0].version}"
    )

    get_req = CatalogInstrumentsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="GET",
        instrument_ref=InstrumentRef(instrument_id=inst_id),
    )
    res_get = await fr_cat_define_instruments(service, get_req)
    if not isinstance(res_get, CatalogInstrumentsSuccess):
        msg = f"Failed get: {res_get}"
        raise TypeError(msg)
    print(
        f"Retrieved instrument: {res_get.instruments[0].symbol} "
        f"with decimals={res_get.instruments[0].price_decimals}"
    )

    print("\n=== SCENARIO: FR-CAT-VERSION_INSTRUMENTS ===")
    v2 = InstrumentVersion(
        instrument_id=inst_id,
        version=2,
        symbol="EURUSD",
        display_name="Euro / US Dollar (Tight Spread)",
        asset_class="FOREX",
        base_currency="EUR",
        quote_currency="USD",
        settlement_currency="USD",
        point_value="100000",
        tick_size="0.00001",
        price_decimals=5,
        quantity_multiplier="1",
        order_constraints=OrderConstraints(
            min_quantity="0.01",
            max_quantity="100",
            quantity_step="0.01",
            min_order_distance="0.00005",
            supported_order_types=("MARKET", "LIMIT"),
            supported_time_in_force=("GTC", "IOC"),
        ),
        default_spread="0.00008",
        exchange="IDEALPRO",
        timezone="America/New_York",
        session_id=session_id,
        effective_from="2026-06-01T00:00:00.000000Z",
        content_hash="b" * 64,
    )
    upsert_req2 = CatalogInstrumentsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="UPSERT_VERSION",
        instrument_version=v2,
        expected_version=1,
    )
    res2 = await fr_cat_version_instruments(service, upsert_req2)
    if not isinstance(res2, CatalogInstrumentsSuccess):
        msg = f"Failed scenario 2: {res2}"
        raise TypeError(msg)
    print(f"Created instrument version 2: {res2.instruments[0].display_name}")

    print("\n=== SCENARIO: FR-CAT-PROTECT_REFERENCED_VERSIONS ===")
    service.record_manifest_reference(
        instrument_id=inst_id,
        version=2,
        manifest_id="manifest-run-20260828-001",
    )
    del_req = CatalogInstrumentsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="DELETE_VERSION",
        instrument_ref=InstrumentRef(instrument_id=inst_id),
        expected_version=2,
    )
    del_res = await fr_cat_protect_referenced_versions(service, del_req)
    if not isinstance(del_res, CatalogueFailure):
        msg = f"Failed scenario 3: expected failure, got {del_res}"
        raise TypeError(msg)
    if del_res.code != "CATALOGUE_REFERENCE_PROTECTED":
        msg = (
            "Failed scenario 3: expected CATALOGUE_REFERENCE_PROTECTED, "
            f"got {del_res.code}"
        )
        raise ValueError(msg)
    print(
        f"Protected version deletion rejected with: {del_res.code} - "
        f"{del_res.problem.detail}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
