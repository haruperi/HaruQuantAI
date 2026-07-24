# Tick-Series Derivation — FEAT-DATA-05

Owns bounded fixed-point tick derivation from real evidence and approved-root
streaming to Parquet. It never fabricates provider evidence.

- Production files: `_kernel.py`, `contracts.py`, `generator.py`, `provenance.py`.
- Requirements: FR-DATA-087–090.
- Usage evidence: `tests/data/usage/05_tick_derivation.py`.
- Side effects: explicit approved-root Parquet writes only.
