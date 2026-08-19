"""Research workbench gateway route tests (FEAT-API-26).

The executor is replaced with a deterministic stub that returns a genuine
Research report built from the shared fixtures, so these tests exercise the
gateway's own lifecycle, projections, and authorization without depending on a
live market data provider.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import app.services.data as data_service
import app.services.research as research_service
import pytest
from app.services.api.identity import require_auth_context
from app.services.api.widgets.research import orchestration
from app.services.api.widgets.research import routes as research_routes
from app.services.api.widgets.research.projections import project_report
from app.services.api.widgets.research.registry import (
    ResearchRun,
    ResearchWorkbenchRegistry,
)
from app.services.api.widgets.research.routes import _research_source, router
from app.services.research import run_edge_lab_profile
from fastapi import FastAPI

from tests.api._support import get_json
from tests.api._support import post_json as _post_json
from tests.research._support import make_dataset, make_edge_lab_config
from tests.strategy.unit.test_models import make_auth

_TERMINAL = {"completed", "failed", "cancelled"}


def post_json(
    app: FastAPI,
    path: str,
    payload: Mapping[str, Any],
    *,
    headers: Mapping[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Submit JSON with a test key for the two idempotent Research writes."""
    if headers is None and (
        path == "/api/v1/research/automation"
        or (path.startswith("/api/v1/research/experiments/") and path.endswith("/runs"))
    ):
        headers = {"Idempotency-Key": f"test-{time.monotonic_ns()}"}
    return _post_json(app, path, payload, headers=headers)


@pytest.fixture(autouse=True)
def _isolate_async_idempotency(monkeypatch: pytest.MonkeyPatch) -> None:
    """Execute reserved async operations without external Identity persistence."""

    async def execute(**values: object) -> object:
        operation = cast("Callable[[], Any]", values["operation"])
        return await operation()

    monkeypatch.setattr(research_routes, "run_idempotent_write_async", execute)


def _stub_executor(
    artifact_root: Path,
) -> Callable[[ResearchRun, Callable[..., None]], Mapping[str, Any]]:
    """Build an executor returning a genuine report from shared fixtures.

    Args:
        artifact_root: Test-only artifact root.

    Returns:
        Executor compatible with the workbench registry.
    """

    def execute(run: ResearchRun, emit: Callable[..., None]) -> Mapping[str, Any]:
        """Run the real Research workflow over fixture evidence.

        Args:
            run: Queued run record.
            emit: Ordered progress emitter.

        Returns:
            Result material retained on the run record.
        """
        emit("data", "Resolving canonical dataset")
        dataset = make_dataset(rows=60)
        config = make_edge_lab_config(
            artifact_root, selected_stages=("data", "metrics")
        )
        response = run_edge_lab_profile(
            dataset, hypothesis=run.hypothesis, config=config
        )
        emit("research", "Research report produced")
        return {
            "report": response.data,
            "dataset": {
                "identity": {
                    "symbol": run.symbol,
                    "timeframe": run.timeframe,
                    "record_count": 60,
                },
                "preview": [],
            },
            "effective_configuration": {"selected_stages": list(run.selected_stages)},
            "artifacts": [],
        }

    return execute


