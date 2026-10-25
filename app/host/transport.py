"""Host gateway authorization, metadata safety, and network diagnostics."""

from __future__ import annotations

import asyncio
import json
import logging
import platform
import secrets
import socket
import sys
import time
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict
from datetime import UTC, datetime
from http import HTTPStatus
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit

import httpx
import psutil
from fastapi import APIRouter, FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

from app.host import resources as _res
from app.host.events import CORE_EVENT_CHANNELS, EventBus, HostEvent
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.host.session import Session, SessionManager, SessionPersistenceError
from app.host.settings import RevisionConflictError, SettingsManager

logger = logging.getLogger("app.access")

_SESSION_COOKIE = "hq_session_token"
_PEER_COOKIE = "hq_peer_id"
_ENTITY = "connection"
_MAX_TIMEOUT = 30.0
_MAX_PROBES = 20
_SECRET_WORDS = ("password", "secret", "token", "api_key", "private_key", "salt")
_BUS_HOLDER: list[EventBus | None] = [None]

type CredentialTester = Callable[[Mapping[str, Any]], Awaitable[bool]]


def get_global_event_bus() -> EventBus:
    """Return singleton event bus instance for host gateway."""
    bus = _BUS_HOLDER[0]
    if bus is None:
        bus = EventBus()
        _BUS_HOLDER[0] = bus
    return bus


def _success(operation: str, data: Any) -> dict[str, Any]:
    meta = ResponseMetadata(operation=operation, duration_ms=0)
    res = StandardResponse.success(
        message="Operation completed", data=data, metadata=meta
    )
    res["status"] = "success"
    return res


def _failure(code: ErrorCode, message: str, operation: str) -> JSONResponse:
    status_map = {
        ErrorCode.UNAUTHORIZED: 401,
        ErrorCode.FORBIDDEN: 403,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.CONFLICT: 409,
        ErrorCode.VALIDATION: 422,
    }
    meta = ResponseMetadata(operation=operation, duration_ms=0)
    err = StandardError(code=code, message=message)
    res = StandardResponse.failure(message=message, error=err, metadata=meta)
    res["status"] = "error"
    return JSONResponse(res, status_code=status_map.get(code, 503))


