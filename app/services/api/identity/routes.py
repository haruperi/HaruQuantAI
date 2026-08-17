"""Typed registration, login, and logout HTTP routes."""

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Final, NoReturn

from fastapi import APIRouter, Cookie, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.services.api.contracts import ROUTE_CONTRACT_REGISTRY
from app.services.api.identity import (
    IdentityError,
    authenticate_user,
    create_session,
    recover_session_identity,
    register_user,
    revoke_session,
    validate_csrf,
)
from app.services.api.workstation.settings.account_mode import resolve_runtime_profile
from app.services.api.workstation.settings.bootstrap import get_api_settings
from app.utils import generate_id, get_logger

if TYPE_CHECKING:
    from app.services.api.identity.sessions import SessionCredential

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_SESSION_COOKIE = "hq_session"
_CSRF_COOKIE = "hq_csrf"

# Permissions that grant control over safety-critical or platform-admin
# surfaces. Self-registered accounts never receive these; only an explicit
# administrative grant should.
_ADMIN_ONLY_PERMISSIONS: Final[frozenset[str]] = frozenset(
    {
        "settings:admin",
        "ops:approve",
        "risk:kill_switch",
        "agentic:approve_promotion",
    }
)


@lru_cache(maxsize=1)
def _default_self_registration_permissions() -> tuple[str, ...]:
    """Return the non-admin permission baseline for self-registered accounts.

    Derived from the route contract catalog so newly declared permissions are
    granted automatically unless explicitly listed in `_ADMIN_ONLY_PERMISSIONS`.

    Returns:
        Deduplicated, sorted, non-admin permission keys.
    """
    granted = {
        contract.permission
        for contract in ROUTE_CONTRACT_REGISTRY.all()
        if contract.permission is not None
        and contract.permission not in _ADMIN_ONLY_PERMISSIONS
    }
    return tuple(sorted(granted))


class _Credentials(BaseModel):
    """Bounded username/password request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)  # pragma: allowlist secret


def _raise_identity_http_error(error: IdentityError) -> NoReturn:
    """Raise a safe HTTP error for one bounded identity failure.

    Raises:
        HTTPException: Always, without credential material.
    """
    code = str(error)
    status_code = (
        status.HTTP_401_UNAUTHORIZED
        if code in {"AUTHENTICATION_REQUIRED", "ACCOUNT_STATE_INVALID"}
        else (
            status.HTTP_429_TOO_MANY_REQUESTS
            if code == "RATE_LIMITED"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
    )
    raise HTTPException(status_code=status_code, detail=code) from error


def _set_session_cookies(
    response: Response,
    session: SessionCredential,
) -> None:
    """Set secure opaque browser session cookies."""
    settings = get_api_settings()
    secure = not any(
        origin.startswith("http://localhost") for origin in settings.ui_origins
    )
    response.set_cookie(
        _SESSION_COOKIE,
        session.session_token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=settings.session_ttl_seconds,
    )
    response.set_cookie(
        _CSRF_COOKIE,
        session.csrf_token,
        httponly=False,
        secure=secure,
        samesite="strict",
        max_age=settings.session_ttl_seconds,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def _register(
    credentials: _Credentials,
    response: Response,
) -> dict[str, object]:
    """Register and authenticate one non-privileged user.

    Returns:
        Secret-free account and session-expiry evidence.

    Raises:
        HTTPException: If account creation or session persistence fails.
    """
    request_id = generate_id("req")
    settings = get_api_settings()
    try:
        user = register_user(
            username=credentials.username,
            password=credentials.password,
            request_id=request_id,
            permissions=_default_self_registration_permissions(),
            tenant_or_environment=(
                "development" if settings.environment == "dev" else settings.environment
            ),
            runtime_profile=settings.runtime_profile,
        )
        session = create_session(
            user,
            request_id=request_id,
            ttl_seconds=settings.session_ttl_seconds,
        )
    except IdentityError as error:
        _raise_identity_http_error(error)
    _set_session_cookies(response, session)
    return {
        "user_id": user.user_id,
        "username": user.username,
        "expires_at": session.expires_at,
        "runtime_profile": resolve_runtime_profile(request_id=request_id),
    }


@router.post("/login")
def _login(
    credentials: _Credentials,
    response: Response,
) -> dict[str, object]:
    """Authenticate one account and replace its active session.

    Returns:
        Secret-free account and session-expiry evidence.

    Raises:
        HTTPException: If credentials or persistence are invalid.
    """
    request_id = generate_id("req")
    try:
        user = authenticate_user(
            username=credentials.username,
            password=credentials.password,
            request_id=request_id,
        )
        session = create_session(
            user,
            request_id=request_id,
            ttl_seconds=get_api_settings().session_ttl_seconds,
        )
    except IdentityError as error:
        _raise_identity_http_error(error)
    _set_session_cookies(response, session)
    return {
        "user_id": user.user_id,
        "username": user.username,
        "expires_at": session.expires_at,
        "runtime_profile": resolve_runtime_profile(request_id=request_id),
    }


@router.get("/me")
def _me(request: Request) -> dict[str, object]:
    """Recover the caller's non-secret identity from server-side session state.

    Returns:
        Current user identity and exact session expiry.

    Raises:
        HTTPException: If the session is missing, expired, revoked, or inactive.
    """
    request_id = generate_id("req")
    settings = getattr(request.app.state, "api_settings", None) or get_api_settings()
    token = request.cookies.get(_SESSION_COOKIE)
    authorization = request.headers.get("authorization", "")
    if token is None and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        if settings.environment == "dev" and settings.dev_auto_login:
            return {
                "user_id": "usr_haruquantai",
                "username": "haruquantai",
                "expires_at": "2099-01-01T00:00:00Z",
                "runtime_profile": resolve_runtime_profile(request_id=request_id),
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTHENTICATION_REQUIRED",
        )
    try:
        identity = recover_session_identity(token, request_id=request_id)
    except IdentityError as error:
        if settings.environment == "dev" and settings.dev_auto_login:
            return {
                "user_id": "usr_haruquantai",
                "username": "haruquantai",
                "expires_at": "2099-01-01T00:00:00Z",
                "runtime_profile": resolve_runtime_profile(request_id=request_id),
            }
        _raise_identity_http_error(error)
    return {
        **identity.model_dump(mode="json"),
        "runtime_profile": resolve_runtime_profile(request_id=request_id),
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def _logout(
    response: Response,
    session_cookie: Annotated[str | None, Cookie(alias=_SESSION_COOKIE)] = None,
    authorization: Annotated[str | None, Header()] = None,
    csrf_token: Annotated[
        str | None,
        Header(alias="X-CSRF-Token"),
    ] = None,
) -> None:
    """Idempotently revoke the caller's opaque session.

    Raises:
        HTTPException: If revocation cannot be confirmed.
    """
    request_id = generate_id("req")
    token = session_cookie
    if token is None and authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    try:
        if session_cookie is not None:
            if csrf_token is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF_REQUIRED",
                )
            validate_csrf(session_cookie, csrf_token, request_id=request_id)
        if token is not None:
            revoke_session(token, request_id=request_id)
    except IdentityError as error:
        if str(error) == "CSRF_INVALID":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF_INVALID",
            ) from error
        _raise_identity_http_error(error)
    response.delete_cookie(_SESSION_COOKIE)
    response.delete_cookie(_CSRF_COOKIE)


__all__ = ("router",)
