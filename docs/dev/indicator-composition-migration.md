# Indicator compositions and signal catalog migration

## Delivered contract

Indicator calculations remain in their owning single-class files. The canonical
catalog now publishes named donor conditions through immutable declarative recipes
or direct references to retained specialized algorithms. No signals package,
per-condition calculation copies, compatibility aliases or forwarding indicator
methods were added.

`app/include/blocks/composition.py` defines CompositionSpec and binds metadata.
`composition_runtime.py` validates and executes a restricted expression grammar.
It reuses the existing comparison functions and canonical indicator classes;
there is no eval, arbitrary expression execution or runtime dependency on SQX.

`app/include/blocks/indicators/donor_compositions.json` contains the complete
inventory of 501 donor indicator files and seven candle-pattern files. It records
source SHA-256, owning indicator, mapping status, parameters, output selection,
relative/absolute reads, per-read precision, specialization reference and explicit
qualification notes. One metadata record per line keeps the file below 1,000
physical lines and 500 KB.

## Catalog exposure

- **340 executable compositions**, including six COT predicates consuming explicit
  precomputed series and predicates requiring externally supplied profile/decision
  data.
- **94 specialized signal descriptors** bound directly to the existing function or
  class method in its owning module, without another implementation or wrapper.
- **65 calculation-family mappings**, **seven COT output projections**, one
  existing conversion-function mapping and one excluded internal diagnostic.
- Together with the existing 233 registrations, discovery publishes **667 unique
  block IDs**, including all 76 canonical indicator classes.

The 65 calculation mappings identify canonical families; they do not certify
that every donor parameter, output and warmup behavior is implemented. In
particular, a family mapping must not be interpreted as claiming that
BiggestRange/SmallestRange are equivalent to boolean is-biggest/is-smallest tests.
Complete calculation qualification remains necessary for those variants.

## Using a composition

```python
from app.include.blocks.registry import BlockRegistry

registry = BlockRegistry()
registry.discover("app/include/blocks")
catalog = registry.snapshot()

descriptor = catalog.require("signal.rsi.rsi_rising")
signal = descriptor.instantiate(period=14, shift=0)
result = signal(bars)
```

`descriptor.composition` exposes the immutable recipe to compiler/editor clients.
`descriptor.parameter_schema` contains configurable values, excluding the BarData
runtime input. `signal.required_inputs(...)` and `required_history(...)` resolve
requirements for a selected configuration. `signal.evaluate_outputs(...)` accepts
already calculated output series for a runner-managed shared calculation cache.
Within one execution, identical calculation nodes are evaluated only once.

Specialized descriptors declare computed-series input ports and configurable
parameters in the ordinary BlockSpec/schema contracts. Their deeply immutable
`descriptor.input_bindings` explicitly distinguishes individual output ports,
whole output dictionaries, market fields and required external feeds. They call
the original algorithm directly; they do not pretend that an undeclared source
feed or incomplete upstream calculation is available.

## Clean migration

Removed **294 redundant generic comparison wrappers**: 284 class methods and
10 module-level COT wrappers. Migrated all identified consumers and the existing
condition qualification tests directly to shared comparisons. The unused ADX
mapping-extraction helper was also removed. Indicator-specific algorithms remain
with their owning calculations.

## Semantics and validation

- Read nodes retain exact historical offsets. A bar-open/band comparison can read
  the current open against the previous band instead of accidentally using the
  current band.
- Rounding belongs to individual reads. CCI reads explicitly rounded to four
  digits stay four-digit reads; raw chart prices and thresholds are not rounded
  again by the comparison layer.
- Strict crossovers retain strict inequalities. Aroon bottom/top recipes retain
  the donor's inclusive/equality boundaries where specified.
- Parameters are strict, extra-forbidding, finite and constrained. Configured
  shifts cannot be negative. Required market/auxiliary feeds fail explicitly.
- A contradictory donor default is not silently corrected: ADX level default 0
  violates its minimum 1, so that level is required in the published configuration
  schema. The original declaration remains in the metadata record.
- Stochastic recipes explicitly constrain currently unsupported MA-method and
  price-field selectors to supported value zero; other choices are rejected.
- MA compositions select SMA/EMA/SMMA/LWMA without restoring a MovingAverage
  facade. Each recipe pins concrete calculation classes at registration.
- Published recipes, nested data and dependency maps are immutable. Source reload
  atomically replaces the owning calculation and derived signal family. Failed
  reloads retain the last valid family; prior snapshots retain their old bound
  targets. Recompile dependent owners after changing other sources: automatic
  transitive reload of shared numerical kernels is not supplied by this change.
- Generic generation eligibility respects donor IgnoreInBuilder and upstream
  causality/eligibility. Specialized and external-feed-dependent signals remain
  ineligible for automatic generation pending further qualification.

## Remaining calculation/runtime qualification

This change implements catalog exposure and reusable execution; it does not
claim full donor numerical parity. VolumeProfile/TPOProfile session calculations
and numerical outputs were subsequently implemented and qualified in
`profile-donor-qualification.md` (42 numerical cases and 36 donor session replays).
Platform/instrument integration remains separate. External VP predicates require explicitly supplied
session-profile series and never substitute a rolling profile. PSAR predicates
require a caller-supplied decision-price series; they do not invent live quotes.
COT raw/derived feed definitions and specialized donor defaults/edge cases still
need reference fixtures. Numeric range/band variants and extrema projections were
subsequently implemented and source-qualified in `numeric-variants-qualification.md`.
Moving-average routing is now explicit; its seed/warmup differences and the other
standalone calculations still need numerical qualification.

The broader strategy-document/compiler and UI integration phases remain separate.
No CodeEditor UI or automatic generator is claimed to have been completed here.

## Verification

Focused tests cover all declarative recipes, donor inventory completeness,
parameter validation, selector rejection, shifts, rounding, boundary semantics,
missing external feeds, prefix causality, immutable recipes, pinned snapshots and
atomic failure rollback. Existing indicator/hash/performance and application
regressions remain part of the full repository test suite.


Final verification: full repository suite **1,124 passed**. After the final
configuration-bound checks, **46 targeted composition/registry tests passed**.
Mypy passed across 316 source files; Ruff lint/format and architecture checks
passed. Implementation and audit artifacts remain uncommitted.