class TransportMiddleware:
    """Access logging and latency tracking ASGI middleware."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize middleware with target ASGI application."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process ASGI request, track duration and log access summary."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.perf_counter()
        try:
            await self.app(scope, receive, send)
        finally:
            path = scope.get("path", "")
            logger.info("FR-HOST-TRANSPORT-MIDDLEWARE: %s", path)
            logger.debug(
                "Request completed; path=%s duration=%.2fms",
                path,
                (time.perf_counter() - start) * 1000,
            )


def register_transport_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers mapping exceptions to StandardResponse."""

    @app.exception_handler(TransportError)
    async def _handle_transport_error(_: Request, exc: TransportError) -> JSONResponse:
        return _failure(exc.code, str(exc), "transport")

    @app.exception_handler(HTTPException)
    async def _handle_http_error(_: Request, exc: HTTPException) -> JSONResponse:
        code_map = {404: ErrorCode.NOT_FOUND, 422: ErrorCode.VALIDATION}
        return _failure(
            code_map.get(exc.status_code, ErrorCode.INTERNAL), exc.detail, "http"
        )

    @app.exception_handler(Exception)
    async def _handle_generic_error(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled server error: %s", exc)
        return _failure(ErrorCode.INTERNAL, "Internal server error", "host")


class Vault(Protocol):
    """Injected secret store; revoke must be idempotent and refs independently owned."""

    def resolve(self, reference: str) -> str:
        """Resolve one opaque reference without logging its secret."""
        ...

    def revoke(self, reference: str) -> None:
        """Permanently revoke a reference; repeated revocation must succeed."""
        ...


class TransportError(RuntimeError):
    """Typed domain exception translated directly into a standard error response."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        """Initialize transport error with code and message."""
        self.code, self.message = code, message
        super().__init__(message)


class ConnectionMetadata(BaseModel):
    """Allowlisted public connection fields; inline credentials cannot be saved."""

    model_config = ConfigDict(extra="forbid", strict=True)
    connection_id: str = Field(
        default_factory=lambda: secrets.token_hex(16), min_length=1, max_length=128
    )
    name: str = Field(min_length=1, max_length=200)
    provider: str = Field(min_length=1, max_length=100)
    kind: Literal["broker", "exchange"] = "broker"
    endpoint: str
    vault_refs: dict[str, str] = Field(default_factory=dict)


def _unwrap(response: dict[str, Any]) -> dict[str, Any]:
    if not response["success"]:
        err = response["error"]
        raise TransportError(
            ErrorCode(err["code"]), "Connection storage operation failed"
        )
    data: dict[str, Any] = response["data"]
    return data


def _endpoint(endpoint: str) -> tuple[str, int]:
    p = urlsplit(endpoint)
    bad = (
        p.scheme not in {"http", "https"}
        or not p.hostname
        or p.username is not None
        or p.password is not None
        or p.query
        or p.fragment
    )
    if bad:
        raise ValueError(
            "Use an HTTP(S) endpoint without credentials, query, or fragment"
        )
    return p.hostname or "127.0.0.1", p.port or (443 if p.scheme == "https" else 80)


def _bounds(timeout: float, probes: int = 1) -> None:
    if isinstance(timeout, bool) or not (0 < timeout <= _MAX_TIMEOUT):
        raise ValueError("timeout must be positive and at most 30 seconds")
    if isinstance(probes, bool) or not (1 <= probes <= _MAX_PROBES):
        raise ValueError("probes must be an integer between 1 and 20")


class ServletConstants:
    """System specifications and runtime constants service."""

    def __init__(self, sessions: SessionManager | None = None) -> None:
        """Initialize constants service with optional session manager."""
        self.sessions = sessions

    @staticmethod
    def get_constants() -> dict[str, Any]:
        """Return application and runtime platform metadata."""
        ver = "unknown"
        with suppress(PackageNotFoundError):
            ver = version("HaruQuantAI")
        meta = ("HaruQuantAI", platform.python_version(), ver, "fastapi+starlette")
        return dict(
            zip(("application", "runtime", "version", "transport"), meta, strict=True)
        )

    @staticmethod
    def get_system_specs() -> dict[str, Any]:
        """Return hardware resource and host platform specifications."""
        tot = psutil.virtual_memory().total
        c1, c2 = psutil.cpu_count(True) or 1, psutil.cpu_count(False) or 1
        return {
            "cpu_cores": c1,
            "physical_cores": c2,
            "memory_total_bytes": tot,
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "python_implementation": platform.python_implementation(),
        }


class ServletConnection:
    """Public connection persistence and asynchronous network/provider diagnostics."""

    def __init__(
        self,
        persistence: HostPersistence | None = None,
        *,
        vault: Vault | None = None,
        testers: Mapping[str, CredentialTester] | None = None,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.persistence = persistence or HostPersistence()
        self.vault = vault
        self.testers = dict(testers or {})
        self.http_transport = http_transport

    async def ping_endpoint(
        self,
        endpoint: str,
        *,
        timeout: float = 5.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Probe local or remote HTTP headers without redirects or response bodies."""
        _endpoint(endpoint)
        _bounds(timeout)
        start = time.perf_counter()
        try:
            async with (
                asyncio.timeout(timeout),
                httpx.AsyncClient(
                    timeout=timeout,
                    transport=self.http_transport,
                    follow_redirects=False,
                    trust_env=False,
                ) as c,
                c.stream("HEAD", endpoint) as resp,
            ):
                status = resp.status_code
            lat = (time.perf_counter() - start) * 1000
            healthy = status < HTTPStatus.BAD_REQUEST
            return {
                "reachable": True,
                "healthy": healthy,
                "http_status": status,
                "latency_ms": lat,
            }
        except httpx.HTTPError, OSError:
            logger.warning("Endpoint probe failed")
            return {
                "reachable": False,
                "healthy": False,
                "http_status": None,
                "latency_ms": None,
                "failure": "network_or_timeout",
            }

    async def check_latency(
        self,
        endpoint: str,
        *,
        probes: int = 3,
        timeout: float = 5.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Measure HTTP RTTs and failed-probe percentage (not ICMP packet loss)."""
        _bounds(timeout, probes)
        results = [
            await self.ping_endpoint(endpoint, timeout=timeout) for _ in range(probes)
        ]
        samples = [r["latency_ms"] for r in results if r["reachable"]]
        lost = probes - len(samples)
        logger.info("Latency probes completed; probes=%d; failed=%d", probes, lost)
        return {
            "probes": probes,
            "received": len(samples),
            "lost": lost,
            "packet_loss_percent": 100 * lost / probes,
            "measurement": "http_probe_failure",
            "min_ms": min(samples) if samples else None,
            "max_ms": max(samples) if samples else None,
            "mean_ms": (sum(samples) / len(samples)) if samples else None,
            "results": results,
        }

    async def diagnose_network(
        self,
        endpoint: str,
        *,
        timeout: float = 5.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Distinguish bounded DNS resolution and TCP socket connection failures."""
        host, port = _endpoint(endpoint)
        _bounds(timeout)
        start = time.perf_counter()
        try:
            async with asyncio.timeout(timeout):
                addresses = await asyncio.get_running_loop().getaddrinfo(
                    host, port, type=socket.SOCK_STREAM
                )
        except OSError:
            logger.warning("Network diagnosis failed; stage=dns")
            return {"dns": "failed", "socket": "not_tested"}
        for family, _, _, _, address in addresses:
            resolved_host = str(address[0])
            try:
                if (rem := timeout - (time.perf_counter() - start)) <= 0:
                    break
                async with asyncio.timeout(rem):
                    _, writer = await asyncio.open_connection(
                        resolved_host, port, family=family
                    )
                    writer.close()
                    await writer.wait_closed()
                lat = (time.perf_counter() - start) * 1000
                return {"dns": "ok", "socket": "ok", "latency_ms": lat}
            except OSError:
                continue
        logger.warning("Network diagnosis failed; stage=socket")
        return {"dns": "ok", "socket": "failed"}

    def list_connections(self, provider: str | None = None) -> list[dict[str, Any]]:
        """List all saved broker/exchange connection metadata through persistence."""
        items, offset, filt = [], 0, {"entity_type": _ENTITY}
        while True:
            page = _unwrap(
                self.persistence.read_records(
                    "host_entities", filters=filt, limit=1000, offset=offset
                )
            )
            for r in page["records"]:
                m = ConnectionMetadata.model_validate_json(r["payload"])
                if provider is None or m.provider == provider:
                    items.append(m.model_dump())
            if not page["pagination"]["has_more"]:
                return items
            offset += 1000

    list = list_connections

    def get(self, connection_id: str) -> ConnectionMetadata:
        """Read one saved connection using its host entity identity."""
        filt = {"entity_id": connection_id, "entity_type": _ENTITY}
        rows = _unwrap(self.persistence.read_records("host_entities", filters=filt))[
            "records"
        ]
        if not rows:
            raise TransportError(ErrorCode.NOT_FOUND, "Connection not found")
        return ConnectionMetadata.model_validate_json(rows[0]["payload"])

    def save_connection(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Create public metadata; require a vault for independently owned refs."""
        record = ConnectionMetadata.model_validate(metadata)
        _endpoint(record.endpoint)
        if (v := self.vault) is not None:
            for ref in record.vault_refs.values():
                v.resolve(ref)
        elif record.vault_refs:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Credential vault is not configured"
            )
        now = datetime.now(UTC).isoformat()
        with self.persistence.transaction() as tx:
            items = ServletConnection(tx).list()
            owned = {r for it in items for r in it["vault_refs"].values()}
            if owned.intersection(record.vault_refs.values()):
                raise TransportError(
                    ErrorCode.CONFLICT, "Vault reference is already owned"
                )
            row = {
                "entity_id": record.connection_id,
                "entity_type": _ENTITY,
                "scope": "host",
                "payload": record.model_dump_json(),
                "created_at_utc": now,
                "updated_at_utc": now,
            }
            _unwrap(tx.create_records("host_entities", row))
        logger.info("Connection metadata saved")
        return record.model_dump()

    save = save_connection

    def delete_connection(self, connection_id: str) -> dict[str, Any]:
        """Revoke owned vault refs before deleting; retain metadata on failure."""
        with self.persistence.transaction() as tx:
            record = ServletConnection(tx).get(connection_id)
            if (v := self.vault) is not None:
                for ref in record.vault_refs.values():
                    v.revoke(ref)
            elif record.vault_refs:
                raise TransportError(
                    ErrorCode.UNAVAILABLE, "Credential vault is not configured"
                )
            filt = {"entity_id": connection_id, "entity_type": _ENTITY}
            _unwrap(tx.delete_record("host_entities", filters=filt))
        logger.info("Connection deleted and vault references revoked")
        return {"connection_id": connection_id, "deleted": True}

    delete = delete_connection

    async def test_connection(
        self,
        *,
        connection_id: str | None = None,
        inline: Mapping[str, Any] | None = None,
        timeout: float = 5.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Test credentials with a real provider adapter without placing orders."""
        _bounds(timeout)
        if (connection_id is None) == (inline is None):
            msg = "Provide exactly one saved connection ID or inline connection"
            raise ValueError(msg)
        raw = dict(inline or {})
        credentials = raw.pop("credentials", {})
        if not isinstance(credentials, dict):
            raise TypeError("credentials must be an object")
        record = (
            await run_in_threadpool(self.get, connection_id)
            if connection_id is not None
            else ConnectionMetadata.model_validate(raw)
        )
        _endpoint(record.endpoint)
        if (tester := self.testers.get(record.provider)) is None:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Provider tester not configured"
            )
        if record.vault_refs and self.vault is None:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Credential vault not configured"
            )
        credentials = dict(credentials)
        if self.vault is not None:
            for name, ref in record.vault_refs.items():
                credentials[name] = await run_in_threadpool(self.vault.resolve, ref)
        start = time.perf_counter()
        try:
            async with asyncio.timeout(timeout):
                auth = await tester({**record.model_dump(), "credentials": credentials})
        except OSError, httpx.HTTPError:
            logger.warning("Provider credential test failed")
            fail: dict[str, Any] = {"authenticated": False, "status": "network_failure"}
            return {**fail, "latency_ms": None}
        lat = (time.perf_counter() - start) * 1000
        logger.info("Provider credential test completed; authenticated=%s", bool(auth))
        status = "ok" if auth is True else "invalid_credentials"
        return {"authenticated": auth is True, "status": status, "latency_ms": lat}


class ConnectionTest(ServletConnection):
    """Diagnostic helpers for network probing and latency analysis."""

    @staticmethod
    def _parse(endpoint: str) -> tuple[str, str, int]:
        """Parse host and port from endpoint URL."""
        return endpoint, *_endpoint(endpoint)


def _secret(key: str) -> bool:
    return any(word in key.lower() for word in _SECRET_WORDS)


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _public(v) for k, v in value.items() if not _secret(k)}
    if isinstance(value, list):
        return [_public(item) for item in value]
    return value


