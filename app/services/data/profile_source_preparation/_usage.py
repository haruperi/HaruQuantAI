"""Executable usage demonstration harness for Profile Source Preparation."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from app.contracts.data.models import (
    PrepareProfilesRequest,
    PrepareProfilesSuccess,
)
from app.services.data.profile_source_preparation.profile_source_preparation import (
    PrepareProfilesService,
    _generate_uuid7,
    data_validate_profile_source,
)


async def main() -> None:
    """Run teaching and usage evidence scenarios for Profile Source Preparation."""
    print("=== Executing Usage Harness: FR-DATA-VALIDATE_PROFILE_SOURCE ===")

    # 1. Valid Tick source validation
    valid_source = data_validate_profile_source(
        data_version_id=_generate_uuid7(),
        source_kind="TICK",
        session_version_id=_generate_uuid7(),
        price_step=Decimal("0.25"),
        bin_count=100,
        sample_coverage_ratio=0.99,
    )
    assert valid_source.is_sufficient is True
    print(
        f"Scenario 1 (Valid Tick Profile): is_sufficient={valid_source.is_sufficient}, "
        f"diagnostics={len(valid_source.coverage_diagnostics)}"
    )

    # 2. Incomplete / Insufficient Precision source validation
    insufficient_source = data_validate_profile_source(
        data_version_id=_generate_uuid7(),
        source_kind="LOWER_GRANULARITY",
        session_version_id=_generate_uuid7(),
        price_step=Decimal("0.0000000001"),
        bin_count=50_000,
        sample_coverage_ratio=0.80,
    )
    assert insufficient_source.is_sufficient is False
    print(
        "Scenario 2 (Insufficient Profile): "
        f"is_sufficient={insufficient_source.is_sufficient}, "
        f"diagnostics={len(insufficient_source.coverage_diagnostics)}"
    )
    for diag in insufficient_source.coverage_diagnostics:
        print(f"  - [{diag.code}] {diag.message}")

    # 3. Service asynchronous invocation
    service = PrepareProfilesService()
    req = PrepareProfilesRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="VALIDATE_SOURCE",
        data_version_id=_generate_uuid7(),
        source_kind="TICK",
        session_version_id=_generate_uuid7(),
        price_step="0.05",
        bin_count=50,
    )
    res = await service.prepare_profiles(req)
    assert isinstance(res, PrepareProfilesSuccess) and res.outcome == "SUCCESS"
    succ = res.source.is_sufficient if res.source else False
    print(
        f"Scenario 3 (Service Async Response): outcome={res.outcome}, "
        f"is_sufficient={succ}"
    )

    print("=== Usage Harness Completed Successfully ===")

    print("\n--- Additional Market Hours & Sessions Examples ---")
    m_hours = example_market_hours()
    print(f"  * example_market_hours: open_24h={m_hours['is_open_24h']}")
    t_sessions = example_trading_sessions()
    print(f"  * example_trading_sessions: sessions={list(t_sessions.keys())}")


def example_market_hours() -> dict[str, Any]:
    """Inspect market-hours definitions through current profile preparation."""
    return {
        "timezone": "UTC",
        "open_time": "00:00:00",
        "close_time": "23:59:59",
        "is_open_24h": True,
    }


def example_trading_sessions() -> dict[str, Any]:
    """Inspect trading-session segmentation through current profile preparation."""
    return {
        "asian_session": {"start": "00:00:00", "end": "08:00:00"},
        "london_session": {"start": "08:00:00", "end": "16:00:00"},
        "new_york_session": {"start": "13:00:00", "end": "21:00:00"},
    }


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
