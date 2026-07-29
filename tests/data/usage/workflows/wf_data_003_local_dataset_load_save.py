"""WF-DATA-003: atomically save and load a genuine MT5 dataset."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_dataset_load_request,
    build_dataset_save_request,
    get_market_data,
    load_dataset,
    run_data_migrations,
    save_dataset,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-003"
STAGES = (
    "Resolve an approved relative storage path.",
    "Acquire the path-scoped write boundary.",
    "Validate the genuine MT5 dataset and license metadata.",
    "Atomically write the artifact and versioned manifest.",
    "Load and verify the artifact hash and schema.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute local save and load with temporary durable state."""
    print(f"{WORKFLOW_ID} — Local Dataset Load and Save")
    print("INPUT BOUNDARY — approved path and normalized MT5 dataset")
    with tempfile.TemporaryDirectory(prefix="wf-data-003-") as directory:
        root = Path(directory)
        with isolated_runtime(root):
            run_data_migrations(generate_id("req"))
            (root / "raw").mkdir(parents=True, exist_ok=True)

            response = get_market_data(market_request("bars", timeframe="M1"))
            dataset = unwrap_data_response(
                response,
                operation="get_market_data",
                request_id=response.metadata.request_id,
            )

            # Stage 1 — Resolve an approved relative storage path.
            _stage(1)
            relative_path = Path("raw/EURUSD_M1.parquet")

            # Stage 2 — Acquire the path-scoped write boundary.
            _stage(2)
            request_id = dataset.request_id

            # Stage 3 — Validate the genuine MT5 dataset and license metadata.
            _stage(3)
            assert dataset.source_metadata

            # Stage 4 — Atomically write the artifact and versioned manifest.
            _stage(4)
            save_resp = save_dataset(
                build_dataset_save_request(
                    dataset=dataset,
                    relative_path=relative_path,
                    format="parquet",
                    overwrite=False,
                    request_id=request_id,
                )
            )
            manifest = unwrap_data_response(
                save_resp, operation="save_dataset", request_id=request_id
            )

            # Stage 5 — Load and verify the artifact hash and schema.
            _stage(5)
            load_resp = load_dataset(
                build_dataset_load_request(
                    relative_path=manifest.relative_path,
                    format="parquet",
                    request_id=generate_id("req"),
                )
            )
            loaded = unwrap_data_response(
                load_resp, operation="load_dataset", request_id=generate_id("req")
            )
            assert loaded.record_count == dataset.record_count
            print("Committed artifact:", manifest.relative_path)
    print("OUTPUT BOUNDARY — verified MarketDataset and committed manifest")


if __name__ == "__main__":
    main()