def _app(*, authenticated: bool, artifact_root: Path) -> FastAPI:
    """Build an isolated API application with a composed workbench registry.

    Args:
        authenticated: Whether to inject a permitted human principal.
        artifact_root: Test-only artifact root.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(router)
    registry = ResearchWorkbenchRegistry(executor=_stub_executor(artifact_root))
    app.state.test_research_registry = registry

    def source(operation: str, *args: object, **kwargs: object) -> object:
        """Dispatch one workbench operation against the test registry.

        Returns:
            Registry or read-model result.

        Raises:
            ValueError: If the operation is unsupported.
        """
        if operation == "registry":
            return registry
        if operation in {"expectancy", "drift", "stress", "intelligence"}:
            return {"available": False, "reason": "NOT_SELECTED"}
        raise ValueError(operation)

    app.dependency_overrides[_research_source] = lambda: source
    if authenticated:
        auth = make_auth().model_copy(
            update={"permissions": ("research:run", "research:read")}
        )
        app.dependency_overrides[require_auth_context] = lambda: auth
    return app


def _await_terminal(app: FastAPI, run_id: str) -> Mapping[str, Any]:
    """Poll one run until it reaches a terminal state.

    Args:
        app: Configured application.
        run_id: Run identity.

    Returns:
        Terminal run detail.
    """
    for _ in range(200):
        status_code, body = get_json(app, f"/api/v1/research/runs/{run_id}")
        assert status_code == 200, body
        detail = dict(body)  # type: ignore[arg-type]
        if str(detail["status"]) in _TERMINAL:
            return detail
        time.sleep(0.05)
    raise AssertionError("run did not reach a terminal state")


def _create_experiment(app: FastAPI) -> str:
    """Create one experiment and return its identity.

    Args:
        app: Configured application.

    Returns:
        Created experiment identity.
    """
    status_code, body = post_json(
        app,
        "/api/v1/research/experiments",
        {
            "name": "Mean reversion sweep",
            "hypothesis": "Returns mean-revert over one research bar.",
            "tags": ["fx"],
        },
    )
    assert status_code == 201, body
    return str(body["experiment_id"])


def test_presets_are_server_owned(tmp_path: Path) -> None:
    """Verify presets expose stages and approved override keys."""
    status_code, body = get_json(
        _app(authenticated=True, artifact_root=tmp_path), "/api/v1/research/presets"
    )

    assert status_code == 200, body
    payload = dict(body)  # type: ignore[arg-type]
    assert {item["preset_id"] for item in payload["presets"]} == {
        "quick_look",
        "standard_edge",
        "deep_validation",
    }
    assert "data" in payload["stages"]
    assert "market-structure" in payload["stage_views"]
    for preset in payload["presets"]:
        assert "allowed_root" not in preset
        assert "limits" not in preset


def test_run_lifecycle_produces_stage_projections(tmp_path: Path) -> None:
    """Verify create, monitor, and stage retrieval over one real report."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)

    status_code, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {
            "dataset": {"symbol": "TEST", "timeframe": "M1", "bar_limit": 60},
            "preset": "quick_look",
            "selected_stages": ["data", "metrics"],
            "reason": "unit test",
        },
    )
    assert status_code == 202, accepted
    run_id = str(accepted["run_id"])
    assert accepted["status"] in {"queued", "running"}

    detail = _await_terminal(app, run_id)
    assert detail["status"] == "completed", detail
    assert detail["report_id"]
    assert detail["dataset_hash"]
    assert detail["advisory_only"] is True

    status_code, metrics = get_json(
        app, f"/api/v1/research/runs/{run_id}/stages/metrics"
    )
    assert status_code == 200, metrics
    assert metrics["state"] == "completed"
    assert "metrics" in metrics["evidence"]

    status_code, studies = get_json(
        app, f"/api/v1/research/runs/{run_id}/stages/studies"
    )
    assert status_code == 200, studies
    assert studies["state"] == "not_selected"
    assert studies["reason"] == "STAGE_NOT_SELECTED"

    status_code, report = get_json(app, f"/api/v1/research/runs/{run_id}/report")
    assert status_code == 200, report
    assert report["available"] is True
    assert report["report"]["schema_id"] == "research.report.v1"


def test_unknown_stage_is_rejected(tmp_path: Path) -> None:
    """Verify an unregistered stage view fails closed."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)
    _, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
    )
    run_id = str(accepted["run_id"])
    _await_terminal(app, run_id)

    status_code, body = get_json(
        app, f"/api/v1/research/runs/{run_id}/stages/not-a-stage"
    )

    assert status_code == 404, body


def test_unsupported_override_is_rejected(tmp_path: Path) -> None:
    """Verify an override outside the approved set is refused at submission."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)

    status_code, body = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {
            "dataset": {"symbol": "TEST", "timeframe": "M1"},
            "preset": "quick_look",
            "approved_overrides": {"allowed_root": "/etc"},
        },
    )

    assert status_code == 422, body


