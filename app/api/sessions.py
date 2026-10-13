"""Host session lifecycle, authentication, and authorization REST API endpoints.

Description:
    Exposes FastAPI routes for logging into the host, inspecting current session
    details, revoking tokens, elevating distinct authority for high-risk actions,
    verifying token scopes, checking clean distribution installation integrity,
    and managing administrative account credentials.

Purpose:
    FEAT-API-SESSIONS: Dedicated REST API routing for session tokens, authentication,
    and security boundaries.

Key Capabilities:
    - FR-API-SESS-LIFECYCLE: HTTP routes for user login, verification, and revocation.
      Associated: `create_sessions_router()`, `SessionsRouter.login_endpoint()`
    - FR-API-SESS-AUTH: HTTP routes for authentication status and account
      credential update.
      Associated: `create_auth_router()`, `_create_account_router()`
      Logging: Emits INFO on account update; WARNING on invalid credentials.
    - FR-API-SESS-DEPENDENCIES: FastAPI request dependency resolving bearer tokens.
      Associated: `extract_bearer_token()`, `get_current_session()`,
      `make_require_session()`
      Logging: Rejects missing/malformed bearer headers with HTTP 401.

Python API Usage:
    ```python
    from app.api.sessions import create_auth_router, create_sessions_router
    from app.host.session import HostAuthentication, SessionManager

    manager = SessionManager()
    sessions_router = create_sessions_router(session_manager=manager)
    ```

CLI Usage:
    Session REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.host.logging import get_logger
from app.host.persistence import PersistenceError, RevisionConflictError
from app.host.response import StandardError, StandardResponse
from app.host.session import (
    EXPECTED_BEARER_PARTS,
    MIN_SESSION_MINUTES,
    AuthenticationError,
    DistinctAuthorityCoordinator,
    ElevationRequest,
    ElevationResponse,
    HostAuthentication,
    LoginCooldownError,
    LoginRequest,
    ScopeAuthorizer,
    ScopeCheckRequest,
    SecurityError,
    SessionContext,
    SessionExpiredError,
    SessionManager,
    SessionToken,
    get_global_authority_coordinator,
    get_global_authorizer,
    get_global_session_manager,
    get_tls_remote_deployment_proposal,
    verify_clean_installation,
    verify_domain_removal,
)
from app.host.settings import HostSettings

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "SessionsRouter",
    "_create_account_router",
    "create_auth_router",
    "create_sessions_router",
    "extract_bearer_token",
    "get_current_session",
    "make_require_session",
]

logger = get_logger(__name__)


def extract_bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Extract bearer token from Authorization header.

    Raises:
        HTTPException: 401 Unauthorized if missing or malformed.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    parts = authorization.split()
    if len(parts) != EXPECTED_BEARER_PARTS or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization scheme: expected 'Bearer <token>'.",
        )
    return parts[1]


def get_current_session(
    token: str = Depends(extract_bearer_token),
    mgr: SessionManager | None = None,
) -> SessionContext:
    """FastAPI dependency resolving the current active SessionContext."""
    resolved_mgr = mgr or get_global_session_manager()
    try:
        return resolved_mgr.verify_session(token)
    except SessionExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def make_require_session(
    authentication: HostAuthentication,
) -> Callable[[Request], None]:
    """Create a FastAPI route dependency enforcing valid session authentication."""

    def require_session(request: Request) -> None:
        token = extract_bearer_token(request.headers.get("authorization"))
        try:
            authentication.verify_session(token)
        except SecurityError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Host session required or expired.",
            ) from None

    return require_session


def _account_change_payload(body: Any) -> tuple[str, str, str, int, int]:
    """Validate account input without including passwords in error details."""
    names = {
        "username",
        "current_password",
        "new_password",
        "session_timeout_mins",
        "expected_revision",
    }
    if not isinstance(body, dict) or set(body) != names:
        raise ValueError("Invalid account request.")
    if any(
        not isinstance(body[key], str)
        for key in ("username", "current_password", "new_password")
    ):
        raise ValueError("Invalid account request.")
    if (
        type(body["expected_revision"]) is not int
        or type(body["session_timeout_mins"]) is not int
    ):
        raise ValueError("Invalid account request.")
    return (
        body["current_password"],
        body["username"],
        body["new_password"],
        body["session_timeout_mins"],
        body["expected_revision"],
    )


def _create_account_router(authentication: HostAuthentication) -> APIRouter:
    """Compose current-password-verified account settings access."""
    router = APIRouter()
    require_sess = make_require_session(authentication)

    @router.get("/auth/account")
    def read_account(request: Request) -> JSONResponse:
        """Project username and effective duration without account verifier material."""
        require_sess(request)
        session = authentication.verify_session(
            extract_bearer_token(request.headers.get("authorization"))
        )
        username = session.username
        snapshot = authentication.settings.get_snapshot()
        legacy = snapshot.values.get("application", {}).get("user_access", {})
        duration = legacy.get("session_timeout_mins", 1440)
        logger.debug("Account settings projected", extra={"fr_id": "FR-API-SESS-AUTH"})
        return JSONResponse(
            content=StandardResponse.success(
                data={
                    "username": username,
                    "revision": snapshot.revision,
                    "session_timeout_mins": max(MIN_SESSION_MINUTES, duration)
                    if type(duration) is int
                    else 1440,
                }
            ).to_dict()
        )

    @router.put("/auth/account")
    async def change_account_endpoint(request: Request) -> JSONResponse:
        """Change the configured account after current-password verification."""
        require_sess(request)
        try:
            body = await request.json()
            payload = _account_change_payload(body)
            revision = await asyncio.to_thread(
                authentication.change_account,
                extract_bearer_token(request.headers.get("authorization")),
                current_password=payload[0],
                username=payload[1],
                new_password=payload[2],
                duration_minutes=payload[3],
                expected_revision=payload[4],
            )
            return JSONResponse(
                content=StandardResponse.success(
                    data={"revision": revision, "reauthenticate": True}
                ).to_dict()
            )
        except RevisionConflictError:
            code, message = 409, "Settings changed. Reopen and retry."
        except AuthenticationError:
            code, message = 403, "Current password verification failed."
        except ValueError, TypeError:
            code, message = 422, "Invalid account settings."
        except PersistenceError:
            code, message = 503, "Account store unavailable."
        logger.warning("Account update rejected", extra={"fr_id": "FR-API-SESS-AUTH"})
        return JSONResponse(
            status_code=code,
            content=StandardResponse.failure(
                error=StandardError(code="ACCOUNT_UPDATE_FAILED", message=message),
                message=message,
            ).to_dict(),
        )

    return router


def create_auth_router(authentication: HostAuthentication) -> APIRouter:
    """Expose legacy login/status aliases using the session-owned authentication."""
    handlers = SessionsRouter(
        authentication.manager,
        get_global_authorizer(),
        get_global_authority_coordinator(),
        authentication,
    )
    router = APIRouter(tags=["sessions"])
    router.add_api_route("/auth/login", handlers.login_endpoint, methods=["POST"])
    router.add_api_route("/login", handlers.login_endpoint, methods=["POST"])

    router.include_router(_create_account_router(authentication))

    @router.get("/auth/status")
    def auth_status(request: Request, token: str | None = None) -> JSONResponse:
        """Inspect whether the supplied shared session is active."""
        resolved = (
            extract_bearer_token(request.headers.get("authorization"))
            if request.headers.get("authorization")
            else token
        )
        try:
            session = authentication.verify_session(resolved or "")
        except SecurityError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Host session required or expired.",
            ) from None
        return JSONResponse(
            content=StandardResponse.success(
                data={"authenticated": True, "username": session.username}
            ).to_dict()
        )

    logger.debug(
        "Authentication router composed",
        extra={"fr_id": "FR-API-SESS-AUTH"},
    )
    return router


class SessionsRouter:
    """Encapsulates FastAPI endpoint methods for host sessions and security."""

    def __init__(
        self,
        session_manager: SessionManager,
        authorizer: ScopeAuthorizer,
        authority_coordinator: DistinctAuthorityCoordinator,
        authentication: HostAuthentication | None = None,
    ) -> None:
        self.mgr = session_manager
        self.auth = authorizer
        self.coord = authority_coordinator
        self.authentication = (
            authentication
            if authentication is not None
            else HostAuthentication(HostSettings(), session_manager)
        )

    async def login_endpoint(self, req: LoginRequest) -> Response:
        """Authenticate and issue a new ephemeral session token."""
        try:
            session = await asyncio.to_thread(self.authentication.authenticate, req)
        except PersistenceError:
            logger.error(  # noqa: TRY400 - Storage errors must not expose details.
                "Login session storage unavailable",
                extra={"fr_id": "FR-API-SESS-LIFECYCLE"},
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=StandardResponse.failure(
                    error=StandardError(
                        code="SESSION_STORAGE_UNAVAILABLE",
                        message="Session storage is unavailable. Retry later.",
                    ),
                    message="Login failed.",
                ).to_dict(),
            )
        except AuthenticationError as exc:
            code = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if isinstance(exc, LoginCooldownError)
                else status.HTTP_401_UNAUTHORIZED
            )
            return JSONResponse(
                status_code=code,
                content=StandardResponse.failure(
                    error=StandardError(
                        code="LOGIN_COOLDOWN"
                        if code == status.HTTP_429_TOO_MANY_REQUESTS
                        else "INVALID_CREDENTIALS",
                        message="Invalid credentials or host setup unavailable.",
                    ),
                    message="Login failed.",
                ).to_dict(),
            )
        token_data = SessionToken(
            token=session.token,
            username=session.username,
            role=session.role,
            scopes=sorted(session.scopes),
            expires_at=session.expires_at,
            host_instance_id=session.host_instance_id,
        )
        resp = StandardResponse.success(
            data=token_data.model_dump(mode="json"),
            message="Ephemeral session created successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def get_current_session_endpoint(
        self,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Inspect active session details and scopes."""
        token = extract_bearer_token(authorization)
        try:
            session = self.mgr.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        token_data = SessionToken(
            token=session.token,
            username=session.username,
            role=session.role,
            scopes=sorted(session.scopes),
            expires_at=session.expires_at,
            host_instance_id=session.host_instance_id,
        )
        resp = StandardResponse.success(
            data=token_data.model_dump(mode="json"),
            message="Active session retrieved successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def revoke_session_endpoint(
        self,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Revoke active session token."""
        token = extract_bearer_token(authorization)
        revoked = self.mgr.revoke_session(token)
        resp = StandardResponse.success(
            data={"revoked": revoked},
            message="Session revoked successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def elevate_endpoint(
        self,
        req: ElevationRequest,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Request time-bounded distinct authority elevation for a dangerous action."""
        token = extract_bearer_token(authorization)
        try:
            session = self.mgr.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        try:
            grant = self.coord.elevate(session, req)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        data = ElevationResponse(
            grant_id=grant.grant_id,
            scope=grant.scope,
            expires_at=grant.expires_at,
            message=(
                f"Session elevated for {grant.scope.value} until {grant.expires_at}."
            ),
        )
        resp = StandardResponse.success(
            data=data.model_dump(mode="json"),
            message="Distinct authority elevated successfully.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def verify_scope_endpoint(
        self,
        req: ScopeCheckRequest,
        authorization: str | None = Header(default=None),
    ) -> Response:
        """Evaluate whether active session possesses required scope."""
        token = extract_bearer_token(authorization)
        try:
            session = self.mgr.verify_session(token)
        except SecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
            ) from exc

        evaluation = self.auth.evaluate_scope(session, req.scope)
        resp = StandardResponse.success(
            data=evaluation.model_dump(mode="json"),
            message="Scope authorization evaluated.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def clean_install_check_endpoint(
        self,
    ) -> Response:
        """Run clean installation verification."""
        result = verify_clean_installation(Path())
        resp = StandardResponse.success(
            data=result.model_dump(mode="json"),
            message="Clean installation check completed.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def domain_removal_check_endpoint(
        self,
        domain_id: str,
    ) -> Response:
        """Run domain removal qualification verification."""
        result = verify_domain_removal(
            domain_id=domain_id,
            base_dir=Path(),
            session_manager=self.mgr,
        )
        resp = StandardResponse.success(
            data=result.model_dump(mode="json"),
            message="Domain removal check completed.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def tls_proposal_endpoint(
        self,
    ) -> Response:
        """Retrieve authoritative remote deployment architecture proposal."""
        proposal = get_tls_remote_deployment_proposal()
        resp = StandardResponse.success(
            data=proposal.model_dump(mode="json"),
            message="TLS remote deployment proposal retrieved.",
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_sessions_router(
    session_manager: SessionManager | None = None,
    authorizer: ScopeAuthorizer | None = None,
    authority_coordinator: DistinctAuthorityCoordinator | None = None,
    authentication: HostAuthentication | None = None,
) -> APIRouter:
    """Create FastAPI router exposing session lifecycle and security endpoints.

    Fires FR-API-SESS-LIFECYCLE.
    """
    mgr = session_manager or get_global_session_manager()
    auth = authorizer or get_global_authorizer()
    coord = authority_coordinator or get_global_authority_coordinator()

    handlers = SessionsRouter(mgr, auth, coord, authentication)
    router = APIRouter(prefix="/sessions", tags=["sessions"])

    router.add_api_route(
        "/login",
        handlers.login_endpoint,
        methods=["POST"],
        summary="Authenticate and issue a new ephemeral session token",
    )
    router.add_api_route(
        "/me",
        handlers.get_current_session_endpoint,
        methods=["GET"],
        summary="Inspect active session details and scopes",
    )
    router.add_api_route(
        "/revoke",
        handlers.revoke_session_endpoint,
        methods=["POST"],
        summary="Revoke active session token",
    )
    router.add_api_route(
        "/elevate",
        handlers.elevate_endpoint,
        methods=["POST"],
        summary="Request time-bounded distinct authority elevation",
    )
    router.add_api_route(
        "/verify-scope",
        handlers.verify_scope_endpoint,
        methods=["POST"],
        summary="Evaluate whether active session possesses required scope",
    )
    router.add_api_route(
        "/distribution/clean-install-check",
        handlers.clean_install_check_endpoint,
        methods=["GET"],
        summary="Run clean installation verification",
    )
    router.add_api_route(
        "/distribution/domain-removal-check",
        handlers.domain_removal_check_endpoint,
        methods=["POST"],
        summary="Run domain removal qualification verification",
    )
    router.add_api_route(
        "/tls-proposal",
        handlers.tls_proposal_endpoint,
        methods=["GET"],
        summary="Retrieve remote deployment architecture proposal",
    )

    return router
