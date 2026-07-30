"""Genuine, non-production infrastructure for Portfolio workflow examples."""

from __future__ import annotations

import hashlib
import sqlite3
import sys
import tempfile
from atexit import register
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from time import perf_counter_ns
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import (
    build_portfolio_rebalance_measurement,
    create_analytics_value,
)
from app.services.data import (
    build_account_state_snapshot,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_data_request,
    get_market_data,
    unwrap_data_response,
)
from app.services.portfolio import (
    create_portfolio_handle,
    create_portfolio_value,
    dump_portfolio_value,
    execute_portfolio_handle_operation,
)
from app.services.risk import (
    create_allocation_risk_decision,
    create_kill_switch_state,
    create_strategy_operational_eligibility_decision,
    get_decision_state,
)
from app.services.simulator import (
    calculate_portfolio_backtest_config_hash,
    create_simulation_value,
    dump_simulation_value,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.services.strategy import (
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.utils import (
    build_response_metadata,
    canonical_json,
    create_auth_context,
    generate_id,
    success_response,
)
from tests.simulator.usage.workflows._support import (
    dependencies as simulation_dependencies,
)
from tests.simulator.usage.workflows._support import (
    live_tick_dataset as _get_live_tick_dataset,
)
from tests.simulator.usage.workflows._support import (
    portfolio_request,
)

NOW = datetime.now(UTC).replace(microsecond=0)
_REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
_WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
_CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"
_ACCOUNT_ID = "req-11111111-1111-4111-8111-111111111112"
_FX_ID = "req-11111111-1111-4111-8111-111111111114"
_SIMULATION_CONTEXT: dict[str, tuple[object, object]] = {}
_EVIDENCE_CACHE: dict[str, object] = {}

ActivePortfolioAllocation = Any
MarketDataset = Any
PortfolioConstructionRequest = Any
PortfolioConstructionResult = Any
PortfolioSettings = Any
PortfolioWorkflowService = Any


def _digest(value: object) -> str:
    """Return the Portfolio validator-compatible digest of an owner value."""
    dump = getattr(value, "model_dump", None)
    material = dump(mode="json") if callable(dump) else value
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def market_request(data_kind: str, *, timeframe: str, limit: int) -> object:
    """Build one bounded genuine MT5 request."""
    end = datetime.now(UTC)
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=end - timedelta(days=5),
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


def live_market_dataset() -> MarketDataset:
    """Return bounded records fetched through the genuine MT5 Data path."""
    cached = _EVIDENCE_CACHE.get("market")
    if cached is not None:
        return cached
    request = market_request("bars", timeframe="M1", limit=20)
    response = get_market_data(request)
    market = unwrap_data_response(
        response,
        operation="portfolio.workflow.market_data",
        request_id=request.request_id,
    )
    _EVIDENCE_CACHE["market"] = market
    return market


def _live_tick_dataset() -> object:
    """Return one cached genuine MT5-derived tick dataset."""
    cached = _EVIDENCE_CACHE.get("ticks")
    if cached is None:
        cached = _get_live_tick_dataset()
        _EVIDENCE_CACHE["ticks"] = cached
    return cached


def settings() -> PortfolioSettings:
    """Return explicit simulation-only Portfolio policy."""
    schedule = create_portfolio_value(
        "RebalanceSchedule",
        anchor_at=NOW,
        interval_seconds=3600,
    )
    return create_portfolio_value(
        "PortfolioSettings",
        portfolio_weight_sum_tolerance=Decimal("0.00000001"),
        portfolio_min_weight=Decimal(0),
        portfolio_max_weight=Decimal(1),
        portfolio_max_strategies=10,
        portfolio_min_evidence_observations=1,
        portfolio_max_evidence_age_seconds=31_536_000,
        portfolio_allocation_decision_ttl_seconds=900,
        portfolio_activation_approval_policy={
            "simulation": "automatic_within_policy",
            "paper": "explicit_human",
            "live": "explicit_human",
        },
        portfolio_rebalance_drift_threshold=Decimal("0.05"),
        portfolio_rebalance_schedule=schedule,
    )


class SqlitePortfolioStore:
    """SQLite-backed Portfolio workflow state with immutable value caches."""

    def __init__(self) -> None:
        """Create an isolated state database and canonical object indexes."""
        self.path = ":memory:"
        self._connection = sqlite3.connect(self.path)
        register(self._connection.close)
        self.constructions: dict[str, object] = {}
        self.allocations: dict[tuple[str, str], object] = {}
        self.histories: dict[str, list[object]] = {}
        self.active_scopes: dict[str, tuple[object, int]] = {}
        self.plans: dict[tuple[str, str], object] = {}
        self.idempotency: dict[str, tuple[str, object]] = {}
        self.trading_calls = 0
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE portfolio_values (
                    kind TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    version TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (kind, identity, version)
                );
                CREATE TABLE portfolio_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def _persist(
        self,
        kind: str,
        identity: str,
        version: str,
        value: object,
        audit_record: object,
    ) -> None:
        """Persist one immutable Portfolio value and audit row atomically."""
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO portfolio_values VALUES (?, ?, ?, ?)",
                (
                    kind,
                    identity,
                    version,
                    canonical_json(dump_portfolio_value(value)),
                ),
            )
            self._connection.execute(
                "INSERT INTO portfolio_audit(event_type, payload) VALUES (?, ?)",
                (
                    str(
                        getattr(audit_record, "get", lambda _key, default: default)(
                            "event_type", "portfolio.workflow"
                        )
                    ),
                    canonical_json(audit_record),
                ),
            )

    def save_construction(self, result: object, audit_record: object) -> object:
        """Persist one construction result."""
        existing = self.constructions.get(result.result_id)
        if existing is not None and existing.canonical_hash != result.canonical_hash:
            raise RuntimeError("construction identity conflict")
        self._persist(
            "construction",
            result.result_id,
            result.portfolio_version,
            result,
            audit_record,
        )
        self.constructions[result.result_id] = result
        return existing or result

    def activate_allocation(
        self,
        allocation: object,
        expected_predecessor: str | None,
        expected_revision: int,
        material_hash: str,
        audit_record: object,
    ) -> object:
        """Persist one compare-and-swap allocation activation."""
        prior = self.idempotency.get(allocation.idempotency_key)
        if prior is not None:
            if prior[0] != material_hash:
                raise RuntimeError("activation identity conflict")
            return prior[1]
        key = canonical_json(dict(allocation.scope))
        active = self.active_scopes.get(key)
        current_version = None if active is None else active[0].allocation_version
        current_revision = 0 if active is None else active[1]
        if (
            current_version != expected_predecessor
            or current_revision != expected_revision
        ):
            raise RuntimeError("active allocation revision conflict")
        self._persist(
            "allocation",
            allocation.portfolio_id,
            allocation.allocation_version,
            allocation,
            audit_record,
        )
        revision = current_revision + 1
        self.allocations[(allocation.portfolio_id, allocation.allocation_version)] = (
            allocation
        )
        self.histories.setdefault(allocation.portfolio_id, []).append(allocation)
        self.active_scopes[key] = (allocation, revision)
        self.idempotency[allocation.idempotency_key] = (material_hash, allocation)
        return allocation

    def save_plan(self, plan: object, audit_record: object) -> object:
        """Persist one immutable rebalance plan."""
        self._persist("plan", plan.plan_id, plan.plan_version, plan, audit_record)
        self.plans[(plan.plan_id, plan.plan_version)] = plan
        return plan

    def load_active(
        self, portfolio_id: str, scope_key: str
    ) -> tuple[object, int] | None:
        """Load active state for an exact Portfolio and scope."""
        value = self.active_scopes.get(scope_key)
        if value is None or value[0].portfolio_id != portfolio_id:
            return None
        return value

    def load_allocation(
        self, portfolio_id: str, allocation_version: str
    ) -> object | None:
        """Load one exact allocation version."""
        return self.allocations.get((portfolio_id, allocation_version))

    def load_history(self, portfolio_id: str) -> tuple[object, ...]:
        """Load ordered immutable allocation history."""
        return tuple(self.histories.get(portfolio_id, ()))

    def load_plan(self, plan_id: str, plan_version: str | None) -> object | None:
        """Load an exact or latest plan version."""
        if plan_version is not None:
            return self.plans.get((plan_id, plan_version))
        matches = [
            value
            for (stored_id, _version), value in self.plans.items()
            if stored_id == plan_id
        ]
        return matches[-1] if matches else None


def _owner_bundle(market: object) -> tuple[dict[str, object], ...]:
    """Build exact owner-domain contracts around genuine market evidence."""
    policy = create_strategy_validation_policy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = create_strategy_manifest(
        strategy_id="strategy-a",
        strategy_version="1.0.0",
        module_path="approved.strategies.strategy_a",
        owner_ref="portfolio-workflow",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("SIMULATION"),),
        source_hash="a" * 64,
        artifact_hash="b" * 64,
        dependency_hash="c" * 64,
        provenance_refs=("portfolio-workflow",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    reference = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("SIMULATION"),
        policy_version="strategy-policy-1",
        validation_policy=policy,
        registry_record_hash="a" * 64,
        request_id="req-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        correlation_id="cor-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    eligibility = create_strategy_operational_eligibility_decision(
        decision_id="eligibility-a",
        strategy_id="strategy-a",
        strategy_version="1.0.0",
        scope={"environment": "simulation", "tenant": "owner"},
        state=get_decision_state("APPROVE"),
        conditions=(),
        policy_version="risk-policy-1",
        evidence_refs={"strategy": "a" * 64},
        suspended=False,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
        audit_ref="risk-eligibility-audit",
    )
    account = build_account_state_snapshot(
        account_id="portfolio-demo",
        currency="USD",
        balances=(
            {"asset": "USD", "total": Decimal(10_000), "available": Decimal(10_000)},
        ),
        equity=Decimal(10_000),
        margin_used=Decimal(0),
        margin_available=Decimal(10_000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="portfolio-workflow",
        request_id=_ACCOUNT_ID,
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    fx_leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.15"),
        source_id="portfolio-workflow",
        provider_symbol="EURUSD",
        as_of=NOW,
        provenance={"market_dataset_id": market.request_id},
    )
    fx = build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="USD",
        legs=(fx_leg,),
        composite_rate=Decimal("1.15"),
        path_policy_id="direct",
        path_policy_version="1",
        provenance={"market_dataset_id": market.request_id},
        request_id=_FX_ID,
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    closes = [Decimal(str(row.close)) for row in market.records]
    returns = [
        abs((current / previous) - Decimal(1))
        for previous, current in pairwise(closes)
        if previous
    ]
    volatility = max(
        sum(returns, Decimal(0)) / Decimal(max(len(returns), 1)),
        Decimal("0.000001"),
    )
    analytics = create_analytics_value(
        "PortfolioAllocationEvidence",
        contract_version="v1",
        schema_id="analytics.portfolio_allocation_evidence.v1",
        evidence_id="analytics-portfolio-workflow",
        allocation_reference="pre-construction",
        result_references=(market.request_id,),
        measurement_start=market.start,
        measurement_end=market.end,
        base_currency="USD",
        component_metrics=(
            {
                "component_id": "component-a",
                "mean_absolute_return": float(volatility),
                "observations": len(market.records),
            },
        ),
        aggregate_metrics=(),
        dependence_evidence={
            "section_key": "dependence",
            "criticality": "optional",
            "metrics": (),
            "status": "skipped",
            "reason": "One component has no cross-component dependence.",
        },
        concentration_evidence={
            "section_key": "concentration",
            "criticality": "optional",
            "metrics": (),
            "status": "skipped",
            "reason": "One component has no concentration comparison.",
        },
        caveats=(),
        fx_lineage={
            "source_contract": "data.fx_conversion_evidence.v1",
            "source_version": "v1",
            "source_schema_id": "data.fx_conversion_evidence.v1",
            "source_ids": (_FX_ID,),
            "configuration_sources": ("portfolio-workflow",),
            "account_currency": "USD",
            "transformations": ("direct EURUSD conversion",),
        },
    )
    return (
        {"component-a": reference},
        {"eligibility-a": eligibility},
        {"account": account},
        {"analytics": analytics},
        {_FX_ID: fx},
        {"volatility": volatility, "observations": len(market.records)},
    )


def _risk_decision(candidate: object, *, active: bool = False) -> object:
    """Compute a Risk-owned decision bound to exact candidate weights."""
    return create_allocation_risk_decision(
        decision_id=f"risk-{candidate.result_id}",
        portfolio_id=candidate.portfolio_id,
        reviewed_version=candidate.portfolio_version,
        state=get_decision_state("APPROVE"),
        capped_weights={
            row.component_id: row.capital_weight for row in candidate.component_weights
        },
        risk_budget_projection={
            row.component_id: row.proposed_risk_budget_weight
            for row in candidate.component_weights
        },
        conditions=(),
        policy_version="risk-policy-1",
        evidence_refs={"construction": candidate.canonical_hash},
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        active=active,
        predecessor_version=None,
        audit_ref=f"risk-audit-{candidate.result_id}",
    )


def _activate_risk(_request: object, decision: object) -> object:
    """Return the exact approved decision as the active Risk projection."""
    values = decision.model_dump(mode="python")
    values["active"] = True
    return create_allocation_risk_decision(**values)


def _inactive_kill_switch(_scope: object) -> tuple[object, ...]:
    """Return current inactive global Risk kill-switch evidence."""
    return (
        create_kill_switch_state(
            state_id="kill-switch-workflow",
            scope_level="global",
            scope={},
            state="inactive",
            reason="simulation-policy-clear",
            version=1,
            updated_at=NOW,
        ),
    )


async def _execute_rebalance(request: object) -> object:
    """Execute bounded simulation-route reductions without broker mutation."""
    outcomes = tuple(
        {"action_id": row["action_id"], "status": "success", "data": {}}
        for row in request.actions
    )
    return success_response(
        {"plan_id": request.plan_id, "outcomes": outcomes},
        message="Simulation-route reductions reconciled",
        metadata=build_response_metadata(
            name="execute_portfolio_rebalance",
            domain="trading",
            risk_level="high",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            start_time=perf_counter_ns(),
            read_only=False,
            writes_file=False,
            modifies_database=True,
            places_trade=True,
            requires_network=False,
            extensions={"redaction_applied": True},
        ),
    )


def construction_workflow() -> tuple[
    PortfolioWorkflowService,
    PortfolioConstructionRequest,
    SqlitePortfolioStore,
    MarketDataset,
]:
    """Compose the Portfolio workflow over genuine MT5 and Simulator paths."""
    market = live_market_dataset()
    refs, decisions, account_row, analytics_row, fx, metrics = _owner_bundle(market)
    account = account_row["account"]
    analytics = analytics_row["analytics"]
    evidence = create_portfolio_value(
        "EvidenceReferenceSet",
        account_snapshot_id=account.request_id,
        account_snapshot_hash=_digest(account),
        account_snapshot_as_of=account.snapshot_at,
        market_dataset_id=market.request_id,
        market_dataset_hash=_digest(market),
        market_dataset_as_of=market.end,
        analytics_evidence_id=analytics.evidence_id,
        analytics_evidence_hash=_digest(analytics),
        analytics_evidence_as_of=analytics.measurement_end,
        fx_evidence_ids=(_FX_ID,),
        fx_evidence_hashes=(_digest(fx[_FX_ID]),),
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest",
        request_id=_REQUEST_ID,
        workflow_id=_WORKFLOW_ID,
        correlation_id=_CORRELATION_ID,
        causation_id=None,
        portfolio_id="portfolio-alpha",
        portfolio_version="version-1",
        scope={"environment": "simulation", "tenant": "owner"},
        components=(
            {
                "component_id": "component-a",
                "strategy_id": "strategy-a",
                "strategy_version": "1.0.0",
                "registry_record_hash": "a" * 64,
                "eligibility_decision_id": "eligibility-a",
            },
        ),
        method="equal",
        fixed_weights=(),
        evidence=evidence,
        measurement_start=market.start,
        measurement_end=market.end,
        base_currency="USD",
        runtime_profile="simulation",
        execution_route="sim",
        simulation_policy_version="simulation-policy-1",
        requested_at=NOW,
    )

    def evidence_source(_request: object) -> object:
        return create_portfolio_value(
            "ConstructionEvidenceInputs",
            account_snapshot=account,
            market_dataset=market,
            analytics_evidence=analytics,
            fx_evidence=fx,
            component_volatilities={"component-a": metrics["volatility"]},
            component_observations={"component-a": metrics["observations"]},
        )

    def simulation_runner(receiver_request: object) -> object:
        dataset, auth = _SIMULATION_CONTEXT[receiver_request.request_id]
        with tempfile.TemporaryDirectory(prefix="wf-port-simulator-") as directory:
            return unwrap_simulation_response(
                run_portfolio_backtest(
                    receiver_request,
                    auth,
                    simulation_dependencies(Path(directory), dataset),
                ),
                operation="portfolio.workflow.run_portfolio_backtest",
            )

    executions: dict[str, object] = {}

    async def trading_executor(receiver_request: object) -> object:
        store.trading_calls += 1
        result = await _execute_rebalance(receiver_request)
        executions[f"trading-execution:{receiver_request.request_id}"] = result
        return result

    store = SqlitePortfolioStore()
    repository = create_portfolio_handle("PortfolioRepository", store)
    dependencies_handle = create_portfolio_handle(
        "PortfolioWorkflowDependencies",
        strategy_reference_source=lambda _request: refs,
        eligibility_decision_source=lambda _request: decisions,
        construction_evidence_source=evidence_source,
        simulation_runner=simulation_runner,
        risk_reviewer=lambda receiver: _risk_decision(
            next(
                item
                for item in store.constructions.values()
                if item.portfolio_version == receiver.portfolio_version
            )
        ),
        risk_budget_activator=_activate_risk,
        kill_switch_source=_inactive_kill_switch,
        trading_executor=trading_executor,
        trading_execution_source=lambda reference: executions[reference],
        analytics_measurer=build_portfolio_rebalance_measurement,
        audit_persister=lambda event: event.event_id,
        clock=lambda: NOW,
    )
    service = create_portfolio_handle(
        "PortfolioWorkflowService",
        settings(),
        repository,
        dependencies_handle,
    )
    return service, request, store, market


def simulation_request(candidate: PortfolioConstructionResult) -> object:
    """Build a Simulator request bound to candidate and genuine tick evidence."""
    dataset = _live_tick_dataset()
    original, _original_auth = portfolio_request(dataset)
    payload = dict(dump_simulation_value(original))
    payload.update(
        {
            "request_id": candidate.request_id,
            "workflow_id": candidate.workflow_id,
            "correlation_id": candidate.correlation_id,
            "portfolio_id": candidate.portfolio_id,
            "construction_result_id": candidate.result_id,
            "construction_version": candidate.portfolio_version,
        }
    )
    component = dict(payload["components"][0])
    component.update(
        {
            "component_id": candidate.component_weights[0].component_id,
            "capital_weight": candidate.component_weights[0].capital_weight,
            "risk_budget": candidate.component_weights[0].proposed_risk_budget_weight,
        }
    )
    payload["components"] = (component,)
    payload.pop("config_hash", None)
    payload["config_hash"] = unwrap_simulation_response(
        calculate_portfolio_backtest_config_hash(payload),
        operation="portfolio.workflow.calculate_simulation_hash",
    )
    request = create_simulation_value("PortfolioBacktestRequestV1", **payload)
    auth = create_auth_context(
        principal_id="portfolio-workflow",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="dev",
        request_id=candidate.request_id,
        workflow_id=candidate.workflow_id,
        correlation_id=candidate.correlation_id,
        issued_at=dataset.start - timedelta(days=1),
    )
    _SIMULATION_CONTEXT[candidate.request_id] = (dataset, auth)
    return request


def active_allocation() -> ActivePortfolioAllocation:
    """Build and activate a genuine workflow allocation."""
    service, request, _store, _market = construction_workflow()
    candidate, evidence = execute_portfolio_handle_operation(
        service, "construct", request
    )
    review = execute_portfolio_handle_operation(
        service, "coordinate_review", candidate, simulation_request(candidate), evidence
    )
    return execute_portfolio_handle_operation(
        service,
        "activate",
        candidate,
        evidence,
        review,
        approval_attestation=None,
        approval_validation=None,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="portfolio-workflow-active",
        expected_predecessor=None,
        expected_revision=0,
    )


def rebalance_workflow() -> tuple[
    PortfolioWorkflowService,
    ActivePortfolioAllocation,
    object,
    dict[str, object],
    SqlitePortfolioStore,
    MarketDataset,
]:
    """Return a fully activated workflow with current Risk evidence."""
    service, request, store, market = construction_workflow()
    candidate, evidence = execute_portfolio_handle_operation(
        service, "construct", request
    )
    review = execute_portfolio_handle_operation(
        service,
        "coordinate_review",
        candidate,
        simulation_request(candidate),
        evidence,
    )
    allocation = execute_portfolio_handle_operation(
        service,
        "activate",
        candidate,
        evidence,
        review,
        approval_attestation=None,
        approval_validation=None,
        expires_at=NOW + timedelta(days=1),
        idempotency_key="portfolio-workflow-rebalance",
        expected_predecessor=None,
        expected_revision=0,
    )
    risk = create_allocation_risk_decision(
        decision_id=allocation.risk_decision_id,
        portfolio_id=allocation.portfolio_id,
        reviewed_version=allocation.allocation_version,
        state=get_decision_state("APPROVE"),
        capped_weights={
            row.component_id: row.capital_weight for row in allocation.component_weights
        },
        risk_budget_projection={
            row.component_id: row.proposed_risk_budget_weight
            for row in allocation.component_weights
        },
        conditions=(),
        policy_version="risk-policy-1",
        evidence_refs={"allocation": allocation.canonical_hash},
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        active=True,
        predecessor_version=None,
        audit_ref="risk-audit-rebalance",
    )
    eligibility = {
        "component-a": create_strategy_operational_eligibility_decision(
            decision_id="eligibility-a",
            strategy_id="strategy-a",
            strategy_version="1.0.0",
            scope={"environment": "simulation", "tenant": "owner"},
            state=get_decision_state("APPROVE"),
            conditions=(),
            policy_version="risk-policy-1",
            evidence_refs={"allocation": allocation.canonical_hash},
            suspended=False,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
            audit_ref="risk-eligibility-rebalance",
        )
    }
    return service, allocation, risk, eligibility, store, market


__all__ = [
    "NOW",
    "SqlitePortfolioStore",
    "active_allocation",
    "construction_workflow",
    "live_market_dataset",
    "rebalance_workflow",
    "settings",
    "simulation_request",
]
