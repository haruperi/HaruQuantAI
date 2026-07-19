"""Runnable usage examples for Simulation reporting."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.simulator.reporting import (
    ArtifactEntry,
    ArtifactManifest,
    ClosedTradeRecord,
    ComponentReturnSeries,
    PortfolioComponentResult,
    PortfolioSimulationResult,
    ReturnObservation,
    RiskBudgetHistoryRow,
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
)
from tests.simulator.unit.test_portfolio_run import _portfolio_request
from tests.simulator.unit.test_reporting_contracts import _result


def test_usage_simulation_result() -> None:
    """Construct one completed canonical result."""
    assert _result().status == "completed"


def test_usage_closed_trade_record() -> None:
    """Construct the exact Analytics-compatible ledger row."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    trade = ClosedTradeRecord(
        ticket="ticket",
        symbol="EURUSD",
        type="BUY",
        volume=Decimal(1),
        entry_time=instant,
        entry_price=Decimal(1),
        stop_loss=None,
        take_profit=None,
        exit_time=instant + timedelta(minutes=1),
        exit_price=Decimal("1.1"),
        comment="simulated",
        commission=Decimal(-1),
        swap=Decimal(0),
        profit=Decimal(10),
        magic="strategy",
        mae=Decimal(-1),
        mfe=Decimal(11),
    )
    assert len(type(trade).model_fields) == 17


def test_usage_artifact_manifest() -> None:
    """Construct one complete acyclic manifest."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    entries = tuple(
        ArtifactEntry(
            relative_path=name,
            media_type="application/octet-stream",
            size_bytes=1,
            sha256=str(index) * 64,
            created_at=instant,
        )
        for index, name in zip(
            "123", ("journal.jsonl", "result.json", "report.md"), strict=True
        )
    )
    assert len(ArtifactManifest(artifacts=entries, created_at=instant).artifacts) == 3


def test_usage_build_artifact_manifest(tmp_path: Path) -> None:
    """Hash three completed canonical artifacts."""
    paths = []
    for name in ("journal.jsonl", "result.json", "report.md"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        paths.append(path)
    manifest = build_artifact_manifest(
        tmp_path,
        paths,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert len(manifest.artifacts) == 3


def test_usage_build_json_report() -> None:
    """Serialize a result to canonical JSON."""
    assert build_json_report(_result()).startswith("{")


def test_usage_build_markdown_report() -> None:
    """Render deterministic execution Markdown."""
    assert build_markdown_report(_result()).startswith("# Simulation")


def test_usage_portfolio_simulation_result() -> None:
    """Construct one complete reconciled portfolio result."""
    request = _portfolio_request()
    component = request.components[0]
    observations = tuple(
        ReturnObservation(
            timestamp=request.measurement_start + timedelta(seconds=index),
            return_value=Decimal("0.001"),
        )
        for index in range(30)
    )
    result = PortfolioSimulationResult(
        result_id="portfolio-result",
        run_id="portfolio-run",
        request_hash="1" * 64,
        config_hash=request.config_hash,
        data_hash="2" * 64,
        result_hash="3" * 64,
        engine_version="simulation-engine-v1",
        status="completed",
        portfolio_id=request.portfolio_id,
        construction_result_id=request.construction_result_id,
        construction_version=request.construction_version,
        measurement_start=request.measurement_start,
        measurement_end=request.measurement_end,
        base_currency=request.base_currency,
        component_results=(
            PortfolioComponentResult(
                component_id=component.component_id,
                simulation_result_id="component-run",
                journal_ref="component-run/journal.jsonl",
                metrics_ref=component.metrics_ref,
                account_currency="USD",
                reconciled=True,
            ),
        ),
        component_return_series=(
            ComponentReturnSeries(
                component_id=component.component_id,
                simulation_result_id="component-run",
                observations=observations,
            ),
        ),
        aggregate_journal_ref="portfolio-run/journal.jsonl",
        aggregate_metrics_ref="portfolio-run/metrics.json",
        risk_budget_history=(
            RiskBudgetHistoryRow(
                risk_decision_id=component.risk_decision_id,
                component_id=component.component_id,
                effective_at=request.measurement_start,
                expires_at=request.measurement_end,
                approved_budget=component.risk_budget,
                currency=request.base_currency,
            ),
        ),
        fx_evidence_ids=request.fx_evidence_ids,
        artifact_manifest_ref="portfolio-run/manifest.json",
    )
    assert result.status == "completed"
