## FEAT-SIM-01: Shared helpers for simulation backends (app.services.simulation.common)

| Function | Purpose |
|----------|---------|
| `signal_to_float_array(data, col_name_map: dict[str, object], names: Iterable[str])` | Return the first named signal column as a float array. |
| `signal_to_object_array(data, col_name_map: dict[str, object], names: Iterable[str])` | Return the first named signal column as an object array. |
| `phase_matches(value, phases: Iterable[str]) -> bool` | Return whether a phase value contains any requested phase. |
| `phase_mask(values, phases: Iterable[str]) -> np.ndarray` | Return a boolean mask for values matching any target phase. |


## FEAT-SIM-02: Typed configuration contract for simulation backtests (app.services.simulation.config)

| Function | Purpose |
|----------|---------|
| `SimulationConfigError` (model) | Raised when a simulation config is missing or invalid. |
| `SimulationPositionSizingError` (model) | Raised when simulation position sizing cannot be resolved. |
| `SimulationSymbolInfo.get_contract_size() -> float` | Public function for position_sizing.get_contract_size. |
| `SimulationSymbolInfo.get_lots_min() -> float` | Public function for position_sizing.get_lots_min. |
| `SimulationSymbolInfo.get_lots_max() -> float` | Public function for position_sizing.get_lots_max. |
| `SimulationSymbolInfo.get_lots_step() -> float` | Public function for position_sizing.get_lots_step. |
| `AccountConfig.from_dict(raw: Mapping[str, Any]) -> AccountConfig` | Public function for config.from_dict. |
| `DataConfig.from_dict(raw: Mapping[str, Any]) -> DataConfig` | Public function for config.from_dict. |
| `StrategyConfig.from_dict(raw: Mapping[str, Any]) -> StrategyConfig` | Public function for config.from_dict. |
| `StatefulRiskControlsConfig.from_dict(raw: Mapping[str, Any] \| None) -> StatefulRiskControlsConfig` | Public function for config.from_dict. |
| `StatefulRiskControlsConfig.to_dict() -> dict[str, Any]` | Public function for config.to_dict. |
| `PositionSizeConfig.from_dict(raw: Mapping[str, Any]) -> PositionSizeConfig` | Public function for config.from_dict. |
| `ExecutionConfig.from_dict(raw: Mapping[str, Any]) -> ExecutionConfig` | Public function for config.from_dict. |
| `ReportingConfig.from_dict(raw: Mapping[str, Any] \| None) -> ReportingConfig` | Public function for config.from_dict. |
| `SimulationConfig.from_dict(raw: Mapping[str, Any]) -> SimulationConfig` | Public function for config.from_dict. |


## FEAT-SIM-03: Data preparation pipeline for simulation backtests (app.services.simulation.data_preparation)

| Function | Purpose |
|----------|---------|
| `resolve_position_size(config: SimulationConfig, prepared: PreparedSimulationData) -> dict[str, Any]` | AI Tool wrapper for _resolve_position_size_impl. |
| `SimulationDataPreparationError` (model) | Raised when simulation data preparation cannot produce ticks. |
| `PreparedSimulationData` (model) | Prepared tick stream and metadata for a simulation run. |
| `SimulationDataPreparer.__init__(engine: Any) -> None` | Internal function for data_preparation.__init__. |
| `SimulationDataPreparer.prepare(config: SimulationConfig) -> PreparedSimulationData` | Prepare and merge all configured symbols into one tick stream. |
| `SimulationDataPreparer.prepare_symbol(config: SimulationConfig, symbol: str) -> PreparedSimulationData` | Prepare signal bars and ticks for one symbol. |


## FEAT-SIM-04: Event-driven simulation backend (app.services.simulation.event_driven)

