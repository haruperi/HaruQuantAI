"""WF-DATA-017: import a declared CSV derived from genuine MT5 bars."""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    ColumnMapping,
    DatasetLoadRequest,
    ExternalImportRequest,
    describe_import_dialects,
    get_market_data,
    import_external_dataset,
    load_dataset,
    run_data_migrations,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-017"
STAGES = (
    "Resolve an approved external artifact path.",
    "Declare the CSV dialect and explicit column mapping.",
    "Map genuine MT5 observations to canonical fields.",
    "Run canonical quality validation.",
    "Commit through manifest-backed storage.",
    "Persist external-origin audit evidence and reload the artifact.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute explicit external artifact admission."""
    print(f"{WORKFLOW_ID} — External Artifact Import")
    print("INPUT BOUNDARY — approved CSV path, dialect, and ColumnMapping")
    bars = get_market_data(market_request("bars", timeframe="M1", limit=5))
    with tempfile.TemporaryDirectory(prefix="wf-data-017-") as directory:
        root = Path(directory)
        raw = root / "raw"
        raw.mkdir()

        # Stage 1 — Resolve an approved external artifact path.
        _stage(1)
        source_path = raw / "provider_export.csv"

        # Stage 2 — Declare the CSV dialect and explicit column mapping.
        _stage(2)
        dialects = describe_import_dialects()
        assert "standard" in dialects
        mapping = ColumnMapping(
            timestamp="timestamp",
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
        )

        # Stage 3 — Map genuine MT5 observations to canonical fields.
        _stage(3)
        with source_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("timestamp", "open", "high", "low", "close", "volume"))
            for bar in bars.records:
                writer.writerow(
                    (
                        bar.timestamp.isoformat(),
                        bar.open,
                        bar.high,
                        bar.low,
                        bar.close,
                        bar.volume,
                    )
                )

        with isolated_runtime(root):
            run_data_migrations(generate_id("req"))

            # Stage 4 — Run canonical quality validation.
            _stage(4)
            request = ExternalImportRequest(
                relative_path=Path("raw/provider_export.csv"),
                format="csv",
                dialect="standard",
                mapping=mapping,
                symbol="EURUSD",
                data_kind="bars",
                timeframe="M1",
                source_id="mt5-export",
                workflow_context="research",
                precision_policy="decimal_string",
                price_unit="USD",
                volume_unit="lots",
                destination_path=Path("raw/EURUSD_M1.csv"),
                request_id=generate_id("req"),
            )

            # Stage 5 — Commit through manifest-backed storage.
            _stage(5)
            manifest = import_external_dataset(request)

            # Stage 6 — Persist external-origin audit evidence and reload the artifact.
            _stage(6)
            loaded = load_dataset(
                DatasetLoadRequest(
                    relative_path=manifest.relative_path,
                    format="csv",
                    request_id=generate_id("req"),
                )
            )
            print(
                "Imported records and origin:",
                loaded.record_count,
                loaded.source_metadata["origin"],
            )
    print(
        "OUTPUT BOUNDARY — committed canonical artifact, manifest, and audit evidence"
    )


if __name__ == "__main__":
    main()
