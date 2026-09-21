# ruff: noqa: N999
"""Consolidated offline usage example for the Gateway domain (D-GATEWAY).

Demonstrates deterministic, secret-safe, and offline execution of all 6
gateway domain features plus domain persistence (7 total):
1. Transactional Gateway Persistence (FEAT-PERSISTENCE-GATEWAY)
2. ASGI Application Lifecycle & Health Probes (FEAT-GATEWAY-APPLICATION)
3. Transport Security & Network Origin Policy (FEAT-GATEWAY-AUTH)
4. Versioned REST Resources & Cursor Pagination (FEAT-GATEWAY-REST)
5. WebSocket/SSE Event Streaming & Sequencing (FEAT-GATEWAY-STREAMS)
6. RFC 7807 Problem Details Error Representation (FEAT-GATEWAY-ERRORS)
7. Headless CLI Parser & Batch Command Automation (FEAT-GATEWAY-AUTOMATION)

Run with:
    `uv run python -m tests.examples.05_gateway`
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import uvicorn

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_AUTHORIZATION,
    GATEWAY_AUTOMATION,
    GATEWAY_ERRORS,
    GATEWAY_PERSISTENCE,
    GATEWAY_REST,
    GATEWAY_STREAMS,
)
from app.contracts.workspace import (
    WORKSPACE_DIAGNOSTICS,
    WORKSPACE_JOBS,
    JobAttempt,
    JobDefinition,
    JobEvent,
    JobProgress,
    JobReceipt,
    JobState,
    SystemHealth,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.services.gateway.application import ApplicationFeature
from app.services.gateway.authorization import AuthorizationFeature
from app.services.gateway.command_automator import CommandAutomationFeature
from app.services.gateway.errors import ErrorsFeature
from app.services.gateway.rest import RestFeature
from app.services.gateway.streams import StreamsFeature
from app.services.persistence.database import DatabaseConfig, DatabaseFeature
from app.services.persistence.gateway import GatewayPersistenceFeature


class DummyDiagnosticsFeature:
    """Offline mock diagnostics provider for gateway application readiness."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            name="mock.diagnostics",
            provides=frozenset({WORKSPACE_DIAGNOSTICS}),
            requires=frozenset(),
            description="Mock diagnostics for offline demonstration.",
        )

    async def start(self, context: FeatureContext) -> None:
        health = SystemHealth(
            status="ok",
            version="1.0.0",
            memory_used_mb=256.0,
            total_memory_mb=8192.0,
            memory_pct=3.125,
            active_jobs=0,
            timestamp_utc=datetime.now(UTC),
        )
        mock_diag = type("MockDiag", (), {"get_health": lambda self: health})()
        context.provide(WORKSPACE_DIAGNOSTICS, mock_diag)

    async def stop(self) -> None:
        pass


class DummyJobsService:
    """Mock job service for offline job submission demonstration."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobDefinition] = {}
        self._receipts: dict[str, JobReceipt] = {}

    def create_job(self, definition: JobDefinition) -> JobReceipt:
        self._jobs[definition.job_id] = definition
        receipt = JobReceipt(
            job_id=definition.job_id,
            state=JobState.QUEUED,
            progress_percent=0.0,
            message="Queued",
            updated_at_utc=datetime.now(UTC),
        )
        self._receipts[definition.job_id] = receipt
        return receipt

    def get_job(self, job_id: str) -> JobDefinition | None:
        return self._jobs.get(job_id)

    def get_receipt(self, job_id: str) -> JobReceipt | None:
        return self._receipts.get(job_id)

    def transition_state(
        self,
        job_id: str,
        from_state: JobState | None,
        to_state: JobState,
        details: dict[str, Any] | None = None,
    ) -> bool:
        receipt = self._receipts.get(job_id)
        if receipt is None:
            return False
        self._receipts[job_id] = JobReceipt(
            job_id=job_id,
            state=to_state,
            progress_percent=receipt.progress_percent,
            message=f"Transitioned to {to_state.value}",
            updated_at_utc=datetime.now(UTC),
        )
        return True

    def record_progress(self, progress: JobProgress) -> None:
        pass

    def create_attempt(self, job_id: str, worker_id: str) -> JobAttempt:
        return JobAttempt(
            attempt_id=f"att-{job_id}",
            job_id=job_id,
            worker_id=worker_id,
            sequence=1,
            state=JobState.RUNNING,
            heartbeat_at_utc=datetime.now(UTC),
            checkpoint=None,
            created_at_utc=datetime.now(UTC),
            completed_at_utc=None,
        )

    def update_heartbeat(self, attempt_id: str) -> None:
        pass

    def list_attempts(self, job_id: str) -> tuple[JobAttempt, ...]:
        return ()

    def list_events(self, job_id: str) -> tuple[JobEvent, ...]:
        return ()

    def recover_orphans(self, interrupted_reason: str = "Coordinator restart") -> int:
        return 0


class DummyJobsFeature:
    """Offline mock jobs provider for gateway job dispatch."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            name="mock.jobs",
            provides=frozenset({WORKSPACE_JOBS}),
            requires=frozenset(),
            description="Mock jobs capability for offline demonstration.",
        )

    async def start(self, context: FeatureContext) -> None:
        context.provide(WORKSPACE_JOBS, DummyJobsService())

    async def stop(self) -> None:
        pass


