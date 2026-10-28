# VolumeProfile and TPOProfile donor qualification

This replaces the former rolling-window approximations with session calculations.
It does **not** certify full parity of the entire Blocks library.

## Implemented contracts

- `VolumeProfile` version 2: all 29 numerical donor outputs, plus 12 stable named
  session ports (London, New York, Sydney, Tokyo POC/VAH/VAL). Calendar, custom-hour,
  independent multi-session and confirmed swing sessions share the same histogram
  calculation. Standard outputs use the first enabled named session in multi mode.
- `TPOProfile` version 2: all 23 numerical donor outputs, including poor/excess
  extremes, single prints, tails, shape, ledges, IB, directional POCs and volumes.
  A bin gets one TPO per time bracket, not one per touching bar. Bars spanning
  multiple brackets touch each bracket; the donor's 62-bracket cap is preserved.
- Calendar selection numbers match the donor: previous day/week/month/year = 1–4;
  actual day/week/month/year = 5–8. VP previous/actual swing = 9/10. Swing reversal
  supports percentage, fixed ticks and SMA true-range ATR thresholds.
- Range and fixed-tick binning, 2,000-bin cap, greedy HVN separation, LVNs,
  Gaussian cluster levels and time-based initial balance follow the source.
- Actual profiles exclude the bar opening at the current timestamp. Completed
  sessions calculate once and carry forward. Sundays are skipped. Empty/flat
  sessions retain prior values; startup values are zero (TPO shape starts at 5),
  matching the donor rather than the old NaN rolling warmup.
- Raw value-area ties expand upward; cluster value-area ties expand downward.
  The donor's shape-analysis order is preserved: shape uses the preceding
  calculation's POC index, before the current POC is assigned.

Parameters stay inside their indicator class. Shared histogram/session code lives
in the existing `app/include/calculators` package. No forwarding aliases, legacy
rolling implementation or additional package has been introduced. `period` and
`ib_bars` are removed; existing callers/tests use the session contract directly.

## Explicit input and configuration differences

Both indicators require real open/high/low/close/volume and aligned, positive,
strictly increasing timestamps. Opens are never approximated from previous closes.
Timestamp units are explicit (`seconds`, the editor's convention, or
`milliseconds`). Calendar boundaries use an explicit chart `timezone` (UTC default).
Pass the broker/chart timezone when its calendar is not UTC.

Fixed bins require a positive instrument `tick_size`; it is not guessed from
prices or supplied with an arbitrary instrument default. `bin_size_mode=1` selects
range bins without instrument metadata. The donor's default fixed-tick mode remains
the default, so default calculation requires setting `tick_size`.

`value_area_pct` uses donor percentage units (70, not 0.7). Custom windows use
minutes after midnight, e.g. `session_start=480, session_end=960` means 08:00–16:00;
end <= start crosses midnight. `profile_mode="custom"` / `"multi"` selects VP
variants, with `session_mode=1` previous or `2` actual. TPO custom hours require a
daily session and `use_custom_hours=True`.

Deliberate correction: the donor multi-session subclass does not restore
`prevPrevPOC` / `prevPrevVAMid` when switching sessions, so delta outputs can compare
different sessions. Our named sessions own their state independently. This is an
intentional difference, not certified bit parity with that donor defect.

Chart rendering/export controls are not accepted as computation parameters.
TPO `UseBlockMode` only controls rendering in the donor and is likewise omitted.

## Evidence and reproducibility

`scripts/capture_profile_donor.py` extracts the donor's numerical methods and
`OnBarUpdate` / boundary methods, compiles them with a JDK, and replays real method
bodies against deterministic OHLCV data. Stubs supply chart access, UTC calendar
operations, configuration, logging and unused chart-export hooks. This does not run
the proprietary SQX application or its broker/chart runtime.

`docs/dev/fixtures/profile-donor-reference.json` records source SHA-256 values and:

- 42 core numerical cases: range/fixed bins, cluster on/off, sparse and single bars,
  zero volume, bull/bear-only volume, and a capped-bin price range.
- 36 bar-by-bar session replays: every calendar mode for both indicators, VP swing
  modes with all three thresholds, and previous/actual same-day and overnight
  custom-hour sessions for both indicators, and multi-session profiles with
  overlapping windows, a single enabled session and all sessions disabled.

Tests compare every donor output at every replayed bar. Tolerance is
`rel=2e-14, abs=1e-12` for Java/Python floating-point math; this is numerical
qualification, not a claim that every Gaussian result has identical bytes.
Prefix-causality regressions compare complete output arrays exactly.

Run:

```powershell
uv run python scripts/capture_profile_donor.py --donor C:\SQX-145\internal\extend\Snippets\SQ
uv run pytest tests/include/blocks/test_profile_sessions.py -q
```

Normal tests read captured fixtures and do not require the donor installation or
a JDK. The old `phase3-family-baselines.json` rolling-profile hashes remain
unchanged as historical evidence. They are explicitly superseded for these two
families by the donor fixtures; other family hashes still run unchanged. The
canonical contract manifest and donor mappings describe the new contracts.

## Remaining qualification

The named multi-session scheduler is also replayed against the donor subclass;
the two delta outputs are explicitly excluded from donor equality and separately
tested for session isolation. Their correction above must remain explicit.
Instrument metadata binding,
non-UTC platform calendars/DST equivalence and native SQX runtime/export behavior
are not certified by the UTC stubs. Profile blocks remain ineligible for automatic
generation until that integration is qualified. Existing signal compositions that
declare external profile feeds still require those feeds; they are not silently
rebound to a profile with guessed session/tick settings.

## Verification

- Full repository suite: **1,214 passed**.
- Final strengthened donor profile fixtures: **94 focused tests passed**, including
  nonzero confirmed outputs for both swing modes under every reversal method.
- Mypy: no issues across 318 source files (blocks, calculators, trading and editor).
- Ruff lint and changed-file formatting checks passed.
- Architecture gate passed, including the 1,000-line file limit; `git diff --check`
  passed. Changes are uncommitted.
