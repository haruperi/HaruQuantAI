# HaruQuant Strategy Domain

This package standardizes the HaruQuant strategy layer as `tools/strategy/`.

It supports two strategy styles:

1. **Vectorized signal strategies** — DataFrame-in, DataFrame-out strategies that write canonical signal columns. Example: `TrendFollowingStrategy`.
2. **Stateful event strategies** — strategies that receive `StrategyContext` and propose `TradeAction` objects. Example: `TradeDecompositionStrategy`.

Stateful strategies only propose actions. They do not place trades. Proposed actions must pass validation, risk review, and execution gates.

## Official AI Tools

- `register_builtin_strategy_tools`
- `list_strategy_names`
- `get_strategy_metadata`
- `validate_strategy_dataframe`
- `normalize_signal_columns`
- `validate_trade_actions`
- `run_vectorized_strategy`
- `extract_strategy_signals`
- `validate_strategy_actions`
- `save_strategy_source_file`

## Import Boundary

Agents and workflows should import official tools from the domain package:

```python
from tools.strategy import list_strategy_names, run_vectorized_strategy
```

Strategy implementations may import base contracts:

```python
from tools.strategy import BaseStrategy, StatefulEventStrategy, TradeAction
```

## Safety Notes

- No broker execution tools are exposed here.
- Dynamic strategy code import is not exposed.
- Delete/import-zip behavior from the old storage module is intentionally not exported.
- `save_strategy_source_file` is medium-risk because it writes files.
