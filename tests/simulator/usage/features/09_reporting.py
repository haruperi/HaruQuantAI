"""Executable Simulation reporting usage example.

Demonstrates FEAT-SIM-09 simulation result construction, trade records, artifact manifests, and report generation.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
    create_simulation_value,
    get_simulation_value_field,
    run_backtest_async,
    unwrap_simulation_response,
)
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


@cache
def _result() -> object:
    """Execute one genuine bounded run for reporting evidence."""
    dataset = live_tick_dataset()
    request = backtest_request(dataset)
    with tempfile.TemporaryDirectory(prefix="sim-reporting-") as directory:
        return _value(
            asyncio.run(
                run_backtest_async(
                    request,
                    authority(request),
                    dependencies(Path(directory), dataset),
                )
            )
        )


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.reporting")


def _contract(name: str, **fields: object) -> object:
    """Build one opaque Simulation reporting contract."""
    return create_simulation_value(name, **fields)


def fr_sim_024() -> None:
    """
    FR-SIM-024: Stage 3 — Expose completed SimulationResult v1 envelope.

    The system shall expose `SimulationResult` v1 with separate compatibility/schema identity, reproducibility identities, completed status, raw fills, the paired closed-trade ledger, journal/artifact references, fixed-precision accounting totals, diagnostics, and realism disclosures, and shall reject incomplete publication. `fills` are execution events; `closed_trades` are the paired round-trips consumers measure, populated from the engine-observed terminal closes of `FR-SIM-020` and never reconstructed after the run. `accounting` is derived from the completed `AccountLedger` totals; no monetary field in the published envelope is a constant.
    """
    _header("Stage 3: Result Contract - SimulationResult v1 Envelope (FR-SIM-024)")
    res = _result()
    print(_format_result(res))
    print(f"Data -> result_status='{res.status}', schema_id='{res.schema_id}'")


def fr_sim_040() -> None:
    """
    FR-SIM-040: Stage 3 — Expose ClosedTradeRecord carrying gross profit and MAE/MFE.

    The system shall expose one closed-trade ledger record carrying exactly `ticket`, `symbol`, `type`, `volume`, `entry_time`, `entry_price`, `stop_loss`, `take_profit`, `exit_time`, `exit_price`, `comment`, `commission`, `swap`, `profit`, `magic`, `mae`, and `mfe`. Timestamps are UTC; monetary and price fields are `Decimal`. `profit` is **gross** — price movement only — and excludes `commission` and `swap`, which carry a negative sign. The field set matches Analytics `FR-ANLT-049` exactly.
    """
    _header("Stage 3: Trade Record - ClosedTradeRecord Contract (FR-SIM-040)")
    trades = getattr(_result(), "closed_trades", ())
    trade = trades[0] if trades else None
    if trade is not None:
        print(_format_result(trade))
        print(f"Data -> gross_profit={getattr(trade, 'profit', None)}")


def fr_sim_033() -> None:
    """
    FR-SIM-033: Stage 3 — Expose PortfolioSimulationResult v1 contract.

    The system shall expose `PortfolioSimulationResult` v1 with separate compatibility/schema identity, run/result/reproducibility identities, construction identity, a bounded UTC measurement window, base currency, ordered reconciled component results, aligned component return evidence, aggregate journal and metric references, ordered Risk-owned budget-history evidence, FX lineage, an artifact manifest, and completed status. Each component row contains exactly `component_id`, `simulation_result_id`, `journal_ref`, `metrics_ref`, `account_currency`, and `reconciled=true`. Each component-return row contains exactly `component_id`, `simulation_result_id`, and `observations`; each observation contains exactly `timestamp` and `return_value`. Return observations are **periodic mark-to-market equity returns** measured by Simulation on one fixed UTC cadence shared by every component, derived from the component's own simulated equity curve; they are never supplied by the caller and never derived on a closed-trade basis. Return timestamps are unique ordered UTC values inside the measurement window, return values are finite, every component/result pair appears exactly once, and at least 30 timestamps are common to every component. Each risk-budget row contains exactly `risk_decision_id`, `component_id`, `effective_at`, `expires_at`, `approved_budget`, and `currency`. Incomplete or unreconciled runs are never published.
    """
    _header(
        "Stage 3: Portfolio Result - PortfolioSimulationResult v1 Envelope (FR-SIM-033)"
    )
    start = datetime(2025, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=30)
    observations = tuple(
        _contract(
            "ReturnObservation",
            timestamp=start + timedelta(days=index + 1),
            return_value=Decimal("0.001"),
        )
        for index in range(30)
    )
    result = _contract(
        "PortfolioSimulationResult",
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
            _contract(
                "PortfolioComponentResult",
                component_id="component",
                simulation_result_id="simulation-run",
                journal_ref="component/journal.jsonl",
                metrics_ref="component/result.json",
                account_currency="USD",
                reconciled=True,
            ),
        ),
        component_return_series=(
            _contract(
                "ComponentReturnSeries",
                component_id="component",
                simulation_result_id="simulation-run",
                observations=observations,
            ),
        ),
        aggregate_journal_ref="aggregate/journal.jsonl",
        aggregate_metrics_ref="aggregate/metrics.json",
        risk_budget_history=(
            _contract(
                "RiskBudgetHistoryRow",
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
    print(_format_result(result))
    print(
        f"Data -> portfolio_result_status='{get_simulation_value_field(result, 'status')}'"
    )


def fr_sim_025() -> None:
    """
    FR-SIM-025: Stage 3 — Expose versioned ArtifactEntry and ArtifactManifest contracts.

    The system shall expose a versioned manifest entry for every canonical artifact with relative path, media type, size, SHA-256 checksum, schema version, and creation time.
    """
    _header("Stage 3: Artifact Manifest - ArtifactManifest & Entry (FR-SIM-025)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    entries = tuple(
        _contract(
            "ArtifactEntry",
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
    manifest = _contract("ArtifactManifest", artifacts=entries, created_at=instant)
    print(_format_result(manifest))
    print(
        f"Data -> schema_version='{get_simulation_value_field(manifest, 'schema_version')}'"
    )


def fr_sim_026() -> None:
    """
    FR-SIM-026: Stage 3 — Build artifact manifest on disk with SHA-256 checksums.

    The system shall read completed canonical artifacts, verify containment and size, calculate checksums, and return a stable manifest without publishing temporary files.
    """
    _header("Stage 3: Manifest Assembly - Build Disk Artifact Manifest (FR-SIM-026)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        paths = []
        for name in ("journal.jsonl", "result.json", "report.md"):
            path = root / name
            path.write_text(name, encoding="utf-8")
            paths.append(path)
        resp = build_artifact_manifest(root, paths, created_at=instant)
        manifest = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> manifest_artifact_count={len(getattr(manifest, 'artifacts', ())) if hasattr(manifest, 'artifacts') else get_simulation_value_field(manifest, 'artifacts')}"
        )


def fr_sim_027() -> None:
    """
    FR-SIM-027: Stage 3 — Serialize SimulationResult to canonical JSON.

    The system shall serialize a `SimulationResult` to deterministic canonical JSON with execution/accounting diagnostics and realism/data-quality disclosures, excluding Analytics-owned metric formulas.
    """
    _header("Stage 3: JSON Report - Build JSON Execution Report (FR-SIM-027)")
    resp = build_json_report(_result())
    json_report = _value(resp)
    print(_format_result(resp))
    print(
        f"Data -> json_report_chars={len(json_report) if isinstance(json_report, str) else 0}"
    )


def fr_sim_028() -> None:
    """
    FR-SIM-028: Stage 3 — Render Markdown execution report with disclosures.

    The system shall render a deterministic Markdown execution report with assumptions, limitations, costs, fills, rejections, data quality, and artifact identities, excluding external distribution claims.
    """
    _header("Stage 3: Markdown Report - Build Markdown Execution Report (FR-SIM-028)")
    resp = build_markdown_report(_result())
    markdown_report = _value(resp)
    print(_format_result(resp))
    print(
        f"Data -> title='{markdown_report.splitlines()[0] if isinstance(markdown_report, str) else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-09 — reporting/ — Results and Canonical Artifacts\n\n"
        "Purpose: Build versioned SimulationResult and PortfolioSimulationResult envelopes, ClosedTradeRecords, checksummed ArtifactManifests, and JSON/Markdown execution reports.\n\n"
        "Module flow:\n"
        "-> Stage 1: Completed backtest outcome and artifact path input mapping\n"
        "-> Stage 2: Factual trade round-trip assembly and SHA-256 checksum calculation\n"
        "-> Stage 3: Immutable SimulationResult v1 envelope construction, artifact manifest assembly, and JSON/Markdown report rendering"
    )

    # Stage 3: Results, trade records, manifests, & reports
    fr_sim_024()
    fr_sim_040()
    fr_sim_033()
    fr_sim_025()
    fr_sim_026()
    fr_sim_027()
    fr_sim_028()


if __name__ == "__main__":
    main()