def test_comparison_is_server_derived(tmp_path: Path) -> None:
    """Verify two completed runs compare without browser-held snapshots."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)
    run_ids: list[str] = []
    for _ in range(2):
        _, accepted = post_json(
            app,
            f"/api/v1/research/experiments/{experiment_id}/runs",
            {
                "dataset": {"symbol": "TEST", "timeframe": "M1"},
                "preset": "quick_look",
                "selected_stages": ["data", "metrics"],
            },
        )
        run_ids.append(str(accepted["run_id"]))
    for run_id in run_ids:
        _await_terminal(app, run_id)

    status_code, body = post_json(
        app, "/api/v1/research/runs/compare", {"run_ids": run_ids}
    )

    assert status_code == 200, body
    assert body["baseline_run_id"] == run_ids[0]
    assert len(body["entries"]) == 2
    # The stub selects data and metrics only, so Research publishes no
    # scorecard and the comparison reports that rather than inventing a score.
    assert body["entries"][1]["score"] is None
    assert set(body["metric_names"]) == {
        "activity",
        "candles",
        "ranges",
        "returns",
        "roc",
        "spread",
        "volatility",
    }
    assert body["entries"][1]["metrics"]["returns"]["delta"] == 0.0


def test_automation_batch_reports_per_symbol_runs(tmp_path: Path) -> None:
    """Verify a batch queues one run per symbol with visible status."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)

    status_code, batch = post_json(
        app,
        "/api/v1/research/automation",
        {
            "experiment_id": experiment_id,
            "symbols": ["TEST", "OTHER"],
            "timeframe": "M1",
            "preset": "quick_look",
            "selected_stages": ["data", "metrics"],
        },
    )

    assert status_code == 202, batch
    assert batch["counts"]["total"] == 2
    batch_id = str(batch["batch_id"])

    for _ in range(200):
        _, view = get_json(app, f"/api/v1/research/automation/{batch_id}")
        if str(dict(view)["status"]) in {"completed", "partial", "failed"}:  # type: ignore[arg-type]
            break
        time.sleep(0.05)
    _, view = get_json(app, f"/api/v1/research/automation/{batch_id}")
    payload = dict(view)  # type: ignore[arg-type]
    assert payload["counts"]["completed"] == 2, payload


def test_research_job_writes_require_idempotency_keys(tmp_path: Path) -> None:
    """Verify run and automation mutations fail before owner delegation."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)

    run_status, run_body = _post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
    )
    automation_status, automation_body = _post_json(
        app,
        "/api/v1/research/automation",
        {
            "experiment_id": experiment_id,
            "symbols": ["TEST"],
            "timeframe": "M1",
            "preset": "quick_look",
        },
        headers={"Idempotency-Key": "   "},
    )

    assert run_status == 400
    assert run_body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"
    assert automation_status == 400
    assert automation_body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_research_job_writes_use_shared_async_idempotency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify both writes reserve their canonical scope before mutation."""
    calls: list[dict[str, object]] = []

    async def execute(**values: object) -> object:
        calls.append(dict(values))
        operation = cast("Callable[[], Any]", values["operation"])
        return await operation()

    monkeypatch.setattr(research_routes, "run_idempotent_write_async", execute)
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)

    run_status, _ = _post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
        headers={"Idempotency-Key": "run-key"},
    )
    automation_status, _ = _post_json(
        app,
        "/api/v1/research/automation",
        {
            "experiment_id": experiment_id,
            "symbols": ["OTHER"],
            "timeframe": "M1",
            "preset": "quick_look",
        },
        headers={"Idempotency-Key": "automation-key"},
    )

    assert run_status == 202
    assert automation_status == 202
    assert [call["route"] for call in calls] == [
        "/api/v1/research/experiments/{experiment_id}/runs",
        "/api/v1/research/automation",
    ]
    assert [call["key"] for call in calls] == ["run-key", "automation-key"]
    assert calls[0]["principal_id"] == "builder"
    assert (
        cast("Mapping[str, object]", calls[0]["request_material"])["experiment_id"]
        == experiment_id
    )