| Function | Purpose |
|----------|---------|
| `run_event_driven_simulation(engine, data, position_size=None, commission_per_lot: float = 0.0, slippage_model: str = 'none', slippage_points: float = 0.0, slippage_min: float \| None = None, slippage_max: float \| None = None, monitor_verbose: bool = False, show_progress: bool = False, progress_desc: str = 'Tester Progress', frame_observer=None, strategy=None) -> dict[str, Any]` | AI Tool wrapper for _run_event_driven_simulation_impl. |


## FEAT-SIM-05: Standard simulation result objects (app.services.simulation.results)

| Function | Purpose |
|----------|---------|
| `SimulationRunResult.from_run_result(config: SimulationConfig, prepared: PreparedSimulationData, run_result: RunResult, metadata: Mapping[str, Any] \| None = None) -> SimulationRunResult` | Public function for results.from_run_result. |
| `SimulationRunResult.processed_ticks -> int` | Public function for results.processed_ticks. |
| `SimulationRunResult.final_balance -> float` | Public function for results.final_balance. |
| `SimulationRunResult.final_equity -> float` | Public function for results.final_equity. |
| `SimulationRunResult.total_profit -> float` | Public function for results.total_profit. |
| `SimulationRunResult.total_return -> float` | Public function for results.total_return. |
| `SimulationRunResult.trade_count -> int` | Public function for results.trade_count. |
| `SimulationRunResult.symbol_summary -> Mapping[str, Mapping[str, float]]` | Public function for results.symbol_summary. |
| `SimulationRunResult.warnings -> tuple[Any, ...]` | Public function for results.warnings. |
| `SimulationRunResult.trades -> list[TradeRecord]` | Public function for results.trades. |
| `build_symbol_summary(symbols: tuple[str, ...], trades: list[TradeRecord]) -> dict[str, Any]` | AI Tool wrapper for _build_symbol_summary_impl. |


## FEAT-SIM-06: High-level simulation run orchestration (app.services.simulation.runner)

| Function | Purpose |
|----------|---------|
| `SimulationRunner.__init__(engine: Any, data_preparer: SimulationDataPreparer \| None = None) -> None` | Internal function for runner.__init__. |
| `SimulationRunner.run(config: SimulationConfig \| Mapping[str, Any]) -> SimulationRunResult` | Public function for runner.run. |


## FEAT-SIM-07: Vectorized simulation backend (app.services.simulation.vectorized)

| Function | Purpose |
|----------|---------|
| `run_vectorized_simulation(engine, data, initial_balance: float = 10000.0, contract_size: float = 100000.0, position_size: float = 0.01, commission_per_lot: float = 0.0, slippage_model: str = 'none', slippage_points: float = 0.0, slippage_min: float \| None = None, slippage_max: float \| None = None, point_value: float = 1e-05) -> dict[str, Any]` | AI Tool wrapper for _run_vectorized_simulation_impl. |
| `prepare_vectorized_data(data, snapshot_policy: str = 'position_update') -> dict[str, Any]` | AI Tool wrapper for _prepare_vectorized_data_impl. |
| `reconstruct_trades(trades_arr, prepared: dict, contract_size: float, engine=None, use_mt5: bool = False) -> dict[str, Any]` | AI Tool wrapper for _reconstruct_trades_impl. |
| `reconstruct_equity_curve(equity_arr, prepared: dict, trade_deltas=None) -> dict[str, Any]` | AI Tool wrapper for _reconstruct_equity_curve_impl. |


## FEAT-SIM-08: Simulation contracts module (app.services.simulator.contracts)

| Function | Purpose |
|----------|---------|
| `Contract.validate_metadata_structure(value: dict[str, Any]) -> dict[str, Any]` | Validate metadata namespacing and secret safety. |
| `Contract.validate_trace_identifiers() -> Contract` | Validate trace identifier fields. |
| `Contract.to_json() -> str` | Serialize this contract to deterministic canonical JSON. |
| `Contract.content_hash() -> str` | Calculate a stable SHA256 hash over business-data fields only. |
| `Contract.contract_hash() -> str` | Calculate SHA256 hash over the full serialized contract. |
| `Contract.check_compatibility(target_version: str) -> bool` | Check whether this contract version is compatible with a target. |
| `BacktestConfig` (class) | Configuration constraints for running a simulator backtest. |
| `BacktestResult` (class) | The canonical outcomes generated by a simulator run. |


