# Current reference release matrix

| Gate | Evidence / expected result | Qualification |
| --- | --- | --- |
| Current JAR inventory | 289 archives, 51,713 raw class entries; exact hashes | Passed current static recheck; source-bound observations retained |
| Complete member metadata | Every raw class occurrence and declared member bound to current archive/hash | Passed current static recheck; complete metadata retained |
| Atomic ledger/schema | Version 4, monotonic IDs, resolved sources/relationships | Passed closure-candidate schema/source/relationship checks; reference tooling only |
| Ownership | Reconciled JAR/resource proposals and registered evidence capability | P00 proposal mapping qualified; application registrations occur in owning feature plans |
| Current UI source maps | Fresh file hashes; prebuilt flows preserved | Identity only; no backend parity |
| P00 host-core disposition | Published bounded research and owner-approved decisions | Owner-approved source limitation and passed static closure checks; P00 complete, bodies still unavailable |
| Target-owned universal host implementation | Ratified exact contracts/defaults/failures, independent target tests and applicable UI connection | Future owning feature/integration delivery; no SQX exact-translation/parity claim |
| Missing AI / engine / domain behavior | Supporting behavior evidence and applicable independent observations | Unresolved; blocks declared dependent behavior/parity claims and feature release; AI obligations belong to P19.1 |
| Installed product build / activation | Independent applicable product/runtime observation | Unverified; no donor execution performed |
| Runtime/numerical parity | Independent normal/boundary/failure donor comparisons | Unqualified; P00 closure does not satisfy this gate |

Use `uv run python -m tests.reference.validate`; optional `--check-donor` requires explicit `SQX_145_REFERENCE_ROOT`. Exit 0 qualifies static reference integrity; the unchanged CLI reports runtime blocked. Use isolated temporary stores; no donor launch or live database modification.

- [Earlier P00 review](sqx145/p00-review.json) remains unchanged. [Host-core research](p00-host-core-research.md) and [closure capture](sqx145/host-core-research.json) record current observations and approved dispositions.
- P00 acceptance is reference readiness and explicit gap disposition. Application implementation/registration and applicable runtime observations are feature-level obligations.
- Earlier mandatory host-body recovery/global runtime prerequisite wording is superseded policy. No body recovery, activation or unperformed observation is marked passed.
- Existing SC-02 and registered release decisions limit blockers to declared dependencies and claims. The host-source exception is limited to the three named universal host services; it never supplies guessed numerical/domain behavior.
