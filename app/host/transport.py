# ruff: noqa: INP001
"""FastAPI gateway, uniform response middleware, and asynchronous EventBus.

Description:
    Implements the unified HTTP/REST gateway, request-correlation and exception
    middleware, multi-channel asynchronous EventBus, Server-Sent Events (/events),
    and WebSocket gateway (/ws) for the HaruQuantAI host platform.

Purpose:
    FEAT-HOST-TRANSPORT - FastAPI gateway, envelope middleware, and async EventBus.

Key Capabilities:
    - FR-HOST-TRANSPORT-MIDDLEWARE: Inject X-Request-Id and X-Response-Time-Ms
      headers and isolate unhandled server exceptions into 500 error envelopes.
    - FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE: Transform HTTPException and
      RequestValidationError into ApiResponse.error envelopes.
    - FR-HOST-TRANSPORT-EVENT-BUS: Publish and subscribe to multi-channel host
      events with monotonic cursors, ring-buffer replay, and queue isolation.
    - FR-HOST-TRANSPORT-SSE-STREAMING: Stream real-time Server-Sent Events over
      GET /events with cursor replay, gap notification, and heartbeats.
    - FR-HOST-TRANSPORT-WS-STREAMING: Stream bidirectional JSON events and
      control frames over WebSocket /ws with dynamic channel subscriptions.
    - FR-HOST-TRANSPORT-SESSION-AUTH: Authenticate operator credentials on
      POST /auth/login and validate bearer tokens on GET /sessions/me.
    - FR-HOST-TRANSPORT-GATEWAY-APP: Assemble the FastAPI host gateway app and
      shell status endpoints across root, /api/v1, and /api/v2.
    - FR-HOST-TRANSPORT-CONNECTION-TEST: Validate endpoint connectivity, measure
      round-trip latency, and diagnose network/DNS failures.
    - FR-HOST-TRANSPORT-SERVLET-CONNECTION: REST endpoint controller for broker
      and exchange connection configurations and connectivity checks.
    - FR-HOST-TRANSPORT-SERVLET-CONSTANTS: Expose system constants, runtime
      environment paths, hardware specs, and supported timeframes.

Python API Usage:
    from app.host.transport import EventBus, create_host_app

CLI Usage:
    uv run python -m app.host.transport --test-bus
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.parse
from collections.abc import AsyncGenerator, Sequence
from contextlib import suppress
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from app.host import resources as _res
from app.host import session as _sess
from app.host.events import CORE_EVENT_CHANNELS, EventBus, HostEvent
from app.host.logging import TelemetryLogger, get_access_logger, get_logger
from app.host.persistence import HostPersistence
from app.host.response import ApiResponse, StandardError
from app.host.settings import RevisionConflictError, SettingsManager, settings
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

__all__ = [
    "CORE_EVENT_CHANNELS",
    "ConnectionTest",
    "EventBus",
    "HostEvent",
    "ServletConnection",
    "ServletConstants",
    "SettingsBatchUpdatePayload",
    "TransportGatewayService",
    "TransportMiddleware",
    "create_host_app",
    "create_transport_router",
    "register_transport_exception_handlers",
]

logger = get_logger(__name__)
access_logger = get_access_logger()

type _Pld = dict[str, Any]
type _Resp = JSONResponse
SUPPORTED_TIMEFRAMES: Final = ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")
_P: Final = "FR-HOST-TRANSPORT-"
FR_MW, FR_EX = f"{_P}MIDDLEWARE", f"{_P}EXCEPTION-ENVELOPE"
FR_SSE, FR_WS, FR_AUTH = f"{_P}SSE-STREAMING", f"{_P}WS-STREAMING", f"{_P}SESSION-AUTH"
FR_APP, CONNECTION_TEST_FR = f"{_P}GATEWAY-APP", f"{_P}CONNECTION-TEST"
SERVLET_CONNECTION_FR = f"{_P}SERVLET-CONNECTION"
SERVLET_CONSTANTS_FR = f"{_P}SERVLET-CONSTANTS"
_SEC_HEADERS: Final = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def _dct(**kw: Any) -> _Pld:
    return kw


def _info(fr_id: str, msg: str) -> None:
    logger.info("%s: %s", fr_id, msg, extra={"fr_id": fr_id})


def _warn(fr_id: str, msg: str) -> None:
    logger.warning("%s: %s", fr_id, msg, extra={"fr_id": fr_id})


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def _format_iso_expiry(expires_at_utc: str) -> str:
    with suppress(ValueError):
        if "T" not in expires_at_utc:
            dt = datetime.fromisoformat(expires_at_utc)
            return dt.replace(tzinfo=UTC).isoformat()
    return expires_at_utc


def extract_bearer_token(
    auth: str | None, query_token: str | None = None
) -> str | None:
    """Extract a bearer token from an ``Authorization`` header or query string."""
    if auth:
        scheme, _, remainder = auth.strip().partition(" ")
        if scheme.lower() == "bearer" and remainder.strip():
            return remainder.strip()
    return query_token.strip() if query_token and query_token.strip() else None


def _ok(req: Request, data: Any, msg: str = "OK", *, fx: bool = False) -> JSONResponse:
    rid = req.headers.get("x-request-id")
    r = ApiResponse.ok(data=data, message=msg, request_id=rid, side_effects=fx)
    return JSONResponse(status_code=200, content=r.to_dict())


def _err(req: Request, sc: int, code: str, msg: str, det: _Pld | None = None) -> _Resp:
    rid, err = req.headers.get("x-request-id"), StandardError(code, msg, det)
    r = ApiResponse.error(msg, err, request_id=rid)
    return JSONResponse(status_code=sc, content=r.to_dict())


async def _jbody(req: Request) -> _Pld:
    with suppress(ValueError):
        if isinstance(raw := await req.json(), dict):
            return raw
    return {}


def _qint(qp: Any, key: str, default: int | None = None) -> int | None:
    v = qp.get(key)
    return int(v) if v is not None and str(v).lstrip("-").isdigit() else default


class SettingsBatchUpdatePayload(BaseModel):
    """Strict logical-field patch with a mandatory optimistic revision."""

    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    changes: dict[str, dict[str, Any]]


class _AccountPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    username: str = Field(min_length=1, max_length=128)
    session_timeout_mins: int = Field(ge=1440, le=43200)
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(default="", max_length=1024)


_BUS_CACHE: list[EventBus] = []
_GLOBAL_LOCK = threading.Lock()


def get_global_event_bus() -> EventBus:
    """Return the lazily initialized global host ``EventBus``."""
    with _GLOBAL_LOCK:
        if not _BUS_CACHE:
            _BUS_CACHE.append(EventBus())
        return _BUS_CACHE[0]


class TransportMiddleware:
    """ASGI middleware injecting ``X-Request-Id`` and ``X-Response-Time-Ms``."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Intercept HTTP requests for correlation headers and error boundary."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        req, t0 = Request(scope, receive=receive), time.perf_counter()
        rid = (
            req.headers.get("x-request-id", "").strip()
            or f"req-{int(time.time() * 1000)}-{secrets.token_hex(4)}"
        )

        async def _send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                dur = (time.perf_counter() - t0) * 1000.0
                hdrs = MutableHeaders(scope=message)
                hdrs["X-Request-Id"], hdrs["X-Response-Time-Ms"] = rid, f"{dur:.2f}"
                for k, v in _SEC_HEADERS.items():
                    hdrs[k] = v
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
            dur = (time.perf_counter() - t0) * 1000.0
            m = f"{FR_MW}: HTTP {req.method} {req.url.path} in {dur:.2f}ms ({rid})."
            access_logger.info(m, extra={"fr_id": FR_MW})
        except Exception as exc:
            dur = (time.perf_counter() - t0) * 1000.0
            m = f"{FR_MW}: Unhandled exception on {req.method} {req.url.path}"
            logger.exception(m, extra={"fr_id": FR_MW})
            msg = str(exc) or "Internal server error occurred."
            det = {"exception_type": type(exc).__name__}
            err = StandardError(code="INTERNAL_SERVER_ERROR", message=msg, details=det)
            r = ApiResponse.error("Error.", err, request_id=rid, duration_ms=dur)
            h = {
                "X-Request-Id": rid,
                "X-Response-Time-Ms": f"{dur:.2f}",
                **_SEC_HEADERS,
            }
            res = JSONResponse(status_code=500, content=r.to_dict(), headers=h)
            await res(scope, receive, send)