def _set_setting(
    current: dict[str, Any], key: str, value: Any, *, secrets_allowed: bool
) -> None:
    if _secret(key) and not secrets_allowed:
        raise ValueError("Use the secrets endpoint")
    target = current
    for part in key.split(".")[:-1]:
        target = target[part]
        if not isinstance(target, dict):
            raise TypeError("Unknown settings path")
    leaf = key.rsplit(".", maxsplit=1)[-1]
    if leaf not in target or isinstance(target[leaf], dict):
        raise ValueError("Unknown field or non-leaf settings update")
    if isinstance(value, (dict, list)) and _public({key: value}) != {key: value}:
        raise ValueError("Nested secret writes are not supported")
    if (prev := target[leaf]) is not None and type(value) is not type(prev):
        raise ValueError("Settings value type does not match stored field")
    target[leaf] = value


def _patch_settings(
    settings: SettingsManager, body: dict[str, Any], *, secrets_allowed: bool
) -> dict[str, Any]:
    snapshot = settings.get_snapshot()
    if not isinstance(changes := body["changes"], dict) or not changes:
        raise TypeError("Non-empty settings changes required")
    updates: dict[str, dict[str, Any]] = {}
    for group, changeset in changes.items():
        stored = group.replace(".", "_", 1)
        if stored == "user_access":
            raise ValueError("Use the account endpoint for credential changes")
        if not isinstance(changeset, dict):
            raise TypeError("Settings group must be an object")
        app_vals = snapshot["values"].get("application", {})
        if not isinstance(current := app_vals.get(stored), dict):
            raise TypeError("Unknown settings group")
        for key, value in changeset.items():
            _set_setting(current, key, value, secrets_allowed=secrets_allowed)
        updates.setdefault("application", {})[stored] = current
    settings.save_settings(updates, expected_revision=body["expected_revision"])
    return _settings_view(settings.get_snapshot())


