"""Run caller-owned source registration, policy, promotion, and broker-read examples."""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerAccountInfo,
    BrokerBalance,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerPage,
    BrokerPermissions,
)
from app.services.brokers.testing import FakeBrokerAdapter
from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    AccountSnapshotRequest,
    AccountStateSnapshot,
    MarketDataRequest,
    RawSourceBatch,
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
    SourcePromotionRequest,
    SourceReadRequest,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.sources import (
    MarketDataSource,
    evaluate_source_policy,
    get_account_state_snapshot,
    promote_source,
    register_source,
    resolve_source,
)
from app.services.data.sources.policy import SourcePolicyConfig, register_source_policy
from app.services.data.storage.migrations import run_data_migrations
from app.utils import AuthContext, generate_id, logger

_OBSERVED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_SOURCE_ID = "mt5"


class ExampleMarketDataSource(MarketDataSource):
    """Concrete read-only source used to illustrate a caller integration."""

    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Return one bounded provider-neutral historical batch."""
        logger.info("Reading historical bars from %s", request.source_id)
        return RawSourceBatch(
            source_id=request.source_id,
            provider_symbol=request.provider_symbol,
            data_kind=request.data_kind,
            records=(
                {
                    "timestamp": _OBSERVED_AT,
                    "open": "100.00",
                    "high": "101.00",
                    "low": "99.50",
                    "close": "100.50",
                    "volume": "500",
                },
            ),
            retrieved_at=_OBSERVED_AT + timedelta(seconds=1),
            revision="example-provider-v1",
            request_id=request.request_id,
        )

    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """Return a deterministic bounded provider symbol page."""
        logger.info("Listing symbols from %s", request.source_id)
        items = tuple(
            symbol
            for symbol in ("AAPL", "MSFT")
            if request.query is None or request.query.casefold() in symbol.casefold()
        )[: request.limit]
        return SymbolPage(
            source_id=request.source_id,
            items=items,
            limit=request.limit,
            revision="example-provider-v1",
            request_id=request.request_id,
        )

    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Return normalized metadata and declare unknown optional fields."""
        logger.info("Reading symbol metadata for %s", request.symbol)
        return SymbolMetadata(
            canonical_symbol=request.symbol,
            provider_symbol=request.symbol,
            asset_class="equity",
            base_currency="USD",
            quote_currency=None,
            digits=2,
            price_step=Decimal("0.01"),
            quantity_step=Decimal(1),
            timezone="America/New_York",
            source_id=request.source_id,
            revision="example-provider-v1",
            retrieved_at=_OBSERVED_AT,
            missing_fields=("quote_currency",),
            request_id=request.request_id,
        )


def _header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def _configure_environment(root: Path) -> None:
    """Configure isolated durable source-policy state."""
    logger.info("Configuring isolated source-policy state under %s", root)
    run_data_migrations(generate_id("req"))


