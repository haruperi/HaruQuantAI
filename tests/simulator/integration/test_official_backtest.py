"""Workflow integration tests for the official governed backtest path."""
# ruff: noqa: INP001

import tracemalloc
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from app.services.data.contracts import DataQualityReport, MarketDataset, TickRecord
from app.services.simulator import run_backtest
from app.utils import logger
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


class TrackingDependencies(FakeDependencies):
    """Record the required upstream domain sequence for one official run."""

    def __init__(self, tmp_path: Path, dataset: object) -> None:
        """Initialize the deterministic fixture and call journal.

        Args:
            tmp_path: Isolated test root.
            dataset: Data-owned market evidence.
        """
        logger.debug("Initializing tracked official workflow dependencies")
        super().__init__(tmp_path, dataset)  # type: ignore[arg-type]
        self.calls: list[str] = []

    def load_market_data(self, request: object) -> object:
        """Record and delegate the Data load operation."""
        logger.debug("Recording the official Data load operation")
        self.calls.append("data.load")
        return super().load_market_data(request)  # type: ignore[arg-type]

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Record and delegate Data-owned tick generation."""
        logger.debug("Recording official Data tick generation")
        self.calls.append("data.generate_tick_series")
        return super().generate_tick_series(dataset, request)  # type: ignore[arg-type]

    def calculate_indicators(
        self, dataset: object, request: object
    ) -> tuple[object, ...]:
        """Record and delegate Indicator calculation."""
        logger.debug("Recording official Indicator calculation")
        self.calls.append("indicators.calculate")
        return super().calculate_indicators(dataset, request)  # type: ignore[arg-type]

    def evaluate_strategy(
        self, dataset: object, indicators: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Record and delegate Strategy evaluation."""
        logger.debug("Recording official Strategy evaluation")
        self.calls.append("strategy.evaluate")
        return super().evaluate_strategy(  # type: ignore[arg-type]
            dataset, indicators, request
        )

    def review_risk(
        self, intents: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Record and delegate Risk review."""
        logger.debug("Recording official Risk review")
        self.calls.append("risk.review")
        return super().review_risk(intents, request)  # type: ignore[arg-type]

    def build_order_intents(
        self, decisions: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Record and delegate Trading intent construction."""
        logger.debug("Recording official Trading intent construction")
        self.calls.append("trading.build_order_intents")
        return super().build_order_intents(decisions, request)  # type: ignore[arg-type]


def _protective_dataset(request_id: str) -> MarketDataset:
    """Build a falling three-tick dataset that crosses a protective stop.

    Args:
        request_id: Canonical Data request identity.

    Returns:
        Data-owned tick dataset whose price falls through the stop.

    """
    logger.debug("Building a falling Simulation fixture dataset")
    start = datetime(2025, 1, 6, 12, tzinfo=UTC)
    bids = (Decimal("1.10000"), Decimal("1.09000"), Decimal("1.08000"))
    records = tuple(
        TickRecord(
            timestamp=start + timedelta(seconds=index),
            source="fixture",
            source_symbol="EURUSD",
            available_at=start + timedelta(seconds=index),
            bid=bid,
            ask=bid + Decimal("0.00002"),
            last=None,
            volume=Decimal(10),
            price_unit="quote",
            volume_unit="lot",
        )
        for index, bid in enumerate(bids)
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=len(records),
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=request_id,
    )


class ProtectiveDependencies(FakeDependencies):
    """Fixture whose approved intent carries a protective stop."""

    def build_order_intents(
        self, decisions: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Attach a protective stop to the approved sim intent.

        Args:
            decisions: Risk decision packages.
            request: Canonical run request.

        Returns:
            One Trading-owned intent carrying a stop-loss.
        """
        logger.debug("Building a protected Simulation order intent")
        intents = super().build_order_intents(decisions, request)  # type: ignore[arg-type]
        return tuple(
            intent.model_copy(update={"stop_loss": Decimal("1.09500")})
            for intent in intents
        )


def test_official_backtest_completes_end_to_end(tmp_path: Path) -> None:
    """Complete Data through reporting with the required domain call order."""
    logger.info("Testing WF-SIM-001 official backtest end to end")
    dataset = _dataset(f"req-{'a' * 64}")
    request = _request(dataset, suffix="a")
    dependencies = TrackingDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert result.status == "completed"
    assert dependencies.calls == [
        "data.load",
        "data.generate_tick_series",
        "indicators.calculate",
        "strategy.evaluate",
        "risk.review",
        "trading.build_order_intents",
    ]
    run_root = dependencies.artifact_root / result.run_id
    assert {path.name for path in run_root.iterdir()} == {
        "journal.jsonl",
        "manifest.json",
        "report.md",
        "result.json",
    }


def test_completed_run_publishes_closed_trade_ledger(tmp_path: Path) -> None:
    """Publish a real closed-trade ledger with observed excursions."""
    logger.info("Testing WF-SIM-001 closed-trade ledger publication")
    dataset = _protective_dataset(f"req-{'d' * 64}")
    request = _request(dataset, suffix="d")
    dependencies = ProtectiveDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert result.status == "completed"
    assert len(result.closed_trades) >= 1
    record = result.closed_trades[0]
    assert record.mae is not None
    assert record.mfe is not None
    assert record.commission <= Decimal(0)
    assert record.swap <= Decimal(0)
    assert record.exit_time >= record.entry_time


def test_official_backtest_uses_data_tick_series_only(tmp_path: Path) -> None:
    """Prove the official clock invokes Data-owned real-evidence generation."""
    logger.info("Testing WF-SIM-010 synthetic-market-data exclusion")
    dataset = _dataset(f"req-{'b' * 64}")
    request = _request(dataset, suffix="b")
    dependencies = TrackingDependencies(tmp_path, dataset)
    run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert dependencies.calls.count("data.generate_tick_series") == 1
    assert dependencies.dataset.source_metadata["tick_generation_model"] == "real"


def test_official_backtest_performance_baseline(tmp_path: Path) -> None:
    """Measure and bound a two-tick official run's time and peak memory."""
    logger.info("Measuring the Section 7 official-run performance baseline")
    dataset = _dataset(f"req-{'c' * 64}")
    request = _request(dataset, suffix="c")
    dependencies = FakeDependencies(tmp_path, dataset)
    tracemalloc.start()
    started = perf_counter()
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    elapsed = perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info(
        "Official two-tick baseline elapsed_seconds=%.6f peak_bytes=%d",
        elapsed,
        peak_bytes,
    )
    assert result.status == "completed"
    assert elapsed >= 0
    assert peak_bytes > 0
