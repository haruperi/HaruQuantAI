"""Real uploaded content, parser policies and canonical publication."""

import pandas as pd
import pytest
from app.workspace.data_manager.data.review import DatasetReview
from app.workspace.data_manager.sources.files import preview_import

from .test_download_jobs import downloads  # noqa: F401 - shared pytest fixture


def test_uploaded_prices_publish_exact_canonical_rows(recorded_history):
    gateway, identifier, _ = recorded_history
    frame = DatasetReview(gateway, identifier).frame()
    assert len(frame) == 6
    assert frame.Open.tolist() == [1.1] * 6
    assert frame.Volume.tolist() == [10, 11, 12, 14, 15, 16]
    assert frame.index.tz is not None


def test_custom_format_reports_bad_rows_and_converts_timezone():
    content = b"2025.01.06;09:00:00;1;2;0.5;1.5;3\nbad;row;1;2;3;4;5\n"
    opts = {
        "timeframe": "M1",
        "timezone": "Europe/Helsinki",
        "ignore_errors": True,
        "format": {
            "separator": ";",
            "columns": ["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
            "dateFormat": "yyyy.MM.dd",
        },
    }
    frame, errors = preview_import(content, "data.txt", opts)
    assert frame.index[0] == pd.Timestamp("2025-01-06T07:00:00Z")
    assert len(errors) == 1
    with pytest.raises(ValueError, match="Row 2"):
        preview_import(content, "data.txt", {**opts, "ignore_errors": False})


def test_http_upload_job_review_and_artifact_use_actual_storage(
    downloads,  # noqa: F811 - imported pytest fixture
    tmp_path,
    monkeypatch,
):
    client, jobs, service, _ = downloads
    client.app.state.data_market_root = tmp_path / "uploaded"
    content = "DateTime,Open,High,Low,Close,Volume\n2025-01-06 09:00:00,1,2,0.5,1.5,7\n"
    response = client.post(
        "/api/v1/data/datasets/import",
        json={
            "name": "prices.csv",
            "content": content,
            "symbol": "UPLOADED",
            "timeframe": "M1",
        },
    )
    assert response.status_code == 200
    job = jobs.wait_for_job(response.json()["data"]["job_id"], timeout=10)
    assert job.status == "COMPLETED", job.error_message
    identifier = job.result["datasets"][0]
    review = client.get(f"/api/v1/data/datasets/{identifier}/review-data").json()[
        "data"
    ]
    assert review["rows"][0]["close"] == 1.5
    export = client.post(
        "/api/v1/data/export",
        json={"format": "csv", "series": [{"dataset_id": identifier}]},
    ).json()["data"]
    completed = jobs.wait_for_job(export["job_id"], timeout=10)
    assert completed.status == "COMPLETED", completed.error_message
    artifact = client.get(f"/api/v1/data/export-artifacts/{completed.job_id}/0")
    assert artifact.status_code == 200 and "1.5" in artifact.text
    from dataclasses import replace

    original = jobs.get_job
    monkeypatch.setattr(
        jobs, "get_job", lambda value: replace(original(value), result=None)
    )
    restored = client.get(f"/api/v1/data/download-jobs/{completed.job_id}").json()[
        "data"
    ]
    assert restored["result"]["artifacts"] == completed.result["artifacts"]


def test_uploaded_metadata_without_prices_is_rejected(symbol_http):
    response = symbol_http.post(
        "/api/v1/data/datasets/import",
        json={"symbol": "NOT_IMPORTED", "timeframe": "M1"},
    )
    assert response.status_code == 422
