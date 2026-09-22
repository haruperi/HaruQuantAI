"""Host gateway owner: versioned HTTP transport, ASGI dispatch, and server lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
import json
import threading
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, override

from app.host.catalog import HOST_CATALOG, Catalog, SelectionRequest
from app.host.execution import (
    HOST_EXECUTION,
    BatchExecutionRequest,
    BatchTrial,
    Execution,
    ExecutionBudget,
    ExecutionBudgetExceededError,
    ExportRequest,
    SingleExecutionRequest,
)
from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import Feature, FeatureSpec
from app.plugins.algebra import validate_graph
from app.plugins.lowering import LoweringTarget
from app.plugins.schema import (
    FrozenObject,
)
from app.plugins.spec import PluginRef
from app.plugins.wire import (
    catalog_view_to_wire,
    graph_document_from_wire,
    graph_document_to_wire,
    parse_strict_json,
    value_from_wire,
    value_to_wire,
)

GATEWAY_API_VERSION = "1.0.0"
MAX_PORT = 65535
DEFAULT_SERVER_START_TIMEOUT_SECONDS = 5.0


class GatewayError(RuntimeError):
    """Base error for gateway failures."""


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    """Configuration for the host gateway HTTP server."""

    bind_host: str = "127.0.0.1"
    port: int = 8000
    allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    max_payload_bytes: int = 10_000_000
    request_timeout_seconds: float = 30.0
    shutdown_timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        """Validate gateway configuration."""
        if not isinstance(self.bind_host, str) or not self.bind_host:
            raise ValueError("bind_host must be a non-empty string")
        if not isinstance(self.port, int) or self.port < 0 or self.port > MAX_PORT:
            raise ValueError(f"port must be an integer between 0 and {MAX_PORT}")
        if not isinstance(self.allowed_origins, tuple):
            raise TypeError("allowed_origins must be a tuple of origin strings")
        for origin in self.allowed_origins:
            if origin == "*":
                raise ValueError("Wildcard '*' is forbidden in allowed_origins")
        if self.max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be > 0")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be > 0")
        if self.shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be > 0")


DEFAULT_GATEWAY_CONFIG = GatewayConfig()


class Gateway(Protocol):
    """Public gateway owner protocol."""

    @property
    def config(self) -> GatewayConfig:
        """Return the active gateway configuration."""
        ...

    @property
    def is_running(self) -> bool:
        """Return True if local server thread is active and listening."""
        ...

    @property
    def bound_address(self) -> tuple[str, int] | None:
        """Return bound (host, port) tuple if server is running, else None."""
        ...

    def create_asgi_app(self) -> Any:
        """Construct and return the Starlette ASGI application with lazy imports."""
        ...

    def start(self) -> None:
        """Start local Uvicorn server in a background thread."""
        ...

    def stop(self) -> None:
        """Stop local Uvicorn server gracefully."""
        ...


HOST_GATEWAY = Capability[Gateway]("host.gateway", major=1)


def _success_envelope(data: Any, request_id: str) -> dict[str, Any]:
    return {
        "api_version": GATEWAY_API_VERSION,
        "request_id": request_id,
        "status": "success",
        "data": data,
        "error": None,
    }


def _error_envelope(
    code: str,
    message: str,
    request_id: str,
    issues: Sequence[Any] | None = None,
) -> dict[str, Any]:
    return {
        "api_version": GATEWAY_API_VERSION,
        "request_id": request_id,
        "status": "error",
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "issues": list(issues) if issues else [],
        },
    }


class _GatewayProvider:
    """Internal concrete provider of the Gateway capability."""

    def __init__(
        self,
        config: GatewayConfig,
        catalog: Catalog | None = None,
        execution: Execution | None = None,
    ) -> None:
        self._config = config
        self._catalog = catalog
        self._execution = execution
        self._server: Any = None
        self._server_thread: threading.Thread | None = None
        self._bound_address: tuple[str, int] | None = None

    @property
    def config(self) -> GatewayConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._server is not None and self._bound_address is not None

    @property
    def bound_address(self) -> tuple[str, int] | None:
        return self._bound_address

    def set_dependencies(
        self,
        catalog: Catalog | None,
        execution: Execution | None,
    ) -> None:
        """Set peer host capabilities after feature discovery."""
        self._catalog = catalog
        self._execution = execution

    async def _read_body_strictly(self, request: Any) -> tuple[Any, str | None]:
        """Read and strictly parse request body, checking max payload size."""
        body = await request.body()
        if len(body) > self._config.max_payload_bytes:
            return None, (
                f"Payload size {len(body)} exceeds maximum "
                f"{self._config.max_payload_bytes} bytes"
            )
        try:
            parsed = parse_strict_json(body) if body else {}
            return parsed, None
        except (ValueError, TypeError, json.JSONDecodeError) as err:
            return None, f"Malformed or duplicate JSON: {err}"

    async def _handle_health(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        cat_ready = self._catalog.is_ready() if self._catalog is not None else False
        exec_ready = self._execution is not None
        status = "ready" if cat_ready and exec_ready else "degraded"
        return JSONResponse(
            _success_envelope(
                {
                    "status": status,
                    "version": GATEWAY_API_VERSION,
                    "services": {
                        "gateway": "ready",
                        "catalog": "ready" if cat_ready else "unavailable",
                        "execution": "ready" if exec_ready else "unavailable",
                    },
                },
                req_id,
            ),
            headers={"X-Request-Id": req_id},
        )

    async def _handle_catalog(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._catalog is None or not self._catalog.is_ready():
            return JSONResponse(
                _error_envelope("CATALOG_UNAVAILABLE", "Catalog is not ready", req_id),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        snapshot = self._catalog.snapshot()
        data = catalog_view_to_wire(snapshot.view)
        return JSONResponse(
            _success_envelope(data, req_id), headers={"X-Request-Id": req_id}
        )

    async def _handle_catalog_select(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._catalog is None or not self._catalog.is_ready():
            return JSONResponse(
                _error_envelope("CATALOG_UNAVAILABLE", "Catalog is not ready", req_id),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        body, err = await self._read_body_strictly(req)
        if err is not None:
            return JSONResponse(
                _error_envelope("INVALID_PAYLOAD", err, req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )
        try:
            enabled_refs = tuple(
                PluginRef.parse(r) for r in body.get("enabled_refs", [])
            )
            sel_req = SelectionRequest(
                enabled_refs=enabled_refs,
                allowed_effects=tuple(body.get("allowed_effects", ["pure"])),
                allowed_kinds=tuple(body.get("allowed_kinds", [])),
                available_capabilities=tuple(body.get("available_capabilities", [])),
                permissions=tuple(body.get("permissions", [])),
            )
            result = self._catalog.select(sel_req)
            resp_data = {
                "available_operations": [
                    {"plugin_ref": r.to_string(), "operation_id": op}
                    for r, op in result.available_operations
                ],
                "unavailable_reasons": [
                    {
                        "plugin_ref": r.to_string(),
                        "operation_id": op,
                        "reason": reason,
                    }
                    for r, op, reason in result.unavailable_reasons
                ],
            }
            return JSONResponse(
                _success_envelope(resp_data, req_id),
                headers={"X-Request-Id": req_id},
            )
        except (KeyError, ValueError, TypeError, RuntimeError) as ex:
            return JSONResponse(
                _error_envelope("SELECTION_FAILED", str(ex), req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )

    async def _handle_graphs_validate(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._catalog is None or not self._catalog.is_ready():
            return JSONResponse(
                _error_envelope("CATALOG_UNAVAILABLE", "Catalog is not ready", req_id),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        body, err = await self._read_body_strictly(req)
        if err is not None:
            return JSONResponse(
                _error_envelope("INVALID_PAYLOAD", err, req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )
        try:
            doc_raw = body.get("graph_document")
            if not isinstance(doc_raw, dict):
                return JSONResponse(
                    _error_envelope(
                        "INVALID_GRAPH",
                        "Missing or invalid 'graph_document' field",
                        req_id,
                    ),
                    status_code=400,
                    headers={"X-Request-Id": req_id},
                )
            doc = graph_document_from_wire(doc_raw)
            snapshot = self._catalog.snapshot()
            val_res = validate_graph(doc, snapshot.view)
            resp_data = {
                "can_execute": val_res.can_execute,
                "issues": [
                    {
                        "path": getattr(i, "path", ""),
                        "code": getattr(i, "code", "VALIDATION_ISSUE"),
                        "message": str(i),
                    }
                    for i in val_res.issues
                ],
                "normalized_document": (
                    graph_document_to_wire(val_res.normalized_document)
                    if val_res.normalized_document is not None
                    else None
                ),
            }
            return JSONResponse(
                _success_envelope(resp_data, req_id),
                headers={"X-Request-Id": req_id},
            )
        except (KeyError, ValueError, TypeError, RuntimeError) as ex:
            return JSONResponse(
                _error_envelope("VALIDATION_ERROR", str(ex), req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )

    async def _handle_executions_evaluate(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._execution is None:
            return JSONResponse(
                _error_envelope(
                    "EXECUTION_UNAVAILABLE", "Execution engine not ready", req_id
                ),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        body, err = await self._read_body_strictly(req)
        if err is not None:
            return JSONResponse(
                _error_envelope("INVALID_PAYLOAD", err, req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )
        try:
            doc_raw = body.get("graph_document")
            if not isinstance(doc_raw, dict):
                return JSONResponse(
                    _error_envelope(
                        "INVALID_GRAPH",
                        "Missing or invalid 'graph_document' field",
                        req_id,
                    ),
                    status_code=400,
                    headers={"X-Request-Id": req_id},
                )
            doc = graph_document_from_wire(doc_raw)
            raw_inputs = body.get("inputs", {})
            inputs = {
                k: value_from_wire(v)
                for k, v in (raw_inputs.items() if isinstance(raw_inputs, dict) else ())
            }
            budget = ExecutionBudget()
            if "budget" in body and isinstance(body["budget"], dict):
                b = body["budget"]
                budget = ExecutionBudget(
                    max_nodes=b.get("max_nodes", 1000),
                    max_samples=b.get("max_samples", 1_000_000),
                    max_output_values=b.get("max_output_values", 10_000_000),
                    max_trials=b.get("max_trials", 1),
                    max_elapsed_seconds=b.get("max_elapsed_seconds", 30.0),
                )
            single_req = SingleExecutionRequest(
                graph_document=doc,
                inputs=inputs,
                budget=budget,
            )
            res = self._execution.execute(single_req)
            resp_data: dict[str, Any] = {
                "success": res.success,
                "elapsed_seconds": res.elapsed_seconds,
                "issues": [
                    {
                        "path": getattr(i, "path", ""),
                        "code": getattr(i, "code", "EXECUTION_ISSUE"),
                        "message": str(i),
                    }
                    for i in res.issues
                ],
                "outputs": {
                    k: value_to_wire(v)
                    for k, v in (res.outputs.items() if res.outputs else ())
                },
                "reproducibility": None,
            }
            if res.reproducibility is not None:
                rep = res.reproducibility
                resp_data["reproducibility"] = {
                    "graph_id": rep.graph_id,
                    "graph_fingerprint": rep.graph_fingerprint,
                    "catalog_fingerprint": rep.catalog_fingerprint,
                    "dependency_fingerprint": rep.dependency_fingerprint,
                    "plugin_versions": [list(item) for item in rep.plugin_versions],
                    "source_digests": [list(item) for item in rep.source_digests],
                    "normalized_parameters": value_to_wire(rep.normalized_parameters),
                    "input_hash": rep.input_hash,
                    "output_hash": rep.output_hash,
                    "numerical_policy": {
                        "tolerance": rep.numerical_policy.tolerance,
                        "nan_policy": rep.numerical_policy.nan_policy,
                        "missing_policy": rep.numerical_policy.missing_policy,
                    },
                    "engine_version": rep.engine_version,
                    "elapsed_seconds": rep.elapsed_seconds,
                    "status": rep.status,
                }
            return JSONResponse(
                _success_envelope(resp_data, req_id),
                headers={"X-Request-Id": req_id},
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            RuntimeError,
            ExecutionBudgetExceededError,
        ) as ex:
            return JSONResponse(
                _error_envelope("EXECUTION_FAILED", str(ex), req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )

    async def _handle_executions_batch(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._execution is None:
            return JSONResponse(
                _error_envelope(
                    "EXECUTION_UNAVAILABLE", "Execution engine not ready", req_id
                ),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        body, err = await self._read_body_strictly(req)
        if err is not None:
            return JSONResponse(
                _error_envelope("INVALID_PAYLOAD", err, req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )
        try:
            doc_raw = body.get("graph_document")
            if not isinstance(doc_raw, dict):
                return JSONResponse(
                    _error_envelope(
                        "INVALID_GRAPH", "Missing 'graph_document'", req_id
                    ),
                    status_code=400,
                    headers={"X-Request-Id": req_id},
                )
            doc = graph_document_from_wire(doc_raw)
            raw_inputs = body.get("inputs", {})
            inputs = {
                k: value_from_wire(v)
                for k, v in (raw_inputs.items() if isinstance(raw_inputs, dict) else ())
            }
            trials_list: list[BatchTrial] = []
            for t in body.get("trials", []):
                overrides: dict[str, FrozenObject] = {}
                for nid, pdict in t.get("parameter_overrides", {}).items():
                    overrides[nid] = FrozenObject.from_mapping(
                        {pk: value_from_wire(pv) for pk, pv in pdict.items()}
                    )
                trials_list.append(
                    BatchTrial(
                        trial_id=t["trial_id"],
                        parameter_overrides=overrides,
                    )
                )
            budget = ExecutionBudget()
            if "budget" in body and isinstance(body["budget"], dict):
                b = body["budget"]
                budget = ExecutionBudget(
                    max_nodes=b.get("max_nodes", 1000),
                    max_samples=b.get("max_samples", 1_000_000),
                    max_output_values=b.get("max_output_values", 10_000_000),
                    max_trials=b.get("max_trials", 100),
                    max_elapsed_seconds=b.get("max_elapsed_seconds", 60.0),
                )
            batch_req = BatchExecutionRequest(
                graph_document=doc,
                inputs=inputs,
                trials=tuple(trials_list),
                budget=budget,
                seed=body.get("seed"),
            )
            res = self._execution.execute_batch(batch_req)
            resp_data = {
                "success": res.success,
                "trials": [
                    {
                        "trial_id": tr.trial_id,
                        "success": tr.result.success,
                        "elapsed_seconds": tr.result.elapsed_seconds,
                        "outputs": {
                            k: value_to_wire(v)
                            for k, v in (
                                tr.result.outputs.items() if tr.result.outputs else ()
                            )
                        },
                    }
                    for tr in res.trials
                ],
                "elapsed_seconds": res.elapsed_seconds,
            }
            return JSONResponse(
                _success_envelope(resp_data, req_id),
                headers={"X-Request-Id": req_id},
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            RuntimeError,
            ExecutionBudgetExceededError,
        ) as ex:
            return JSONResponse(
                _error_envelope("BATCH_EXECUTION_FAILED", str(ex), req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )

    async def _handle_exports(self, req: Any) -> Any:
        from starlette.responses import JSONResponse

        req_id = req.headers.get("X-Request-Id") or str(uuid.uuid4())
        if self._execution is None:
            return JSONResponse(
                _error_envelope(
                    "EXECUTION_UNAVAILABLE", "Execution engine not ready", req_id
                ),
                status_code=503,
                headers={"X-Request-Id": req_id},
            )
        body, err = await self._read_body_strictly(req)
        if err is not None:
            return JSONResponse(
                _error_envelope("INVALID_PAYLOAD", err, req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )
        try:
            doc_raw = body.get("graph_document")
            if not isinstance(doc_raw, dict):
                return JSONResponse(
                    _error_envelope(
                        "INVALID_GRAPH", "Missing 'graph_document'", req_id
                    ),
                    status_code=400,
                    headers={"X-Request-Id": req_id},
                )
            doc = graph_document_from_wire(doc_raw)
            target_dict = body.get(
                "target", {"target_id": "python", "version": [1, 0, 0]}
            )
            target = LoweringTarget(
                target_id=target_dict["target_id"],
                version=tuple(target_dict["version"]),
            )
            exp_req = ExportRequest(graph_document=doc, target=target)
            res = self._execution.export(exp_req)
            resp_data = {
                "success": res.success,
                "target": {
                    "target_id": res.target.target_id,
                    "version": list(res.target.version),
                },
                "source_code": res.source_code,
                "manifest": value_to_wire(res.manifest) if res.manifest else None,
                "issues": [
                    {
                        "path": getattr(i, "path", ""),
                        "code": getattr(i, "code", "EXPORT_ISSUE"),
                        "message": str(i),
                    }
                    for i in res.issues
                ],
            }
            return JSONResponse(
                _success_envelope(resp_data, req_id),
                headers={"X-Request-Id": req_id},
            )
        except (KeyError, ValueError, TypeError, RuntimeError) as ex:
            return JSONResponse(
                _error_envelope("EXPORT_FAILED", str(ex), req_id),
                status_code=400,
                headers={"X-Request-Id": req_id},
            )

    def create_asgi_app(self) -> Any:
        """Construct and return the Starlette ASGI application with lazy imports."""
        try:
            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.middleware.cors import CORSMiddleware
            from starlette.routing import Route
        except ImportError as err:
            raise RuntimeError(
                "Starlette is required to create the gateway ASGI application"
            ) from err

        routes = [
            Route("/api/v1/health", self._handle_health, methods=["GET"]),
            Route("/api/v1/catalog", self._handle_catalog, methods=["GET"]),
            Route(
                "/api/v1/catalog/select",
                self._handle_catalog_select,
                methods=["POST"],
            ),
            Route(
                "/api/v1/graphs/validate",
                self._handle_graphs_validate,
                methods=["POST"],
            ),
            Route(
                "/api/v1/executions/evaluate",
                self._handle_executions_evaluate,
                methods=["POST"],
            ),
            Route(
                "/api/v1/executions/batch",
                self._handle_executions_batch,
                methods=["POST"],
            ),
            Route("/api/v1/exports", self._handle_exports, methods=["POST"]),
        ]

        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=list(self._config.allowed_origins),
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                allow_credentials=False,
            )
        ]

        return Starlette(debug=False, routes=routes, middleware=middleware)

    def start(self) -> None:
        """Start local Uvicorn server in a background thread."""
        if self._server is not None:
            return

        try:
            import uvicorn
        except ImportError as err:
            raise RuntimeError(
                "Uvicorn is required to run the gateway local HTTP server"
            ) from err

        asgi_app = self.create_asgi_app()
        server_config = uvicorn.Config(
            app=asgi_app,
            host=self._config.bind_host,
            port=self._config.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(server_config)

        def _run() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._server.serve())
            finally:
                with contextlib.suppress(RuntimeError, OSError):
                    loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

        self._server_thread = threading.Thread(target=_run, daemon=True)
        self._server_thread.start()

        # Wait for server to bind
        start_time = time.perf_counter()
        while (
            not self._server.started
            and time.perf_counter() - start_time < DEFAULT_SERVER_START_TIMEOUT_SECONDS
        ):
            time.sleep(0.02)

        if getattr(self._server, "servers", None):
            sock = self._server.servers[0].sockets[0]
            host, port = sock.getsockname()[:2]
            self._bound_address = (host, port)
        else:
            self._bound_address = (self._config.bind_host, self._config.port)

    def stop(self) -> None:
        """Stop local Uvicorn server gracefully."""
        if self._server is None:
            return
        self._server.should_exit = True
        if self._server_thread is not None:
            self._server_thread.join(timeout=self._config.shutdown_timeout_seconds)
            self._server_thread = None
        if hasattr(self._server, "servers"):
            for s in self._server.servers:
                with contextlib.suppress(OSError, RuntimeError):
                    s.close()
        self._server = None
        self._bound_address = None


class _GatewayFeature(Feature):
    """Host lifecycle feature providing the Gateway capability."""

    spec = FeatureSpec(
        "host.gateway",
        requires=frozenset({HOST_CATALOG, HOST_EXECUTION}),
        provides=frozenset({HOST_GATEWAY}),
    )

    def __init__(
        self,
        config: GatewayConfig = DEFAULT_GATEWAY_CONFIG,
        auto_start: bool = False,
    ) -> None:
        self._config = config
        self._auto_start = auto_start
        self._provider = _GatewayProvider(config)

    @override
    async def start(self, context: FeatureContext) -> None:
        """Inject peer capabilities, publish capability, and optionally start server."""
        catalog = context.require(HOST_CATALOG)
        execution = context.require(HOST_EXECUTION)
        self._provider.set_dependencies(catalog, execution)

        context.on_close(self._provider.stop)
        context.provide(HOST_GATEWAY, self._provider)

        if self._auto_start:
            self._provider.start()


def _gateway_feature(
    config: GatewayConfig = DEFAULT_GATEWAY_CONFIG,
    auto_start: bool = False,
) -> Feature:
    """Construct the private gateway feature. Imported only by app.host.bootstrap."""
    return _GatewayFeature(config=config, auto_start=auto_start)


__all__ = (
    "DEFAULT_GATEWAY_CONFIG",
    "GATEWAY_API_VERSION",
    "HOST_GATEWAY",
    "Gateway",
    "GatewayConfig",
    "GatewayError",
)
