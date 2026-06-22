# Strategy Module (`app/services/strategy`)

## Overview
The Strategy Module is a production-grade, modular framework for designing, configuring, and executing quantitative trading strategies. It provides interfaces and structural contracts for both batch (vectorized) backtesting and real-time/historical event-driven execution. 

A central design guarantee of this module is that strategy decision-making is strictly side-effect-free (pure functions). Strategies evaluate current market state and context, returning the updated state alongside trade intents, while leaving state mutation and order routing to external governance components.

## Design Philosophy & Non-Negotiable Rules
* **Rule 1 (Pure Decision Generation):** The orchestration layer must remain free of side-effects. Strategies take in state and data and return a new state and a list of `TradeIntent` objects. They do not execute orders directly.
* **Rule 2 (No Lookahead Leakage):** Vectorized strategies must strictly shift indicator calculations and signals to align timing policies. The mathematical inspector enforces this by perturbing future data and verifying past outputs are unaltered.
* **Rule 3 (Unified Entry Point):** All external components must interact with the Strategy module through exports defined in `app/services/strategy/__init__.py`.

## Features

### `models.py` — Data Schemes and Configurations
Defines the core validation contracts utilizing Pydantic:
* `TradeIntent`: Validates details of a strategy's trade decision.
* `StrategyConfig`: Strategy hyperparameter schemas.
* `StrategyContext`: Runtime environment snapshot (time, portfolio state, market data).
* `StrategyResult`: Outputs and metrics of a backtest or live execution.
* `StrategyManifest`: Resource limitations and metadata descriptors.

### `base.py` — Lifecycle Hooks & Protocols
Defines `BaseStrategy` with hooks:
* `on_init()`
* `on_bar(state, bar_data, context)`
* `on_tick(state, tick_data, context)`
* `on_stop(state, context)`
* `on_exception(state, error, context)`
* `on_timer(state, timer_event, context)`
* `calculate_vectorized_signals(df)`

Also defines `StrategyProtocol` structural contract.

### `service.py` — Orchestrator & Inspector
Orchestrates strategy runs. Integrates:
* `TradeIntentInspector`: Validates intents for lookahead risks and data staleness.

### `examples.py` — Concrete Implementations
* `MovingAverageCrossover`: Stateless, signal-only moving average crossover strategy.
* `MartingaleStrategy`: Stateful position tracker that doubles sizing on losses.

## Installation
### Prerequisites
* `uv` installed and available globally.

### Dependencies
* **Standard Library:** `typing`, `enum`, `datetime`, `abc`, `uuid`
* **Required Third-Party:** `pandas`, `numpy`, `pydantic`, `loguru`

## Usage Examples

### Vectorized Backtest Execution
```python
import pandas as pd
from app.services.strategy import MovingAverageCrossover, StrategyConfig, StrategyService

# 1. Initialize config and strategy
config = StrategyConfig(
    strategy_id="sma_cross",
    strategy_version="1.0.0",
    parameters={"symbol": "EURUSD", "fast_period": 10, "slow_period": 20}
)
strategy = MovingAverageCrossover(config=config)

# 2. Run vectorized signals calculation
df = pd.DataFrame(...) # Historical OHLCV DataFrame
service = StrategyService()
df_signals, intents = service.process_vectorized(strategy, df)
```

## API Reference

### `StrategyService`
#### `process_bar(strategy, state, bar_data, context) -> Tuple[Any, List[TradeIntent]]`
Orchestrates a bar event transition in a pure, side-effect-free manner.

## Testing Strategy
### Unit Tests
Tests include coverage of:
1. Pydantic validation rules.
2. Crossover stateless event transitions.
3. Martingale state transitions under take-profit and stop-loss boundaries.
4. Perturbation-based lookahead bias checks in the inspector.

**Test command:**
```bash
pytest tests/unit/app/services/strategy/
```
