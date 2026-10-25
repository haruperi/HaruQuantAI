"""FastAPI host gateway and bounded network diagnostics.

Connection records use host_entities (entity_type='connection'). Only explicit
public fields and vault references are persisted. A production vault and real
provider credential testers are injected at bootstrap; missing integrations
return unavailable, never a fabricated authentication success. No orders execute.
HTTP probes measure HTTP round trips, not ICMP packet delivery.
"""

# Public diagnostic APIs expose a bounded per-probe timeout as well as cancellation.
# ruff: noqa: ASYNC109

from __future__ import annotations

import asyncio
import math
import platform
import secrets
import socket
import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit

import httpx
import psutil
from fastapi import APIRouter, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.host.session import Session, SessionPersistenceError
from app.host.settings import (
    RevisionConflictError,
    SettingsManager,
)
from app.include.enums import Timeframe

logger = get_logger(__name__)
_ENTITY = "connection"
_MAX_PROBES = 20
_MAX_TIMEOUT = 30
_HTTP_ERROR = 400
_PEER_COOKIE = "haru_peer"
_SESSION_COOKIE = "haru_session"
_SECRET_WORDS = ("password", "secret", "token", "api_key", "private_key", "salt")
type CredentialTester = Callable[[Mapping[str, Any]], Awaitable[bool]]


class Vault(Protocol):
    """Injected secret store; revoke must be idempotent and refs independently owned."""

    def resolve(self, reference: str) -> str:
        """Resolve one opaque reference without logging its secret."""
        ...

    def revoke(self, reference: str) -> None:
        """Permanently revoke a reference; repeated revocation must succeed."""
        ...


