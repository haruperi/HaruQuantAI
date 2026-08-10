# Instrument and Venue Profiles

> **Status:** Completed feature `FEAT-BRK-00`.

This feature owns authoritative `InstrumentVenueProfile v1` evidence covering
provider-symbol and venue metadata, asset class, price precision, tick size,
quantity step, contract multiplier, trading sessions, supported order types,
margin eligibility, shorting rules, settlement, halt state, lifecycle state,
and trading eligibility.

The feature reads current, reverse, and historical symbol identity mappings
from the Brokers-owned `broker_symbol_map` table through private persistence.
Profile evidence is immutable and remains in memory; this feature owns no
additional table.

- `profiles.py` builds and parses integrity-protected profile evidence
  (`FR-BRK-147`).
- `symbols.py` resolves current, reverse, and as-of symbol identities
  (`FR-BRK-142`–`FR-BRK-144`).
- `__init__.py` is internal; external consumers import functions only from
  `app.services.brokers`.

Usage evidence is
`tests/brokers/usage/features/00_instrument_profiles.py`. Focused tests are in
`tests/brokers/unit/test_instrument_profiles.py` and transport compatibility is
covered by `tests/brokers/integration/test_operational_contract_transport.py`.
