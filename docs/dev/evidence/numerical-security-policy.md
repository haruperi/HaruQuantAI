# Phase 0 numerical, generated-tick, and security policy

This policy is a prerequisite boundary, not evidence that an unimplemented feature
already satisfies it. The owning feature card may select a stricter rule but may not
silently weaken these defaults.

## Numerical representation

- Money, prices, fees, margin and quantities crossing persistence or contract
  boundaries use signed 64-bit scaled integers with an explicit scale. Overflow is
  checked before arithmetic and returns a typed refusal; wraparound is forbidden.
- `Decimal` is permitted for bounded policy/configuration calculations when its
  context and rounding mode are pinned. Binary `float` is permitted only for
  explicitly statistical/visual calculations with an algorithm-specific tolerance,
  finite-value checks and a recorded conversion boundary. There is no universal
  `1e-9` tolerance.
- Every numerical acceptance oracle states absolute/relative tolerance, units,
  rounding, empty/zero behavior, missing-data behavior and overflow behavior.
- Randomized algorithms require an explicit seed and record the generator family,
  version and seed. Equal inputs and environment must reproduce equal canonical
  outputs or a declared tolerance-bounded result.

## Causality and generated ticks

- Data and indicator operations consume only observations whose event timestamp is
  not later than the decision timestamp. Arrival time and event time remain distinct.
- Recorded ticks preserve provider sequence and timestamp. Generated ticks use the
  owning `FEAT-SIM-MODEL_TICKS` algorithm only after its profile, seed, bar fields,
  spread model and gap policy are validated.
- Until Task 4.06 ratifies that algorithm, generated-tick output is
  `UNQUALIFIED_GENERATED_TICKS`; no parity, fill-quality or production claim may use
  it. `EVD-TICKS-01` supplies a closed hash-pinned recorded/golden fixture, not a
  claim that the future generator is already implemented.
- Simulation order is `(event timestamp, provider sequence, deterministic tie-break)`;
  a fill may affect state only after its triggering event and before the next event.

## Native state and checkpoints

- Checkpoints identify schema version, feature/version, input hashes, deterministic
  seed/state, last committed event identity and output ledger revision.
- Restore validates every identifier and checksum before state becomes visible.
  Unknown versions, partial bytes and incompatible native/runtime state fail closed.
- Native extensions and worker payloads are untrusted inputs. Their ABI, toolchain,
  architecture and resource limits are pinned before a qualified result is accepted.

## Security and isolation

- Secrets, credentials, personal data, workspace paths, raw payloads, fence/session
  tokens and sensitive trading/account data are never logged or embedded in evidence.
- Credential-bearing providers resolve opaque Workspace references at the last
  responsible boundary. Evidence records only redacted provider/version/readiness.
- Custom code runs only in an admitted isolated worker with bounded CPU, memory,
  wall time, output, filesystem roots and network policy. Timeout/cancellation kills
  descendants and records a redacted terminal receipt.
- SQL values use parameters. Dynamic identifiers come from an explicit allowlist.
  Filesystem paths are canonicalized and containment-checked; UNC, drive-relative,
  device and traversal paths are rejected at public boundaries.
- No live order or external mutation is implicit. Development defaults to offline,
  demo, sandbox or testnet targets, and a missing evidence item blocks only the claim
  named in `external-evidence-calendar.json`.

## Phase 1 inputs

The exact repository bar, tick and catalogue fixtures and their SHA-256 hashes are in
`fixture-manifest.json`. Reproduce them with:

```powershell
uv run --frozen python scripts/generate_phase0_fixtures.py --check
```
