# Provider Specification Snapshots (`FEAT-BRK-18`)

> **Feature:** `FEAT-BRK-18` Provider Specification Snapshots
> **Status:** `Completed` (parity programme Phase 4a)
> **Module:** `app/services/brokers/specifications/`

Owns the typed, versioned **current** provider specification snapshot
(`brokers.provider_specification.v1`) for one symbol and account observation.
The snapshot is the evidence source the parity programme consumes: Brokers
owns the current observation, Data (Phase 4b) owns the immutable
effective-dated history of these snapshots, and Simulation never interprets
raw MT5 metadata.

## Public API (package root only)

Exposed through `app.services.brokers`:

- `build_provider_specification_snapshot(**fields)` — fail-closed build from
  one raw MT5 `symbol_info` observation plus explicit connection identity.
- `parse_provider_specification_snapshot(value)` — parse and checksum-verify
  one canonical JSON-safe mapping.
- `dump_provider_specification_snapshot(snapshot)` — canonical JSON-safe
  serialization.
- `get_provider_specification_snapshot_field(snapshot, field)` — bounded field
  read.
- `verify_provider_specification_snapshot(snapshot)` — recompute and compare
  the canonical checksum.
- `get_broker_provider_specification(adapter, symbol)` — read one snapshot
  through the connected adapter (`BrokerCapabilityId.GET_PROVIDER_SPECIFICATION`).

## Contract summary

The frozen slotted snapshot carries: execution/order/filling/expiration/GTC
modes (verified MT5 bit-flag mappings; zero filling mask admits MT5's RETURN
default; unmapped indices become `UNKNOWN` and fail canonical eligibility);
stops/freeze levels; directional `volume_limit`; calculation mode; initial,
maintenance, and hedged margin evidence plus currencies; swap mode/rates and
the triple-swap weekday; instrument scalars (point, digits, tick size, tick
values profit/loss, contract size, base/profit/margin currencies); and the
identity block (broker, server, redacted 64-hex account digest — the raw
account ID is never stored — environment, terminal build, source revision,
aware-UTC `observed_at`, retrieval provenance, SHA-256 checksum).

Dynamic commission/fee evidence is a separate typed reference
(`evidence_id` + checksum); no static symbol rate is ever guessed
(`FR-BRK-162`). The type exposes no effective bounds and parse rejects them
(`FR-BRK-163`, current observation only). Every required raw field fails
closed (`FR-BRK-161`). Account-permission evidence records `margin_mode`
(from `account_info`) and derives `hedging_permitted`; stop-out policy and
FIFO discipline are not exposed by the upstream Python contract and remain
explicit `unverified` exclusions.

## Files

| File | Responsibility |
| --- | --- |
| `contracts.py` | Private frozen snapshot/permission/cost-reference models and verified vocabularies |
| `build.py` | Fail-closed raw-record mapping, canonical dump/parse, checksum build/verify |
| `public.py` | Function-only public surface for the package root |

## Tests and usage evidence

- Unit: `tests/brokers/unit/test_provider_specifications.py` (per-FR rows)
- Integration: `tests/brokers/integration/test_provider_specification_contract.py`
  (adapter path, capability release, conformance fake, isolation)
- Usage: `tests/brokers/usage/features/18_specifications.py`
  (`fr_brokers_159()`–`fr_brokers_163()`)
