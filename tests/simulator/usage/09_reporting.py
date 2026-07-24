"""Executable Simulation reporting usage example.

Demonstrates simulation result construction, trade records, artifact manifests,
and report generation.
"""

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import (
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
from tests.simulator.unit.test_reporting_contracts import _result


def example_reporting() -> None:
    """Demonstrate reporting models, manifest building, and report rendering."""
    print("=" * 80)
    print("Simulator Example 9: Result Contracts and Reporting")
    print("=" * 80)

    result = _result()
    print(f"Simulation result status: {result.status}")

    # 1. ClosedTradeRecord
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
    print(f"ClosedTradeRecord ticket: {trade.ticket}, profit: {trade.profit}")

    # 2. ArtifactManifest
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
    manifest = ArtifactManifest(artifacts=entries, created_at=instant)
    print(f"ArtifactManifest entries count: {len(manifest.artifacts)}")

    # 3. Build artifact manifest on disk
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        paths = []
        for name in ("journal.jsonl", "result.json", "report.md"):
            path = tmp_path / name
            path.write_text(name, encoding="utf-8")
            paths.append(path)
        disk_manifest = build_artifact_manifest(tmp_path, paths, created_at=instant)
        print(f"Disk manifest created with {len(disk_manifest.artifacts)} files")

    # 4. JSON and Markdown report generation
    json_report = build_json_report(result)
    markdown_report = build_markdown_report(result)
    print(f"JSON report length: {len(json_report)} chars")
    print(f"Markdown report title: {markdown_report.splitlines()[0]}")


def fr_sim_024() -> None:
    """Demonstrate FR-SIM-024.

    Responsibility:
        The system shall expose `SimulationResult` v1 with separate compatibility/schema
        identity, reproducibility identities, completed status, raw fills, the paired
        closed-trade ledger, journal/artifact references, fixed-precision accounting
        totals, diagnostics, and realism disclosures, and shall reject incomplete
        publication. `fills` are execution events; `closed_trades` are the paired
        round-trips consumers measure, populated from the engine-observed terminal
        closes of `FR-SIM-020` and never reconstructed after the run. `accounting` is
        derived from the completed `AccountLedger` totals; no monetary field in the
        published envelope is a constant.
    """
    print(f"Simulation result status: {_result().status}")


def fr_sim_040() -> None:
    """Demonstrate FR-SIM-040.

    Responsibility:
        The system shall expose one closed-trade ledger record carrying exactly
        `ticket`, `symbol`, `type`, `volume`, `entry_time`, `entry_price`, `stop_loss`,
        `take_profit`, `exit_time`, `exit_price`, `comment`, `commission`, `swap`,
        `profit`, `magic`, `mae`, and `mfe`. Timestamps are UTC; monetary and price
        fields are `Decimal`. `profit` is **gross** — price movement only — and excludes
        `commission` and `swap`, which carry a negative sign. The field set matches
        Analytics `FR-ANLT-049` exactly.
    """
    trade = _result().closed_trades[0]
    print(f"Closed trade gross profit: {trade.profit}")


def fr_sim_033() -> None:
    """Demonstrate FR-SIM-033.

    Responsibility:
        The system shall expose `PortfolioSimulationResult` v1 with separate
        compatibility/schema identity, run/result/reproducibility identities,
        construction identity, a bounded UTC measurement window, base currency, ordered
        reconciled component results, aligned component return evidence, aggregate
        journal and metric references, ordered Risk-owned budget-history evidence, FX
        lineage, an artifact manifest, and completed status. Each component row contains
        exactly `component_id`, `simulation_result_id`, `journal_ref`, `metrics_ref`,
        `account_currency`, and `reconciled=true`. Each component-return row contains
        exactly `component_id`, `simulation_result_id`, and `observations`; each
        observation contains exactly `timestamp` and `return_value`. Return observations
        are **periodic mark-to-market equity returns** measured by Simulation on one
        fixed UTC cadence shared by every component, derived from the component's own
        simulated equity curve; they are never supplied by the caller and never derived
        on a closed-trade basis. Return timestamps are unique ordered UTC values inside
        the measurement window, return values are finite, every component/result pair
        appears exactly once, and at least 30 timestamps are common to every component.
        Each risk-budget row contains exactly `risk_decision_id`, `component_id`,
        `effective_at`, `expires_at`, `approved_budget`, and `currency`. Incomplete or
        unreconciled runs are never published.
    """
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=30)
    observations = tuple(
        ReturnObservation(
            timestamp=start + timedelta(days=index + 1),
            return_value=Decimal("0.001"),
        )
        for index in range(30)
    )
    result = PortfolioSimulationResult(
        result_id="portfolio-result",
        run_id="portfolio-run",
        request_hash="a" * 64,
        config_hash="b" * 64,
        data_hash="c" * 64,
        result_hash="d" * 64,
        engine_version="v1",
        status="completed",
        portfolio_id="portfolio",
        construction_result_id="construction",
        construction_version="v1",
        measurement_start=start,
        measurement_end=end,
        base_currency="USD",
        component_results=(
            PortfolioComponentResult(
                component_id="component",
                simulation_result_id="simulation-run",
                journal_ref="component/journal.jsonl",
                metrics_ref="component/result.json",
                account_currency="USD",
                reconciled=True,
            ),
        ),
        component_return_series=(
            ComponentReturnSeries(
                component_id="component",
                simulation_result_id="simulation-run",
                observations=observations,
            ),
        ),
        aggregate_journal_ref="aggregate/journal.jsonl",
        aggregate_metrics_ref="aggregate/metrics.json",
        risk_budget_history=(
            RiskBudgetHistoryRow(
                risk_decision_id="risk",
                component_id="component",
                effective_at=start,
                expires_at=end,
                approved_budget=Decimal(100),
                currency="USD",
            ),
        ),
        fx_evidence_ids=("fx-1",),
        artifact_manifest_ref="aggregate/manifest.json",
    )
    print(f"Portfolio result status: {result.status}")


