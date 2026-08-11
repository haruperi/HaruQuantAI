# Evidence — FEAT-DATA-12

Owns normalized account-state, market-context, freshness, and FX-conversion
evidence. Account positions preserve optional genuine broker ownership
references without synthesizing missing ownership. This feature produces
evidence and never a Risk or Trading decision.

- Production files: account, freshness, FX, and market-context modules.
- Requirements: FR-DATA-008, 028, 075–076, and 078–079.
- Usage evidence: `tests/data/usage/14_evidence.py`.
- Side effects: injected read-only provider calls only.
