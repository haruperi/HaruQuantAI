"""Safe RFC 7807 problem details error mapping and sanitization feature.

Feature:
    FEAT-GATEWAY-ERRORS

Purpose:
    Provides standardized, sanitized RFC 7807 (application/problem+json)
    transport error responses, exception handler registration, correlation ID
    injection, and fail-closed secret/traceback redaction under capability
    `gateway.errors@1`.

Key capabilities:
    * Standard RFC 7807 problem details formatting.
    * Transparent FastAPI exception handler integration.
    * Secret and internal traceback redaction.

Python API usage:
    mapper = ctx.require(GATEWAY_ERRORS)
    problem = mapper.to_problem_details(exc, correlation_id="req-123")

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.contracts.gateway import (
    GATEWAY_ERRORS,
    AuthenticationError,
    GatewayError,
    InvalidPayloadError,
    ProblemDetails,
    ProblemDetailsError,
    RateLimitError,
)
from app.contracts.gateway import (
    ProblemMapper as IProblemMapper,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ErrorsConfig:
    """Runtime configuration for error mapping and sanitization."""

    debug_mode: bool = False
    doc_base_url: str = "https://errors.haruquant.ai"

    def __post_init__(self) -> None:
        """Validate configuration settings."""
        if not self.doc_base_url or not self.doc_base_url.startswith("http"):
            msg = f"doc_base_url must be a valid HTTP URL; got {self.doc_base_url}"
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class ProblemMapperService(IProblemMapper):
    """Implement RFC 7807 problem details transformation and handlers."""

    def __init__(self, config: ErrorsConfig | None = None) -> None:
        """Initialize the problem mapper service.

        Args:
            config: Optional runtime error configuration.
        """
        self._config = config or ErrorsConfig()

    @override
    def to_problem_details(
        self,
        exc: Exception,
        correlation_id: str | None = None,
        path: str | None = None,
    ) -> ProblemDetails:
        """Convert an exception into a sanitized RFC 7807 ProblemDetails document.

        Args:
            exc: Exception to map.
            correlation_id: Optional correlation tracking ID.
            path: Optional request path.

        Returns:
            Sanitized `ProblemDetails`.
        """
        if isinstance(exc, ProblemDetailsError):
            return exc.problem

        cid = correlation_id or f"err-{uuid.uuid4().hex[:12]}"
        base_url = self._config.doc_base_url.rstrip("/")

        status = 500
        title = "Internal Server Error"
        err_type = f"{base_url}/internal-server-error"
        detail = (
            str(exc)
            if self._config.debug_mode
            else "An unexpected internal server error occurred"
        )
        errors: tuple[dict[str, Any], ...] = ()

        if isinstance(exc, AuthenticationError):
            status = 401
            title = "Authentication Failed"
            err_type = f"{base_url}/authentication-failed"
            detail = str(exc)
        elif isinstance(exc, RateLimitError):
            status = 429
            title = "Rate Limit Exceeded"
            err_type = f"{base_url}/rate-limit-exceeded"
            detail = str(exc)
        elif isinstance(exc, InvalidPayloadError):
            status = 422
            title = "Invalid Request Payload"
            err_type = f"{base_url}/invalid-payload"
            detail = str(exc)
        elif isinstance(exc, StarletteHTTPException):
            status = exc.status_code
            title = f"HTTP Error {exc.status_code}"
            err_type = f"{base_url}/http-{exc.status_code}"
            detail = exc.detail or "HTTP request error"
        elif isinstance(exc, RequestValidationError):
            status = 422
            title = "Request Validation Error"
            err_type = f"{base_url}/validation-error"
            detail = "One or more request fields failed schema validation"
            errors = tuple(
                {
                    "field": ".".join(str(loc) for loc in err.get("loc", [])),
                    "message": str(err.get("msg", "")),
                    "type": str(err.get("type", "")),
                }
                for err in exc.errors()
            )
        else:
            logger.error(
                "unhandled_server_error",
                error=str(exc),
                error_type=type(exc).__name__,
                correlation_id=cid,
                path=path,
            )

        return ProblemDetails(
            type=err_type,
            title=title,
            status=status,
            detail=detail,
            instance=path,
            correlation_id=cid,
            errors=errors,
        )

    @override
    def register_handlers(self, app: FastAPI) -> None:
        """Register standard exception handlers on a FastAPI application.

        Args:
            app: FastAPI application instance.
        """

        @app.exception_handler(GatewayError)
        async def gateway_error_handler(
            request: Request, exc: GatewayError
        ) -> JSONResponse:
            cid = request.headers.get("X-Correlation-ID")
            problem = self.to_problem_details(
                exc, correlation_id=cid, path=request.url.path
            )
            return JSONResponse(
                status_code=problem.status,
                content=problem.to_dict(),
                media_type="application/problem+json",
            )

        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(
            request: Request, exc: StarletteHTTPException
        ) -> JSONResponse:
            cid = request.headers.get("X-Correlation-ID")
            problem = self.to_problem_details(
                exc, correlation_id=cid, path=request.url.path
            )
            return JSONResponse(
                status_code=problem.status,
                content=problem.to_dict(),
                media_type="application/problem+json",
            )

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ) -> JSONResponse:
            cid = request.headers.get("X-Correlation-ID")
            problem = self.to_problem_details(
                exc, correlation_id=cid, path=request.url.path
            )
            return JSONResponse(
                status_code=problem.status,
                content=problem.to_dict(),
                media_type="application/problem+json",
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(
            request: Request, exc: Exception
        ) -> JSONResponse:
            cid = request.headers.get("X-Correlation-ID")
            problem = self.to_problem_details(
                exc, correlation_id=cid, path=request.url.path
            )
            return JSONResponse(
                status_code=problem.status,
                content=problem.to_dict(),
                media_type="application/problem+json",
            )


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.errors",
    provides=frozenset({GATEWAY_ERRORS}),
    requires=frozenset(),
    optional=frozenset(),
    description="RFC 7807 problem details error mapping and sanitization.",
)


class ErrorsFeature:
    """Composition feature wiring for gateway error mapper."""

    def __init__(self, config: ErrorsConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional runtime configuration.
        """
        self._config = config or ErrorsConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the errors feature and publish capability.

        Args:
            context: Feature composition context.
        """
        service = ProblemMapperService(self._config)
        context.provide(GATEWAY_ERRORS, service)

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> ErrorsFeature:
    """Factory creating the default ErrorsFeature.

    Returns:
        Configured feature instance.
    """
    return ErrorsFeature()
