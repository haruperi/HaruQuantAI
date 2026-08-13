# Sources — FEAT-DATA-09

Owns source contracts, registry/composition, policy, promotion, licensing, local
adapters, and runtime enforcement of read-only broker access.

- Production files: adapters, persistent asynchronous provider runtime, composition,
  contracts, licensing, policy, protocol, read-only enforcement, and registry.
- Requirements: FR-DATA-010–011, 022–027, 101–104, 113–116, and 159.
- Usage evidence: `tests/data/usage/features/09_sources.py`.
- Side effects: registration is I/O-free; explicit reads are bounded and promotions
  delegate their atomic source-state/audit write to `data.persistence`.
- MT5 lifecycle: one cached MT5 adapter owns one persistent serialized event loop
  from connect through every read and disconnect. API shutdown closes composed
  provider sessions before removing their injected runtime configuration.