def test_dashboard_retains_negative_evidence(tmp_path: Path) -> None:
    """Verify the ledger reports status and readiness distributions."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)
    _, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
    )
    _await_terminal(app, str(accepted["run_id"]))

    status_code, body = get_json(app, "/api/v1/research/dashboard")

    assert status_code == 200, body
    payload = dict(body)  # type: ignore[arg-type]
    assert payload["status_distribution"]["completed"] == 1
    assert payload["readiness_distribution"]
    assert set(payload["study_counts"]) == {
        "confirmed",
        "contradicted",
        "inconclusive",
    }


def test_workbench_fails_closed_without_authentication(tmp_path: Path) -> None:
    """Verify unauthenticated callers cannot reach the workbench."""
    status_code, body = get_json(
        _app(authenticated=False, artifact_root=tmp_path),
        "/api/v1/research/dashboard",
    )

    assert status_code == 401, body


def test_cancel_marks_a_run_cancelled(tmp_path: Path) -> None:
    """Verify cooperative cancellation reaches a terminal cancelled state."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)
    _, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
    )
    run_id = str(accepted["run_id"])

    status_code, cancelled = post_json(
        app, f"/api/v1/research/runs/{run_id}/cancel", {}
    )

    assert status_code == 200, cancelled
    detail = _await_terminal(app, run_id)
    assert detail["status"] in {"cancelled", "completed"}


def test_unknown_run_fails_closed(tmp_path: Path) -> None:
    """Verify an unknown run identity is refused rather than invented."""
    status_code, body = get_json(
        _app(authenticated=True, artifact_root=tmp_path),
        "/api/v1/research/runs/rrn-00000000-0000-4000-8000-000000000000",
    )

    assert status_code == 404, body


def test_artifacts_report_the_server_owned_root(tmp_path: Path) -> None:
    """Verify artifact listings never expose a filesystem root to a browser."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    experiment_id = _create_experiment(app)
    _, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {"dataset": {"symbol": "TEST", "timeframe": "M1"}, "preset": "quick_look"},
    )
    run_id = str(accepted["run_id"])
    _await_terminal(app, run_id)

    status_code, body = get_json(app, f"/api/v1/research/runs/{run_id}/artifacts")

    assert status_code == 200, body
    payload = dict(body)  # type: ignore[arg-type]
    assert payload["artifact_root_owner"] == "api"
    assert str(tmp_path) not in str(payload)


def test_presets_never_expose_server_owned_limits(tmp_path: Path) -> None:
    """Verify no browser-visible preset carries a root or a resource ceiling."""
    _, body = get_json(
        _app(authenticated=True, artifact_root=tmp_path), "/api/v1/research/presets"
    )

    serialized = str(body)
    assert "allowed_root" not in serialized
    assert "max_rows" not in serialized
    assert "max_artifact_bytes" not in serialized


def test_expectancy_and_drift_never_enact_governance(tmp_path: Path) -> None:
    """Verify the read routes report state and claim no enacting authority."""
    app = _app(authenticated=True, artifact_root=tmp_path)

    expectancy_status, expectancy = get_json(app, "/api/v1/research/expectancy")
    drift_status, drift = get_json(app, "/api/v1/research/drift")

    assert expectancy_status == 200, expectancy
    assert drift_status == 200, drift
    assert dict(expectancy)["transition_permitted"] is False  # type: ignore[arg-type]
    assert dict(drift)["suspension_enacted_by_ui"] is False  # type: ignore[arg-type]


def test_intelligence_route_uses_persisted_dataset_decision_time(
    tmp_path: Path,
) -> None:
    """Verify intelligence is scoped by the run symbol and dataset availability."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    registry = app.state.test_research_registry
    experiment_id = _create_experiment(app)
    _, accepted = post_json(
        app,
        f"/api/v1/research/experiments/{experiment_id}/runs",
        {
            "dataset": {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "asset_class": "forex",
            },
            "preset": "quick_look",
        },
    )
    run_id = str(accepted["run_id"])
    _await_terminal(app, run_id)
    run = registry.get_run(run_id, principal_id="builder")
    assert run is not None
    run.dataset = {
        **dict(run.dataset or {}),
        "identity": {
            **dict(dict(run.dataset or {}).get("identity", {})),
            "available_at": "2026-01-02T00:00:00+00:00",
        },
    }
    calls: list[dict[str, object]] = []

    def source(operation: str, **values: object) -> object:
        """Capture route inputs while retaining registry access."""
        if operation == "registry":
            return registry
        if operation == "intelligence":
            calls.append(dict(values))
            return {"available": False, "reason": "INTELLIGENCE_COVERAGE_MISSING"}
        raise ValueError(operation)

    app.dependency_overrides[_research_source] = lambda: source
    status_code, _ = get_json(
        app, f"/api/v1/research/runs/{run_id}/stages/intelligence"
    )

    assert status_code == 200
    assert calls == [
        {
            "asset_class": "forex",
            "symbol": "EURUSD",
            "available_at": "2026-01-02T00:00:00+00:00",
        }
    ]