def register_transport_exception_handlers(app: FastAPI) -> None:
    """Register ``HTTPException`` and ``RequestValidationError`` envelope handlers."""
    _info(FR_EX, "Registered transport exception handlers on FastAPI app.")

    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException) -> JSONResponse:
        raw: Any = exc.detail
        sc, msg = exc.status_code, (raw if isinstance(raw, str) else json.dumps(raw))
        det = raw if isinstance(raw, dict) else None
        _warn(FR_EX, f"HTTPException {sc} on {request.url.path}")
        return _err(request, sc, f"HTTP_{sc}", msg or f"HTTP {sc}", det)

    @app.exception_handler(RequestValidationError)
    async def _val_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        issues = [
            _dct(
                path=".".join(str(p) for p in i.get("loc", [])),
                code=str(i.get("type", "value_error")),
                message=str(i.get("msg", "Validation error")),
            )
            for i in exc.errors()
        ]
        det = {"issues": issues}
        res = _err(request, 422, "VALIDATION_ERROR", "Validation error.", det)
        payload = json.loads(bytes(res.body).decode("utf-8"))
        payload["error"]["issues"] = issues
        _warn(FR_EX, f"ValidationError on {request.url.path} ({len(issues)} issues).")
        return JSONResponse(status_code=422, content=payload)


def _parse_channels_param(raw_channels: str | None) -> list[str]:
    if not raw_channels or not raw_channels.strip():
        return ["*"]
    return [c.strip() for c in raw_channels.split(",") if c.strip()] or ["*"]