def _settings_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    public: dict[str, Any] = _public(snapshot)
    for group, vals in public["values"].get("application", {}).items():
        public["values"][group.replace("_", ".", 1)] = vals
    return public


def _catalogue(snapshot: dict[str, Any]) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    unknown: list[dict[str, str]] = []
    reason = "Nullable field has no declared type"

    def visit(scope: str, group: str, key: str, value: Any) -> None:
        if isinstance(value, dict) and not _secret(key):
            for child, item in value.items():
                visit(scope, group, f"{key}.{child}" if key else child, item)
            return
        hidden = _secret(key)
        if value is None and not hidden:
            unknown.append({"scope": scope, "key": key, "reason": reason})
            return
        k = {bool: "bool", int: "int", float: "float", list: "list"}.get(
            type(value), "str"
        )
        f = {
            "scope": scope,
            "group": group,
            "key": key,
            "label": key,
            "kind": k,
            "readonly": group == "user_access",
            "secret": hidden,
            "configured" if hidden else "value": bool(value)
            if hidden
            else _public(value),
        }
        fields.append(f)

    for group, value in snapshot["values"].get("application", {}).items():
        visit(group.replace("_", ".", 1), group, "", value)
    return {"revision": snapshot["revision"], "fields": fields, "unknown": unknown}


