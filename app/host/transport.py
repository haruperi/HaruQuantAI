# ruff: noqa: INP001
"""FastAPI gateway, network diagnostics, connection CRUD, and system constants.

Description:
    Implements the unified HTTP/REST/SSE/WebSocket gateway, request-correlation
    and exception middleware, network reachability and latency diagnostics
    (ConnectionTest), HostPersistence-backed broker/exchange connection CRUD with
    in-memory secret-vault isolation (ServletConnection), and runtime constants
    and hardware specification endpoints (ServletConstants).
Purpose:
    FEAT-HOST-TRANSPORT - FastAPI gateway, network diagnostics, connection CRUD,
    and system constants.
Key Capabilities:
    - FR-HOST-TRANSPORT-PING: Ping [ConnectionTest.ping_endpoint()] (INFO).
    - FR-HOST-TRANSPORT-LATENCY: Latency [ConnectionTest.check_latency()] (INFO).
    - FR-HOST-TRANSPORT-DIAGNOSE: DNS [ConnectionTest.diagnose_network()] (INFO).
    - FR-HOST-SERVLET-CONN-LIST: List [ServletConnection.list_connections()] (INFO).
    - FR-HOST-SERVLET-CONN-SAVE: Save [ServletConnection.save_connection()] (INFO).
    - FR-HOST-SERVLET-CONN-DELETE: Del [ServletConnection.delete_connection()] (INFO).
    - FR-HOST-SERVLET-CONN-TEST: Test [ServletConnection.test_connection()] (INFO).
    - FR-HOST-SERVLET-CONSTANTS: Info [ServletConstants.get_constants()] (INFO).
    - FR-HOST-SERVLET-SPECS: Specs [ServletConstants.get_system_specs()] (INFO).
Python API Usage:
    from app.host.transport import ConnectionTest, ServletConnection, ServletConstants
CLI Usage:
    uv run python -m app.host.transport
"""

from __future__ import annotations

import asyncio
import socket
import sys
from argparse import ArgumentParser
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict
from datetime import UTC, datetime
from json import dumps, loads
from os import cpu_count
from pathlib import Path
from secrets import token_hex
from tempfile import TemporaryDirectory
from time import monotonic, perf_counter
from typing import Any

from app.host import resources as _res
from app.host import session as _sess
from app.host.events import CORE_EVENT_CHANNELS, EventBus, HostEvent
from app.host.logging import TelemetryLogger, get_access_logger, get_logger
from app.host.persistence import HostPersistence
from app.host.response import ApiResponse
from app.host.settings import RevisionConflictError, SettingsManager, settings
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

logger, access_logger = get_logger(__name__), get_access_logger()
type _Pld = dict[str, Any]
SUPPORTED_TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")
_SEC_K = ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy")
_SEC_HDRS = dict(zip(_SEC_K, ("nosniff", "DENY", "no-referrer"), strict=True))
_BUS_CACHE: list[EventBus] = []


def _log(fr: str, msg: str, *, warn: bool = False) -> None:
    (logger.warning if warn else logger.info)("%s: %s", fr, msg, extra={"fr_id": fr})


def extract_bearer_token(auth: str | None, qtok: str | None = None) -> str | None:
    """Extract a bearer token from an ``Authorization`` header or query string."""
    if auth and (parts := auth.strip().partition(" "))[0].lower() == "bearer":
        return parts[2].strip() or None
    return qtok.strip() if qtok and qtok.strip() else None


def _ok(req: Request, data: Any, msg: str = "OK", *, fx: bool = False) -> JSONResponse:
    rid, meta = req.headers.get("x-request-id"), {"message": msg, "side_effects": fx}
    return JSONResponse(ApiResponse.ok(data=data, meta=meta, request_id=rid), 200)


def _err(req: Request, sc: int, c: str, m: str, det: _Pld | None = None) -> Any:
    rid = req.headers.get("x-request-id")
    body = ApiResponse.error(c, m, details=det, status_code=sc, request_id=rid)
    return JSONResponse(body, sc)


async def _jbody(req: Request) -> _Pld:
    with suppress(ValueError):
        if isinstance(raw := await req.json(), dict):
            return raw
    return {}


def _qint(qp: Any, key: str, default: int | None = None) -> int | None:
    v = qp.get(key)
    return int(v) if v is not None and str(v).lstrip("-").isdigit() else default


def get_global_event_bus() -> EventBus:
    """Return the lazily initialized global host ``EventBus``."""
    if not _BUS_CACHE:
        _BUS_CACHE.append(EventBus())
    return _BUS_CACHE[0]


class SettingsBatchUpdatePayload(BaseModel):
    """Strict logical-field patch with a mandatory optimistic revision."""

    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0)
    changes: dict[str, dict[str, Any]]