class TransportError(RuntimeError):
    """Public gateway failure with a stable response category."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


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
        error = response["error"]
        raise TransportError(
            ErrorCode(error["code"]), "Connection storage operation failed"
        )
    data: dict[str, Any] = response["data"]
    return data


def _endpoint(endpoint: str) -> tuple[str, int]:
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Use an HTTP(S) endpoint without credentials, query, or fragment"
        )
    return parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def _bounds(timeout: float, probes: int = 1) -> None:
    if (
        isinstance(timeout, bool)
        or not math.isfinite(timeout)
        or not 0 < timeout <= _MAX_TIMEOUT
    ):
        raise ValueError("timeout must be positive and at most 30 seconds")
    if (
        isinstance(probes, bool)
        or not isinstance(probes, int)
        or not 1 <= probes <= _MAX_PROBES
    ):
        raise ValueError("probes must be an integer between 1 and 20")


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
        self.persistence = persistence if persistence is not None else HostPersistence()
        self.vault = vault
        self.testers = dict(testers or {})
        self.http_transport = http_transport

    async def ping_endpoint(
        self, endpoint: str, *, timeout: float = 5.0
    ) -> dict[str, Any]:
        """Probe local or remote HTTP headers without redirects or response bodies.

        Any HTTP response proves network reachability. HTTP status independently
        indicates application health; a 401 is reachable but not healthy.
        """
        _endpoint(endpoint)
        _bounds(timeout)
        start = time.perf_counter()
        try:
            async with (
                asyncio.timeout(timeout),
                httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=False,
                    trust_env=False,
                    transport=self.http_transport,
                ) as client,
                client.stream("HEAD", endpoint) as response,
            ):
                status = response.status_code
            result = {
                "reachable": True,
                "healthy": status < _HTTP_ERROR,
                "http_status": status,
                "latency_ms": (time.perf_counter() - start) * 1000,
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
        logger.debug("Endpoint probe completed; http_status=%d", status)
        return result

    async def check_latency(
        self, endpoint: str, *, probes: int = 3, timeout: float = 5.0
    ) -> dict[str, Any]:
        """Measure HTTP RTTs and failed-probe percentage (not ICMP packet loss)."""
        _bounds(timeout, probes)
        results = [
            await self.ping_endpoint(endpoint, timeout=timeout) for _ in range(probes)
        ]
        samples = [result["latency_ms"] for result in results if result["reachable"]]
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
            "mean_ms": sum(samples) / len(samples) if samples else None,
            "results": results,
        }

    async def diagnose_network(
        self, endpoint: str, *, timeout: float = 5.0
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
                remaining = timeout - (time.perf_counter() - start)
                if remaining <= 0:
                    break
                async with asyncio.timeout(remaining):
                    _, writer = await asyncio.open_connection(
                        resolved_host, port, family=family
                    )
                    writer.close()
                    await writer.wait_closed()
                return {
                    "dns": "ok",
                    "socket": "ok",
                    "latency_ms": (time.perf_counter() - start) * 1000,
                }
            except OSError:
                continue
        logger.warning("Network diagnosis failed; stage=socket")
        return {"dns": "ok", "socket": "failed"}

    def list(self) -> list[dict[str, Any]]:
        """List all saved broker/exchange connection metadata through persistence."""
        result: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = _unwrap(
                self.persistence.read_records(
                    "host_entities",
                    filters={"entity_type": _ENTITY},
                    limit=1000,
                    offset=offset,
                )
            )
            result.extend(
                ConnectionMetadata.model_validate_json(row["payload"]).model_dump()
                for row in page["records"]
            )
            if not page["pagination"]["has_more"]:
                return result
            offset += 1000

    def get(self, connection_id: str) -> ConnectionMetadata:
        """Read one saved connection using its host entity identity."""
        rows = _unwrap(
            self.persistence.read_records(
                "host_entities",
                filters={
                    "entity_id": connection_id,
                    "entity_type": _ENTITY,
                },
            )
        )["records"]
        if not rows:
            raise TransportError(ErrorCode.NOT_FOUND, "Connection not found")
        return ConnectionMetadata.model_validate_json(rows[0]["payload"])

    def save(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Create public metadata; require a vault for independently owned refs.

        Connections are immutable: delete an old connection before replacing it.
        Reference reuse is rejected to avoid revoking another connection's secret.
        """
        record = ConnectionMetadata.model_validate(metadata)
        _endpoint(record.endpoint)
        if record.vault_refs and self.vault is None:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Credential vault is not configured"
            )
        if self.vault is not None:
            for reference in record.vault_refs.values():
                self.vault.resolve(reference)
        now = datetime.now(UTC).isoformat()
        with self.persistence.transaction() as tx:
            existing = ServletConnection(tx).list()
            owned = {ref for item in existing for ref in item["vault_refs"].values()}
            if owned.intersection(record.vault_refs.values()):
                raise TransportError(
                    ErrorCode.CONFLICT, "Vault reference is already owned"
                )
            _unwrap(
                tx.create_records(
                    "host_entities",
                    {
                        "entity_id": record.connection_id,
                        "entity_type": _ENTITY,
                        "scope": "host",
                        "payload": record.model_dump_json(),
                        "created_at_utc": now,
                        "updated_at_utc": now,
                    },
                )
            )
        logger.info("Connection metadata saved")
        return record.model_dump()

    def delete(self, connection_id: str) -> dict[str, Any]:
        """Revoke owned vault refs before deleting; retain metadata on failure.

        Vault and SQLite cannot share a transaction. Idempotent revocation permits
        retries after partial failure. A failed database delete may leave revoked
        metadata, but cannot leave forgotten live credentials.
        """
        with self.persistence.transaction() as tx:
            record = ServletConnection(tx).get(connection_id)
            if record.vault_refs and self.vault is None:
                raise TransportError(
                    ErrorCode.UNAVAILABLE, "Credential vault is not configured"
                )
            if self.vault is not None:
                for reference in record.vault_refs.values():
                    self.vault.revoke(reference)
            _unwrap(
                tx.delete_record(
                    "host_entities",
                    filters={
                        "entity_id": connection_id,
                        "entity_type": _ENTITY,
                    },
                )
            )
        logger.info("Connection metadata deleted and owned vault references revoked")
        return {"connection_id": connection_id, "deleted": True}

    async def test_connection(
        self,
        *,
        connection_id: str | None = None,
        inline: Mapping[str, Any] | None = None,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Test credentials with a real provider adapter without placing orders."""
        _bounds(timeout)
        if (connection_id is None) == (inline is None):
            raise ValueError(
                "Provide exactly one saved connection ID or inline connection"
            )
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
        tester = self.testers.get(record.provider)
        if tester is None:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Provider credential tester is not configured"
            )
        if record.vault_refs and self.vault is None:
            raise TransportError(
                ErrorCode.UNAVAILABLE, "Credential vault is not configured"
            )
        credentials = dict(credentials)
        if self.vault is not None:
            for name, reference in record.vault_refs.items():
                credentials[name] = await run_in_threadpool(
                    self.vault.resolve, reference
                )
        start = time.perf_counter()
        try:
            async with asyncio.timeout(timeout):
                authenticated = await tester(
                    {**record.model_dump(), "credentials": credentials}
                )
        except OSError, httpx.HTTPError:
            logger.warning("Provider credential test failed")
            return {
                "authenticated": False,
                "status": "network_failure",
                "latency_ms": None,
            }
        logger.info(
            "Provider credential test completed; authenticated=%s",
            authenticated is True,
        )
        return {
            "authenticated": authenticated is True,
            "status": "ok" if authenticated is True else "invalid_credentials",
            "latency_ms": (time.perf_counter() - start) * 1000,
        }


def _success(operation: str, data: Any) -> dict[str, Any]:
    result = StandardResponse.success(
        message="Operation completed",
        data=data,
        metadata=ResponseMetadata(operation=operation, duration_ms=0),
    )
    result["status"] = "success"  # Existing UI transport envelope.
    return result


def _failure(code: ErrorCode, message: str, operation: str) -> JSONResponse:
    status = {
        ErrorCode.UNAUTHORIZED: 401,
        ErrorCode.FORBIDDEN: 403,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.CONFLICT: 409,
        ErrorCode.VALIDATION: 422,
    }.get(code, 503)
    result = StandardResponse.failure(
        message=message,
        error=StandardError(code=code, message=message),
        metadata=ResponseMetadata(operation=operation, duration_ms=0),
    )
    result["status"] = "error"
    return JSONResponse(result, status_code=status)


def _secret(key: str) -> bool:
    return any(word in key.lower() for word in _SECRET_WORDS)


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items() if not _secret(key)}
    if isinstance(value, list):
        return [_public(item) for item in value]
    return value


def _token(request: Request | WebSocket) -> str:
    header = request.headers.get("authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return request.cookies.get(_SESSION_COOKIE, "")


def _peer(request: Request | WebSocket) -> str:
    peer = request.cookies.get(_PEER_COOKIE, "")
    return peer if peer.startswith("ui:") else ""


def _cookies(response: JSONResponse, request: Request, token: str, peer: str) -> None:
    for key, value in ((_PEER_COOKIE, peer), (_SESSION_COOKIE, token)):
        response.set_cookie(
            key,
            value,
            max_age=86400,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="strict",
            path="/api/v1",
        )


def _require(request: Request | WebSocket, scope: str) -> Session:
    sessions = request.app.state.sessions
    token, peer = _token(request), _peer(request)
    session: Session | None = sessions.validate_session(token, peer)
    if session is None:
        raise TransportError(ErrorCode.UNAUTHORIZED, "A UI session is required")
    if not sessions.authorize(token, peer, scope):
        raise TransportError(ErrorCode.FORBIDDEN, "Capability is not granted")
    request.state.authenticated_session = session
    return session


async def _body(request: Request) -> dict[str, Any]:
    value = await request.json()
    if not isinstance(value, dict):
        raise TypeError("JSON object required")
    return value


async def _auth_route(request: Request) -> Any:
    sessions, settings = request.app.state.sessions, request.app.state.settings
    if request.method == "GET":
        if request.url.path.endswith("/auth"):
            return {"authentication_required": True}
        session = await run_in_threadpool(_require, request, "session:read")
        return {
            "username": session.username,
            "peer_id": session.peer_id,
            "expires_at": session.expires_at_utc.isoformat(),
        }
    body = await _body(request)
    if body.get("action") == "logout":
        await run_in_threadpool(_require, request, "session:read")
        await run_in_threadpool(
            sessions.revoke_session, _token(request), _peer(request)
        )
        response = JSONResponse(_success("logout", {"revoked": True}))
        response.delete_cookie(_SESSION_COOKIE, path="/api/v1")
        return response
    access = await run_in_threadpool(settings.get_scope, "user_access")
    username = body.get("username", access["username"])
    valid = await run_in_threadpool(
        sessions.verify_credentials,
        username,
        body.get("password", ""),
        expected_username=access["username"],
        password_hash=access["password_hash"],
    )
    if not valid:
        raise TransportError(ErrorCode.UNAUTHORIZED, "Invalid credentials")
    peer = _peer(request) or "ui:" + secrets.token_hex(16)
    token = await run_in_threadpool(sessions.create_session, username, peer)
    session = await run_in_threadpool(sessions.validate_session, token, peer)
    response = JSONResponse(
        _success(
            "login",
            {
                "token": token,
                "peer_id": peer,
                "expires_at": session.expires_at_utc.isoformat(),
            },
        )
    )
    _cookies(response, request, token, peer)
    logger.info("UI login completed")
    return response


async def _meta(request: Request) -> Any:
    name = request.url.path.rsplit("/", 1)[-1]
    if name == "status":
        return {"status": "ok"}
    if name == "readiness":
        await run_in_threadpool(request.app.state.settings.reload)
        return {"ready": True}
    await run_in_threadpool(_require, request, "host:read")
    if name == "app-loaded":
        logger.info("UI reported application loaded")
        return {"acknowledged": True}
    if name == "specs":
        return {
            "cpu_cores": psutil.cpu_count(logical=False),
            "hardware_concurrency": psutil.cpu_count(),
            "supported_timeframes": [item.value for item in Timeframe],
            "memory_headroom": {"available_bytes": psutil.virtual_memory().available},
        }
    result: dict[str, Any] = {
        "application": "HaruQuantAI",
        "runtime": platform.python_version(),
    }
    try:
        result["version"] = version("HaruQuantAI")
    except PackageNotFoundError:
        result["version"] = "unknown"
    if name == "constants":
        result.update(
            {
                "host_instance_id": request.app.state.sessions.host_instance_id,
                "supported_timeframes": [item.value for item in Timeframe],
                "build_timestamp": "unknown",
                "data_directory": str(
                    request.app.state.persistence.database_path.parent.parent
                ),
                "core_channels": [],
            }
        )
    return result


def _settings_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    public: dict[str, Any] = _public(snapshot)
    for group, values in public["values"].get("application", {}).items():
        public["values"][group.replace("_", ".", 1)] = values
    return public


def _catalogue(snapshot: dict[str, Any]) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    unknown: list[dict[str, str]] = []

    def visit(scope: str, group: str, key: str, value: Any) -> None:
        if isinstance(value, dict) and not _secret(key):
            for child, item in value.items():
                visit(scope, group, f"{key}.{child}" if key else child, item)
            return
        hidden = _secret(key)
        if value is None and not hidden:
            unknown.append(
                {
                    "scope": scope,
                    "key": key,
                    "reason": "Nullable field has no declared type",
                }
            )
            return
        kind = (
            "bool"
            if isinstance(value, bool)
            else "int"
            if isinstance(value, int)
            else "float"
            if isinstance(value, float)
            else "list"
            if isinstance(value, list)
            else "str"
        )
        field: dict[str, Any] = {
            "scope": scope,
            "group": group,
            "key": key,
            "label": key,
            "kind": kind,
            "readonly": group == "user_access",
            "secret": hidden,
        }
        field.update(
            {"configured": bool(value)} if hidden else {"value": _public(value)}
        )
        fields.append(field)

    for group, value in snapshot["values"].get("application", {}).items():
        visit(group.replace("_", ".", 1), group, "", value)
    return {"revision": snapshot["revision"], "fields": fields, "unknown": unknown}


def _set_setting(
    current: dict[str, Any], key: str, value: Any, *, secrets_allowed: bool
) -> None:
    if _secret(key) and not secrets_allowed:
        raise ValueError("Use the secrets endpoint")
    target = current
    parts = key.split(".")
    for part in parts[:-1]:
        target = target[part]
        if not isinstance(target, dict):
            raise TypeError("Unknown settings path")
    leaf = parts[-1]
    if leaf not in target or isinstance(target[leaf], dict):
        raise ValueError("Unknown field or non-leaf settings update")
    if isinstance(value, (dict, list)) and _public({key: value}) != {key: value}:
        raise ValueError("Nested secret writes are not supported")
    previous = target[leaf]
    if previous is not None and type(value) is not type(previous):
        raise ValueError("Settings value type does not match stored field")
    target[leaf] = value


def _patch_settings(
    settings: SettingsManager, body: dict[str, Any], *, secrets_allowed: bool
) -> dict[str, Any]:
    snapshot = settings.get_snapshot()
    changes = body["changes"]
    if not isinstance(changes, dict) or not changes:
        raise TypeError("Non-empty settings changes required")
    updates: dict[str, dict[str, Any]] = {}
    for group, changeset in changes.items():
        stored = group.replace(".", "_", 1)
        if stored == "user_access":
            raise ValueError("Use the account endpoint for credential changes")
        if not isinstance(changeset, dict):
            raise TypeError("Settings group must be an object")
        current = snapshot["values"].get("application", {}).get(stored)
        if not isinstance(current, dict):
            raise TypeError("Unknown settings group")
        for key, value in changeset.items():
            _set_setting(current, key, value, secrets_allowed=secrets_allowed)
        updates.setdefault("application", {})[stored] = current
    settings.save_settings(updates, expected_revision=body["expected_revision"])
    return _settings_view(settings.get_snapshot())


async def _cfg_route(request: Request) -> Any:
    await run_in_threadpool(
        _require,
        request,
        "settings:read" if request.method == "GET" else "settings:write",
    )
    settings = request.app.state.settings
    await run_in_threadpool(settings.reload)
    path = request.url.path
    if path.endswith("/auth/account"):
        access = await run_in_threadpool(settings.get_scope, "user_access")
        if request.method == "PUT":
            body = await _body(request)
            sessions = request.app.state.sessions
            valid = await run_in_threadpool(
                sessions.verify_password,
                body["current_password"],
                access["password_hash"],
            )
            if not valid:
                raise TransportError(ErrorCode.UNAUTHORIZED, "Invalid credentials")
            password_hash = await run_in_threadpool(
                sessions.hash_password, body["new_password"]
            )
            access["password_hash"] = password_hash
            access.pop("password_salt", None)
            if "username" in body:
                if (
                    not isinstance(body["username"], str)
                    or not body["username"].strip()
                ):
                    raise ValueError("Non-empty username required")
                access["username"] = body["username"]
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
        return await run_in_threadpool(
            _patch_settings,
            settings,
            await _body(request),
            secrets_allowed=path.endswith("/secrets"),
        )
    snapshot = await run_in_threadpool(settings.get_snapshot)
    return (
        _catalogue(snapshot)
        if path.endswith("/catalogue")
        else _settings_view(snapshot)
    )


async def _conn_route(request: Request) -> Any:
    action = (
        "read"
        if request.method == "GET"
        else "delete"
        if request.method == "DELETE"
        else "test"
        if request.url.path.endswith("/test")
        else "write"
    )
    await run_in_threadpool(_require, request, f"connections:{action}")
    state = request.app.state
    service = ServletConnection(
        state.persistence,
        vault=getattr(state, "vault", None),
        testers=getattr(state, "connection_testers", None),
    )
    connection_id = request.path_params.get("connection_id")
    if request.method == "GET":
        return await run_in_threadpool(service.list)
    if request.method == "DELETE":
        return await run_in_threadpool(service.delete, str(connection_id))
    if request.url.path.endswith("/test"):
        return await service.test_connection(
            connection_id=connection_id,
            inline=None if connection_id else await _body(request),
        )
    return await run_in_threadpool(service.save, await _body(request))


async def _ws(websocket: WebSocket) -> None:
    try:
        await run_in_threadpool(_require, websocket, "host:read")
    except TransportError, SessionPersistenceError:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            await run_in_threadpool(_require, websocket, "host:read")
            await websocket.send_json(
                _success("ws", {"type": "pong" if message == "ping" else "unsupported"})
            )
    except WebSocketDisconnect:
        logger.debug("Host websocket disconnected")
    except TimeoutError:
        await websocket.close(code=1000)
    except TransportError, SessionPersistenceError:
        await websocket.close(code=1008)


def _handler(
    handler: Callable[[Request], Awaitable[Any]],
) -> Callable[[Request], Awaitable[Any]]:
    async def dispatch(request: Request) -> Any:
        start = time.perf_counter()
        try:
            result = await handler(request)
            if isinstance(result, JSONResponse):
                return result
            response = _success(handler.__name__, result)
            response["metadata"]["duration_ms"] = (time.perf_counter() - start) * 1000
            result_response = JSONResponse(response)
            if getattr(request.state, "authenticated_session", None) is not None:
                _cookies(result_response, request, _token(request), _peer(request))
            return result_response
        except TransportError as error:
            return _failure(error.code, str(error), handler.__name__)
        except RevisionConflictError:
            return _failure(
                ErrorCode.CONFLICT, "Settings revision changed", handler.__name__
            )
        except ValueError, TypeError, KeyError:
            return _failure(
                ErrorCode.VALIDATION,
                "Invalid request or stored configuration",
                handler.__name__,
            )
        except Exception:  # noqa: BLE001
            logger.error("Host gateway operation failed; handler=%s", handler.__name__)  # noqa: TRY400
            return _failure(
                ErrorCode.UNAVAILABLE, "Host service is unavailable", handler.__name__
            )

    return dispatch


def install_transport(application: FastAPI) -> None:
    """Mount the UI host gateway at /api/v1, including its authenticated websocket."""
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )
    router = APIRouter(prefix="/api/v1")
    groups = {
        _auth_route: [
            ("GET", "/auth"),
            ("POST", "/auth"),
            ("POST", "/auth/login"),
            ("GET", "/sessions/me"),
        ],
        _meta: [
            ("GET", "/status"),
            ("GET", "/readiness"),
            ("POST", "/app-loaded"),
            ("GET", "/about"),
            ("GET", "/constants"),
            ("GET", "/specs"),
        ],
        _cfg_route: [
            ("GET", "/settings"),
            ("PUT", "/settings"),
            ("GET", "/settings/catalogue"),
            ("PUT", "/settings/secrets"),
            ("GET", "/auth/account"),
            ("PUT", "/auth/account"),
        ],
        _conn_route: [
            ("GET", "/connections"),
            ("POST", "/connections"),
            ("POST", "/connections/test"),
            ("DELETE", "/connections/{connection_id}"),
            ("POST", "/connections/{connection_id}/test"),
        ],
    }
    for handler, routes in groups.items():
        for method, path in routes:
            router.add_api_route(
                path, _handler(handler), methods=[method], name=handler.__name__
            )
    router.add_api_websocket_route("/ws", _ws)
    application.include_router(router)