def _resolve_since_cursor(cur: int | None, last_id: str | None) -> int | None:
    if cur is not None:
        return cur
    return int(s) if last_id and (s := last_id.strip()).isdigit() else None


class ConnectionTest:
    """Network reachability, latency probe, and socket diagnostic utility."""

    @staticmethod
    def ping_endpoint(endpoint: str, timeout: float = 3.0) -> _Pld:
        """Ping remote or local server endpoint to verify network connectivity."""
        raw = endpoint.strip()
        p = urllib.parse.urlparse(raw if "://" in raw else f"tcp://{raw}")
        host, port = p.hostname or raw, p.port or (443 if p.scheme == "https" else 80)
        t0, ok, err_str = time.perf_counter(), False, None
        try:
            with socket.create_connection((host, port), timeout=timeout):
                ok = True
        except OSError as err:
            err_str = str(err)
        lat = round((time.perf_counter() - t0) * 1000.0, 2)
        if ok:
            _info(CONNECTION_TEST_FR, f"Endpoint {raw} reachable ({lat:.2f}ms).")
        else:
            _warn(CONNECTION_TEST_FR, f"Endpoint {raw} unreachable: {err_str}")
        d = _dct(endpoint=raw, host=host, port=port, reachable=ok)
        return {**d, "latency_ms": lat, "error": err_str}

    @staticmethod
    def check_latency(endpoint: str, samples: int = 3, timeout: float = 3.0) -> _Pld:
        """Measure round-trip latency across multiple samples and report packet loss."""
        num = max(1, min(samples, 10))
        probes = [ConnectionTest.ping_endpoint(endpoint, timeout) for _ in range(num)]
        lats = [float(r["latency_ms"]) for r in probes if r["reachable"]]
        loss = round(((num - len(lats)) / num) * 100.0, 2)
        avg = round(sum(lats) / len(lats), 2) if lats else 0.0
        mn, mx = (round(min(lats), 2), round(max(lats), 2)) if lats else (0.0, 0.0)
        _info(CONNECTION_TEST_FR, f"Latency {endpoint}: avg={avg:.2f}ms loss={loss}%.")
        d = _dct(endpoint=endpoint, samples=num, packet_loss_pct=loss)
        d |= _dct(avg_latency_ms=avg, min_latency_ms=mn, max_latency_ms=mx)
        return {**d, "successful_samples": len(lats)}

    @staticmethod
    def diagnose_network(host: str, port: int | None = None) -> _Pld:
        """Diagnose DNS resolution and socket connection parameters."""
        ips: list[str] = []
        dns_ok, dns_err, p_port = False, None, port or 80
        try:
            for item in socket.getaddrinfo(host, p_port, proto=socket.IPPROTO_TCP):
                if (ip := str(item[4][0])) not in ips:
                    ips.append(ip)
            dns_ok = True
        except (socket.gaierror, OSError) as err:
            dns_err = str(err)
        ok, r_err = False, None
        if dns_ok and ips:
            try:
                with socket.create_connection((ips[0], p_port), timeout=2.0):
                    ok = True
            except OSError as err:
                r_err = str(err)
        _info(CONNECTION_TEST_FR, f"Diagnosed {host}: dns={dns_ok} reachable={ok}.")
        d = _dct(host=host, port=p_port, dns_resolved=dns_ok, reachable=ok)
        d |= _dct(ip_addresses=ips, dns_error=dns_err, connection_error=r_err)
        return d


class ServletConnection:
    """REST endpoint handler for broker and exchange connection configurations."""

    def __init__(
        self, host_settings: Any = None, *, in_memory_only: bool = False
    ) -> None:
        self.settings = None if in_memory_only else (host_settings or settings)
        self._in_memory_connections: dict[str, _Pld] = {}

    def list_connections(self) -> list[_Pld]:
        """List existing broker and exchange connections."""
        conns: _Pld = {}
        if self.settings is not None:
            with suppress(AttributeError, KeyError, RuntimeError):
                if isinstance(scope := self.settings.get_scope("connections"), dict):
                    conns.update(scope)
        conns.update(self._in_memory_connections)
        recs = [
            TelemetryLogger.redact_secrets({"connection_id": cid, **cd})
            if isinstance(cd, dict)
            else _dct(connection_id=cid, value=cd)
            for cid, cd in conns.items()
            if cd != {} and cd is not None
        ]
        _info(SERVLET_CONNECTION_FR, f"Listed {len(recs)} connections.")
        return recs

    def save_connection(self, connection_id: str, data: _Pld) -> _Pld:
        """Save or update connection credentials in host settings."""
        rec = {**data, "connection_id": connection_id, "updated_at_utc": _now_utc_iso()}
        if self.settings is not None:
            try:
                self.settings.save_settings({"connections": {connection_id: rec}})
            except RevisionConflictError, RuntimeError, ValueError:
                if hasattr(self.settings, "set_in_memory"):
                    self.settings.set_in_memory("connections", connection_id, rec)
        self._in_memory_connections[connection_id] = rec
        _info(SERVLET_CONNECTION_FR, f"Saved connection '{connection_id}'.")
        redacted = TelemetryLogger.redact_secrets(rec)
        return dict(redacted) if isinstance(redacted, dict) else rec

    def delete_connection(self, connection_id: str) -> bool:
        """Delete connection configuration and cached tokens."""
        existed = False
        if self.settings is not None:
            with suppress(RevisionConflictError, RuntimeError, ValueError):
                if self.settings.get_scope("connections").get(connection_id):
                    existed = True
                    self.settings.save_settings({"connections": {connection_id: {}}})
        if connection_id in self._in_memory_connections:
            existed = True
            del self._in_memory_connections[connection_id]
        _info(SERVLET_CONNECTION_FR, f"Deleted '{connection_id}' (existed={existed}).")
        return existed

    def test_connection(
        self, connection_id: str | None = None, endpoint: str | None = None
    ) -> _Pld:
        """Test connection credentials and report latency status."""
        if not endpoint and connection_id:
            for c in self.list_connections():
                if c.get("connection_id") == connection_id:
                    endpoint = c.get("endpoint") or c.get("host")
                    break
        target = str(endpoint or "127.0.0.1")
        res = ConnectionTest.ping_endpoint(target)
        _info(SERVLET_CONNECTION_FR, f"Tested connection '{connection_id}' ({target}).")
        d = _dct(connection_id=connection_id, endpoint=target, test_result=res)
        return {**d, "timestamp": _now_utc_iso()}


