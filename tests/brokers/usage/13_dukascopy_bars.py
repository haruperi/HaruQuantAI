"""FEAT-BRK-13: genuine Dukascopy BID bars."""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import _support  # noqa: F401
from _support import UsageEvidenceError, real_session, require_success
from app.services.brokers import get_broker_historical_bars, get_broker_value_field


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


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
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


async def fr_brokers_129_to_132_dukascopy_bars(adapter: object) -> None:
    """FR-BRK-129..132: Stage 1..3 — Instrument Specification, Web-Chart BID Fetch, & Canonical Bar Page Output."""
    _header(
        "Stage 1..3: Instrument & Web-Chart BID Fetch to Canonical Bars (FR-BRK-129..132)"
    )
    end = datetime.now(UTC).replace(second=0, microsecond=0)
    result = await get_broker_historical_bars(
        adapter,
        "EURUSD",
        "1m",
        start_time=end - timedelta(minutes=5),
        end_time=end,
        limit=5,
    )
    require_success("Result", result)
    data = get_broker_value_field(result, "data")
    items = get_broker_value_field(data, "items")
    print(_format_result(result))
    print(f"Data -> bar_count={len(items) if items is not None else 0}")


async def _run() -> None:
    """Execute genuine Dukascopy bar evidence in one sandbox session."""
    _feature_header(
        "FEATURE: FEAT-BRK-13 — dukascopy_bars/ — Dukascopy BID Bars\n\n"
        "Purpose: Provide Dukascopy historical M1 BID candle retrieval from web-chart endpoint.\n\n"
        "Module flow:\n"
        "-> instrument + date range\n"
        "-> web-chart BID fetch\n"
        "-> canonical bars"
    )

    try:
        async with real_session("dukascopy") as adapter:
            # Stage 1..3: Instrument & range to BID fetch to canonical bar page
            await fr_brokers_129_to_132_dukascopy_bars(adapter)
    except UsageEvidenceError as err:
        print("Output Result -> UsageEvidenceError : UsageEvidenceError")
        print(f"Data -> status='FAIL_CLOSED', reason='{err}'")


def main() -> None:
    """Run the standalone genuine Dukascopy bar program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