## FEAT-SIM-09: A deliberately simple, deterministic, no-lookahead bar backtest engine (app.services.simulator.engine)

| Function | Purpose |
|----------|---------|
| `Engine.__init__(backend='sim') -> None` | Initialise trading engine. |
| `Engine.run_vectorized(data, initial_balance=10000.0, contract_size=100000.0, position_size=0.01, commission_per_lot=0.0, slippage_model='none', slippage_points=0.0, slippage_min=None, slippage_max=None)` | Run prepared tick data through the vectorized backend. |
| `Engine.run(config: SimulationConfig \| Mapping[str, Any])` | Public simulation entry point. |
| `Engine.run_prepared(prepared, config: SimulationConfig) -> int` | Execute already-prepared simulation data through the selected engine. |
| `Engine.account_info()` | Public function for engine.account_info. |
| `Engine.terminal_info()` | Public function for engine.terminal_info. |
| `Engine.trading_symbols` | Public function for engine.trading_symbols. |
| `Engine.trading_deals` | Public function for engine.trading_deals. |
| `Engine.trading_history_deals` | Public function for engine.trading_history_deals. |
| `Engine.trading_orders` | Public function for engine.trading_orders. |
| `Engine.trading_history_orders` | Public function for engine.trading_history_orders. |
| `Engine.completed_trades` | Public function for engine.completed_trades. |
| `Engine.equity_curve` | Public function for engine.equity_curve. |
| `Engine.get_completed_trades()` | Public function for engine.get_completed_trades. |
| `Engine.get_equity_curve()` | Public function for engine.get_equity_curve. |
| `Engine.get_run_result(processed_ticks: int = 0)` | Public function for engine.get_run_result. |
| `Engine.reset_runtime(account_config: AccountConfig)` | Reset simulator runtime state to a clean account baseline. |
| `Engine.clear_completed_trades() -> None` | Public function for engine.clear_completed_trades. |
| `Engine.history_deals_get(date_from=None, date_to=None, group=None, ticket=None)` | Public function for engine.history_deals_get. |
| `Engine.history_deals_total(date_from, date_to)` | Public function for engine.history_deals_total. |
| `Engine.positions_get(symbol=None, group=None, ticket=None)` | Public function for engine.positions_get. |
| `Engine.positions_total()` | Public function for engine.positions_total. |
| `Engine.orders_get(symbol=None, group=None, ticket=None)` | Public function for engine.orders_get. |
| `Engine.orders_total()` | Public function for engine.orders_total. |
| `Engine.history_orders_get(date_from=None, date_to=None, group=None, ticket=None)` | Public function for engine.history_orders_get. |
| `Engine.history_orders_total(date_from, date_to)` | Public function for engine.history_orders_total. |
| `Engine.symbols_get(group=None)` | Public function for engine.symbols_get. |
| `Engine.symbols_total()` | Public function for engine.symbols_total. |
| `Engine.symbol_info(name: str)` | Public function for engine.symbol_info. |
| `Engine.symbol_info_tick(name: str)` | Public function for engine.symbol_info_tick. |
| `Engine.order_send(request, verbose: bool = False)` | Public function for engine.order_send. |
| `Engine.configure_run_schedule(auto: bool = True, positions_every=None, pending_orders_every=None, account_every=None, portfolio_every=None, risk_every=None) -> None` | Configure optional callback intervals for Engine.run tick scheduling. |
| `Engine.configure_position_sizing(enabled: bool = True, position_sizing_method: str = 'fixed_lot', position_sizing_config=None, historical_data=None) -> None` | Public function for engine.configure_position_sizing. |
| `Engine.configure_risk_management(enabled: bool = True, historical_data=None, position_sizing_method: str = 'fixed_risk', position_sizing_config=None, risk_limits=None, governor_timeframe: str = 'H1', governor_start_pos: int = 0, governor_end_pos: int = 500, enable_regime_detection: bool = True, regime_config=None, enable_allocation: bool = False, correlation_preference=None, risk_budgets=None, symbol_clusters=None) -> None` | Public function for engine.configure_risk_management. |
| `Engine.run_event_driven(data, position_size=None, commission_per_lot=0.0, slippage_model='none', slippage_points=0.0, slippage_min=None, slippage_max=None, monitor_verbose: bool = False, show_progress: bool = False, progress_desc: str = 'Tester Progress', frame_observer=None, strategy=None)` | Run prepared tick data through the event-driven backend. |
| `Engine.monitor_positions(verbose: bool = False)` | Public function for engine.monitor_positions. |
| `Engine.monitor_pending_orders(verbose: bool = False)` | Public function for engine.monitor_pending_orders. |
| `Engine.monitor_account(verbose: bool = False)` | Public function for engine.monitor_account. |
| `Engine.monitor_portfolio(verbose: bool = False) -> None` | Public function for engine.monitor_portfolio. |
| `Engine.monitor_risk(verbose: bool = False) -> None` | Public function for engine.monitor_risk. |
| `Engine.order_check(request)` | Public function for engine.order_check. |
| `SimpleBacktestEngine.run(strategy: BaseStrategy, bars: Sequence[Bar], *, symbol: str \| None = None, timeframe: str \| None = None, additional_chart_bars: Mapping[str, Sequence[Bar]] \| None = None, chart_timeframes: Mapping[str, str] \| None = None, feature_provider: FeatureProvider \| None = None) -> BacktestResult` | Run a bar-by-bar simulation and return a fully auditable result. |


