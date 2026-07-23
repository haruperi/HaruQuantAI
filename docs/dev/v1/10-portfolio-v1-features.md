## FEAT-PORT-01: Risk-aware portfolio allocation service (app.services.portfolio.allocation_service)

| Function | Purpose |
|----------|---------|
| `AllocationService.propose(proposal: AllocationProposal) -> AllocationDecision` | Public function for allocation_service.propose. |
| `AllocationService.equal_capital(strategy_ids: list[str], available_capital: float) -> dict[str, float]` | Public function for allocation_service.equal_capital. |
| `AllocationService.confidence_weighted(metrics: dict[str, dict[str, float]], available_capital: float) -> dict[str, float]` | Public function for allocation_service.confidence_weighted. |


## FEAT-PORT-02: Portfolio audit checks for governed execution and lifecycle evidence (app.services.portfolio.audit_service)

| Function | Purpose |
|----------|---------|
| `PortfolioAuditService.audit(snapshot: dict[str, Any]) -> dict[str, Any]` | Public function for audit_service.audit. |


## FEAT-PORT-03: Portfolio cost governance service (app.services.portfolio.cost_service)

| Function | Purpose |
|----------|---------|
| `CostService.report(*, period: str, usage: list[dict[str, Any]], budget: float) -> CostReport` | Public function for cost_service.report. |


## FEAT-PORT-04: Portfolio incident reporting service (app.services.portfolio.incident_service)

| Function | Purpose |
|----------|---------|
| `IncidentService.create_incident(**kwargs: Any) -> IncidentReport` | Public function for incident_service.create_incident. |


## FEAT-PORT-05: Portfolio kill switch with fail-closed live execution controls (app.services.portfolio.kill_switch)

| Function | Purpose |
|----------|---------|
| `PortfolioKillSwitch.__init__() -> None` | Internal function for kill_switch.__init__. |
| `PortfolioKillSwitch.evaluate(snapshot: dict[str, Any]) -> dict[str, Any]` | Public function for kill_switch.evaluate. |
| `PortfolioKillSwitch.trigger(reason: str) -> dict[str, Any]` | Public function for kill_switch.trigger. |
| `PortfolioKillSwitch.resume(*, approval_id: str \| None = None) -> dict[str, Any]` | Public function for kill_switch.resume. |


## FEAT-PORT-06: Governed strategy lifecycle transition service (app.services.portfolio.lifecycle_service)

| Function | Purpose |
|----------|---------|
| `LifecycleService.transition(request: LifecycleTransitionRequest) -> LifecycleTransitionResult` | Public function for lifecycle_service.transition. |


## FEAT-PORT-07: Portfolio performance reporting service (app.services.portfolio.reporting_service)

| Function | Purpose |
|----------|---------|
| `ReportingService.generate(*, report_type: str, data: dict[str, Any]) -> PerformanceReport` | Public function for reporting_service.generate. |


## FEAT-PORT-08: Standardized Portfolio Department tools for HaruQuant agents (app.services.portfolio.standard_tools)

| Function | Purpose |
|----------|---------|
| `get_open_positions(**kwargs: Any) -> dict[str, Any]` | Return current open positions supplied by the caller/context. |
| `get_open_orders(**kwargs: Any) -> dict[str, Any]` | Return current open orders supplied by the caller/context. |
| `get_strategy_allocations(**kwargs: Any) -> dict[str, Any]` | Return current strategy allocation weights. |
| `get_portfolio_equity_curve(**kwargs: Any) -> dict[str, Any]` | Return portfolio equity curve from supplied state. |
| `calculate_portfolio_returns(**kwargs: Any) -> dict[str, Any]` | Calculate portfolio returns from an equity curve. |
| `calculate_portfolio_volatility(**kwargs: Any) -> dict[str, Any]` | Calculate portfolio return volatility. |
| `calculate_portfolio_correlation(**kwargs: Any) -> dict[str, Any]` | Calculate correlation matrix for portfolio return series. |
| `calculate_portfolio_var(**kwargs: Any) -> dict[str, Any]` | Calculate historical portfolio VaR. |
| `calculate_portfolio_cvar(**kwargs: Any) -> dict[str, Any]` | Calculate historical portfolio CVaR. |
| `calculate_risk_contribution(**kwargs: Any) -> dict[str, Any]` | Calculate per-strategy or per-symbol risk contribution. |
| `calculate_margin_usage(**kwargs: Any) -> dict[str, Any]` | Calculate margin utilization. |
| `calculate_currency_exposure(**kwargs: Any) -> dict[str, Any]` | Calculate FX currency basket exposure. |
| `detect_strategy_overlap(**kwargs: Any) -> dict[str, Any]` | Detect duplicate or overlapping strategy symbols/types. |
| `detect_symbol_cluster_risk(**kwargs: Any) -> dict[str, Any]` | Detect concentrated symbol cluster exposure. |
| `build_portfolio_risk_snapshot(**kwargs: Any) -> dict[str, Any]` | Build current portfolio risk package. |
| `calculate_fixed_fractional_size(**kwargs: Any) -> dict[str, Any]` | Calculate fixed fractional position size. |
| `calculate_volatility_adjusted_size(**kwargs: Any) -> dict[str, Any]` | Calculate volatility-adjusted position size. |
| `calculate_risk_parity_weights(**kwargs: Any) -> dict[str, Any]` | Calculate inverse-volatility risk parity weights. |
| `calculate_correlation_adjusted_size(**kwargs: Any) -> dict[str, Any]` | Reduce size for correlated exposure. |
| `calculate_margin_aware_size(**kwargs: Any) -> dict[str, Any]` | Calculate broker margin-aware size. |
| `calculate_cost_adjusted_size(**kwargs: Any) -> dict[str, Any]` | Calculate cost-aware size. |
| `calculate_max_safe_position_size(**kwargs: Any) -> dict[str, Any]` | Calculate hard-cap position size. |
| `propose_strategy_allocation(**kwargs: Any) -> dict[str, Any]` | Propose strategy capital allocation. |
| `rebalance_strategy_allocations(**kwargs: Any) -> dict[str, Any]` | Rebalance strategy allocation weights. |
| `validate_allocation_proposal(**kwargs: Any) -> dict[str, Any]` | Check allocation proposal against policy. |
| `admit_strategy_to_portfolio(**kwargs: Any) -> dict[str, Any]` | Add a strategy candidate to portfolio. |
| `promote_strategy_to_paper(**kwargs: Any) -> dict[str, Any]` | Move a strategy to paper trading. |
| `promote_strategy_to_live_candidate(**kwargs: Any) -> dict[str, Any]` | Prepare a strategy for live approval. |
| `suspend_strategy(**kwargs: Any) -> dict[str, Any]` | Temporarily pause a strategy. |
| `retire_strategy(**kwargs: Any) -> dict[str, Any]` | Remove a strategy from active portfolio. |
| `demote_strategy_to_paper(**kwargs: Any) -> dict[str, Any]` | Demote a live strategy to paper trading. |
| `update_strategy_status(**kwargs: Any) -> dict[str, Any]` | Update portfolio strategy lifecycle status. |
| `build_risk_decision_package(**kwargs: Any) -> dict[str, Any]` | Build final risk decision package. |

