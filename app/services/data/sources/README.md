# Data Source Governance — FEAT-DATA-10

Owns source contracts, registry/composition, policy, promotion, licensing, local
adapters, and runtime enforcement of read-only broker access.

- Production files: adapters, composition, contracts, licensing, policy, protocol,
  read-only enforcement, and registry.
- Requirements: FR-DATA-010–011, 022–027, 101–104, and 113–116.
- Usage evidence: `tests/data/usage/10_sources.py`.
- Side effects: registration is I/O-free; explicit reads are bounded and promotions
  delegate their atomic source-state/audit write to `data.persistence`.
