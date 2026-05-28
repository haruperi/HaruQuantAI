# HaruQuant Indicators Domain

Production package path:

```text
tools/indicators/
```

This domain provides deterministic, read-only indicator tools that consume validated data and return the standard HaruQuant AI Tool response schema.

## Official tools

- Trend: `sma`, `ema`, `wma`
- Momentum: `rsi`
- Volatility: `atr`, `adr`, `bbands`
- Volume: `accumulation_distribution`
- Statistical: `calculate_hurst`, `hurst`
- Currency strength: `calculate_pair_strength`, `calculate_currency_strength`, `currency_strength_indicator`, `get_top_pairs`
- SMC: `fvg`, `swing_highs_lows`, `bos_choch`, `ob`, `previous_high_low`, `phl`

## Import boundary

Agents and workflows should import from the domain package:

```python
from tools.indicators import rsi, atr, fvg
```

Avoid deep imports from implementation modules in agent code.

## Warmup policy

Most rolling indicators default to `warmup_policy="nan"` so no artificial values are injected into backtests. Optional policies:

- `nan`: keep warmup rows as `NaN`.
- `fill`: fill output columns with `fill_value`.
- `drop`: remove rows where output columns are `NaN`.

## No-lookahead policy

SMC tools default to `confirmed_only=True` where applicable. This marks/derives signals only after confirmation to reduce accidental future leakage in backtests.