## FEAT-SIM-10: Deterministic error-code mapping for the simulator service boundary (app.services.simulator.errors)

| Function | Purpose |
|----------|---------|
| `ErrorPayload` (TypedDict) | Structured error payload used by standard error envelopes. |
| `to_simulator_error_payload(exception: BaseException, *, request_id: str \| None = None) -> ErrorPayload` | Map an exception to a redacted, deterministic Simulator error payload. |
| `SimulationError` (exception) | Base error type for all simulation and backtesting operations. |
| `SimLookaheadDetectedError` (exception) | Raised when strategy attempts to access future data. |
| `SimPersistenceFailedError` (exception) | Raised when journal persistence operations fail. |


## FEAT-SIM-11: Typed models for the deterministic bar-by-bar backtest engine (app.services.simulator.models)

| Function | Purpose |
|----------|---------|
| `IntrabarConflictPolicy` (enum) | Resolution when the same OHLC bar reaches both SL and TP. |
| `FillReason` (enum) | Reason a position or pending order was executed. |
| `BacktestConfig.spread_price -> float (property)` | Return full bid/ask spread in price units. |
| `BacktestConfig.slippage_price -> float (property)` | Return adverse slippage in price units. |
| `SimPosition` (dataclass) | Mutable simulated position owned by the backtest engine. |
| `SimPendingOrder` (dataclass) | Mutable simulated stop/limit order awaiting a bar-path trigger. |
| `ClosedTrade` (dataclass) | One fully or partially realized position segment. |
| `EquityPoint` (dataclass) | Marked-to-market account value after a completed bar. |
| `BacktestEvent` (dataclass) | Auditable simulation event, including fills and ignored intents. |
| `BacktestMetrics` (dataclass) | Small result summary intended for first-pass research comparisons. |
| `BacktestResult.to_dict() -> dict[str, object]` | Return a JSON-friendly summary without serializing every ledger row. |