class TransportMiddleware:
    """ASGI middleware injecting ``X-Request-Id`` and ``X-Response-Time-Ms``."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Intercept HTTP requests for correlation headers and error boundary."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        req, t0 = Request(scope, receive=receive), perf_counter()
        rid = req.headers.get("x-request-id", "").strip() or f"req-{token_hex(6)}"
        fr = "FR-HOST-TRANSPORT-MIDDLEWARE"

        async def _send(msg: Message) -> None:
            if msg["type"] == "http.response.start":
                dur = f"{(perf_counter() - t0) * 1000.0:.2f}"
                h = {"X-Request-Id": rid, "X-Response-Time-Ms": dur, **_SEC_HDRS}
                MutableHeaders(scope=msg).update(h)
            await send(msg)

        try:
            await self.app(scope, receive, _send)
            access_logger.info("%s: %s", fr, req.url.path, extra={"fr_id": fr})
        except Exception as exc:
            logger.exception("%s: Unhandled error", fr, extra={"fr_id": fr})
            det = {"exception_type": type(exc).__name__}
            res = _err(req, 500, "INTERNAL_SERVER_ERROR", str(exc) or "Error.", det)
            await res(scope, receive, _send)


def register_transport_exception_handlers(app: FastAPI) -> None:
    """Register ``HTTPException`` and ``RequestValidationError`` envelope handlers."""
    fr = "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE"
    _log(fr, "Registered transport exception handlers on FastAPI app.")

    @app.exception_handler(HTTPException)
    async def _http_exc(req: Request, exc: HTTPException) -> Any:
        raw: Any = exc.detail
        sc, msg = exc.status_code, (raw if isinstance(raw, str) else dumps(raw))
        _log(fr, f"HTTPException {sc} on {req.url.path}", warn=True)
        return _err(req, sc, f"HTTP_{sc}", msg, raw if isinstance(raw, dict) else None)

    @app.exception_handler(RequestValidationError)
    async def _val_exc(req: Request, exc: RequestValidationError) -> Any:
        ks = ("path", "code", "message")
        errs = exc.errors()
        vals = [(".".join(map(str, i["loc"])), i["type"], i["msg"]) for i in errs]
        issues = [dict(zip(ks, v, strict=True)) for v in vals]
        res = _err(req, 422, "VALIDATION_ERROR", "Validation.", {"issues": issues})
        payload = loads(bytes(res.body).decode("utf-8"))
        payload["error"]["issues"] = issues
        _log(fr, f"ValidationError on {req.url.path}", warn=True)
        return JSONResponse(payload, 422)


class ConnectionTest:
    """Network reachability, latency probe, and socket diagnostic utility."""

    @staticmethod
    def _parse(target: str, def_port: int = 80) -> tuple[str, str, int]:
        raw = target.strip()
        s, _, rest = raw.partition("://") if "://" in raw else ("tcp", "", raw)
        h, _, p = rest.partition("/")[0].partition(":")
        port = int(p) if p.isdigit() else (443 if s == "https" else def_port)
        return raw, h or raw, port

    @staticmethod
    def ping_endpoint(url: str, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
        """Ping remote and local server endpoints to verify network connectivity."""
        raw, host, port = ConnectionTest._parse(url, 80)
        t0, ok, err_str = perf_counter(), False, None
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                ok = True
        except OSError as err:
            err_str = str(err)
        lat = round((perf_counter() - t0) * 1000.0, 2)
        _log("FR-HOST-TRANSPORT-PING", f"Ping {raw} ok={ok} ({lat}ms).", warn=not ok)
        d: _Pld = {"url": raw, "endpoint": raw, "host": host, "port": port}
        return {**d, "reachable": ok, "latency_ms": lat, "error": err_str}

    @staticmethod
    def check_latency(
        host: str, *, port: int = 443, samples: int = 3
    ) -> dict[str, Any]:
        """Measure round-trip latency and report packet loss across probes."""
        _, h, p = ConnectionTest._parse(host, port)
        num, tgt = max(1, min(samples, 10)), f"{h}:{p}"
        prs = [
            ConnectionTest.ping_endpoint(tgt, timeout_seconds=1.5) for _ in range(num)
        ]
        lats = [float(r["latency_ms"]) for r in prs if r["reachable"]]
        loss = round(((num - len(lats)) / num) * 100.0, 2)
        avg = round(sum(lats) / len(lats), 2) if lats else 0.0
        mn, mx = (round(min(lats), 2), round(max(lats), 2)) if lats else (0.0, 0.0)
        _log("FR-HOST-TRANSPORT-LATENCY", f"Latency {tgt}: avg={avg}ms loss={loss}%.")
        d = {"host": h, "port": p, "endpoint": tgt, "samples": num}
        d |= {"successful_samples": len(lats), "packet_loss_pct": loss}
        return {**d, "avg_latency_ms": avg, "min_latency_ms": mn, "max_latency_ms": mx}

    @staticmethod
    def diagnose_network(target: str) -> dict[str, Any]:
        """Diagnose DNS resolution and socket connection failures."""
        raw, host, port = ConnectionTest._parse(target, 80)
        ips: list[str] = []
        dns_ok, dns_err = False, None
        try:
            for item in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
                if (ip := str(item[4][0])) not in ips:
                    ips.append(ip)
            dns_ok = True
        except OSError as err:
            dns_err = str(err)
        fn = ConnectionTest.ping_endpoint
        pr: _Pld = fn(f"{ips[0]}:{port}", timeout_seconds=2.0) if ips else {}
        ok, r_err = bool(pr.get("reachable", False)), pr.get("error")
        _log("FR-HOST-TRANSPORT-DIAGNOSE", f"Diagnosed {raw}: dns={dns_ok} ok={ok}.")
        d = {"target": raw, "host": host, "port": port, "dns_resolved": dns_ok}
        d |= {"reachable": ok, "ip_addresses": ips, "dns_error": dns_err}
        return {**d, "connection_error": r_err}


class ServletConnection:
    """HostPersistence-backed broker and exchange connection controller."""

    def __init__(self) -> None:
        self._vault: dict[str, str] = {}

    def list_connections(self, provider: str | None = None) -> list[dict[str, Any]]:
        """List existing broker and exchange connections from HostPersistence."""
        flt = {"scope": provider} if provider else None
        rows = HostPersistence.read_entity("connection", filters=flt)
        recs: list[dict[str, Any]] = []
        for row in rows:
            with suppress(ValueError, TypeError):
                if isinstance(pld := loads(str(row.get("payload", "{}"))), dict):
                    merged = {"connection_id": row["entity_id"], **pld}
                    if isinstance(red := TelemetryLogger.redact_secrets(merged), dict):
                        recs.append(red)
        _log("FR-HOST-SERVLET-CONN-LIST", f"Listed {len(recs)} connections.")
        return recs

    def save_connection(self, connection: Mapping[str, Any]) -> dict[str, Any]:
        """Save public connection metadata and vault references via HostPersistence."""
        cid = str(connection.get("connection_id") or f"conn-{token_hex(4)}").strip()
        prov = str(connection.get("provider") or "default").strip() or "default"
        now, red = (
            datetime.now(UTC).isoformat(),
            TelemetryLogger.redact_secrets(dict(connection)),
        )
        pub: _Pld = dict(red) if isinstance(red, dict) else {}
        v_refs: dict[str, str] = dict(pub.get("vault_refs") or {})
        for k, v in connection.items():
            if isinstance(v, str) and v and pub.get(k) != v:
                ref = f"vault://connections/{cid}/{k}"
                self._vault[ref], v_refs[k] = v, ref
        pub |= {"connection_id": cid, "provider": prov, "vault_refs": v_refs}
        pub["updated_at_utc"] = now
        row = {"scope": prov, "payload": dumps(pub), "updated_at_utc": now}
        if HostPersistence.read_entity("connection", cid, limit=1):
            HostPersistence.update_entity("connection", cid, row)
        else:
            HostPersistence.create_entity(
                "connection", {"entity_id": cid, "created_at_utc": now, **row}
            )
        _log("FR-HOST-SERVLET-CONN-SAVE", f"Saved connection '{cid}'.")
        return pub

    def delete_connection(self, connection_id: str) -> dict[str, Any]:
        """Delete connection metadata via HostPersistence and revoke vault refs."""
        pfx = f"vault://connections/{connection_id}/"
        rev = [self._vault.pop(k) for k in list(self._vault) if k.startswith(pfx)]
        res = HostPersistence.delete_entity("connection", connection_id)
        ok = bool(int(res.get("deleted", 0)) > 0 or rev)
        _log("FR-HOST-SERVLET-CONN-DELETE", f"Deleted '{connection_id}' (ok={ok}).")
        d = {"connection_id": connection_id, "deleted": ok}
        return {**d, "revoked_vault_refs": len(rev)}

    def test_connection(
        self, connection_id_or_config: str | Mapping[str, Any]
    ) -> dict[str, Any]:
        """Test saved or inline connection credentials and report latency status."""
        arg = connection_id_or_config
        c: Mapping[str, Any] = {"connection_id": arg} if isinstance(arg, str) else arg
        cid = str(r) if (r := c.get("connection_id")) else None
        ep = c.get("endpoint") or c.get("host") or c.get("url")
        if not ep and cid:
            conns = self.list_connections()
            if hit := next((i for i in conns if i.get("connection_id") == cid), None):
                ep = hit.get("endpoint") or hit.get("host") or hit.get("url")
        tgt = str(ep or "127.0.0.1")
        ping = ConnectionTest.ping_endpoint(tgt, timeout_seconds=3.0)
        _log("FR-HOST-SERVLET-CONN-TEST", f"Tested connection '{cid}' ({tgt}).")
        d = {"connection_id": cid, "endpoint": tgt, "test_result": ping}
        return {**d, "timestamp": datetime.now(UTC).isoformat()}


class ServletConstants:
    """System constants, environment paths, and runtime metadata endpoints."""

    def __init__(self, session_mgr: Any = None, resource_mgr: Any = None) -> None:
        self.session_mgr = session_mgr or _sess.session_manager
        self.resource_mgr = resource_mgr

    def get_constants(self) -> dict[str, Any]:
        """Expose application version, build timestamp, and runtime paths."""
        _log("FR-HOST-SERVLET-CONSTANTS", "Retrieved system constants.")
        rt = f"CPython {sys.version.split()[0]} (FastAPI)"
        hid = self.session_mgr.host_instance_id
        d: _Pld = {"application": "HaruQuantAI", "version": "1.0.0", "runtime": rt}
        d |= {"host_instance_id": hid, "build_timestamp": "2026-10-18T00:00:00Z"}
        d["data_directory"] = str(Path.cwd() / "data")
        d["core_channels"] = list(CORE_EVENT_CHANNELS)
        return {**d, "supported_timeframes": list(SUPPORTED_TIMEFRAMES)}

    def get_system_specs(self) -> dict[str, Any]:
        """Serve system resource limits, hardware concurrency, and timeframes."""
        cpus = max(1, cpu_count() or 1)
        _log("FR-HOST-SERVLET-SPECS", f"Retrieved system specs (cores={cpus}).")
        d: _Pld = {"cpu_cores": cpus, "hardware_concurrency": cpus}
        d["supported_timeframes"] = list(SUPPORTED_TIMEFRAMES)
        d["memory_headroom"] = asdict(_res.check_memory_headroom())
        d["worker_capacity"] = asdict(_res.get_worker_capacity())
        return {**d, "system_health": asdict(_res.inspect_resources())}


class TransportGatewayService:
    """Coordinates session auth, shell status, SSE, and WebSocket endpoints."""

    def __init__(self, **kw: Any) -> None:
        self.event_bus: EventBus = kw.get("event_bus") or get_global_event_bus()
        sm = kw.get("session_mgr") or _sess.session_manager
        self.session_mgr: _sess.SessionManager = sm
        self.resource_mgr, self.job_mgr = kw.get("resource_mgr"), kw.get("job_mgr")
        hs = kw.get("host_settings")
        self.settings: SettingsManager = settings if hs is None else hs
        self.password_hash: str | None = kw.get("password_hash")
        self.require_auth = bool(kw.get("require_auth", False))
        self.heartbeat_sec = float(kw.get("heartbeat_sec", 15.0))
        self.started_at, self.app_loaded_acknowledged = monotonic(), False
        self.connection_servlet = ServletConnection()
        self.constants_servlet = ServletConstants(self.session_mgr, self.resource_mgr)

    def _verify(self, req: Request, qtok: str | None = None) -> Any:
        tok = extract_bearer_token(req.headers.get("authorization"), qtok)
        return self.session_mgr.verify_session(tok) if tok is not None else None

    def _chk_pw(self, candidate: str) -> bool:
        self.settings.reload()
        db_h = self.settings.get("user_access", "password_hash", None)
        cfg = db_h if isinstance(db_h, str) and db_h else self.password_hash
        return _sess.verify_password(candidate, cfg) if cfg else not self.require_auth

    def _guard(self, req: Request, scope: str) -> Any:
        if not self.require_auth:
            return None
        if (s := self._verify(req)) and self.session_mgr.authorize(s, scope):
            return None
        sc, c = (401, "UNAUTHORIZED") if s is None else (403, "FORBIDDEN")
        return _err(req, sc, c, "Active authorized session required.")

    async def _auth_route(self, req: Request) -> Any:
        fr = "FR-HOST-TRANSPORT-SESSION-AUTH"
        if req.method == "GET":
            if (rec := self._verify(req)) is None:
                _log(fr, "Unauthorized /sessions/me call.", warn=True)
                return _err(req, 401, "UNAUTHORIZED", "Valid session token required.")
            _log(fr, f"Verified active session '{rec.session_id}'.")
            exp = rec.expires_at_utc
            if "T" not in exp:
                exp = datetime.fromisoformat(exp).replace(tzinfo=UTC).isoformat()
            return _ok(req, {**rec.to_dict(), "expires_at": exp}, "Verified.")
        body, peer = await _jbody(req), (req.client.host if req.client else "127.0.0.1")
        if not self._chk_pw(str(body.get("password") or "")):
            _log(fr, f"Rejected login attempt from {peer}.", warn=True)
            return _err(req, 401, "INVALID_CREDENTIALS", "Invalid host password.")
        du = str(self.settings.get("user_access", "username", "haruquantai") or "admin")
        u = str(body.get("username") or "").strip() or du
        dur = int(self.settings.get("user_access", "session_timeout_mins", 1440))
        tok, rec = self.session_mgr.create_session(u, peer, duration_mins=dur)
        _log(fr, f"Issued session '{rec.session_id}' for '{rec.username}'.")
        exp = rec.expires_at_utc
        if "T" not in exp:
            exp = datetime.fromisoformat(exp).replace(tzinfo=UTC).isoformat()
        d = {"token": tok, "expires_at": exp, "session_id": rec.session_id}
        return _ok(req, {**d, "username": rec.username}, "Authenticated.", fx=True)

    async def _meta(self, req: Request) -> Any:
        p, eb = req.url.path, self.event_bus
        hid, fx = self.session_mgr.host_instance_id, False
        if p.endswith(("/diagnostics", "/resources")):
            if (den := self._guard(req, "diagnostics:read")) is not None:
                return den
            rt = getattr(req.app.state, "runtime", None)
            rm = self.resource_mgr or getattr(rt, "resource_manager", None)
            wd = rm.check_memory_headroom() if rm else _res.check_memory_headroom()
            hl = rm.inspect_resources() if rm else _res.inspect_resources()
            d = {"status": hl.status, "hardware": asdict(_res.probe_hardware())}
            d |= {"memory_watchdog": asdict(wd), "database": asdict(hl.database)}
            d["worker_capacity"] = asdict(_res.get_worker_capacity())
            return _ok(req, {**d, "storage": asdict(hl.storage)})
        if p.endswith("/app-loaded"):
            if self.require_auth and self._verify(req) is None:
                return _err(req, 401, "UNAUTHORIZED", "Active session required.")
            self.app_loaded_acknowledged, fx = True, True
            eb.publish("system", "app_loaded", {"host_instance_id": hid})
            _log("FR-HOST-TRANSPORT-GATEWAY-APP", f"/app-loaded (host={hid}).")
            data: Any = {"acknowledged": True, "host_instance_id": hid}
        elif p.endswith("/publish"):
            b, fx = await _jbody(req), True
            pld: _Pld = b["payload"] if isinstance(b.get("payload"), dict) else {}
            ch = str(b.get("channel") or "system")
            et = str(b.get("event_type") or "update")
            data = eb.publish(ch, et, pld).model_dump()
        elif p.endswith(("/about", "/constants")):
            data = self.constants_servlet.get_constants()
        elif p.endswith("/specs"):
            data = self.constants_servlet.get_system_specs()
        elif p.endswith("/channels"):
            d = {"core_channels": list(CORE_EVENT_CHANNELS)}
            d["active_channels"] = eb.channels
            data = {**d, "current_cursor": eb.current_cursor}
        elif p.endswith("/snapshot"):
            qp = req.query_params
            cur, lim = _qint(qp, "since_cursor"), _qint(qp, "limit", 100) or 100
            data = eb.get_snapshot(qp.get("channel", "*"), cur, lim).model_dump()
        else:
            up = round(max(0.0, monotonic() - self.started_at), 3)
            cpus = max(1, cpu_count() or 1)
            d = {"state": "READY", "is_ready": True, "version": "1.0.0"}
            d |= {"uptime_seconds": up, "cpu_count": cpus, "host_instance_id": hid}
            d["app_loaded"] = self.app_loaded_acknowledged
            data = {**d, "channels": eb.channels}
        return _ok(req, data, fx=fx)

    def _put_account(self, raw: _Pld) -> _Pld:
        u = str(raw.get("username") or "").strip()
        cpw = str(raw.get("current_password") or "")
        mins, er = raw.get("session_timeout_mins"), raw.get("expected_revision")
        if not u or not cpw or not isinstance(mins, int) or not isinstance(er, int):
            raise ValueError("Invalid account payload")
        if not self._chk_pw(cpw):
            raise HTTPException(status_code=401, detail="Invalid password")
        cur = self.settings.get("user_access", "password_hash", None)
        cur = cur or self.password_hash
        npw = str(raw.get("new_password") or "")
        pw = _sess.hash_password(npw) if npw else cur
        if not isinstance(pw, str) or not pw:
            raise ValueError("Password required")
        rev = self.settings.save_account(u, mins, pw, expected_revision=er)
        self.session_mgr.invalidate_sessions()
        self.password_hash = None
        ev_p = {"revision": rev, "scopes": ["user.access"]}
        self.event_bus.publish("settings.changed", "updated", ev_p)
        return {"revision": rev, "reauthenticate": True}

    async def _cfg_route(self, req: Request) -> Any:
        is_put, is_acc = req.method == "PUT", req.url.path.endswith("/account")
        if den := self._guard(req, "settings:write" if is_put else "settings:read"):
            return den
        try:
            if not is_put:
                s, cat = self.settings, req.url.path.endswith("/catalogue")
                res = s.get_catalogue() if cat else s.get_snapshot()
                return _ok(req, s.get_account() if is_acc else res)
            raw = await _jbody(req)
            if is_acc:
                out, fx = self._put_account(raw), True
            else:
                sb = SettingsBatchUpdatePayload.model_validate(raw)
                sec, er = req.url.path.endswith("/secrets"), sb.expected_revision
                out = self.settings.save_changes(
                    sb.changes, expected_revision=er, include_secrets=sec
                )
                if fx := bool(out["wrote"]):
                    ev_p = {"revision": out["revision"], "scopes": sorted(sb.changes)}
                    self.event_bus.publish("settings.changed", "updated", ev_p)
            return _ok(req, out, fx=fx)
        except RevisionConflictError as exc:
            det = {"expected_revision": exc.expected_revision}
            det["current_revision"] = exc.current_revision
            return _err(req, 409, "REVISION_CONFLICT", "Revision conflict.", det)
        except (KeyError, ValidationError, ValueError) as exc:
            _log("FR-HOST-TRANSPORT-GATEWAY-APP", "Invalid config patch.", warn=True)
            miss = isinstance(exc, KeyError)
            c = "INVALID_ACCOUNT" if is_acc else "INVALID_SETTINGS"
            return _err(
                req,
                503 if miss else 422,
                "ACCOUNT_UNCONFIGURED" if miss else c,
                "Invalid.",
            )
        except HostPersistence.Error:
            _log("FR-HOST-TRANSPORT-GATEWAY-APP", "DB unavailable.", warn=True)
            return _err(req, 503, "SETTINGS_UNAVAILABLE", "Database unavailable.")

    async def _conn_route(self, req: Request, connection_id: str = "") -> Any:
        is_rd = req.method == "GET" or req.url.path.endswith("/test")
        if den := self._guard(
            req, "connections:read" if is_rd else "connections:write"
        ):
            return den
        cs = self.connection_servlet
        if req.method == "GET":
            recs = cs.list_connections(req.query_params.get("provider"))
            return _ok(req, {"connections": recs, "count": len(recs)})
        if req.method == "DELETE":
            res = cs.delete_connection(connection_id)
            return (
                _ok(req, res, fx=True)
                if res["deleted"]
                else _err(req, 404, "NOT_FOUND", "Not found.")
            )
        body = await _jbody(req)
        if req.url.path.endswith("/test"):
            cid = connection_id or body.get("connection_id")
            cfg: str | _Pld = (
                {**body, "connection_id": cid} if body else (connection_id or {})
            )
            return _ok(req, cs.test_connection(cfg))
        return _ok(req, cs.save_connection(body), fx=True)

    async def _jobs_route(self, req: Request, job_id: str = "") -> Any:
        if den := self._guard(
            req, "jobs:write" if req.method == "POST" else "jobs:read"
        ):
            return den
        rt = getattr(req.app.state, "runtime", None)
        jm = self.job_mgr or getattr(rt, "job_manager", None)
        if req.method == "POST":
            if not (bool(jm.cancel_job(job_id)) if jm and job_id else False):
                return _err(req, 404, "JOB_NOT_CANCELLABLE", "Not cancellable.")
            self.event_bus.publish("jobs", "cancelled", {"job_id": job_id})
            return _ok(req, {"job_id": job_id, "cancelled": True}, fx=True)
        if job_id:
            if jm:
                row: _Pld | None = r.to_dict() if (r := jm.get_job(job_id)) else None
            else:
                r_db = HostPersistence.read_records(
                    "host_jobs", {"job_id": job_id}, limit=1
                )
                row = r_db[0] if r_db else None
            return (
                _ok(req, row) if row else _err(req, 404, "JOB_NOT_FOUND", "Not found.")
            )
        sf = req.query_params.get("status_filter")
        lim = _qint(req.query_params, "limit", 50) or 50
        if jm:
            jobs = [r.to_dict() for r in jm.list_jobs(status=sf, limit=lim)]
        else:
            jobs = HostPersistence.read_records(
                "host_jobs", {"status": sf} if sf else None, limit=lim
            )
        return _ok(req, {"count": len(jobs), "jobs": jobs})

    async def _sse(self, req: Request) -> Any:
        qp = req.query_params
        tok = extract_bearer_token(req.headers.get("authorization"), qp.get("token"))
        if (self.require_auth or tok) and not (
            tok and self.session_mgr.verify_session(tok)
        ):
            return _err(req, 401, "UNAUTHORIZED", "Valid session token required.")
        h = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(
            self._sse_gen(req, tok), media_type="text/event-stream", headers=h
        )

    async def _sse_gen(self, req: Request, tok: str | None) -> AsyncGenerator[str]:
        qp, lid = req.query_params, req.headers.get("last-event-id")
        cur = _qint(qp, "since_cursor")
        if cur is None and lid and (s := lid.strip()).isdigit():
            cur = int(s)
        raw_c = (qp.get("channels") or "").split(",")
        chans = [c.strip() for c in raw_c if c.strip()] or ["*"]
        lim, sent = _qint(qp, "limit"), 0
        sub_id, q, replay, gap = self.event_bus.subscribe(chans, since_cursor=cur)
        _log("FR-HOST-TRANSPORT-SSE-STREAMING", f"SSE sub={sub_id}.")
        try:
            if gap:
                g = dumps({"channel": "system", "event_type": "gap"})
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
                    dj = ev.model_dump_json()
                    yield f"id: {ev.cursor}\nevent: {ev.channel}\ndata: {dj}\n\n"
                    sent += 1
                except TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.event_bus.unsubscribe(sub_id)
            _log("FR-HOST-TRANSPORT-SSE-STREAMING", f"SSE unsub={sub_id}.")

    async def _ws(self, ws: WebSocket) -> None:
        qp = ws.query_params
        tok = extract_bearer_token(ws.headers.get("authorization"), qp.get("token"))
        if self.require_auth and not (tok and self.session_mgr.verify_session(tok)):
            await ws.close(code=1008)
            return
        await ws.accept()
        raw_c = (qp.get("channels") or "").split(",")
        chans = [c.strip() for c in raw_c if c.strip()] or ["*"]
        sub_id, q, replay, gap = self.event_bus.subscribe(
            chans, _qint(qp, "since_cursor")
        )
        _log("FR-HOST-TRANSPORT-WS-STREAMING", f"WS sub={sub_id}.")
        try:
            if gap:
                await ws.send_json(
                    {"channel": "system", "event_type": "gap", "payload": {}}
                )
            for ev in replay:
                await ws.send_json(ev.model_dump())
            while True:
                rt = asyncio.create_task(ws.receive_json())
                qt = asyncio.create_task(q.get())
                done, pend = await asyncio.wait(
                    {rt, qt}, return_when=asyncio.FIRST_COMPLETED
                )
                for t in pend:
                    t.cancel()
                await asyncio.gather(*pend, return_exceptions=True)
                if qt in done:
                    await ws.send_json(qt.result().model_dump())
                if rt in done and not await self._ws_cmd(ws, sub_id, rt.result()):
                    break
        except WebSocketDisconnect:
            pass
        finally:
            self.event_bus.unsubscribe(sub_id)
            _log("FR-HOST-TRANSPORT-WS-STREAMING", f"WS unsub={sub_id}.")

    async def _ws_cmd(self, ws: WebSocket, sub_id: str, msg: Any) -> bool:
        if not isinstance(msg, dict):
            return True
        act = str(msg.get("action", "")).lower()
        if act == "close":
            return False
        if act == "ping":
            await ws.send_json(
                {"channel": "system", "event_type": "pong", "payload": {}}
            )
        elif act == "subscribe" and isinstance(raw := msg.get("channels"), list):
            chans = [str(c) for c in raw if str(c).strip()] or ["*"]
            self.event_bus.update_subscription(sub_id, chans)
            f = {
                "channel": "system",
                "event_type": "subscribed",
                "payload": {"channels": chans},
            }
            await ws.send_json(f)
        elif act == "publish":
            pld: _Pld = msg["payload"] if isinstance(msg.get("payload"), dict) else {}
            ch, et = (
                str(msg.get("channel", "system")),
                str(msg.get("event_type", "update")),
            )
            self.event_bus.publish(ch, et, pld)
        return True


_ROUTE_SPECS = (
    "GET:/auth:_auth_route POST:/auth:_auth_route POST:/auth/login:_auth_route "
    "GET:/sessions/me:_auth_route GET:/status:_meta GET:/readiness:_meta "
    "POST:/app-loaded:_meta GET:/about:_meta GET:/constants:_meta GET:/specs:_meta "
    "GET:/settings:_cfg_route PUT:/settings:_cfg_route "
    "GET:/settings/catalogue:_cfg_route PUT:/settings/secrets:_cfg_route "
    "GET:/auth/account:_cfg_route PUT:/auth/account:_cfg_route "
    "GET:/diagnostics:_meta GET:/resources:_meta GET:/jobs:_jobs_route "
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
        m, path, attr = spec.split(":")
        if m == "WS":
            router.add_api_websocket_route(path, getattr(s, attr))
        else:
            router.add_api_route(
                path, getattr(s, attr), methods=[m], response_model=None
            )
    _log("FR-HOST-TRANSPORT-GATEWAY-APP", f"Router prefix='{prefix or '/'}'.")
    return router


def create_host_app(
    *, extra_routers: Sequence[APIRouter] | None = None, **kw: Any
) -> FastAPI:
    """Create the configured FastAPI host gateway application."""
    bus = kw.get("event_bus") or get_global_event_bus()
    sessions = kw.get("session_mgr") or _sess.session_manager
    kw.update(event_bus=bus, session_mgr=sessions)
    app = FastAPI(title="HaruQuantAI Host Platform Gateway", version="1.0.0")
    app.state.event_bus, app.state.session_manager = bus, sessions
    hosts = ("localhost", "127.0.0.1")
    origins = [f"http://{h}:{p}" for h in hosts for p in (3000, 8000)]
    cors_kw: _Pld = {"allow_origins": origins, "allow_credentials": True}
    app.add_middleware(
        CORSMiddleware, **cors_kw, allow_methods=["*"], allow_headers=["*"]
    )
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)
    for pfx in ("", "/api/v1", "/api/v2"):
        app.include_router(create_transport_router(prefix=pfx, **kw))
    for extra in extra_routers or ():
        app.include_router(extra)
    _log("FR-HOST-TRANSPORT-GATEWAY-APP", f"Gateway ({sessions.host_instance_id}).")
    return app


class TransportCLI:
    """Headless CLI runner and formatter for FEAT-HOST-TRANSPORT diagnostics."""

    @staticmethod
    def format_output(data: Mapping[str, Any]) -> str:
        """Format transport diagnostic dictionary as indented JSON."""
        return dumps(dict(data), indent=2)

    @classmethod
    def run(cls, argv: Sequence[str] | None = None) -> int:
        """Run EventBus, ConnectionTest, ServletConnection, and ServletConstants CLI."""
        p = ArgumentParser(prog="app.host.transport")
        p.add_argument("--test-bus", action="store_true")
        args, bus = p.parse_args(argv), EventBus()
        if args.test_bus:
            for ch in CORE_EVENT_CHANNELS:
                bus.publish(ch, "self_test", {"channel": ch, "ok": True})
            out: _Pld = bus.get_snapshot("*").model_dump()
        else:
            prev_db = HostPersistence.DEFAULT_DB_PATH
            with TemporaryDirectory(
                prefix="hqai_tr_", ignore_cleanup_errors=True
            ) as tmp:
                HostPersistence.DEFAULT_DB_PATH = Path(tmp) / "transport_cli.db"
                try:
                    with socket.create_server(("127.0.0.1", 0)) as srv:
                        port = int(srv.getsockname()[1])
                        loc = f"127.0.0.1:{port}"
                        ping = ConnectionTest.ping_endpoint
                        diag = ConnectionTest.diagnose_network
                        ct: _Pld = {"ping_local": ping(loc, timeout_seconds=0.5)}
                        ct["ping_remote"] = ping("https://1.1.1.1", timeout_seconds=0.5)
                        ct["latency"] = ConnectionTest.check_latency(
                            "127.0.0.1", port=port, samples=3
                        )
                        ct["diagnostics"] = diag(loc)
                        ct["diagnostics_failure"] = diag("invalid.hqai.local:80")
                        sc = ServletConnection()
                        c_in = {
                            "connection_id": "demo-conn",
                            "name": "Local",
                            "endpoint": loc,
                        }
                        s_conn = {
                            "saved": sc.save_connection(c_in),
                            "listed": sc.list_connections(),
                        }
                        s_conn["tested"] = sc.test_connection("demo-conn")
                        s_conn["deleted"] = sc.delete_connection("demo-conn")
                finally:
                    HostPersistence.DEFAULT_DB_PATH = prev_db
            cs = ServletConstants()
            s_const = {
                "constants": cs.get_constants(),
                "system_specs": cs.get_system_specs(),
            }
            out = {
                "core_channels": list(CORE_EVENT_CHANNELS),
                "ring_capacity": bus.ring_capacity,
            }
            out |= {"max_queue_size": bus.max_queue_size, "connection_test": ct}
            out |= {"servlet_connection": s_conn, "servlet_constants": s_const}
        sys.stdout.write(cls.format_output(out) + "\n")
        return 0


__all__ = [
    "CORE_EVENT_CHANNELS",
    "ConnectionTest",
    "EventBus",
    "HostEvent",
    "ServletConnection",
    "ServletConstants",
    "TransportCLI",
    "TransportGatewayService",
    "TransportMiddleware",
    "create_host_app",
    "create_transport_router",
    "extract_bearer_token",
    "get_global_event_bus",
    "register_transport_exception_handlers",
]

if __name__ == "__main__":
    raise SystemExit(TransportCLI.run())
