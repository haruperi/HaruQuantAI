"""Synthetic data and isolated telemetry for dataset requirements."""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from app.host.logging import configure_host_logging, flush, reset_logging
from app.workspace.DataManager.Data.contracts import BarRecord, Catalog, Dataset


@pytest.fixture
def dataset() -> Dataset:
    return Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        source_id="feed",
        broker_id="broker",
        groups=("majors",),
        records=(BarRecord(0, 10, 11, 9, 10, 3), BarRecord(60_000, 10, 11, 9, 10, 4)),
    )


@pytest.fixture
def catalog(dataset: Dataset) -> Catalog:
    return Catalog((dataset, Dataset("stock", "AAPL", "Apple", asset_type="stock")))


@pytest.fixture(autouse=True)
def isolated_telemetry(
    tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None]:
    def reject_database(*args: object, **kwargs: object) -> None:
        raise AssertionError("Dataset cohort must not access a database")

    monkeypatch.setattr(sqlite3, "connect", reject_database)
    configure_host_logging(log_dir=tmp_path / "logs", include_console=False)
    yield
    try:
        assert flush()
        name = request.node.path.stem.removeprefix("test_")
        if name != "contracts":
            requirement = "FR-DATASET-" + name.upper().replace("_", "-")
            content = (tmp_path / "logs" / "app.log").read_text(encoding="utf-8")
            assert requirement in content, (
                "Requirement executed without its own telemetry"
            )
            assert "Dataset operation" in content
            assert "Record values" not in content
            assert "private endpoint and credential" not in content
            assert "outcome" in content
    finally:
        reset_logging()