def fr_sim_025() -> None:
    """Demonstrate FR-SIM-025.

    Responsibility:
        The system shall expose a versioned manifest entry for every canonical artifact
        with relative path, media type, size, SHA-256 checksum, schema version, and
        creation time.
    """
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    entries = tuple(
        ArtifactEntry(
            relative_path=name,
            media_type="application/octet-stream",
            size_bytes=1,
            sha256=character * 64,
            created_at=instant,
        )
        for character, name in zip(
            "abc",
            ("journal.jsonl", "result.json", "report.md"),
            strict=True,
        )
    )
    manifest = ArtifactManifest(artifacts=entries, created_at=instant)
    print(f"Manifest schema: {manifest.schema_version}")


def fr_sim_026() -> None:
    """Demonstrate FR-SIM-026.

    Responsibility:
        The system shall read completed canonical artifacts, verify containment and
        size, calculate checksums, and return a stable manifest without publishing
        temporary files.
    """
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        paths = []
        for name in ("journal.jsonl", "result.json", "report.md"):
            path = root / name
            path.write_text(name, encoding="utf-8")
            paths.append(path)
        manifest = build_artifact_manifest(root, paths, created_at=instant)
        print(f"Built artifacts: {len(manifest.artifacts)}")


def fr_sim_027() -> None:
    """Demonstrate FR-SIM-027.

    Responsibility:
        The system shall serialize a `SimulationResult` to deterministic canonical JSON
        with execution/accounting diagnostics and realism/data-quality disclosures,
        excluding Analytics-owned metric formulas.
    """
    print(f"JSON report bytes: {len(build_json_report(_result()))}")


def fr_sim_028() -> None:
    """Demonstrate FR-SIM-028.

    Responsibility:
        The system shall render a deterministic Markdown execution report with
        assumptions, limitations, costs, fills, rejections, data quality, and artifact
        identities, excluding external distribution claims.
    """
    print(build_markdown_report(_result()).splitlines()[0])


def main() -> None:
    """Run Simulator reporting usage example."""
    fr_sim_024()
    fr_sim_040()
    fr_sim_033()
    fr_sim_025()
    fr_sim_026()
    fr_sim_027()
    fr_sim_028()


if __name__ == "__main__":
    main()
