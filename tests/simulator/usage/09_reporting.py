"""Executable Simulation reporting usage example.

Demonstrates simulation result construction, trade records, artifact manifests, and report generation.
"""

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator.reporting import (
    ArtifactEntry,
    ArtifactManifest,
    ClosedTradeRecord,
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


def main() -> None:
    """Run Simulator reporting usage example."""
    example_reporting()


if __name__ == "__main__":
    main()
