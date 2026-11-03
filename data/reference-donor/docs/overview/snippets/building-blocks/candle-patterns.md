# CandlePatterns — building block catalog

> Reference enumeration of the `CandlePatterns` building-block snippets (7 classes): classic
> candlestick reversal/pattern recognizers. This is a lookup table; for the general building-block
> model see [`README.md`](README.md).

## How this file is organized

All classes live in `SQ.Blocks.CandlePatterns` and extend `ConditionBlock` — each evaluates the
geometry (open/high/low/close, body vs. wick sizes) of the current bar and, for multi-candle
patterns, the preceding bar(s), returning true when the pattern is detected. Every block takes a
`ChartData Chart` parameter (omitted below as boilerplate) and a `Shift` parameter (`int`, default
`1`) that shifts the pattern check back by that many bars. Descriptions below reflect each pattern's
actual geometric test in `OnBlockEvaluate`.

| Display name | Class | Description |
|---|---|---|
| BullishEngulfing pattern | `BullishEngulfing` | A bullish (up) candle whose body fully engulfs the prior bearish candle's body and is larger than it — a bullish reversal signal. |
| BearishEngulfing pattern | `BearishEngulfing` | A bearish (down) candle whose body fully engulfs the prior bullish candle's body and is larger than it — a bearish reversal signal. |
| Hammer pattern | `Hammer` | A candle with a small body near the top of the range, a long lower wick (at least ~2x the body) and little/no upper wick, forming after a local low — a bullish reversal signal. |
| ShootingStar pattern | `ShootingStar` | A candle with a small body near the bottom of the range, a long upper wick (at least ~2x the body) and little/no lower wick, forming after a local high — a bearish reversal signal. |
| DarkCloud pattern | `DarkCloud` | A bearish candle that opens above the prior bullish candle's close and closes more than halfway into the prior candle's body — a bearish reversal signal. |
| PiercingLine pattern | `PiercingLine` | A bullish candle that opens below the prior bearish candle's close and closes more than halfway into the prior candle's body — a bullish reversal signal (mirror of DarkCloud). |
| Doji pattern | `Doji` | A candle whose open and close are almost equal (absolute difference below ~0.6 ticks) — signals market indecision. |

## Related

- Building-block model overview: [`README.md`](README.md)
- Technical indicators these patterns are often combined with: [`indicators.md`](indicators.md)
- Comparison/logical operators used to combine pattern conditions with other rules: [`comparisons.md`](comparisons.md)
- Bar/time conditions for gating when a pattern is checked: [`bar-and-time.md`](bar-and-time.md)
