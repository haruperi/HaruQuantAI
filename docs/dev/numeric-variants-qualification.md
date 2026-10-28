# Numeric calculation variants

This closes the missing consolidated range/band calculation variants and replaces
ambiguous family links with explicit numeric outputs. It is not a declaration of
full numerical parity for every one of the remaining indicator families.

## Implemented variants

| Donor variant | Canonical implementation | Qualified behavior |
| --- | --- | --- |
| BiggestRange | `indicator.volatility.biggest_range` | Maximum eight-decimal candle range over available history; startup does not wait for a full period. Returns a price range, not a boolean. |
| SmallestRange | `indicator.volatility.smallest_range` | Minimum eight-decimal candle range over available history, including the donor's 100,000,000 initial upper sentinel. |
| HighestInRange | `indicator.volatility.highest_in_range` | Completed HHMM-window high; end boundary excluded; carries the last usable completed result across gaps. |
| LowestInRange | `indicator.volatility.lowest_in_range` | Completed HHMM-window low with the source's startup/sentinel and gap behavior. |
| BBRange | `indicator.volatility.bb_range` | Two times deviation times the donor population standard deviation, including partial-window startup. |
| BBWidthRatio | `indicator.volatility.bb_width_ratio` | Squared distances from the current recursive SMA, divided by the configured period even during partial startup, then normalized by positive SMA. Zero when SMA <= 0. |
| Highest / Lowest | `HighestLowest.highest` / `.lowest` | Explicit numeric output projections, tested against both donor classes. |
| HighestIndex / LowestIndex | `HighestLowest.highest_index` / `.lowest_index` | Explicit bar-lag output projections, including equal-value ties and expiry. Source IgnoreInBuilder is retained in the mapping. |
| BarRange | `BarRange.value` | Raw high minus low; independently checked to avoid confusing it with the rounded rolling extrema. |

Six independently selectable calculations have one class and one source file each.
Parameters live inside those classes. Shared rolling/time-window algorithms stay
in `app/include/calculators/extrema.py`; rolling deviations stay in the existing
`std_dev.py`. Numeric extrema use an O(N) monotonic deque; the variance calculation
uses NumPy window chunks with bounded temporary memory. No compatibility aliases,
extra packages or duplicate params classes were introduced.

The old `BarRange.highest_in_range` and `lowest_in_range` implementations were
removed and their callers migrated. `is_biggest_range` / `is_smallest_range` remain
distinct boolean predicates; they are not used as implementations of the donor's
numeric BiggestRange / SmallestRange blocks. The existing BollingerBands outputs
retain their established calculation contract; BBWidthRatio is not misrepresented
as its `bandwidth` output, and BBRange has its own donor startup contract.

## Exact mappings and input dependencies

`donor_compositions.json` now gives every variant above a concrete target ID and
output rather than a vague family counterpart. EMA, SMA, SMMA, LWMA and TEMA each
route only to their own class, with the donor's period-14 default recorded in the
mapping. Generic MovingAverage routes methods 0/1/2/3 to SMA/EMA/SMMA/LWMA;
TEMA is not an alternative of that selector. Its IgnoreInBuilder is preserved.
This corrects routing; it does **not** change or certify the existing MA kernels'
different seed/warmup policies. Their broader numerical migration remains separate.

The canonical inventory now has 82 indicator classes. The ten new or clarified
numeric output projections supplement the existing seven COT projections. All
508 donor indicator/pattern mapping records remain accounted for.

Bollinger numeric variants support all seven computed-price selectors: close,
open, high, low, median, typical and weighted. Selection is shared with composition
execution. `BaseIndicator.required_inputs()` exposes parameter-dependent market
requirements; selecting Open does not accept absent Open data. Periods, deviations,
selectors, real HHMM values and chart timezones are validated before calculation.
Invalid/nonpositive periods are rejected rather than adopting invalid donor
configuration fallbacks. Empty BarData remains invalid under the shared contract.

The time-window blocks use explicitly selected seconds/milliseconds and chart
timezone (UTC default). The source's first-window LowestInRange accumulator starts
at zero, so an input that starts inside a positive-price window can initially
publish zero. This source quirk is intentionally preserved and fixture-tested.

## Reference evidence

`scripts/capture_numeric_variants_donor.py` compiles the original 11 donor numeric
classes with their original Abstract/Average/StdDev/Highest/Lowest calculator
bodies. Framework annotations, logging, chart access and UTC calendar access are
stubbed. Source SHA-256 values are recorded with the captures.

`fixtures/numeric-variants-donor-reference.json` contains 255 source-executed cases
covering periods 1/3/14 where supported, all seven Bollinger price selectors,
partial history, repeated extrema and expiry, same-day and overnight windows,
gaps, constant/zero/negative prices and the smallest-range sentinel ceiling.
Every output array is checked against the donor reference with tolerance
`rtol=2e-14, atol=1e-12`; multiple prefix runs must match exactly. Catalog tests
also exercise explicit output routes and configured market-input requirements.

Reproduce captures with a local JDK and donor checkout:

```powershell
uv run python scripts/capture_numeric_variants_donor.py --donor C:\SQX-145\internal\extend\Snippets\SQ
uv run pytest tests/include/blocks/test_numeric_variants.py -q
```

Normal tests require neither the donor installation nor Java. Historical Phase 0
and Phase 3 numeric hashes are retained unchanged: this adds the missing numeric
contracts without silently redefining or overwriting those baselines.

## Qualification limits

The harness supplies SQUtils.round as Java Math.round at eight decimals; native
proprietary rounding at binary/decimal halfway boundaries is not certified by
these stubs. Indicator instances run at input Shift=0, with historical output
selection handled separately through the shared series contract. Native framework
shift propagation and non-UTC platform/DST equivalence need runtime qualification.
Moving-average seed/warmup parity, Stochastic's remaining selectors, COT feeds and
the other standalone indicator calculations still require their own qualification.

## Verification

- 255 donor-executed numeric cases, with exact prefix-causality checks.
- 259 focused numeric tests, including catalog routes, strict configuration and
  parameter-dependent composition inputs, passed.
- Full repository run: 1,472 passed; the existing unchanged RSI 100k timing check
  exceeded its 95 ms budget (111.11 ms). The complete affected benchmark test then
  passed in isolation. Timing budgets were not changed.
- Mypy passed across 324 source files; Ruff lint/format and all architecture gates
  passed. Historical calculation hashes were not rewritten.
