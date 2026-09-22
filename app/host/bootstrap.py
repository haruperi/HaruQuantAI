"""Application composition root for approved host owners."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from app.host.artifacts import ArtifactsConfig, _artifacts_feature
from app.host.catalog import HOST_CATALOG, CatalogRoot, _catalog_feature
from app.host.execution import (
    HOST_EXECUTION,
    ExecutionBudget,
    SingleExecutionRequest,
    _execution_feature,
)
from app.host.gateway import GatewayConfig, _gateway_feature
from app.host.jobs import JobsConfig, _jobs_feature
from app.host.storage import StorageConfig, _storage_feature
from app.host.telemetry import (
    DEFAULT_DIAGNOSTIC_CAPACITY,
    DEFAULT_MAX_SUBSCRIBERS,
    _telemetry_feature,
)
from app.host.workers import WorkersConfig, _workers_feature
from app.kernel.bootstrapper import Runtime
from app.kernel.feature import Feature
from app.plugins.wire import (
    graph_document_from_wire,
    parse_strict_json,
    to_canonical_json_bytes,
    value_to_wire,
)


def approved_catalog_roots(repo_root: Path | None = None) -> tuple[CatalogRoot, ...]:
    """Return explicit CatalogRoot configurations for approved quantitative families."""
    base = (repo_root or Path(__file__).resolve().parent.parent) / "plugins"
    return (
        CatalogRoot(
            logical_family="indicators",
            path=base / "indicators",
            accepted_kinds=("indicator",),
        ),
        CatalogRoot(
            logical_family="comparisons",
            path=base / "comparisons",
            accepted_kinds=("comparison",),
        ),
        CatalogRoot(
            logical_family="exporters",
            path=base / "exporters",
            accepted_kinds=("exporter",),
        ),
        CatalogRoot(
            logical_family="workspaces",
            path=base / "workspaces",
            accepted_kinds=("workspace",),
        ),
    )


def create_runtime(
    *,
    telemetry_max_subscribers: int = DEFAULT_MAX_SUBSCRIBERS,
    diagnostic_capacity: int = DEFAULT_DIAGNOSTIC_CAPACITY,
    catalog_roots: tuple[CatalogRoot, ...] = (),
    storage_config: StorageConfig | None = None,
    artifacts_config: ArtifactsConfig | None = None,
    workers_config: WorkersConfig | None = None,
    jobs_config: JobsConfig | None = None,
    gateway_config: GatewayConfig | None = None,
    gateway_auto_start: bool = False,
) -> Runtime:
    """Construct a fresh, inactive runtime for the currently approved host."""
    telemetry = _telemetry_feature(
        max_subscribers=telemetry_max_subscribers,
        diagnostic_capacity=diagnostic_capacity,
    )

    feature_factories: list[Callable[[], Feature]] = [
        lambda: telemetry,
    ]

    if storage_config is not None:
        storage = _storage_feature(storage_config)
        feature_factories.append(lambda: storage)

    if artifacts_config is not None:
        artifacts = _artifacts_feature(artifacts_config)
        feature_factories.append(lambda: artifacts)

    catalog = _catalog_feature(roots=catalog_roots)
    execution = _execution_feature()

    feature_factories.append(lambda: catalog)
    feature_factories.append(lambda: execution)

    if workers_config is not None:
        workers = _workers_feature(workers_config)
        feature_factories.append(lambda: workers)

    if jobs_config is not None:
        jobs = _jobs_feature(jobs_config)
        feature_factories.append(lambda: jobs)

    if gateway_config is not None:
        gateway = _gateway_feature(gateway_config, auto_start=gateway_auto_start)
        feature_factories.append(lambda: gateway)

    return Runtime(
        tuple(feature_factories),
        diagnostic_sink=telemetry.diagnose,
    )


def worker_main(argv: Sequence[str] | None = None) -> int:
    """Entry point for worker subprocess mode."""
    _ = argv
    task_id = ""

    async def _execute() -> None:
        nonlocal task_id
        try:
            raw_input = sys.stdin.buffer.read()
            if not raw_input:
                sys.stderr.write("Worker received empty input\n")
                sys.exit(1)

            req = parse_strict_json(raw_input)
            version = req.get("version")
            task_id = str(req.get("task_id", ""))
            task_kind = str(req.get("task_kind", ""))
            payload = req.get("payload", {})

            if version != 1 or task_kind != "execution.evaluate":
                err_resp = {
                    "version": 1,
                    "task_id": task_id,
                    "success": False,
                    "result": None,
                    "error_code": "UNSUPPORTED_TASK_KIND",
                    "error_message": f"Unsupported worker task kind: {task_kind}",
                }
                sys.stdout.buffer.write(to_canonical_json_bytes(err_resp))
                sys.stdout.buffer.flush()
                return

            graph_data = payload.get("graph") or payload.get("graph_document")
            inputs_data = payload.get("inputs", {})
            seed = payload.get("seed")
            budget_raw = payload.get("budget", {})
            catalog_fp = payload.get("catalog_fingerprint")

            if not isinstance(graph_data, dict):
                err_resp = {
                    "version": 1,
                    "task_id": task_id,
                    "success": False,
                    "result": None,
                    "error_code": "INVALID_GRAPH_DOCUMENT",
                    "error_message": "Missing or malformed graph_document in payload",
                }
                sys.stdout.buffer.write(to_canonical_json_bytes(err_resp))
                sys.stdout.buffer.flush()
                return

            graph_doc = graph_document_from_wire(graph_data)
            inputs = {
                k: parse_strict_json(v) if isinstance(v, str) else v
                for k, v in inputs_data.items()
            }
            budget = ExecutionBudget(
                max_nodes=int(budget_raw.get("max_nodes", 1_000)),
                max_samples=int(budget_raw.get("max_samples", 1_000_000)),
                max_output_values=int(budget_raw.get("max_output_values", 10_000_000)),
                max_trials=int(budget_raw.get("max_trials", 100)),
                max_elapsed_seconds=float(budget_raw.get("max_elapsed_seconds", 60.0)),
            )

            async with create_runtime(
                catalog_roots=approved_catalog_roots(),
            ) as runtime:
                catalog_svc = runtime.require(HOST_CATALOG)
                execution_svc = runtime.require(HOST_EXECUTION)

                # Verify catalog fingerprint if provided
                if (
                    catalog_fp
                    and catalog_svc.snapshot().whole_fingerprint != catalog_fp
                ):
                    err_resp = {
                        "version": 1,
                        "task_id": task_id,
                        "success": False,
                        "result": None,
                        "error_code": "CATALOG_FINGERPRINT_MISMATCH",
                        "error_message": (
                            "Catalog fingerprint changed across worker boundary"
                        ),
                    }
                    sys.stdout.buffer.write(to_canonical_json_bytes(err_resp))
                    sys.stdout.buffer.flush()
                    return

                result = execution_svc.execute(
                    SingleExecutionRequest(
                        graph_document=graph_doc,
                        inputs=inputs,
                        seed=seed,
                        budget=budget,
                    )
                )

                result_dict = {
                    "success": result.success,
                    "outputs": value_to_wire(result.outputs),
                    "reproducibility": (
                        {
                            "graph_id": result.reproducibility.graph_id,
                            "graph_fingerprint": (
                                result.reproducibility.graph_fingerprint
                            ),
                            "catalog_fingerprint": (
                                result.reproducibility.catalog_fingerprint
                            ),
                            "dependency_fingerprint": (
                                result.reproducibility.dependency_fingerprint
                            ),
                            "plugin_versions": list(
                                result.reproducibility.plugin_versions
                            ),
                            "source_digests": list(
                                result.reproducibility.source_digests
                            ),
                            "normalized_parameters": value_to_wire(
                                result.reproducibility.normalized_parameters
                            ),
                            "input_hash": result.reproducibility.input_hash,
                            "seed": result.reproducibility.seed,
                            "output_hash": result.reproducibility.output_hash,
                            "elapsed_seconds": result.reproducibility.elapsed_seconds,
                            "status": result.reproducibility.status,
                        }
                        if result.reproducibility
                        else None
                    ),
                    "issues": [
                        {"code": i.code, "message": i.message, "path": i.path}
                        for i in result.issues
                    ],
                    "elapsed_seconds": result.elapsed_seconds,
                }

                resp = {
                    "version": 1,
                    "task_id": task_id,
                    "success": result.success,
                    "result": result_dict,
                    "error_code": None,
                    "error_message": None,
                }
                sys.stdout.buffer.write(to_canonical_json_bytes(resp))
                sys.stdout.buffer.flush()

        except Exception as err:  # noqa: BLE001 - worker process boundary
            err_resp = {
                "version": 1,
                "task_id": task_id,
                "success": False,
                "result": None,
                "error_code": type(err).__name__,
                "error_message": str(err),
            }
            sys.stdout.buffer.write(to_canonical_json_bytes(err_resp))
            sys.stdout.buffer.flush()

    asyncio.run(_execute())
    return 0


if __name__ == "__main__":
    sys.exit(worker_main(sys.argv[1:]))


__all__ = ("approved_catalog_roots", "create_runtime", "worker_main")
