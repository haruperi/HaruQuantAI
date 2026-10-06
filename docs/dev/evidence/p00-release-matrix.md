# Current reference release matrix

| Gate | Evidence / expected result | Qualification |
| --- | --- | --- |
| Current JAR inventory | 289 archives, 51,713 raw class entries; exact hashes | Static candidate; actual checks in walkthrough |
| Complete member metadata | Every raw class occurrence and declared member bound to current archive/hash | Static candidate; actual checks in walkthrough |
| Atomic ledger/schema | Version 4, current source root/IDs, resolved sources/relationships | Reference tooling only |
| Ownership | All JAR and resource feature proposals mapped; owning registrations required | Application runtime unqualified |
| Current UI source maps | Fresh file hashes; prebuilt flows preserved | Identity only; no backend parity |
| Common core / AI / engine | Required missing bodies and independent observed outputs | Unresolved; dependent implementation blocked |
| Installed product build / activation | Independent product/runtime observation | Unverified |
| Runtime/numerical parity | Independent normal/boundary/failure donor comparisons | Unqualified |

Use `uv run python -m tests.reference.validate`; optional `--check-donor` requires explicit `SQX_145_REFERENCE_ROOT`. Static success cannot bypass missing runtime gates. Use isolated temporary stores; no donor launch or live database modification.