def test_intelligence_builds_point_in_time_fundamental_and_sentiment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify both branches use bounded Data queries and the closed lexicon."""
    queries: list[dict[str, object]] = []

    def build_query(**values: object) -> object:
        queries.append(dict(values))
        return values

    monkeypatch.setattr(data_service, "build_research_source_query", build_query)

    def assess(asset_class: str, *, model: str) -> object:
        """Return applicable evidence for every registered model."""
        del model
        return SimpleNamespace(status="applicable", asset_class=asset_class, reasons=())

    def build_fundamental(query: object, **values: object) -> object:
        """Return tagged fundamental evidence for projection."""
        del query
        return {"branch": "fundamental", **values}

    monkeypatch.setattr(research_service, "assess_intelligence_applicability", assess)
    monkeypatch.setattr(
        research_service,
        "build_fundamental_source_evidence",
        build_fundamental,
    )
    sentiment_calls: list[dict[str, object]] = []

    def build_sentiment(query: object, **values: object) -> object:
        del query
        sentiment_calls.append(dict(values))
        return {"branch": "sentiment", **values}

    monkeypatch.setattr(
        research_service, "build_sentiment_source_evidence", build_sentiment
    )
    monkeypatch.setattr(
        research_service,
        "project_intelligence_evidence",
        lambda evidence: evidence,
    )

    result = orchestration._intelligence_view(
        "forex", "EURUSD", "2026-01-02T02:00:00+02:00"
    )

    assert result["available"] is True
    assert dict(result["fundamental"])["branch"] == "fundamental"
    assert dict(result["sentiment"])["branch"] == "sentiment"
    assert [query["source_kinds"] for query in queries] == [
        ("macro",),
        ("news", "social", "alternative", "macro"),
    ]
    assert all(query["asset_scope"] == ("EURUSD",) for query in queries)
    assert all(
        str(query["decision_time"]) == "2026-01-02 00:00:00+00:00" for query in queries
    )
    assert sentiment_calls == [{"measurement_version": "lexicon-v1"}]


@pytest.mark.parametrize(
    ("available_at", "reason"),
    [
        (None, "DECISION_TIME_MISSING"),
        ("2026-01-02T00:00:00", "DECISION_TIME_INVALID"),
        ("not-a-time", "DECISION_TIME_INVALID"),
    ],
)
def test_intelligence_never_falls_back_to_wall_clock(
    available_at: str | None,
    reason: str,
) -> None:
    """Verify absent or unsafe decision instants fail closed."""
    result = orchestration._intelligence_view("forex", "EURUSD", available_at)

    assert result["available"] is False
    assert result["reason"] == reason


def test_intelligence_reports_source_coverage_gaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify absent eligible records remain explicit negative evidence."""

    def assess(asset_class: str, *, model: str) -> object:
        """Return applicable evidence for every registered model."""
        del model
        return SimpleNamespace(status="applicable", asset_class=asset_class, reasons=())

    def missing_fundamental(query: object, **values: object) -> object:
        """Represent missing eligible fundamental records."""
        del query, values
        raise ValueError("FUNDAMENTAL_COVERAGE_MISSING")

    def missing_sentiment(query: object, **values: object) -> object:
        """Represent missing eligible sentiment records."""
        del query, values
        raise ValueError("SENTIMENT_COVERAGE_MISSING")

    monkeypatch.setattr(
        data_service, "build_research_source_query", lambda **values: values
    )
    monkeypatch.setattr(research_service, "assess_intelligence_applicability", assess)
    monkeypatch.setattr(
        research_service,
        "build_fundamental_source_evidence",
        missing_fundamental,
    )
    monkeypatch.setattr(
        research_service,
        "build_sentiment_source_evidence",
        missing_sentiment,
    )

    result = orchestration._intelligence_view(
        "forex", "EURUSD", "2026-01-02T00:00:00+00:00"
    )

    assert result["available"] is False
    assert result["reason"] == "INTELLIGENCE_COVERAGE_MISSING"
    assert result["fundamental_reason"] == "FUNDAMENTAL_COVERAGE_MISSING"
    assert result["sentiment_reason"] == "SENTIMENT_COVERAGE_MISSING"


