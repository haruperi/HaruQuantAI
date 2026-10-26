"""Real backend download jobs with isolated persistence and deterministic providers."""

import sqlite3
import threading
from contextlib import closing

import pandas as pd
import pytest
from app.host.events import EventBus
from app.host.jobs import JobManager
from app.host.persistence import HostPersistence
from app.host.resources import MemoryObservation, ResourceMonitor
from app.host.transport import register_transport_exception_handlers
from app.include.contracts import BridgeError
from app.workspace.data_manager import http
from app.workspace.data_manager.dukascopy import Dukascopy
from app.workspace.data_manager.logs import Logs
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def downloads(tmp_path, monkeypatch):
    from app.workspace.data_manager import download_jobs, dukascopy

    database = tmp_path / "jobs.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript("""
            CREATE TABLE host_jobs (
                job_id TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'default',
                kind TEXT NOT NULL DEFAULT 'compute', status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0, accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0, message TEXT NOT NULL DEFAULT '',
                attempt_id INTEGER DEFAULT 1, submitted_at_utc TEXT NOT NULL DEFAULT '',
                started_at_utc TEXT, finished_at_utc TEXT, error_message TEXT);
            CREATE TABLE host_job_events (
                event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_id TEXT,
                from_state TEXT, to_state TEXT NOT NULL, details_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL);
        """)
    gateway = HostPersistence(database)
    catalog = tmp_path / "catalog.csv"
    catalog.write_text(
        "EURUSD;Euro;Forex;Majors;05.05.2003;05.05.2003;5;100000;3;0.0001;0.00001;3\n"
    )
    logs = Logs(EventBus())
    service = Dukascopy(
        gateway, storage_root=tmp_path / "market", catalog_path=catalog, logs=logs
    )
    assert service.add("EURUSD")["success"]
    monitor = ResourceMonitor(
        scratch_root=tmp_path / "scratch",
        probe_memory_fn=lambda: MemoryObservation(100, 50, 50, 50, 1, 0.5, True),
    )
    jobs = JobManager(
        persistence=gateway, resource_mgr=monitor, max_workers=1, use_process_pool=False
    )
    application = FastAPI()
    application.state.persistence = gateway
    application.state.data_logs = logs
    application.state.download_jobs = jobs
    application.include_router(http.create_router())
    application.dependency_overrides[http._access] = lambda: None
    register_transport_exception_handlers(application)
    monkeypatch.setattr(download_jobs, "Dukascopy", lambda *args, **kwargs: service)

    class Provider:
        entered = threading.Event()
        release = threading.Event()
        fail = False
        wait = False

        def __init__(self, **kwargs):
            pass

        def get_bars(self, *args, **kwargs):
            self.entered.set()
            if self.wait:
                assert self.release.wait(10)
            if self.fail:
                raise BridgeError("Provider failed", code="NETWORK_ERROR")
            return pd.DataFrame(
                {column: [1.1] for column in ["Open", "High", "Low", "Close"]},
                index=pd.to_datetime([kwargs["date_from"]], utc=True),
            )

        def disconnect(self):
            pass

    monkeypatch.setattr(dukascopy, "DukascopyClient", Provider)
    with TestClient(application) as client:
        yield client, jobs, service, Provider
    Provider.release.set()
    jobs.shutdown(cancel_futures=True)


def _start(client):
    response = client.post(
        "/api/v1/data/providers/download",
        json={
            "provider": "dukascopy",
            "targets": [{"symbol": "EURUSD", "timeframe": "M1"}],
            "date_from": "2025-01-01",
            "date_to": "2025-01-02",
            "overwrite": True,
            "download_type": "standard",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["job_id"]


@pytest.mark.parametrize("status", ["RUNNING", "PAUSED", "QUEUED"])
def test_restart_interrupts_orphan_download_without_touching_other_jobs(
    downloads, status
):
    client, _, service, _ = downloads
    gateway = service.gateway
    for job_id, kind in [("orphan", "dukascopy.download"), ("other", "basket.update")]:
        assert gateway.create_records(
            "host_jobs",
            {
                "job_id": job_id,
                "kind": kind,
                "status": status,
            },
        )["success"]
    del client.app.state.download_jobs
    try:
        response = client.get("/api/v1/data/download-jobs/orphan")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "INTERRUPTED"
        assert "restarted" in response.json()["data"]["error_message"]
        other = gateway.read_records("host_jobs", filters={"job_id": "other"})
        assert other["data"]["records"][0]["status"] == status
    finally:
        client.app.state.download_jobs.shutdown(cancel_futures=True)


def test_backend_job_publishes_and_reports_actual_completion(downloads):
    client, jobs, service, _ = downloads
    job_id = _start(client)
    record = jobs.wait_for_job(job_id, timeout=10)
    assert record.status == "COMPLETED", record.error_message
    result = client.get(f"/api/v1/data/download-jobs/{job_id}").json()["data"]
    assert result["progress"] == 100 and result["status"] == "COMPLETED"
    assert service.scan_polars("EURUSD").collect().height == 1
    assert service.logs.list_active()["data"] == []


def test_pause_and_resume_control_worker_before_publication(downloads):
    client, jobs, service, provider = downloads
    provider.wait = True
    job_id = _start(client)
    assert provider.entered.wait(5)
    paused = client.post(f"/api/v1/data/download-jobs/{job_id}/pause", json={})
    assert paused.json()["data"]["status"] == "PAUSED"
    provider.release.set()
    assert service.catalog_record("EURUSD", "M1")["bars"] == 0
    assert (
        client.post(f"/api/v1/data/download-jobs/{job_id}/resume", json={}).status_code
        == 200
    )
    assert jobs.wait_for_job(job_id, timeout=10).status == "COMPLETED"


def test_stop_prevents_publication_and_failure_is_not_completion(downloads):
    client, jobs, service, provider = downloads
    provider.wait = True
    job_id = _start(client)
    assert provider.entered.wait(5)
    assert (
        client.post(f"/api/v1/data/download-jobs/{job_id}/stop", json={}).status_code
        == 200
    )
    provider.release.set()
    assert jobs.wait_for_job(job_id, timeout=10).status == "CANCELLED"
    assert service.catalog_record("EURUSD", "M1")["bars"] == 0
    provider.wait = False
    provider.fail = True
    failed = _start(client)
    assert jobs.wait_for_job(failed, timeout=10).status == "FAILED"
    assert service.catalog_record("EURUSD", "M1")["bars"] == 0


def test_download_request_rejects_invalid_targets_and_modes(downloads):
    client, _, _, _ = downloads
    for body in [
        {"provider": "other"},
        {"provider": "dukascopy"},
        {
            "provider": "dukascopy",
            "symbol": "EURUSD",
            "date_from": "bad",
            "date_to": "2025-01-01",
        },
    ]:
        assert (
            client.post("/api/v1/data/providers/download", json=body).status_code == 422
        )