def extract_bearer_token(
    request_or_header: Request | WebSocket | str | None,
) -> str | None:
    """Extract a bearer token from an Authorization header string or Request object."""
    if not request_or_header:
        return None
    if isinstance(request_or_header, str):
        return (
            h[7:].strip()
            if (h := request_or_header.strip()).startswith("Bearer ")
            else None
        )
    if (hdr := request_or_header.headers.get("authorization", "").strip()).startswith(
        "Bearer "
    ):
        return hdr[7:].strip()
    c = request_or_header.cookies.get(_SESSION_COOKIE)
    return c.strip() if c else None


def _token(request: Request | WebSocket) -> str:
    return extract_bearer_token(request) or request.cookies.get(_SESSION_COOKIE, "")


def _peer(request: Request | WebSocket) -> str:
    peer = request.cookies.get(_PEER_COOKIE, "")
    return peer if peer.startswith("ui:") else ""


def _cookies(response: JSONResponse, request: Request, token: str, peer: str) -> None:
    sec = request.url.scheme == "https"
    for key, val in ((_PEER_COOKIE, peer), (_SESSION_COOKIE, token)):
        response.set_cookie(
            key,
            val,
            max_age=86400,
            httponly=True,
            secure=sec,
            samesite="strict",
            path="/api/v1",
        )


def _require(request: Request | WebSocket, scope: str) -> Session:
    sess = request.app.state.sessions
    tok, peer = _token(request), _peer(request)
    session: Session | None = sess.validate_session(tok, peer)
    if session is None:
        raise TransportError(ErrorCode.UNAUTHORIZED, "A UI session is required")
    if not sess.authorize(tok, peer, scope):
        raise TransportError(ErrorCode.FORBIDDEN, "Capability is not granted")
    request.state.authenticated_session = session
    return session


async def _body(request: Request) -> dict[str, Any]:
    if not isinstance(v := await request.json(), dict):
        raise TypeError("JSON object required")
    return v


