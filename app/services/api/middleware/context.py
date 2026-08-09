"""Request context middleware for API boundary requests."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final, cast, override

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.services.api.contracts.catalog import (
    ROUTE_CONTRACT_REGISTRY,
    RouteContractRegistry,
)
from app.utils import generate_id, get_auth_context_type, utc_now, validate_id

if TYPE_CHECKING:
    from app.services.api.contracts.models import RouteContract

CANONICAL_CONTEXT_STATE_KEY: Final = "api_request_context"
CANONICAL_AUTH_STATE_KEY: Final = "api_auth_context"
_REQUEST_ID_HEADER: Final = "x-request-id"
_CORRELATION_ID_HEADER: Final = "x-correlation-id"
_MAX_IDENTIFIER_LENGTH: Final = 128
_MAX_PATH_LENGTH: Final = 2048
_ID_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_VALIDATION_ERROR_CODE: Final = "VALIDATION_ERROR"
_AUTHENTICATION_REQUIRED_CODE: Final = "AUTHENTICATION_REQUIRED"
_IDEMPOTENCY_KEY_REQUIRED_CODE: Final = "IDEMPOTENCY_KEY_REQUIRED"
type AuthContext = Any


@dataclass(frozen=True, slots=True)
class _CanonicalRequestContext:
    """Canonical request context captured before route handling."""

    request_id: str
    correlation_id: str
    method: str
    path: str
    route_id: str | None
    route_intent: str
    auth_required: bool
    permission: str | None
    governance_scope: str
    actor_id: str | None
    tenant: str | None
    auth_context: AuthContext | None = None
    created_at: datetime = field(default_factory=utc_now)


AuthContextFactory = Callable[[Request], object]


def _normalize_identifier(value: str) -> str:
    """Normalize and validate an identifier-like header value.

    Returns:
        The validated, bounded result.

    Raises:
        HTTPException: If the declared validation fails.
    """
    if len(value) > _MAX_IDENTIFIER_LENGTH:
        raise HTTPException(status_code=400, detail=_VALIDATION_ERROR_CODE)
    normalized = value.strip()
    if not _ID_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=400, detail=_VALIDATION_ERROR_CODE)
    return normalized


def _build_request_id(value: str | None = None) -> str:
    """Build or validate a request identifier.

    Returns:
        The validated, bounded result.

    Raises:
        HTTPException: If a caller-supplied request identifier is invalid.
    """
    if value is None:
        return generate_id("req")
    normalized = _normalize_identifier(value)
    try:
        return validate_id(normalized, expected_prefix="req")
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=_VALIDATION_ERROR_CODE,
        ) from error


def _build_correlation_id(value: str | None = None) -> str:
    """Build or validate a correlation identifier.

    Returns:
        The validated, bounded result.
    """
    if value is None:
        return generate_id("cor")
    return _normalize_identifier(value)


def _normalize_path(value: str) -> str:
    """Normalize one request path for contract lookup.

    Returns:
        The validated, bounded result.

    Raises:
        HTTPException: If the declared validation fails.
    """
    if not value or not value.startswith("/"):
        raise HTTPException(status_code=400, detail=_VALIDATION_ERROR_CODE)
    normalized = value.rstrip("/")
    if not normalized:
        normalized = "/"
    if len(normalized) > _MAX_PATH_LENGTH:
        raise HTTPException(status_code=400, detail=_VALIDATION_ERROR_CODE)
    return normalized


def _resolve_route_contract(
    contracts: RouteContractRegistry,
    method: str,
    path: str,
) -> RouteContract | None:
    """Return one matching route contract or ``None``."""
    return contracts.get(method, _normalize_path(path))


def _classify_route_intent(contract: RouteContract | None) -> str:
    """Classify a route contract into a bounded intent label.

    Returns:
        The validated, bounded result.
    """
    if contract is None:
        return "unknown"
    if contract.auth_required:
        return "protected"
    if contract.governance_scope != "none":
        return "governed"
    return "public"


def _default_auth_context_provider(_: Request) -> AuthContext:
    """Fail closed unless composition injects an authenticated context resolver."""
    from app.services.api.identity.authorization import _raise_authentication_required

    _raise_authentication_required()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach validated request IDs, route intent, and optional auth context."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        route_contract_registry: RouteContractRegistry | None = None,
        auth_context_provider: AuthContextFactory | None = None,
        request_id_header: str = _REQUEST_ID_HEADER,
        correlation_id_header: str = _CORRELATION_ID_HEADER,
    ) -> None:
        """Create one request-context middleware instance."""
        super().__init__(app)
        self._route_contracts = route_contract_registry or ROUTE_CONTRACT_REGISTRY
        self._auth_context_provider = (
            auth_context_provider or _default_auth_context_provider
        )
        self._request_id_header = request_id_header
        self._correlation_id_header = correlation_id_header

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Attach request context before delegated handling and pass it to state.

        Returns:
            The validated, bounded result.
        """
        try:
            request_id = _build_request_id(
                request.headers.get(self._request_id_header),
            )
            correlation_id = _build_correlation_id(
                request.headers.get(self._correlation_id_header),
            )
        except HTTPException as error:
            return JSONResponse(
                content={"detail": error.detail},
                status_code=error.status_code,
            )
        path = _normalize_path(request.url.path)
        method = request.method.upper()
        route_contract = _resolve_route_contract(
            self._route_contracts,
            method,
            path,
        )
        preliminary_context = _CanonicalRequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            method=method,
            path=path,
            route_id=route_contract.route_id if route_contract else None,
            route_intent=_classify_route_intent(route_contract),
            auth_required=route_contract.auth_required if route_contract else False,
            permission=route_contract.permission if route_contract else None,
            governance_scope=(
                route_contract.governance_scope if route_contract else "none"
            ),
            actor_id=None,
            tenant=None,
        )
        setattr(request.state, CANONICAL_CONTEXT_STATE_KEY, preliminary_context)
        if (
            route_contract is not None
            and route_contract.idempotency_policy == "required"
            and not request.headers.get("idempotency-key")
        ):
            return JSONResponse(
                content={"detail": _IDEMPOTENCY_KEY_REQUIRED_CODE},
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        if route_contract is not None and route_contract.auth_required:
            try:
                auth_context = self._auth_context_provider(request)
            except HTTPException as error:
                return JSONResponse(
                    content={"detail": error.detail},
                    status_code=error.status_code,
                )
            if not isinstance(auth_context, get_auth_context_type()):
                return JSONResponse(
                    content={"detail": _AUTHENTICATION_REQUIRED_CODE},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
            validated_auth = cast("AuthContext", auth_context)
            actor_id = validated_auth.principal_id
            tenant = validated_auth.tenant_or_environment
            auth_context = validated_auth
        else:
            auth_context = None
            actor_id = None
            tenant = None

        request_context = _CanonicalRequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            method=method,
            path=path,
            route_id=route_contract.route_id if route_contract else None,
            route_intent=_classify_route_intent(route_contract),
            auth_required=route_contract.auth_required if route_contract else False,
            permission=route_contract.permission if route_contract else None,
            governance_scope=route_contract.governance_scope
            if route_contract
            else "none",
            actor_id=actor_id,
            tenant=tenant,
            auth_context=auth_context,
        )
        setattr(request.state, CANONICAL_CONTEXT_STATE_KEY, request_context)
        setattr(request.state, CANONICAL_AUTH_STATE_KEY, auth_context)

        response = await call_next(request)
        response.headers[self._request_id_header] = request_id
        response.headers[self._correlation_id_header] = correlation_id
        return response


def build_request_context_middleware(
    app: ASGIApp,
    *,
    route_contract_registry: RouteContractRegistry | None = None,
    auth_context_provider: AuthContextFactory | None = None,
    request_id_header: str = _REQUEST_ID_HEADER,
    correlation_id_header: str = _CORRELATION_ID_HEADER,
) -> object:
    """Build a request-context middleware instance from explicit constructor inputs.

    Returns:
        The validated, bounded result.
    """
    return RequestContextMiddleware(
        app,
        route_contract_registry=route_contract_registry,
        auth_context_provider=auth_context_provider,
        request_id_header=request_id_header,
        correlation_id_header=correlation_id_header,
    )
