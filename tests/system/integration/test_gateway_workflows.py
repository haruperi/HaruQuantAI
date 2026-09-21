"""System integration tests for Gateway cross-domain workflows (WF-GATEWAY-JOB).

Workflow:
    WF-GATEWAY-JOB: End-to-end asynchronous job submission, idempotency caching,
    durable workspace job transition, and real-time streaming progress.

Acceptance:
    ATW-GATEWAY-JOB-001
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_AUTHORIZATION,
    GATEWAY_REST,
    GATEWAY_STREAMS,
)
from app.contracts.workspace import (
    WORKSPACE_JOBS,
    JobState,
)
from app.kernel.bootstrapper import Runtime
from app.services.gateway.application import (
    ApplicationConfig,
    ApplicationFeature,
)
from app.services.gateway.authorization import (
    AuthorizationConfig,
    AuthorizationFeature,
)
from app.services.gateway.rest import (
    RestConfig,
    RestFeature,
)
from app.services.gateway.streams import (
    StreamsConfig,
    StreamsFeature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
)
from app.services.persistence.gateway import (
    GatewayPersistenceConfig,
    GatewayPersistenceFeature,
)
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
)
from app.services.workspace.diagnostics import feature as diagnostics_feature
from app.services.workspace.jobs import feature as jobs_feature


@pytest.mark.anyio
async def test_wf_gateway_job_submission_and_streaming(tmp_path: Path) -> None:
    """ATW-GATEWAY-JOB-001: Test end-to-end job submission, idempotency, and streaming."""
    gateway_db_path = tmp_path / "gateway_wf.db"
    workspace_db_path = str(tmp_path / "workspace_wf.db")

    def _database_factory() -> DatabaseFeature:
        return DatabaseFeature(DatabaseConfig(database_path=gateway_db_path))

    def _gateway_persistence_factory() -> GatewayPersistenceFeature:
        return GatewayPersistenceFeature(GatewayPersistenceConfig())

    def _workspace_persistence_factory() -> WorkspacePersistenceFeature:
        return WorkspacePersistenceFeature(
            WorkspacePersistenceConfig(db_path=workspace_db_path, wal_mode=True)
        )

    def _auth_factory() -> AuthorizationFeature:
        return AuthorizationFeature(
            AuthorizationConfig(
                token_auth_enabled=True,
                remote_access_allowed=True,
                loopback_hosts=frozenset({"127.0.0.1", "localhost", "test"}),
            )
        )

    def _app_factory() -> ApplicationFeature:
        return ApplicationFeature(ApplicationConfig(port=8099))

    def _rest_factory() -> RestFeature:
        return RestFeature(RestConfig())

    def _streams_factory() -> StreamsFeature:
        return StreamsFeature(StreamsConfig())

    features = (
        _database_factory,
        _gateway_persistence_factory,
        _workspace_persistence_factory,
        diagnostics_feature,
        jobs_feature,
        _auth_factory,
        _app_factory,
        _rest_factory,
        _streams_factory,
    )

    async with Runtime(features) as runtime:
        auth_service = runtime.require(GATEWAY_AUTHORIZATION)
        app_service = runtime.require(GATEWAY_APPLICATION)
        runtime.require(GATEWAY_REST)
        streams_service = runtime.require(GATEWAY_STREAMS)
        jobs_service = runtime.require(WORKSPACE_JOBS)

        # 1. Issue a production token via the authorization service
        token = auth_service.issue_token("workflow-runner", scopes=("read", "write"))
        assert isinstance(token, str) and len(token) > 20

        transport = httpx.ASGITransport(app=app_service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "wf-idem-key-100",
                "X-Correlation-ID": "corr-wf-alpha",
            }
            job_payload = {
                "action": "backtest_generation",
                "params": {
                    "project": "Alpha101",
                    "symbol": "EURUSD",
                    "timeframe": "H1",
                },
            }

            # 2. Submit job via REST gateway POST /api/v1/jobs
            resp = await client.post(
                "/api/v1/jobs",
                json=job_payload,
                headers=headers,
            )
            assert resp.status_code == 202
            receipt_data = resp.json()
            assert receipt_data["status"] == "accepted"
            assert receipt_data["correlation_id"] == "corr-wf-alpha"
            job_id = receipt_data["job_id"]

            # 3. Verify cross-domain dispatch into WORKSPACE_JOBS capability
            durable_def = jobs_service.get_job(job_id)
            assert durable_def is not None
            assert durable_def.operation == "backtest_generation"
            assert durable_def.payload["symbol"] == "EURUSD"

            # 4. Progress job state in workspace: QUEUED -> RUNNING
            jobs_service.transition_state(
                job_id=job_id,
                from_state=None,
                to_state=JobState.RUNNING,
            )
            receipt = jobs_service.get_receipt(job_id)
            assert receipt is not None
            assert receipt.state == JobState.RUNNING

            # 5. Broadcast progress update through EventStreamGateway
            await streams_service.broadcast_update(
                project_name="Alpha101",
                channel_name="jobs",
                payload={"job_id": job_id, "percent": 50, "status": "running"},
            )

            # Verify stream event sequencing and cursor generation
            events = streams_service.get_events_after("jobs", cursor="")
            assert len(events) >= 1
            # Broadcast with cursor
            await streams_service.broadcast_update(
                project_name="Alpha101",
                channel_name="jobs",
                payload={"job_id": job_id, "percent": 100, "status": "completed"},
            )

            # 6. Verify Idempotency replay on duplicate REST submission
            resp_dup = await client.post(
                "/api/v1/jobs",
                json=job_payload,
                headers=headers,
            )
            assert resp_dup.status_code == 202
            dup_data = resp_dup.json()
            assert dup_data["job_id"] == job_id
            assert dup_data["correlation_id"] == "corr-wf-alpha"

            # 7. Finalize job in workspace: RUNNING -> SUCCEEDED
            jobs_service.transition_state(
                job_id=job_id,
                from_state=JobState.RUNNING,
                to_state=JobState.SUCCEEDED,
            )
            final_receipt = jobs_service.get_receipt(job_id)
            assert final_receipt is not None
            assert final_receipt.state == JobState.SUCCEEDED