async def _auth_route(request: Request) -> Any:
    sessions, settings = request.app.state.sessions, request.app.state.settings
    if request.method == "GET":
        if request.url.path.endswith("/auth"):
            return {"authentication_required": True}
        s = await run_in_threadpool(_require, request, "session:read")
        exp = s.expires_at_utc.isoformat()
        return {"username": s.username, "peer_id": s.peer_id, "expires_at": exp}
    body = await _body(request)
    if body.get("action") == "logout":
        await run_in_threadpool(_require, request, "session:read")
        tok, peer = _token(request), _peer(request)
        await run_in_threadpool(sessions.revoke_session, tok, peer)
        res = JSONResponse(_success("logout", {"revoked": True}))
        res.delete_cookie(_SESSION_COOKIE, path="/api/v1")
        return res
    access = await run_in_threadpool(settings.get_scope, "user_access")
    username = body.get("username", access["username"])
    if not await run_in_threadpool(
        sessions.verify_credentials,
        username,
        body.get("password", ""),
        expected_username=access["username"],
        password_hash=access["password_hash"],
    ):
        raise TransportError(ErrorCode.UNAUTHORIZED, "Invalid credentials")
    peer = _peer(request) or "ui:" + secrets.token_hex(16)
    token = await run_in_threadpool(sessions.create_session, username, peer)
    s = await run_in_threadpool(sessions.validate_session, token, peer)
    data = {"token": token, "peer_id": peer, "expires_at": s.expires_at_utc.isoformat()}
    res = JSONResponse(_success("login", data))
    _cookies(res, request, token, peer)
    logger.info("UI login completed")
    return res


async def _meta(request: Request) -> Any:
    name = request.url.path.rsplit("/", 1)[-1]
    if name == "status":
        return {"status": "ok"}
    if name == "readiness":
        await run_in_threadpool(request.app.state.settings.reload)
        return {"ready": True}
    await run_in_threadpool(_require, request, "host:read")
    if name == "app-loaded":
        payload = {"host_instance_id": request.app.state.sessions.host_instance_id}
        get_global_event_bus().publish("system", "app_loaded", payload)
        return {"acknowledged": True}
    if name in ("diagnostics", "resources"):
        data = asdict(_res.inspect_resources())
        data["memory_watchdog"] = asdict(_res.check_memory_headroom())
        return data
    sc = ServletConstants(request.app.state.sessions)
    return sc.get_system_specs() if name == "specs" else sc.get_constants()


class SettingsBatchUpdatePayload(BaseModel):
    """Payload model for batch updating settings."""

    expected_revision: int
    changes: dict[str, Any]


async def _cfg_route(request: Request) -> Any:
    scope = "settings:read" if request.method == "GET" else "settings:write"
    await run_in_threadpool(_require, request, scope)
    settings = request.app.state.settings
    await run_in_threadpool(settings.reload)
    path = request.url.path
    if path.endswith("/auth/account"):
        access = await run_in_threadpool(settings.get_scope, "user_access")
        if request.method == "PUT":
            body = await _body(request)
            sess = request.app.state.sessions
            if not await run_in_threadpool(
                sess.verify_password, body["current_password"], access["password_hash"]
            ):
                raise TransportError(ErrorCode.UNAUTHORIZED, "Invalid credentials")
            access["password_hash"] = await run_in_threadpool(
                sess.hash_password, body["new_password"]
            )
            access.pop("password_salt", None)
            if "username" in body:
                if not isinstance(u := body["username"], str) or not u.strip():
                    raise ValueError("Non-empty username required")
                access["username"] = u
            await run_in_threadpool(
                settings.save_settings,
                {"application": {"user_access": access}},
                expected_revision=body["expected_revision"],
            )
        return {
            "username": access["username"],
            "revision": settings.revision,
            "session_timeout_mins": 1440,
        }
    if request.method == "PUT":
        body = await _body(request)
        SettingsBatchUpdatePayload.model_validate(body)
        return await run_in_threadpool(
            _patch_settings, settings, body, secrets_allowed=path.endswith("/secrets")
        )
    snapshot = await run_in_threadpool(settings.get_snapshot)
    return (
        _catalogue(snapshot)
        if path.endswith("/catalogue")
        else _settings_view(snapshot)
    )