class ServletConstants:
    """System constants, environment paths, and runtime metadata endpoints."""

    def __init__(self, session_mgr: Any = None, resource_mgr: Any = None) -> None:
        self.session_mgr = session_mgr or _sess.session_manager
        self.resource_mgr = resource_mgr

    def get_constants(self) -> _Pld:
        """Expose application version, build timestamp, and runtime paths."""
        _info(SERVLET_CONSTANTS_FR, "Retrieved system constants.")
        rt = f"CPython {sys.version.split()[0]} (FastAPI)"
        hid = self.session_mgr.host_instance_id
        d = _dct(application="HaruQuantAI", version="1.0.0", runtime=rt)
        d |= _dct(host_instance_id=hid, build_timestamp="2026-10-18T00:00:00Z")
        d |= _dct(data_directory=str(Path.cwd() / "data"))
        d |= _dct(core_channels=list(CORE_EVENT_CHANNELS))
        return {**d, "supported_timeframes": list(SUPPORTED_TIMEFRAMES)}

    def get_system_specs(self) -> _Pld:
        """Serve system resource limits, concurrency specs, and supported timeframes."""
        cpus = max(1, os.cpu_count() or 1)
        _info(SERVLET_CONSTANTS_FR, f"Retrieved system specs (cores={cpus}).")
        d = _dct(cpu_cores=cpus, hardware_concurrency=cpus)
        d["supported_timeframes"] = list(SUPPORTED_TIMEFRAMES)
        d["memory_headroom"] = asdict(_res.check_memory_headroom())
        d["worker_capacity"] = asdict(_res.get_worker_capacity())
        d["system_health"] = asdict(_res.inspect_resources())
        return d