def _source_descriptor() -> SourceDescriptor:
    """Build the source declaration shared by registration examples."""
    logger.info("Building an explicit source descriptor")
    return SourceDescriptor(
        source_id=_SOURCE_ID,
        readiness="staging",
        capabilities=("bars", "symbol_discovery", "symbol_metadata"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="America/New_York",
        revision="example-provider-v1",
        license_policy=SourceLicensePolicy(
            source_id=_SOURCE_ID,
            status="approved",
            permitted_workflows=("research", "validation"),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("bounded-read", "metadata-review"),
    )


def _register_example_source() -> None:
    """Register one lazy source, its identity map, and bounded policy."""
    logger.info("Registering the example read-only source")
    identity = SourceIdentity(
        source_id=_SOURCE_ID,
        canonical_symbol="EURUSD",
        friendly_name="EURUSD",
        provider_symbol="EURUSD",
        mapping_revision="mapping-v1",
        provenance={"catalog": "usage-v1"},
        request_id=generate_id("req"),
    )
    register_source(
        _source_descriptor(),
        ExampleMarketDataSource,
        identities=(identity,),
    )
    register_source_policy(
        SourcePolicyConfig(
            source_id=_SOURCE_ID,
            rate_limit=60,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=30,
        )
    )


def example_fr_data_022_bounded_fetch() -> RawSourceBatch:
    """Fetch a bounded historical batch through the source protocol."""
    _header("FR-DATA-022: fetching through a registered source")
    source = resolve_source(_SOURCE_ID)
    batch = source.fetch(
        SourceReadRequest(
            source_id=_SOURCE_ID,
            provider_symbol="AAPL",
            data_kind="bars",
            timeframe="D1",
            start=_OBSERVED_AT - timedelta(days=1),
            end=_OBSERVED_AT,
            limit=10,
            request_id=generate_id("req"),
        )
    )
    print(f"Fetched {len(batch.records)} raw records at revision {batch.revision}")
    return batch


def example_fr_data_023_symbol_discovery() -> SymbolPage:
    """Page provider symbols deterministically through the source protocol."""
    _header("FR-DATA-023: listing a bounded source symbol page")
    page = resolve_source(_SOURCE_ID).list_symbols(
        SymbolListRequest(
            source_id=_SOURCE_ID,
            query="A",
            limit=10,
            request_id=generate_id("req"),
        )
    )
    print(f"Discovered symbols={page.items}")
    return page


def example_fr_data_024_symbol_metadata() -> SymbolMetadata:
    """Read normalized symbol metadata with explicit missingness."""
    _header("FR-DATA-024: reading normalized symbol metadata")
    metadata = resolve_source(_SOURCE_ID).get_symbol_metadata(
        SymbolMetadataRequest(
            source_id=_SOURCE_ID,
            symbol="AAPL",
            request_id=generate_id("req"),
        )
    )
    print(f"Metadata timezone={metadata.timezone} missing={metadata.missing_fields}")
    return metadata


def example_fr_data_025_lazy_registration() -> MarketDataSource:
    """Resolve the lazily registered source without import-time I/O."""
    _header("FR-DATA-025: resolving a lazily registered source")
    source = resolve_source(_SOURCE_ID)
    print(f"Resolved source type={type(source).__name__}")
    return source


def example_fr_data_026_source_policy() -> None:
    """Evaluate caller-selected source order against explicit policy."""
    _header("FR-DATA-026: evaluating source readiness and license policy")
    plan = evaluate_source_policy(
        MarketDataRequest(
            source_id=_SOURCE_ID,
            symbol="AAPL",
            data_kind="bars",
            timeframe="D1",
            start=_OBSERVED_AT - timedelta(days=5),
            end=_OBSERVED_AT,
            limit=10,
            use_cache=False,
            quality_failure_behavior="fail",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    print(f"Approved source order={plan.ordered_sources}")


def example_fr_data_027_source_promotion() -> SourceDescriptor:
    """Promote source readiness only with authorization and complete evidence."""
    _header("FR-DATA-027: promoting a source with complete evidence")
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="data-owner",
        principal_type="USER",
        roles=("admin",),
        permissions=(),
        scopes=("data:source:promote",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_OBSERVED_AT,
    )
    promoted = promote_source(
        SourcePromotionRequest(
            source_id=_SOURCE_ID,
            target_readiness="production",
            evidence=("bounded-read", "metadata-review"),
            request_id=generate_id("req"),
        ),
        auth,
    )
    print(f"Promoted source readiness={promoted.readiness}")
    return promoted


def _broker_capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Declare read-only fake-adapter capabilities for boundary demonstration."""
    logger.info("Declaring read-only broker capabilities")
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="FAKE",
        )
        for operation in BrokerCapabilityId
    }


def example_fr_data_028_read_only_account_snapshot() -> AccountStateSnapshot:
    """Normalize caller-owned broker account reads into a schema-enforced snapshot."""
    _header("FR-DATA-028: normalizing caller-owned broker account reads")
    config = BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    fixtures: dict[BrokerCapabilityId, object] = {
        BrokerCapabilityId.GET_ACCOUNT_INFO: BrokerAccountInfo(
            account_id="demo-account",
            retrieved_at=_OBSERVED_AT,
            currency="USD",
            balance=Decimal(10000),
            equity=Decimal(10025),
            margin=Decimal(200),
            free_margin=Decimal(9825),
            status="ACTIVE",
        ),
        BrokerCapabilityId.GET_BALANCES: (
            BrokerBalance(
                asset="USD",
                unit="CURRENCY",
                retrieved_at=_OBSERVED_AT,
                total=Decimal(10000),
                available=Decimal(9800),
                locked=Decimal(200),
            ),
        ),
        BrokerCapabilityId.GET_POSITIONS: BrokerPage(items=(), limit=10),
        BrokerCapabilityId.GET_ORDERS: BrokerPage(items=(), limit=10),
        BrokerCapabilityId.GET_PERMISSIONS: BrokerPermissions(
            observed_at=_OBSERVED_AT,
            trade_write=False,
            market_data_read=True,
            account_read=True,
        ),
        BrokerCapabilityId.IS_CONNECTED: True,
    }
    adapter = FakeBrokerAdapter(config, _broker_capabilities(), fixtures=fixtures)
    asyncio.run(adapter.connect())

    class FixedClock:
        """Provide deterministic current UTC time for freshness validation."""

        def now(self) -> datetime:
            """Return the fixed observation time."""
            logger.info("Reading the fixed usage-example clock")
            return _OBSERVED_AT

    snapshot = get_account_state_snapshot(
        AccountSnapshotRequest(
            source_id="caller-owned-broker",
            account_id="demo-account",
            max_age_seconds=30,
            request_id=generate_id("req"),
        ),
        adapter,
        clock=FixedClock(),
    )
    print(
        f"Account={snapshot.account_id} connected={snapshot.connected} trading_allowed={snapshot.trading_allowed}"
    )
    return snapshot


if __name__ == "__main__":
    with TemporaryDirectory(prefix="haru-data-sources-") as directory:
        demo_root = Path(directory)
        settings = DataSettings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=demo_root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            _configure_environment(demo_root)
            _register_example_source()
            example_fr_data_022_bounded_fetch()
            example_fr_data_023_symbol_discovery()
            example_fr_data_024_symbol_metadata()
            example_fr_data_025_lazy_registration()
            example_fr_data_026_source_policy()
            example_fr_data_027_source_promotion()
            example_fr_data_028_read_only_account_snapshot()