async def _conn_route(request: Request) -> Any:
    action = (
        "test"
        if request.url.path.endswith("/test")
        else {"GET": "read", "DELETE": "delete"}.get(request.method, "write")
    )
    await run_in_threadpool(_require, request, f"connections:{action}")
    state = request.app.state
    v, t = getattr(state, "vault", None), getattr(state, "connection_testers", None)
    service = ServletConnection(state.persistence, vault=v, testers=t)
    cid = request.path_params.get("connection_id")
    if request.method == "GET":
        return (
            (await run_in_threadpool(service.get, str(cid))).model_dump()
            if cid
            else await run_in_threadpool(service.list)
        )
    if request.method == "DELETE":
        return await run_in_threadpool(service.delete, str(cid))
    if request.url.path.endswith("/test"):
        inline = None if cid else await _body(request)
        return await service.test_connection(connection_id=cid, inline=inline)
    return await run_in_threadpool(service.save, await _body(request))


async def _jobs_route(request: Request) -> Any:
    await run_in_threadpool(_require, request, "jobs:read")
    sch = getattr(request.app.state, "scheduler", None)
    jid = request.path_params.get("job_id")
    if request.method == "POST" and request.url.path.endswith("/cancel"):
        await run_in_threadpool(_require, request, "jobs:cancel")
        if sch is None:
            raise TransportError(ErrorCode.UNAVAILABLE, "Scheduler is not running")
        return await run_in_threadpool(sch.cancel_job, str(jid))
    if jid:
        job = await run_in_threadpool(sch.get_job, str(jid)) if sch else None
        if job is None:
            raise TransportError(ErrorCode.NOT_FOUND, "Job not found")
        return job
    return await run_in_threadpool(sch.list_jobs) if sch else []


async def _event_route(request: Request) -> Any:
    path = request.url.path
    if path.endswith("/publish"):
        await run_in_threadpool(_require, request, "events:write")
        b, bus = await _body(request), get_global_event_bus()
        ev = bus.publish(b["channel"], b.get("event_type", "update"), b.get("payload"))
        return ev.model_dump()
    await run_in_threadpool(_require, request, "events:read")
    if path.endswith("/channels"):
        chans = list(CORE_EVENT_CHANNELS)
        act = get_global_event_bus().channels
        return {"core_channels": chans, "channels": chans, "active_channels": act}
    chan = request.query_params.get("channel", "*")
    return get_global_event_bus().get_snapshot(chan).model_dump()


async def _sse_gen(
    req: Request,
    sub_id: str,
    q: asyncio.Queue[HostEvent],
    replay: list[HostEvent],
    *,
    gap: bool = False,
    limit: int | None = None,
) -> AsyncGenerator[str]:
    sent = 0
    try:
        if gap:
            gap_data = json.dumps({"channel": "system", "event_type": "gap"})
            yield f"event: system.gap\ndata: {gap_data}\n\n"
        while (limit is None or sent < limit) and not await req.is_disconnected():
            try:
                ev = replay.pop(0) if replay else await asyncio.wait_for(q.get(), 15.0)
                body = ev.model_dump_json()
                yield f"id: {ev.cursor}\nevent: {ev.channel}\ndata: {body}\n\n"
                sent += 1
            except TimeoutError:
                yield ": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        get_global_event_bus().unsubscribe(sub_id)


async def _sse(request: Request) -> StreamingResponse:
    await run_in_threadpool(_require, request, "events:read")
    bus = get_global_event_bus()
    qp = request.query_params
    chan = qp.get("channels") or qp.get("channel") or "*"
    chans = [c.strip() for c in chan.split(",") if c.strip()]
    since = qp.get("since_cursor")
    cur = int(since) if since and since.isdigit() else None
    lim = int(qp["limit"]) if "limit" in qp and qp["limit"].isdigit() else None
    sub_id, q, replay, gap = bus.subscribe(chans, since_cursor=cur)
    gen = _sse_gen(request, sub_id, q, replay, gap=gap, limit=lim)
    hdrs = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(gen, media_type="text/event-stream", headers=hdrs)