class TransportGatewayService:
    """Coordinates session auth, shell status, SSE, and WebSocket endpoints."""

    def __init__(self, **kw: Any) -> None:
        self.event_bus: EventBus = kw.get("event_bus") or get_global_event_bus()
        sm = kw.get("session_mgr") or _sess.session_manager
        self.session_mgr: _sess.SessionManager = sm
        self.resource_mgr, self.job_mgr = kw.get("resource_mgr"), kw.get("job_mgr")
        self.settings: SettingsManager = (
            settings if kw.get("host_settings") is None else kw["host_settings"]
        )
        self.password_hash: str | None = kw.get("password_hash")
        self.require_auth: bool = bool(kw.get("require_auth", False))
        self.heartbeat_sec: float = float(kw.get("heartbeat_sec", 15.0))
        self.started_at, self.app_loaded_acknowledged = time.monotonic(), False
        self.connection_servlet = ServletConnection(host_settings=self.settings)
        self.constants_servlet = ServletConstants(self.session_mgr, self.resource_mgr)

    def _verify_session(self, req: Request, qtok: str | None = None) -> Any:
        token = extract_bearer_token(req.headers.get("authorization"), qtok)
        return self.session_mgr.verify_session(token) if token is not None else None

    def _check_password(self, candidate_password: str) -> bool:
        self.settings.reload()
        db_hash = self.settings.get("user_access", "password_hash", None)
        cfg = db_hash if isinstance(db_hash, str) and db_hash else self.password_hash
        return (
            _sess.verify_password(candidate_password, cfg)
            if cfg
            else not self.require_auth
        )

    async def _auth_route(self, request: Request) -> JSONResponse:
        if request.method == "GET":
            if (rec := self._verify_session(request)) is None:
                _warn(FR_AUTH, "Unauthorized /sessions/me call.")
                msg = "Valid session token required."
                return _err(request, 401, "UNAUTHORIZED", msg)
            _info(FR_AUTH, f"Verified active session '{rec.session_id}'.")
            d = {**rec.to_dict(), "expires_at": _format_iso_expiry(rec.expires_at_utc)}
            return _ok(request, d, "Active session verified.")
        body = await _jbody(request)
        peer = request.client.host if request.client else "127.0.0.1"
        if not self._check_password(str(body.get("password") or "")):
            _warn(FR_AUTH, f"Rejected login attempt from {peer}.")
            return _err(request, 401, "INVALID_CREDENTIALS", "Invalid host password.")
        def_u = str(
            self.settings.get("user_access", "username", "haruquantai") or "admin"
        )
        u = str(body.get("username") or "").strip() or def_u
        duration = int(self.settings.get("user_access", "session_timeout_mins", 1440))
        tok, rec = self.session_mgr.create_session(
            username=u, peer_id=peer, duration_mins=duration
        )
        _info(FR_AUTH, f"Issued session '{rec.session_id}' for '{rec.username}'.")
        exp = _format_iso_expiry(rec.expires_at_utc)
        d = _dct(token=tok, expires_at=exp, session_id=rec.session_id)
        return _ok(request, {**d, "username": rec.username}, "Authenticated.", fx=True)

    async def _meta(self, request: Request) -> JSONResponse:
        p, eb, hid = request.url.path, self.event_bus, self.session_mgr.host_instance_id
        fx = False
        if p.endswith("/app-loaded"):
            if self.require_auth and self._verify_session(request) is None:
                return _err(request, 401, "UNAUTHORIZED", "Active session required.")
            self.app_loaded_acknowledged, fx = True, True
            eb.publish("system", "app_loaded", {"host_instance_id": hid})
            _info(FR_APP, f"Browser shell /app-loaded acknowledged (host={hid}).")
            data: Any = _dct(acknowledged=True, host_instance_id=hid)
        elif p.endswith("/publish"):
            b, fx = await _jbody(request), True
            ch = str(b.get("channel") or "system")
            et = str(b.get("event_type") or "update")
            pld = b["payload"] if isinstance(b.get("payload"), dict) else {}
            data = eb.publish(ch, et, pld).model_dump()
        elif p.endswith(("/about", "/constants")):
            data = self.constants_servlet.get_constants()
        elif p.endswith("/specs"):
            data = self.constants_servlet.get_system_specs()
        elif p.endswith("/channels"):
            cc = list(CORE_EVENT_CHANNELS)
            d = _dct(core_channels=cc, active_channels=eb.channels)
            data = {**d, "current_cursor": eb.current_cursor}
        elif p.endswith("/snapshot"):
            qp = request.query_params
            ch, cur = qp.get("channel", "*"), _qint(qp, "since_cursor")
            data = eb.get_snapshot(ch, cur, _qint(qp, "limit", 100) or 100).model_dump()
        else:
            up = round(max(0.0, time.monotonic() - self.started_at), 3)
            d = _dct(state="READY", is_ready=True, version="1.0.0", uptime_seconds=up)
            d |= _dct(cpu_count=max(1, os.cpu_count() or 1), host_instance_id=hid)
            d |= _dct(app_loaded=self.app_loaded_acknowledged, channels=eb.channels)
            data = d
        return _ok(request, data, fx=fx)

    def _require_scope(self, request: Request, scope: str) -> JSONResponse | None:
        if not self.require_auth:
            return None
        sess = self._verify_session(request)
        if sess is not None and self.session_mgr.authorize(sess, scope):
            return None
        sc, code = (401, "UNAUTHORIZED") if sess is None else (403, "FORBIDDEN")
        return _err(request, sc, code, "Active authorized session required.")

    async def _settings_route(self, request: Request) -> JSONResponse:
        is_put = request.method == "PUT"
        scope = "settings:write" if is_put else "settings:read"
        if (denied := self._require_scope(request, scope)) is not None:
            return denied
        try:
            if not is_put:
                data = (
                    self.settings.get_catalogue()
                    if request.url.path.endswith("/catalogue")
                    else self.settings.get_snapshot()
                )
                return _ok(request, data)
            body = SettingsBatchUpdatePayload.model_validate(await _jbody(request))
            data = self.settings.save_changes(
                body.changes,
                expected_revision=body.expected_revision,
                include_secrets=request.url.path.endswith("/secrets"),
            )
            if data["wrote"]:
                self.event_bus.publish(
                    "settings.changed",
                    "updated",
                    {
                        "revision": data["revision"],
                        "scopes": sorted(body.changes),
                    },
                )
            return _ok(request, data, fx=data["wrote"])
        except RevisionConflictError as exc:
            return _err(
                request,
                409,
                "REVISION_CONFLICT",
                "Settings changed; reload and retry.",
                {
                    "expected_revision": exc.expected_revision,
                    "current_revision": exc.current_revision,
                },
            )
        except ValidationError, ValueError:
            _warn(FR_APP, "Rejected invalid settings patch.")
            return _err(
                request,
                422,
                "INVALID_SETTINGS",
                "Invalid, unknown or protected settings field.",
            )
        except HostPersistence.Error:
            _warn(FR_APP, "Settings persistence failed.")
            return _err(
                request,
                503,
                "SETTINGS_UNAVAILABLE",
                "Settings database is unavailable; no success acknowledged.",
            )

    def _account_password(self, body: _AccountPayload) -> str:
        if not self._check_password(body.current_password):
            raise HTTPException(status_code=401, detail="Invalid current password")
        current = (
            self.settings.get("user_access", "password_hash", None)
            or self.password_hash
        )
        result = (
            _sess.hash_password(body.new_password) if body.new_password else current
        )
        if not isinstance(result, str) or not result:
            raise ValueError("A configured account password is required")
        return result

    async def _account_route(self, request: Request) -> JSONResponse:
        scope = "settings:read" if request.method == "GET" else "settings:write"
        if (denied := self._require_scope(request, scope)) is not None:
            return denied
        try:
            if request.method == "GET":
                return _ok(request, self.settings.get_account())
            body = _AccountPayload.model_validate(await _jbody(request))
            new_hash = self._account_password(body)
            revision = self.settings.save_account(
                body.username,
                body.session_timeout_mins,
                new_hash,
                expected_revision=body.expected_revision,
            )
            self.session_mgr.invalidate_sessions()
            self.password_hash = None
            self.event_bus.publish(
                "settings.changed",
                "updated",
                {"revision": revision, "scopes": ["user.access"]},
            )
            return _ok(request, {"revision": revision, "reauthenticate": True}, fx=True)
        except RevisionConflictError as exc:
            return _err(
                request,
                409,
                "REVISION_CONFLICT",
                "Account changed; reload and retry.",
                {"current_revision": exc.current_revision},
            )
        except (KeyError, ValidationError, ValueError) as exc:
            _warn(FR_AUTH, "Rejected invalid account update.")
            missing = isinstance(exc, KeyError)
            return _err(
                request,
                503 if missing else 422,
                "ACCOUNT_UNCONFIGURED" if missing else "INVALID_ACCOUNT",
                "Account identity and session duration are not configured."
                if missing
                else "Invalid account update.",
            )
        except HostPersistence.Error:
            return _err(
                request, 503, "SETTINGS_UNAVAILABLE", "Account database unavailable."
            )

    async def _conn_route(
        self, request: Request, connection_id: str | None = None
    ) -> JSONResponse:
        is_rd = request.method == "GET" or request.url.path.endswith("/test")
        scope = "connections:read" if is_rd else "connections:write"
        if (denied := self._require_scope(request, scope)) is not None:
            return denied
        cs = self.connection_servlet
        if request.method == "GET":
            recs = cs.list_connections()
            return _ok(request, _dct(connections=recs, count=len(recs)))
        if request.method == "DELETE":
            if not cs.delete_connection(connection_id or ""):
                return _err(request, 404, "NOT_FOUND", "Connection not found.")
            d = _dct(connection_id=connection_id, deleted=True)
            return _ok(request, d, fx=True)
        body = await _jbody(request)
        if request.url.path.endswith("/test"):
            cid = connection_id or body.get("connection_id")
            return _ok(request, cs.test_connection(cid, body.get("endpoint")))
        cid = str(body.get("connection_id") or f"conn-{secrets.token_hex(4)}")
        return _ok(request, cs.save_connection(cid, body), fx=True)

    def _resolve_mgr(self, request: Request, attr: str, fallback: Any) -> Any:
        rt = getattr(request.app.state, "runtime", None)
        return fallback or getattr(rt, attr, None)

    async def _diag(self, request: Request) -> JSONResponse:
        if (denied := self._require_scope(request, "diagnostics:read")) is not None:
            return denied
        rm = self._resolve_mgr(request, "resource_manager", self.resource_mgr)
        wd = rm.check_memory_headroom() if rm else _res.check_memory_headroom()
        hlth = rm.inspect_resources() if rm else _res.inspect_resources()
        d = _dct(status=hlth.status, hardware=asdict(_res.probe_hardware()))
        d |= _dct(memory_watchdog=asdict(wd), database=asdict(hlth.database))
        d |= _dct(worker_capacity=asdict(_res.get_worker_capacity()))
        return _ok(request, {**d, "storage": asdict(hlth.storage)})

    async def _jobs_route(self, req: Request, job_id: str | None = None) -> _Resp:
        scope = "jobs:write" if req.method == "POST" else "jobs:read"
        if (denied := self._require_scope(req, scope)) is not None:
            return denied
        jm = self._resolve_mgr(req, "job_manager", self.job_mgr)
        if req.method == "POST":
            if not (bool(jm.cancel_job(job_id)) if jm and job_id else False):
                return _err(req, 404, "JOB_NOT_CANCELLABLE", "Job not cancellable.")
            self.event_bus.publish("jobs", "cancelled", {"job_id": job_id})
            return _ok(req, _dct(job_id=job_id, cancelled=True), fx=True)
        if job_id is not None:
            pk = {"job_id": job_id}
            db_r: list[_Pld] = (
                []
                if jm
                else HostPersistence.read_records("host_jobs", pk_values=pk, limit=1)
            )
            row = (
                r.to_dict()
                if jm and (r := jm.get_job(job_id))
                else (db_r[0] if db_r else None)
            )
            return (
                _ok(req, row) if row else _err(req, 404, "JOB_NOT_FOUND", "Not found.")
            )
        sf = req.query_params.get("status_filter")
        lim, w = (
            _qint(req.query_params, "limit", 50) or 50,
            ({"status": sf} if sf else None),
        )
        jobs = (
            [r.to_dict() for r in jm.list_jobs(status=sf, limit=lim)]
            if jm
            else HostPersistence.read_records("host_jobs", where=w, limit=lim)
        )
        return _ok(req, _dct(count=len(jobs), jobs=jobs))

    async def _sse(self, request: Request) -> StreamingResponse | JSONResponse:
        qp, ah = request.query_params, request.headers.get("authorization")
        tok = extract_bearer_token(ah, qp.get("token"))
        if (self.require_auth or tok) and not (
            tok and self.session_mgr.verify_session(tok)
        ):
            return _err(request, 401, "UNAUTHORIZED", "Valid session token required.")
        h = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
        h["X-Accel-Buffering"] = "no"
        return StreamingResponse(
            self._sse_gen(request, tok), media_type="text/event-stream", headers=h
        )

    async def _sse_gen(self, req: Request, tok: str | None) -> AsyncGenerator[str]:
        qp = req.query_params
        cur = _resolve_since_cursor(
            _qint(qp, "since_cursor"), req.headers.get("last-event-id")
        )
        chans, lim = _parse_channels_param(qp.get("channels")), _qint(qp, "limit")
        sub_id, q, replay, gap = self.event_bus.subscribe(chans, since_cursor=cur)
        _info(FR_SSE, f"SSE connected (sub_id={sub_id} channels={chans}).")
        sent = 0
        try:
            if gap:
                g = json.dumps(_dct(channel="system", event_type="gap"))
                yield f"event: system.gap\ndata: {g}\n\n"
            while (lim is None or sent < lim) and not await req.is_disconnected():
                if tok and self.session_mgr.verify_session(tok) is None:
                    break
                try:
                    ev = (
                        replay.pop(0)
                        if replay
                        else await asyncio.wait_for(q.get(), self.heartbeat_sec)
                    )
                    d_json = ev.model_dump_json()
                    yield f"id: {ev.cursor}\nevent: {ev.channel}\ndata: {d_json}\n\n"
                    sent += 1
                except TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.event_bus.unsubscribe(sub_id)
            _info(FR_SSE, f"SSE disconnected (sub_id={sub_id}).")

    async def _ws(self, ws: WebSocket) -> None:
        qp = ws.query_params
        tok = extract_bearer_token(ws.headers.get("authorization"), qp.get("token"))
        if self.require_auth and not (tok and self.session_mgr.verify_session(tok)):
            await ws.close(code=1008)
            return
        await ws.accept()
        chans = _parse_channels_param(qp.get("channels"))
        sub_id, q, replay, gap = self.event_bus.subscribe(
            chans, _qint(qp, "since_cursor")
        )
        _info(FR_WS, f"WebSocket connected (sub_id={sub_id} channels={chans}).")
        try:
            if gap:
                await ws.send_json(_sys_frame("gap", {"message": "Gap."}))
            for ev in replay:
                await ws.send_json(ev.model_dump())
            while True:
                rt, qt = (
                    asyncio.create_task(ws.receive_json()),
                    asyncio.create_task(q.get()),
                )
                done, pend = await asyncio.wait(
                    {rt, qt}, return_when=asyncio.FIRST_COMPLETED
                )
                for t in pend:
                    t.cancel()
                await asyncio.gather(*pend, return_exceptions=True)
                if qt in done:
                    await ws.send_json(qt.result().model_dump())
                if rt in done and not await self._on_ws_msg(ws, sub_id, rt.result()):
                    break
        except WebSocketDisconnect:
            pass
        finally:
            self.event_bus.unsubscribe(sub_id)
            _info(FR_WS, f"WebSocket disconnected (sub_id={sub_id}).")

    async def _on_ws_msg(self, ws: WebSocket, sub_id: str, msg: Any) -> bool:
        if not isinstance(msg, dict):
            return True
        act = str(msg.get("action", "")).lower()
        if act == "close":
            return False
        if act == "ping":
            await ws.send_json(_sys_frame("pong", {}))
        elif act == "subscribe" and isinstance(raw := msg.get("channels"), list):
            chans = [str(c) for c in raw if str(c).strip()] or ["*"]
            self.event_bus.update_subscription(sub_id, chans)
            await ws.send_json(_sys_frame("subscribed", {"channels": chans}))
        elif act == "publish":
            pld = msg["payload"] if isinstance(msg.get("payload"), dict) else {}
            ch = str(msg.get("channel", "system"))
            et = str(msg.get("event_type", "update"))
            self.event_bus.publish(ch, et, pld)
        return True


