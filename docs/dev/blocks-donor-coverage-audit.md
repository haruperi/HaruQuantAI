# SQ Blocks donor coverage audit

Audit date: 2026-10-28.

This report records the **pre-composition snapshot** (233 registrations). The
subsequent catalog-exposure migration is documented in
`indicator-composition-migration.md`; its 667 registrations address the missing
signal-mapping layer while the calculation/parity findings below remain relevant.

Subsequent profile work is recorded in `profile-donor-qualification.md`: the
rolling VP/TPO approximations described below have been replaced with session
calculations and all numerical outputs, checked against executed donor methods.
The remaining families and platform/instrument integration still need qualification.

**Conclusion: full donor coverage is not complete.** The canonical package is
healthy and broadly populated, but calculation migration, catalog exposure and
SQX behavioral parity are distinct claims. Earlier Phase 3 qualification measured
migration against the existing Python implementation; it did not certify every
feature in the current donor source.

## Evidence and scope

Inventoried all 670 Java files under
`C:/SQX-145/internal/extend/Snippets/SQ/Blocks`. Discovered the current
`app/include/blocks` tree using the real independent BlockRegistry: **233 unique
registered IDs and zero discovery diagnostics**. The accompanying
`fixtures/blocks-donor-coverage-inventory.json` records every donor path, source
SHA-256, structural role, direct catalog match where found, candidate consolidated
family sources and an explicit unverified behavioral-parity status.

This is a complete file inventory and structural mapping with targeted semantic
review, not exhaustive numerical or platform parity certification. Name matching
and source-family presence are not used as evidence of calculation equivalence.
No implementation code was changed during this audit.

## Folder coverage

| Donor folder | Java files | Structural result |
| --- | ---: | --- |
| BarAndTime | 37 | All 37 have registered counterparts. |
| CandlePatterns | 7 | All seven pattern APIs/outputs exist in CandlestickPatterns; no seven separately registered condition entries or explicit catalog composition mappings. |
| Comparisons | 27 | All 21 concrete/logical operations have counterparts; six supporting comparison bases are consolidated. Canonical package has 23 registrations, including changes-up/down extras. |
| Functions | 18 | All 18 have registered counterparts. |
| Indicators | 501 | 76 canonical indicator registrations, including application additions. Many donor variants are methods/ports/compositions, not individual catalog entries; substantial profile-feature gaps confirmed. |
| Order | 12 | All 12 have registered counterparts; formula/ATM/export parity limitations remain documented. |
| Other | 5 | All five have registered counterparts in types. |
| OtherActions | 8 | All eight have registered counterparts in actions; actual side effects depend on injected/runtime services. |
| Price | 30 | All 29 block operations have registered counterparts; SessionOHLCCalculator is supporting infrastructure. |
| StrategyControl | 25 | All 25 have registered counterparts; deliberate accounting/history/runtime differences are documented. |

The 155 non-indicator operations outside CandlePatterns all have direct catalog
counterparts. This count excludes the six comparison bases and session calculator.
The indicator diagnostic DataLoggingIndy accounts for the other supporting file.
Having fewer Python registrations than Java files is not itself a defect: output
ports and generic condition composition can legitimately consolidate donor blocks.

## Confirmed gaps

### 1. VolumeProfile is a reduced implementation

Python `indicators/volume/volume_profile.py` configures a rolling period, profile
rows, value-area fraction and initial-balance bars, exposing 10 outputs. The donor
VolumeProfile family also declares calendar/swing session selection, previous vs
actual sessions, range vs fixed-tick bins, ticks per bin, HVN/LVN detection,
volume-cluster enhancement and additional profile/volume outputs.

Missing declared capabilities include HVN1-HVN5, LVN1-LVN5, VPOC/VVAH/VVAL,
TotalVolume/TotalBullVolume/TotalBearVolume, DeltaPOC/DeltaVA and ProfileRange.
The current custom-hours helpers merely mask volume outside time windows and run
the rolling calculation. That does not implement donor previous/actual session
profiles, nor separate London/NewYork/Sydney/Tokyo profile outputs in the donor
multi-session block. These are real parameter/calculation/output gaps, not just
registry naming differences.

### 2. TPOProfile exposes only a subset

Python `indicators/volume/tpo_profile.py` exposes POC, VAH, VAL and IB high/low:
5 outputs. The donor TPOProfile declares 23 series outputs, including poor highs/
lows, excess highs/lows, single prints, buying/selling tail lengths, profile
shape, ledges, volume-profile values and volume totals. Those outputs are absent
from the Python schema and calculation result.

### 3. Indicator conditions lack complete catalog mappings

Most retained condition methods and module-level COT helpers have no BlockSpec or
@block annotation. Registry discovery publishes the indicator class, not its
arbitrary methods. Candle pattern helpers and VolumeProfile custom-hour methods
have the same limitation.

Some donor conditions are already expressible through existing generic blocks:
RSIChangesUp can be represented by RSI.value plus condition.changes_up;
MACDMainCrossAboveSignal by MACD.main/signal plus condition.crosses_above.
This does not require duplicating calculations or creating one source file per
condition. It does require explicit mappings that preserve parameters, output
selection, shifts and rounding, and a way for the builder/editor/generator to
select or compose them consistently. The current catalog contains no complete
donor-to-composition manifest for these variants.

RSI, MACD and BollingerBands currently provide calculations/ports without their
former named signal methods. This can be a valid composition design, but it
cannot be counted as complete donor block exposure until the mappings exist.

### 4. Supporting diagnostic is not ported

No counterpart was identified for Indicators/Other/DataLoggingIndy.java. This is
an internal OHLCV CSV diagnostic indicator without @BuildingBlock annotation,
not evidence of a missing selectable trading signal. Record an intentional
exclusion or implement an equivalent diagnostic if full donor-source coverage
is required.

### 5. Runtime and parity qualification remain distinct

The Order/StrategyControl migration deliberately uses explicit typed runtime
contracts, evaluated prices/sizes and Python accounting/history semantics.
Formula evaluation, sizing selection, ATM exit orchestration, bar-validity
scheduling and SQX platform/export-specific behavior are not fully reproduced.
These limitations are documented in trading-block-migration.md.

Passing the existing Python regression suite demonstrates application consistency,
not full SQX feature equivalence. Other families not singled out here still need
parameter/output/edge-case and numerical comparison before a parity claim.

## Recommended next qualification

1. Establish explicit mappings for all donor indicator variants to canonical
   calculations, named outputs and conditions/compositions, retaining helpers in
   their owning files and avoiding duplicate algorithms.
2. Complete VolumeProfile and TPOProfile session/configuration/output behavior.
3. Qualify donor parameters, defaults, warmup, rounding, shifts and edge cases with
   reproducible donor/reference fixtures. Mark deliberate exclusions explicitly.
4. Close the documented strategy-runtime integration gaps when the corresponding
   compiler/execution phases resume.

Do not report a single coverage percentage from Java file counts versus Python
registration counts: the two represent different units, and Python adds indicators
that do not exist in this donor folder.
