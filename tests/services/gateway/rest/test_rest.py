"""Functional tests for gateway REST service and cursor pagination."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from app.services.gateway.application import (
    ApplicationConfig,
    ApplicationService,
)
from app.services.gateway.rest import (
    RestConfig,
    RestGatewayService,
)
from fastapi import APIRouter


def test_rest_service_receipts_and_pagination() -> None:
    """Test job receipt generation and deterministic cursor pagination."""
    app_service = ApplicationService(ApplicationConfig())
    rest_service = RestGatewayService(app_service, RestConfig(default_page_limit=5))

    # 1. Job receipt factory
    receipt = rest_service.create_job_receipt(
        job_id="job-build-123",
        action="build_strategies",
        correlation_id="corr-xyz",
    )
    assert receipt.job_id == "job-build-123"
    assert receipt.status == "accepted"
    assert receipt.status_url == "/api/v1/jobs/job-build-123"
    assert receipt.stream_url == "/websocket/updates"
    assert receipt.correlation_id == "corr-xyz"

    # 2. Cursor pagination
    items = [f"strat-{i}" for i in range(12)]

    # Page 1
    page1 = rest_service.paginate(items, cursor=None, limit=5)
    assert len(page1.items) == 5
    assert page1.items == tuple(f"strat-{i}" for i in range(5))
    assert page1.total_items == 12
    assert page1.next_cursor is not None

    # Page 2
    page2 = rest_service.paginate(items, cursor=page1.next_cursor, limit=5)
    assert len(page2.items) == 5
    assert page2.items == tuple(f"strat-{i}" for i in range(5, 10))
    assert page2.next_cursor is not None

    # Page 3 (final)
    page3 = rest_service.paginate(items, cursor=page2.next_cursor, limit=5)
    assert len(page3.items) == 2
    assert page3.items == ("strat-10", "strat-11")
    assert page3.next_cursor is None

    # Register sub-resource
    sub_router = APIRouter(prefix="/items")

    @sub_router.get("")
    def get_items() -> dict[str, list[str]]:
        return {"items": ["a", "b", "c"]}

    rest_service.register_resource(sub_router)

    async def _test() -> None:
        transport = httpx.ASGITransport(app=app_service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/items")
            assert resp.status_code == 200
            assert resp.json() == {"items": ["a", "b", "c"]}

            resp_schema = await client.get("/api/v1/openapi-schema")
            assert resp_schema.status_code == 200
            assert "paths" in resp_schema.json()

    asyncio.run(_test())


def test_rest_service_register_resource_validation() -> None:
    """Verify register_resource raises TypeError for non-APIRouter resources."""
    import pytest

    app_service = ApplicationService(ApplicationConfig())
    rest_service = RestGatewayService(app_service)

    with pytest.raises(TypeError, match="Resource must be an APIRouter instance"):
        rest_service.register_resource("not-a-router")


def test_rest_idempotency_and_jobs(tmp_path: Path) -> None:
    """Verify REST job submission with idempotency caching and duplicate replay."""
    from app.services.persistence.database import (
        DatabaseConfig,
        DatabaseServiceImpl,
    )
    from app.services.persistence.gateway import (
        GatewayPersistenceService,
    )

    db = DatabaseServiceImpl(DatabaseConfig(database_path=tmp_path / "rest_idem.db"))
    pers = GatewayPersistenceService(db)
    pers.initialize_schema()

    app_service = ApplicationService(ApplicationConfig())
    _rest_service = RestGatewayService(app_service, persistence=pers)

    async def _test() -> None:
        transport = httpx.ASGITransport(app=app_service.get_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # 1. First request with Idempotency-Key
            resp1 = await client.post(
                "/api/v1/jobs",
                json={"action": "build_strategies", "params": {"count": 10}},
                headers={"Idempotency-Key": "idem-uuid-001"},
            )
            assert resp1.status_code == 202
            data1 = resp1.json()
            assert data1["status"] == "accepted"
            job_id1 = data1["job_id"]

            # 2. Duplicate request with identical Idempotency-Key returns cached response
            resp2 = await client.post(
                "/api/v1/jobs",
                json={"action": "build_strategies", "params": {"count": 10}},
                headers={"Idempotency-Key": "idem-uuid-001"},
            )
            assert resp2.status_code == 202
            data2 = resp2.json()
            assert data2["job_id"] == job_id1

            # 3. New request without Idempotency-Key returns fresh job_id
            resp3 = await client.post(
                "/api/v1/jobs",
                json={"action": "build_strategies", "params": {"count": 10}},
            )
            assert resp3.status_code == 202
            data3 = resp3.json()
            assert data3["job_id"] != job_id1

    asyncio.run(_test())