async def _ws(websocket: WebSocket) -> None:
    try:
        await run_in_threadpool(_require, websocket, "host:read")
    except TransportError, SessionPersistenceError:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            msg = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            await run_in_threadpool(_require, websocket, "host:read")
            resp = _success("ws", {"type": "pong" if msg == "ping" else "unsupported"})
            await websocket.send_json(resp)
    except WebSocketDisconnect:
        logger.debug("Host websocket disconnected")
    except TimeoutError:
        await websocket.close(code=1000)
    except TransportError, SessionPersistenceError:
        await websocket.close(code=1008)


def _handler(
    handler: Callable[[Request], Awaitable[Any]],
) -> Callable[[Request], Awaitable[Any]]:
    op = handler.__name__

    async def dispatch(request: Request) -> Any:
        start = time.perf_counter()
        try:
            result = await handler(request)
            if isinstance(result, (JSONResponse, StreamingResponse)):
                return result
            response = _success(op, result)
            response["metadata"]["duration_ms"] = (time.perf_counter() - start) * 1000
            res = JSONResponse(response)
            if getattr(request.state, "authenticated_session", None) is not None:
                _cookies(res, request, _token(request), _peer(request))
            return res
        except TransportError as error:
            return _failure(error.code, str(error), op)
        except RevisionConflictError:
            return _failure(ErrorCode.CONFLICT, "Settings revision changed", op)
        except ValueError, TypeError, KeyError:
            return _failure(ErrorCode.VALIDATION, "Invalid configuration", op)
        except Exception:
            logger.exception("Host gateway operation failed: %s", op)
            return _failure(ErrorCode.UNAVAILABLE, "Host service is unavailable", op)

    return dispatch


def create_transport_router(*, prefix: str = "/api/v1") -> APIRouter:
    """Create and configure the APIRouter for host transport routes."""
    router = APIRouter(prefix=prefix)
    spec = (
        (_auth_route, "GET /auth;POST /auth;POST /auth/login;GET /sessions/me"),
        (
            _meta,
            (
                "GET /status;GET /readiness;POST /app-loaded;GET /about;"
                "GET /constants;GET /specs;GET /diagnostics;GET /resources"
            ),
        ),
        (
            _cfg_route,
            (
                "GET /settings;PUT /settings;GET /settings/catalogue;"
                "PUT /settings/secrets;GET /auth/account;PUT /auth/account"
            ),
        ),
        (
            _conn_route,
            (
                "GET /connections;POST /connections;POST /connections/test;"
                "DELETE /connections/{connection_id};"
                "POST /connections/{connection_id}/test"
            ),
        ),
        (_jobs_route, "GET /jobs;GET /jobs/{job_id};POST /jobs/{job_id}/cancel"),
        (
            _event_route,
            "POST /events/publish;GET /events/channels;GET /events/snapshot",
        ),
    )
    for fn, endpoints in spec:
        for ep in endpoints.split(";"):
            m, p = ep.split()
            router.add_api_route(p, _handler(fn), methods=[m], name=fn.__name__)
    router.add_api_route("/events", _sse, methods=["GET"], name="_sse")
    router.add_api_websocket_route("/ws", _ws)
    return router


def install_transport(application: FastAPI) -> None:
    """Mount the UI host gateway at /api/v1, including middleware and websocket."""
    ports = (3000, 8000)
    origins = [f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in ports]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )
    application.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(application)
    application.include_router(create_transport_router(prefix="/api/v1"))


def create_host_app(
    *, extra_routers: Sequence[APIRouter] | None = None, **kw: Any
) -> FastAPI:
    """Create the configured FastAPI host gateway application."""
    from app.main import create_app

    app = create_app(**kw)
    for extra in extra_routers or ():
        app.include_router(extra)
    return app


class TransportCLI:
    """CLI commands for host transport operations and diagnostics."""

    @staticmethod
    def run(argv: Sequence[str] | None = None) -> int:
        """Execute transport CLI flags, e.g. --test-bus."""
        args = list(argv if argv is not None else sys.argv[1:])
        if "--test-bus" in args:
            ev = get_global_event_bus().publish("system", "cli_test", {"ok": True})
            return 0 if ev.cursor > 0 else 1
        return 0


if __name__ == "__main__":
    sys.exit(TransportCLI.run())
