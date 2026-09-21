"""Functional tests for RFC 7807 problem details error mapping."""

from __future__ import annotations

import asyncio

import httpx
from app.contracts.gateway import (
    AuthenticationError,
    InvalidPayloadError,
    ProblemDetails,
    ProblemDetailsError,
    RateLimitError,
)
from app.services.gateway.errors import (
    ErrorsConfig,
    ProblemMapperService,
)
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException


def test_problem_details_transformation() -> None:
    """Verify exception mapping into standard RFC 7807 problem details."""
    service = ProblemMapperService(ErrorsConfig())

    # 1. ProblemDetailsError wraps directly
    pd = ProblemDetails(
        type="https://errors.haruquant.ai/custom",
        title="Custom",
        status=400,
        detail="Custom error",
    )
    res1 = service.to_problem_details(ProblemDetailsError(pd))
    assert res1 == pd

    # 2. AuthenticationError -> 401
    res2 = service.to_problem_details(AuthenticationError("Bad credentials"))
    assert res2.status == 401
    assert res2.title == "Authentication Failed"
    assert res2.detail == "Bad credentials"

    # 3. RateLimitError -> 429
    res3 = service.to_problem_details(RateLimitError("Too fast"))
    assert res3.status == 429
    assert res3.title == "Rate Limit Exceeded"

    # 4. InvalidPayloadError -> 422
    res4 = service.to_problem_details(InvalidPayloadError("Bad JSON"))
    assert res4.status == 422
    assert res4.title == "Invalid Request Payload"

    # 5. HTTPException -> matching status
    res5 = service.to_problem_details(
        StarletteHTTPException(status_code=404, detail="Not Found")
    )
    assert res5.status == 404
    assert res5.detail == "Not Found"

    # 6. Unhandled exception -> 500 with redaction
    res6 = service.to_problem_details(RuntimeError("secret_db_password_in_traceback"))
    assert res6.status == 500
    assert "secret_db_password" not in res6.detail
    assert res6.detail == "An unexpected internal server error occurred"


def test_fastapi_exception_handlers_integration() -> None:
    """Verify registered exception handlers return application/problem+json."""
    app = FastAPI()
    service = ProblemMapperService(ErrorsConfig())
    service.register_handlers(app)

    @app.get("/trigger-auth")
    def trigger_auth() -> None:
        raise AuthenticationError("No token provided")

    @app.get("/trigger-500")
    def trigger_500() -> None:
        raise RuntimeError("Internal crash")

    async def _test() -> None:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # 401
            resp1 = await client.get(
                "/trigger-auth", headers={"X-Correlation-ID": "req-999"}
            )
            assert resp1.status_code == 401
            assert resp1.headers["content-type"] == "application/problem+json"
            data1 = resp1.json()
            assert data1["status"] == 401
            assert data1["correlation_id"] == "req-999"

            # 500
            resp2 = await client.get("/trigger-500")
            assert resp2.status_code == 500
            assert resp2.headers["content-type"] == "application/problem+json"
            data2 = resp2.json()
            assert data2["status"] == 500
            assert "crash" not in data2["detail"]

    asyncio.run(_test())
