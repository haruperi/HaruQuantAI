# WhatIf scenarios

Implemented in `app/include/what_if`, one scenario class per file. This package
performs post-backtest transformations, independently of strategy block discovery
and the deferred Phase 5 integration. It does not rerun a strategy or simulate
execution changes caused by removing trades.

## Contracts and use

`WhatIfRecord` is a frozen, strictly validated analysis snapshot. Its `kind`
distinguishes completed trades, unfilled pending orders, and balance entries.
Timestamps are Unix milliseconds. Profit is gross monetary P/L; commission, swap
and fee are signed monetary amounts. `net_profit` adds these four components.
`WhatIfRecord.from_closed_trade()` adapts the canonical strategy-history
`ClosedTrade` in `app/include/blocks/strategy_control/history.py` without an upward dependency from include to workspace.

Each `BaseWhatIf` subclass declares Pydantic configuration in the class and
implements `filter_trades(records) -> list[WhatIfRecord]`. No source list or record
is mutated. `get_parameter_schema()` exposes the configuration schema.
`SCENARIOS` enumerates the 15 built-ins. Custom CodeEditor templates and inheritance
validation use this same contract. No compatibility facade or strategy-block
registration is introduced.

```python
from app.include.what_if import ByDays, UseFixedLots, WhatIfRecord

records = [WhatIfRecord.from_closed_trade(t) for t in closed_trades]
weekdays = ByDays(days=(1, 2, 3, 4, 5), timezone="UTC").filter_trades(records)
resized = UseFixedLots(size=0.5).filter_trades(weekdays)
```

## Scenario mapping and semantics

- ByDays / ByHours / ByMonths: allowed calendar values, default all enabled;
  explicit IANA timezone, default UTC. Day numbering is ISO Monday=1, Sunday=7.
  These calendar filters apply to all record kinds, as in the supplied snippets.
- ExcludeTradesWithBiggestPl / LowestPl: descending gross-profit ordering,
  remove the requested count, skip balance entries. Pending entries participate.
- ExcludePctTradesWithBiggestPl / LowestPl: percentage of completed trades only,
  rounded upward. Non-trades remain. Lowest removal scans from the end of the
  stable descending ordering, including its tie behavior.
- ExcludeShortTrades: short *duration*, independent of direction. Uses whole
  elapsed minutes, strictly below the configured threshold. Removal quota is
  rounded up from the entire input count, and balance entries are skipped.
- ExcludeOverlappingTrades: stable ascending open-time ordering; an entry opening
  exactly at the previous accepted close is excluded. All entry kinds participate,
  matching the visible donor algorithm. The donor filename misspelling `Exlude`
  is corrected in the Python name.
- RemoveBalanceTransactions / RemovePendingTrades: remove only the named kind.
- TakeEverySecondTrade: stable chronological ordering; keep the first completed
  trade, remove the second, and repeat. Other entries do not advance the toggle.
- TakeMaxTradesPerDay: stable chronological ordering; balance entries do not count,
  pending entries do. Grouping uses full local calendar dates.
- UseFixedLots: scale completed-trade gross profit by new/old volume and set the
  volume. Retain existing costs. Unlike the donor's unguarded division, leave
  balance and unfilled pending entries unchanged. Zero-size completed trades are
  rejected by the record contract. This is a P/L sensitivity calculation, not
  margin, fill or fee resimulation.
- Swap: add hypothetical monetary carry per lot to existing swap. Defaults are
  long +10, short -10, 23:00 UTC rollover and Wednesday triple charge. A rollover
  is charged when open < rollover <= close. Each local calendar day participates,
  including weekends; no exchange holiday calendar is implied. Configurable
  timezone, hour/minute and triple day make assumptions explicit. Balance and
  pending entries are unchanged. Repeated application adds carry again.

The supplied Swap snippet delegates arithmetic to SQX's core SwapCalculator,
which is outside the supplied snippet folder. Exact parity with that calculator
has not been established. This implementation defines and tests its own monetary
rollover convention; it does not claim point-based or account-currency conversion.

## Validation

Behavioral tests cover all 15 scenarios, empty histories, immutable source records,
strict parameter rejection, mixed entry kinds, ranking ties, percentage rounding,
timezone boundaries, overlap equality, sizing costs, rollover endpoints, adapter
parity and generated editor extensions. The implementation has no dependency on
unfinished strategy block migration, Stats or MonteCarlo packages.