def _sys_frame(et: str, pld: _Pld) -> _Pld:
    return _dct(channel="system", event_type=et, timestamp=_now_utc_iso(), payload=pld)


_ROUTE_SPECS: Final[str] = (
    "GET:/auth:_auth_route POST:/auth:_auth_route POST:/auth/login:_auth_route "
    "GET:/sessions/me:_auth_route GET:/status:_meta GET:/readiness:_meta "
    "POST:/app-loaded:_meta GET:/about:_meta GET:/constants:_meta GET:/specs:_meta "
    "GET:/settings:_settings_route PUT:/settings:_settings_route "
    "GET:/settings/catalogue:_settings_route PUT:/settings/secrets:_settings_route "
    "GET:/auth/account:_account_route PUT:/auth/account:_account_route "
    "GET:/diagnostics:_diag GET:/resources:_diag GET:/jobs:_jobs_route "
    "GET:/jobs/{job_id}:_jobs_route POST:/jobs/{job_id}/cancel:_jobs_route "
    "POST:/events/publish:_meta GET:/events/snapshot:_meta "
    "GET:/events/channels:_meta GET:/events:_sse GET:/connections:_conn_route "
    "POST:/connections:_conn_route WS:/ws:_ws POST:/connections/test:_conn_route "
    "DELETE:/connections/{connection_id}:_conn_route "
    "POST:/connections/{connection_id}/test:_conn_route"
)