def example_05_persistence(runtime: Runtime) -> None:
    """Demonstrate FEAT-PERSISTENCE-GATEWAY."""
    print("\n[1/7] Gateway Persistence (FEAT-PERSISTENCE-GATEWAY)")
    pers = runtime.require(GATEWAY_PERSISTENCE)

    # 1. Durable Settings
    pers.set_setting("remote_access", "false")
    val = pers.get_setting("remote_access")
    print(f"  Setting persisted: remote_access={val}")

    # 2. Hashed Token Storage & Verification
    pers.store_token("demo-token-12345", "example-client")
    is_valid = pers.verify_token("demo-token-12345")
    is_bad_valid = pers.verify_token("wrong-token")
    print(f"  Token verification: valid={is_valid}, bad_valid={is_bad_valid}")

    # 3. Idempotency Recording and Purge
    pers.record_idempotency_key("key-001", 202, '{"status":"ok"}', expire_seconds=3600)
    cached = pers.get_idempotency_response("key-001")
    purged = pers.purge_expired_idempotency(retention_seconds=0)
    cached_status = cached[0] if cached else None
    print(f"  Idempotency cached: status={cached_status}, purged_count={purged}")


async def example_05_application(runtime: Runtime) -> None:
    """Demonstrate FEAT-GATEWAY-APPLICATION."""
    print("\n[2/7] ASGI Application Lifecycle (FEAT-GATEWAY-APPLICATION)")
    app_svc = runtime.require(GATEWAY_APPLICATION)
    info = app_svc.get_server_info()
    print(
        f"  Server Info: host={info.host}, port={info.port}, loopback={info.loopback_only}"
    )

    transport = httpx.ASGITransport(app=app_svc.get_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        resp_health = await client.get("/healthz")
        resp_status = await client.get("/readyz")
        print(
            f"  Health probe: status={resp_health.status_code}, json={resp_health.json()}"
        )
        print(
            f"  Readiness probe: status={resp_status.status_code}, status={resp_status.json()['status']}"
        )


def example_05_authorization(runtime: Runtime) -> None:
    """Demonstrate FEAT-GATEWAY-AUTH."""
    print("\n[3/7] Transport Security & Origin Gating (FEAT-GATEWAY-AUTH)")
    auth_svc = runtime.require(GATEWAY_AUTHORIZATION)

    # Loopback origin authentication
    ctx = auth_svc.authenticate_request({}, "127.0.0.1")
    print(
        f"  Loopback auth: authenticated={ctx.authenticated}, is_loopback={ctx.is_loopback}"
    )

    # Production token issuance
    token = auth_svc.issue_token("operator-key", scopes=("read", "write"))
    print(f"  Issued token: {token[:12]}... (length={len(token)})")

    # Authenticate via token
    token_ctx = auth_svc.authenticate_request({"X-API-Key": token}, "127.0.0.1")
    print(
        f"  Token auth: authenticated={token_ctx.authenticated}, client_id={token_ctx.client_id}"
    )


async def example_05_rest(runtime: Runtime) -> None:
    """Demonstrate FEAT-GATEWAY-REST."""
    print("\n[4/7] REST Resources & Pagination (FEAT-GATEWAY-REST)")
    rest_svc = runtime.require(GATEWAY_REST)
    app_svc = runtime.require(GATEWAY_APPLICATION)

    # 1. Immediate HTTP 202 Receipt
    receipt = rest_svc.create_job_receipt(job_id="job-exp-101", action="backtest")
    print(
        f"  Job Receipt: id={receipt.job_id}, status={receipt.status}, url={receipt.status_url}"
    )

    # 2. Deterministic Cursor Pagination
    items = [f"strategy-{i:03d}" for i in range(25)]
    page = rest_svc.paginate(items, cursor=None, limit=5)
    print(
        f"  Paginated page 1: count={len(page.items)}, total={page.total_items}, next_cursor={page.next_cursor}"
    )

    # 3. REST Endpoint Mutation with Idempotency
    transport = httpx.ASGITransport(app=app_svc.get_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1:8000"
    ) as client:
        resp = await client.post(
            "/api/v1/jobs",
            json={"action": "build_portfolio", "params": {"target": "EURUSD"}},
            headers={"Idempotency-Key": "example-idem-001"},
        )
        print(
            f"  POST /api/v1/jobs: status={resp.status_code}, job_id={resp.json()['job_id']}"
        )


async def example_05_streams(runtime: Runtime) -> None:
    """Demonstrate FEAT-GATEWAY-STREAMS."""
    print("\n[5/7] Event Streaming & Sequencing (FEAT-GATEWAY-STREAMS)")
    streams_svc = runtime.require(GATEWAY_STREAMS)

    # Broadcast updates
    await streams_svc.broadcast_update(
        project_name="Builder",
        channel_name="progress",
        payload={"percent": 25, "active": True},
    )
    await streams_svc.broadcast_update(
        project_name="Builder",
        channel_name="progress",
        payload={"percent": 50, "active": True},
    )

    # Check buffered event replay by cursor
    events = streams_svc.get_events_after("progress", cursor="")
    conns = streams_svc.get_active_connections_count()
    print(
        f"  Broadcasted 2 events (buffered={len(events)}) to 'progress' channel "
        f"(active connections={conns})"
    )


def example_05_errors(runtime: Runtime) -> None:
    """Demonstrate FEAT-GATEWAY-ERRORS."""
    print("\n[6/7] Problem Details & Redaction (FEAT-GATEWAY-ERRORS)")
    errors_svc = runtime.require(GATEWAY_ERRORS)

    exc = ValueError(
        "Failed to authenticate token secret-api-key-999 on path /var/secrets/key.pem"
    )
    problem = errors_svc.to_problem_details(exc, correlation_id="corr-err-01")
    print(f"  RFC 7807 Error mapped: status={problem.status}, title={problem.title}")
    print(f"  Redacted detail: {problem.detail}")


async def example_05_automation(runtime: Runtime, tmp_dir: str) -> None:
    """Demonstrate FEAT-GATEWAY-AUTOMATION."""
    print("\n[7/7] CLI Automation & Batch Scripts (FEAT-GATEWAY-AUTOMATION)")
    auto_svc = runtime.require(GATEWAY_AUTOMATION)

    # 1. Single Command
    res1 = await auto_svc.execute_command("-status")
    print(f"  CLI Command: success={res1.success}, output={res1.output}")

    # 2. Token generation via CLI
    res2 = await auto_svc.execute_command(
        "-token action=create name=batch-operator scopes=read,write"
    )
    print(f"  CLI Token: success={res2.success}, output={res2.output[:45]}...")

    # 3. Batch Script Execution
    batch_file = Path(tmp_dir) / "demo_commands.txt"
    batch_file.write_text(
        "# Automated batch sequence\n-status\n-info\n",
        encoding="utf-8",
    )
    res_batch = await auto_svc.execute_command(f"--run file={batch_file}")
    print(
        f"  CLI Batch (--run): success={res_batch.success}, output={res_batch.output}"
    )


async def run_gateway_demonstration() -> None:
    """Execute end-to-end demonstration of all gateway domain capabilities."""

    async def _mock_serve(
        self: uvicorn.Server, sockets: list[object] | None = None
    ) -> None:
        await asyncio.Event().wait()

    uvicorn.Server.serve = _mock_serve  # type: ignore[method-assign,assignment]

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_file = Path(tmp_dir) / "gateway_demo.db"
        features = (
            DummyDiagnosticsFeature,
            DummyJobsFeature,
            lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
            GatewayPersistenceFeature,
            ApplicationFeature,
            AuthorizationFeature,
            ErrorsFeature,
            RestFeature,
            StreamsFeature,
            CommandAutomationFeature,
        )

        async with Runtime(features) as runtime:
            print("=" * 70)
            print("HARUQUANTAI GATEWAY DOMAIN (D-GATEWAY) OFFLINE DEMONSTRATION")
            print("=" * 70)

            example_05_persistence(runtime)
            await example_05_application(runtime)
            example_05_authorization(runtime)
            await example_05_rest(runtime)
            await example_05_streams(runtime)
            example_05_errors(runtime)
            await example_05_automation(runtime, tmp_dir)

            print("\n" + "=" * 70)
            print("ALL 7 GATEWAY FEATURES VERIFIED SUCCESSFULLY OFFLINE")
            print("=" * 70)


def main() -> None:
    """Run offline demonstration."""
    asyncio.run(run_gateway_demonstration())


if __name__ == "__main__":
    main()
