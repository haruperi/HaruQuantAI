"""Run source composition and local artifact access examples (FEAT-DATA-10)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from _research_sources_support import main as run_research_source_support
from app.contracts.common.models import create_auth_context
from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_source_promotion_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    close_data_provider_sessions,
    data_settings_context,
    discover_symbols,
    ensure_source,
    evaluate_source_policy,
    fetch_symbol_metadata,
    get_market_data,
    get_source_descriptor,
    list_composable_sources,
    list_registered_sources,
    promote_source,
    verify_read_only_call,
    wrap_broker_client,
)

_SYMBOL = "EURUSD"
_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj.keys()))
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_010_025_101_102() -> None:
    """FR-DATA-010, FR-DATA-025, FR-DATA-101, FR-DATA-102: Stage 1 — Compose, list, and register configured sources at defined readiness without network/credential requirements."""
    _header(
        "Stage 1: Source Discovery & Registration - Source Governance (FR-DATA-010, FR-DATA-025, FR-DATA-101, FR-DATA-102)"
    )
    res_composable = list_composable_sources()
    print(_format_result(res_composable))

    res_registered = list_registered_sources()
    print(_format_result(res_registered))

    req_id = generate_id("req")
    ensure_source("csv", req_id)
    descriptor_res = get_source_descriptor("csv")
    print(_format_result(descriptor_res))
    if descriptor_res.status == "success" and descriptor_res.data is not None:
        desc = descriptor_res.data
        print(
            f"Data -> SourceDescriptor(source_id={desc.source_id}, readiness={desc.readiness})"
        )


def fr_data_011_113_114() -> None:
    """FR-DATA-011, FR-DATA-113, FR-DATA-114: Stage 2 — Enforce source license policy, workflow context, and attribution restrictions."""
    _header(
        "Stage 2: Source Descriptor & License Governance - Source License (FR-DATA-011, FR-DATA-113, FR-DATA-114)"
    )
    desc_res = get_source_descriptor("csv")
    print(_format_result(desc_res))
    if desc_res.status == "success" and desc_res.data is not None:
        license_policy = desc_res.data.license_policy
        print(
            f"Data -> SourceLicensePolicy(status={license_policy.status}, export_allowed={license_policy.export_allowed})"
        )


def fr_data_022_023_024_103_104() -> None:
    """FR-DATA-022, FR-DATA-023, FR-DATA-024, FR-DATA-103, FR-DATA-104: Stage 3 — Bounded adapter reads, symbol discovery, and timeframe-scoped local artifact resolution."""
    _header(
        "Stage 3: Bounded Adapter Read & Symbol Resolution - Local Artifact Read (FR-DATA-022, FR-DATA-023, FR-DATA-024, FR-DATA-103, FR-DATA-104)"
    )
    sym_req = build_symbol_list_request(
        source_id="csv",
        limit=10,
        request_id=generate_id("req"),
    )
    symbols_res = discover_symbols(sym_req)
    print(_format_result(symbols_res))

    meta_req = build_symbol_metadata_request(
        source_id="csv",
        symbol=_SYMBOL,
        request_id=generate_id("req"),
    )
    meta_res = fetch_symbol_metadata(meta_req)
    print(_format_result(meta_res))

    market_res = get_market_data(
        source_id="csv",
        symbol=_SYMBOL,
        timeframe="M1",
        start=_START,
        end=_END,
        limit=2,
        request_id=generate_id("req"),
    )
    print(_format_result(market_res))
    if market_res.status == "success" and market_res.data is not None:
        ds = market_res.data
        print(f"Data -> MarketDataset(symbol={ds.symbol}, count={ds.record_count})")


def fr_data_026_027() -> None:
    """FR-DATA-026, FR-DATA-027: Stage 4 — Evaluate fallback source order against capability, readiness, and authenticated promotion criteria."""
    _header(
        "Stage 4: Source Policy Resolution & Promotion Governance - Policy & Promotion (FR-DATA-026, FR-DATA-027)"
    )
    m_req = build_market_data_request(
        source_id="csv",
        symbol=_SYMBOL,
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=2,
        use_cache=False,
        quality_failure_behavior="reject",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    eval_res = evaluate_source_policy(m_req)
    print(_format_result(eval_res))

    auth = create_auth_context(
        principal_id="operator",
        principal_type="USER",
        roles=("admin",),
        permissions=("data:write",),
        scopes=("system",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )
    prom_req = build_source_promotion_request(
        source_id="csv",
        target_readiness="production",
        evidence=("Verified local storage",),
        request_id=generate_id("req"),
    )
    prom_res = promote_source(prom_req, auth)
    print(_format_result(prom_res))


def fr_data_115_116() -> None:
    """FR-DATA-115, FR-DATA-116: Stage 5 — Wrap broker client proxy to enforce read-only contract on attribute access at runtime."""
    _header(
        "Stage 5: Read-Only Broker Surface Enforcement - Broker Proxy (FR-DATA-115, FR-DATA-116)"
    )

    class _DummyClient:
        def get_account(self) -> dict[str, str]:
            return {"account_id": "demo-1"}

        def place_order(self) -> str:
            return "order-placed"

    client = _DummyClient()
    proxy_res = wrap_broker_client(client)
    print(_format_result(proxy_res))

    read_check = verify_read_only_call("get_account")
    print(_format_result(read_check))


def fr_data_159() -> None:
    """FR-DATA-159: Stage 6 — Close composed provider-session resources."""
    _header("Stage 6: Provider Session Shutdown (FR-DATA-159)")
    result = close_data_provider_sessions(generate_id("req"))
    print(_format_result(result))
    if result.status != "success":
        raise RuntimeError("provider-session shutdown failed")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        raw_root = root / "data" / "raw"
        raw_root.mkdir(parents=True)
        settings = build_data_settings(
            database_url="sqlite:///data.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            data_local_sources=("csv",),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            print("=" * 80)
            print("FEATURE: FEAT-DATA-10 - Data Source Governance")
            print(
                "PURPOSE: Compose, govern, discover, and read data sources with strict license, readiness, and proxy enforcement"
            )
            print(
                "MODULE FLOW: Stage 1 (Discovery & Registration) -> Stage 2 (Descriptor & License) -> Stage 3 (Adapter Read & Symbol Resolution) -> Stage 4 (Policy & Promotion) -> Stage 5 (Read-Only Enforcement)"
            )
            print("=" * 80)

            fr_data_010_025_101_102()
            fr_data_011_113_114()
            fr_data_022_023_024_103_104()
            fr_data_026_027()
            fr_data_115_116()
            run_research_source_support()
            fr_data_159()
            print("SUCCESS: FEAT-DATA-10 completed")


if __name__ == "__main__":
    main()