def create_transport_router(*, prefix: str = "", **kwargs: Any) -> APIRouter:
    """Create a FastAPI ``APIRouter`` exposing host auth, shell, SSE, and WS routes."""
    s = TransportGatewayService(**kwargs)
    router = APIRouter(prefix=prefix, tags=["host-transport"])
    for spec in _ROUTE_SPECS.split():
        method, path, attr = spec.split(":")
        fn = getattr(s, attr)
        if method == "WS":
            router.add_api_websocket_route(path, fn)
        else:
            router.add_api_route(path, fn, methods=[method], response_model=None)
    _info(FR_APP, f"Created transport router (prefix='{prefix or '/'}').")
    return router


def create_host_app(
    *, extra_routers: Sequence[APIRouter] | None = None, **kwargs: Any
) -> FastAPI:
    """Create the configured FastAPI host gateway application."""
    bus = kwargs.get("event_bus") or get_global_event_bus()
    sessions = kwargs.get("session_mgr") or _sess.session_manager
    kwargs.update(event_bus=bus, session_mgr=sessions)
    app = FastAPI(title="HaruQuantAI Host Platform Gateway", version="1.0.0")
    app.state.event_bus, app.state.session_manager = bus, sessions
    origins = [
        f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (3000, 8000)
    ]
    cors_kw: _Pld = _dct(allow_origins=origins, allow_credentials=True)
    app.add_middleware(
        CORSMiddleware, **cors_kw, allow_methods=["*"], allow_headers=["*"]
    )
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)
    for pfx in ("", "/api/v1", "/api/v2"):
        app.include_router(create_transport_router(prefix=pfx, **kwargs))
    for extra in extra_routers or ():
        app.include_router(extra)
    _info(FR_APP, f"Initialized FastAPI host gateway ({sessions.host_instance_id}).")
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for verifying EventBus and ConnectionTest diagnostics."""
    p = argparse.ArgumentParser(prog="app.host.transport")
    p.add_argument("--test-bus", action="store_true")
    args, bus = p.parse_args(argv), EventBus()
    if args.test_bus:
        for ch in CORE_EVENT_CHANNELS:
            bus.publish(ch, "self_test", {"channel": ch, "ok": True})
        out: Any = bus.get_snapshot("*").model_dump()
    else:
        with socket.create_server(("127.0.0.1", 0)) as srv:
            port = int(srv.getsockname()[1])
            loc = f"127.0.0.1:{port}"
            ct = _dct(
                ping_local=ConnectionTest.ping_endpoint(loc, timeout=0.5),
                ping_remote=ConnectionTest.ping_endpoint("https://1.1.1.1", 0.5),
                latency=ConnectionTest.check_latency(loc, samples=3, timeout=0.5),
                diagnostics=ConnectionTest.diagnose_network("127.0.0.1", port),
                diagnostics_failure=ConnectionTest.diagnose_network(
                    "invalid.haruquantai.local", 80
                ),
            )
            sc = ServletConnection(in_memory_only=True)
            saved = sc.save_connection("demo-conn", {"name": "Local", "endpoint": loc})
            s_conn = _dct(
                saved=saved,
                listed=sc.list_connections(),
                tested=sc.test_connection("demo-conn"),
                deleted=sc.delete_connection("demo-conn"),
            )
        consts = ServletConstants()
        s_const = _dct(
            constants=consts.get_constants(),
            system_specs=consts.get_system_specs(),
        )
        out = _dct(
            core_channels=list(CORE_EVENT_CHANNELS),
            ring_capacity=bus.ring_capacity,
            max_queue_size=bus.max_queue_size,
            connection_test=ct,
            servlet_connection=s_conn,
            servlet_constants=s_const,
        )
    sys.stdout.write(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