def test_expectancy_transition_requires_govern_permission(tmp_path: Path) -> None:
    """Verify the governed transition is unavailable to ordinary readers."""
    status_code, body = post_json(
        _app(authenticated=True, artifact_root=tmp_path),
        "/api/v1/research/expectancy/exp-1/transition",
        {
            "target_state": "under_review",
            "decision": "submit",
            "reason": "Evidence is ready for review.",
        },
        headers={"Idempotency-Key": "transition-1"},
    )

    assert status_code == 403, body


def test_expectancy_and_stress_creation_require_idempotency(
    tmp_path: Path,
) -> None:
    """Verify both governed creation workflows require durable keys."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )
    app.dependency_overrides[require_auth_context] = lambda: auth

    expectancy_status, expectancy_body = _post_json(
        app,
        "/api/v1/research/expectancy",
        {
            "run_id": "rrn-1",
            "exact_version": "1",
            "strategy_ref": "strategy-demo",
            "sample_from_utc": "2026-01-01T00:00:00Z",
            "sample_to_utc": "2026-06-01T00:00:00Z",
            "sample_size": 100,
            "out_of_sample_status": "walk_forward",
            "win_rate": 0.6,
            "avg_win_r": 2.0,
            "avg_loss_r": 1.0,
            "expected_value_r": 0.8,
            "max_drawdown_r": 4.0,
            "min_reward_risk": 1.5,
        },
    )
    stress_status, stress_body = _post_json(
        app,
        "/api/v1/research/stress-scenarios",
        {
            "scenario_key": "broad_market_dislocation",
            "hypothesis": "Can the evidence tolerate a broad dislocation?",
        },
    )

    assert expectancy_status == 400
    assert expectancy_body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"
    assert stress_status == 400
    assert stress_body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_expectancy_and_stress_creation_delegate_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify creation delegates persistence once and returns owner evidence."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )
    calls: list[tuple[str, bool]] = []

    def source(operation: str, **values: object) -> object:
        """Provide deterministic previews and capture owner persistence."""
        if operation == "registry":
            return object()
        if operation == "build_expectancy":
            calls.append((operation, bool(values["persist"])))
            return {"available": True, "profile": {"profile_id": "id-profile"}}
        if operation == "build_stress":
            calls.append((operation, bool(values["persist"])))
            return {"available": True, "evidence": {"scenario_id": "id-scenario"}}
        raise ValueError(operation)

    app.dependency_overrides[_research_source] = lambda: source
    app.dependency_overrides[require_auth_context] = lambda: auth
    monkeypatch.setattr(
        research_routes, "run_idempotent_write", lambda **values: values["operation"]()
    )

    expectancy_status, _ = _post_json(
        app,
        "/api/v1/research/expectancy",
        {
            "run_id": "rrn-1",
            "exact_version": "1",
            "strategy_ref": "strategy-demo",
            "sample_from_utc": "2026-01-01T00:00:00Z",
            "sample_to_utc": "2026-06-01T00:00:00Z",
            "sample_size": 100,
            "out_of_sample_status": "walk_forward",
            "win_rate": 0.6,
            "avg_win_r": 2.0,
            "avg_loss_r": 1.0,
            "expected_value_r": 0.8,
            "max_drawdown_r": 4.0,
            "min_reward_risk": 1.5,
        },
        headers={"Idempotency-Key": "expectancy-create-1"},
    )
    stress_status, _ = _post_json(
        app,
        "/api/v1/research/stress-scenarios",
        {
            "scenario_key": "broad_market_dislocation",
            "hypothesis": "Can the evidence tolerate a broad dislocation?",
        },
        headers={"Idempotency-Key": "stress-create-1"},
    )

    assert expectancy_status == 201
    assert stress_status == 201
    assert calls == [
        ("build_expectancy", False),
        ("build_expectancy", True),
        ("build_stress", False),
        ("build_stress", True),
    ]


def test_expectancy_transition_requires_idempotency_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify governed expectancy writes require a durable replay key."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )
    app.dependency_overrides[require_auth_context] = lambda: auth
    monkeypatch.setattr(
        research_routes, "run_idempotent_write", lambda **values: values["operation"]()
    )

    status_code, body = post_json(
        app,
        "/api/v1/research/expectancy/exp-1/transition",
        {
            "target_state": "under_review",
            "decision": "submit",
            "reason": "Evidence is ready for review.",
        },
    )

    assert status_code == 400, body
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_expectancy_transition_delegates_authenticated_review_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify transition evidence is server-bound to the reviewer identity."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )
    calls: list[dict[str, object]] = []

    def source(operation: str, **values: object) -> object:
        """Capture the transition or return owner truth for replay."""
        if operation == "transition_expectancy":
            calls.append(dict(values))
            return {"available": True, "reason": None, "profile": values}
        if operation == "expectancy":
            return {"available": True, "reason": None, "profile": {}}
        raise ValueError(operation)

    app.dependency_overrides[_research_source] = lambda: source
    app.dependency_overrides[require_auth_context] = lambda: auth
    monkeypatch.setattr(
        research_routes, "run_idempotent_write", lambda **values: values["operation"]()
    )

    status_code, body = post_json(
        app,
        "/api/v1/research/expectancy/exp-1/transition",
        {
            "target_state": "under_review",
            "decision": "submit",
            "reason": "Evidence is ready for review.",
        },
        headers={"Idempotency-Key": "transition-1"},
    )

    assert status_code == 200, body
    assert len(calls) == 1
    assert calls[0]["reviewer"] == auth.principal_id
    assert calls[0]["profile_id"] == "exp-1"


def test_expectancy_transition_replay_reads_owner_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify a completed identical replay does not repeat the transition."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )
    operations: list[str] = []

    def source(operation: str, **values: object) -> object:
        """Record which owner operation the route requests."""
        operations.append(operation)
        return {"available": True, "reason": None, "profile": values}

    app.dependency_overrides[_research_source] = lambda: source
    app.dependency_overrides[require_auth_context] = lambda: auth
    monkeypatch.setattr(
        research_routes, "run_idempotent_write", lambda **values: values["replay"]()
    )

    status_code, body = post_json(
        app,
        "/api/v1/research/expectancy/exp-1/transition",
        {
            "target_state": "under_review",
            "decision": "submit",
            "reason": "Evidence is ready for review.",
        },
        headers={"Idempotency-Key": "transition-1"},
    )

    assert status_code == 200, body
    assert operations == ["expectancy"]


def test_expectancy_transition_rejects_invalid_lifecycle_edge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify a Research-rejected lifecycle edge fails closed as conflict."""
    app = _app(authenticated=True, artifact_root=tmp_path)
    auth = make_auth().model_copy(
        update={"permissions": ("research:read", "research:govern")}
    )

    def source(operation: str, **values: object) -> object:
        """Reject the transition as Research's composed workflow would."""
        del values
        if operation == "transition_expectancy":
            raise ValueError("EXPECTANCY_TRANSITION_NOT_PERMITTED")
        return {"available": True, "reason": None, "profile": {}}

    app.dependency_overrides[_research_source] = lambda: source
    app.dependency_overrides[require_auth_context] = lambda: auth
    monkeypatch.setattr(
        research_routes, "run_idempotent_write", lambda **values: values["operation"]()
    )

    status_code, body = post_json(
        app,
        "/api/v1/research/expectancy/exp-1/transition",
        {
            "target_state": "approved",
            "decision": "approve",
            "reason": "Attempt to skip review.",
        },
        headers={"Idempotency-Key": "transition-invalid"},
    )

    assert status_code == 409, body
    assert body["detail"] == "EXPECTANCY_TRANSITION_NOT_PERMITTED"


