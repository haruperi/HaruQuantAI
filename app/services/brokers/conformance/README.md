# FEAT-BRK-10 Adapter Contract Test Kit

This folder is the sole production owner of this focused completed Brokers feature. Public API, contracts, requirements, and usage evidence are registered only in `app/services/brokers/README.md`.

Calculation evidence uses immutable `brokers.calculation_fixture.v1` artifacts
with bounded string inputs/outputs, complete projected account fields, aware-UTC
observation time, demo/simulation identity, redacted account digest, provider
specification checksum, terminal build, and a canonical SHA-256 checksum.

`collect_broker_calculation_fixture` is write-scoped and guarded to the exact
`ENVIRONMENT=dev` plus Broker `demo` pair. It is never imported or called by
the default conformance suite. Collection requires separate execution approval;
normal tests and usage validate sanitized offline artifacts only.

Simulation conformance additionally reconciles the released bounded deal-history,
exact-deal, and account-transaction capabilities with the protocol, adapter,
delivery-evidence rules, and capability catalogue.