def test_completed_run_survives_registry_rebuild(tmp_path: Path) -> None:
    """Verify persisted reports retain projection behavior after hydration."""
    experiments: dict[str, dict[str, object]] = {}
    runs: dict[str, dict[str, object]] = {}
    batches: dict[str, dict[str, object]] = {}

    def persist_experiment(**values: object) -> None:
        """Retain one projected experiment row."""
        experiments[str(values["experiment_id"])] = {
            **values,
            "tags": list(values["tags"]),  # type: ignore[arg-type]
        }

    def persist_run(**values: object) -> None:
        """Retain the latest projected run lifecycle."""
        runs[str(values["run_id"])] = {
            **values,
            "request": values["request_material"],
        }

    def persist_batch(**values: object) -> None:
        """Retain the latest projected batch state."""
        batches[str(values["batch_id"])] = {
            **values,
            "request": values["request_material"],
        }

    def load_experiments(**values: object) -> tuple[Mapping[str, object], ...]:
        """Return experiment rows for one principal."""
        principal_id = str(values["principal_id"])
        return tuple(
            row for row in experiments.values() if row["principal_id"] == principal_id
        )

    def load_runs(**values: object) -> tuple[Mapping[str, object], ...]:
        """Return run rows for one principal."""
        principal_id = str(values["principal_id"])
        return tuple(
            row for row in runs.values() if row["principal_id"] == principal_id
        )

    def load_batches(**values: object) -> tuple[Mapping[str, object], ...]:
        """Return batch rows for one principal."""
        principal_id = str(values["principal_id"])
        return tuple(
            row for row in batches.values() if row["principal_id"] == principal_id
        )

    store = SimpleNamespace(
        persist_research_experiment=persist_experiment,
        load_research_experiments=load_experiments,
        persist_research_run=persist_run,
        load_research_runs=load_runs,
        persist_research_run_batch=persist_batch,
        load_research_run_batches=load_batches,
    )
    first = ResearchWorkbenchRegistry(executor=_stub_executor(tmp_path), store=store)
    experiment = first.create_experiment(
        principal_id="user-test",
        name="Durable edge",
        hypothesis="The measured edge survives reconstruction.",
        notes=None,
        tags=("durable",),
    )
    run = first.submit_run(
        principal_id="user-test",
        experiment_id=experiment.experiment_id,
        hypothesis=experiment.hypothesis,
        symbol="EURUSD",
        timeframe="H1",
        preset="quick",
        selected_stages=("data", "metrics"),
        reason="Verify durable evidence",
        force_rerun=False,
        request_material={},
    )
    deadline = time.monotonic() + 5.0
    while run.status not in _TERMINAL and time.monotonic() < deadline:
        time.sleep(0.01)
    assert run.status == "completed"

    rebuilt = ResearchWorkbenchRegistry(executor=_stub_executor(tmp_path), store=store)
    hydrated = rebuilt.get_run(run.run_id, principal_id="user-test")

    assert hydrated is not None
    assert hydrated.status == "completed"
    assert (
        project_report(hydrated.report)["report_id"]
        == project_report(run.report)["report_id"]
    )
    assert project_report(hydrated.report)["generated_at"] is not None
