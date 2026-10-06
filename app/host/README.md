# Host authority and current reference tooling

Status: P00 complete for SQX145 reference readiness and owner-approved gap dispositions; static publication checks passed. Application host runtime is a separate delivery scope.

The host owns universal lifecycle, telemetry, sessions, typed capability discovery,
transport, jobs and shared resource custody. Domain numerical algorithms belong to
their owning workspace/plugin. This documentation activates no service or schema.

[Project](../../docs/PROJECT.md), [architecture](../../docs/ARCHITECTURE.md),
[evidence procedure](../../docs/dev/evidence/README.md) and `AGENTS.md` own authority.

## Registered feature

| Identity | Responsibility | Status |
| --- | --- | --- |
| `FEAT-HOST-EVIDENCE` | Host-governed reference manifests, fixtures and qualification in tests/reference | Implemented tooling; P00 reference readiness/disposition complete with recorded static passes; application/runtime qualification belongs to owning features |

## Registered functional requirements

| Identity | Responsibility | Required logs |
| --- | --- | --- |
| `FR-HOST-EVIDENCE-ROOT-RESOLUTION` | Resolve explicit sole donor/repository roots and contain locators; never substitute donor roots. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` | Reject malformed, duplicate, nonfinite, oversized or incorrectly typed reference JSON; verify source identities. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` | Reconcile current archive/resource bytes, complete member metadata and exact fingerprints/counts. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-FIXTURE-VALIDATION` | Validate independent observations, exact outputs, timestamps, source hashes and truthful static/runtime provenance. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-LEDGER-INTEGRITY` | Validate schema v4, atomic records, current sources, monotonic allocation, related records, mappings and pass artifacts. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-OWNERSHIP-GATES` | Bind current archive/features/FR seeds to proposed owners; check registered identities and reject unqualified runtime release. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-QUALIFICATION-CLI` | Run offline evidence gates by default and explicit read-only --check-donor checks; emit outcome logs and nonzero failures. | DEBUG checks, INFO accepted counts/lifecycle, ERROR stable failure codes; structured fr_id; no physical paths or secret values. |

## Ratified reference decisions

Owner approved the current-only migration plan version 1 and P00 closure plan version 2 on 2026-10-06 with `APPROVED: EXECUTE`. Closure approval ratifies the two disposition decisions below; it registers no application feature or FR.

| Identity | Approved decision |
| --- | --- |
| `DEC-HOST-P00-AUTHORITY-RESTORATION` | Project/architecture and owning READMEs define current target authority; retained UI status does not establish backend service availability. |
| `DEC-HOST-P00-SCHEMA-EVOLUTION` | Strict schema version 4 binds only 145-dev1; atomic claims, classifications, limits, source locations/hashes, mapping/review/clean-room fields and truthful validation remain mandatory. |
| `DEC-HOST-P00-REGISTRY-BOUNDARY` | Register only the existing evidence tooling capability here. All application JAR/resource feature and FR allocations remain proposals until their owning feature plans ratify them. Domain READMEs own status. |
| `DEC-HOST-P00-LOGGING-ADAPTER` | Reference tooling uses explicit standard-library named loggers, structured FR identifiers and stable redacted codes. No logging configuration or I/O at import; API callers/CLI explicitly configure handlers. |
| `DEC-HOST-P00-VALIDATION-DEPENDENCY` | Use the declared and locked development jsonschema dependency for full Draft 2020-12/format validation. This migration adds no dependency. |
| `DEC-HOST-P00-BOUNDED-FIXTURES` | UTF-8 JSON reads reject duplicate keys/nonfinite numbers and exceedance of 4 MiB. Relative forward-slash locators reject traversal, absolute/drive/UNC paths and resolved escapes. Fixtures use isolated static observations; no donor writes. |
| `DEC-HOST-P00-RELEASE-GATES` | Exact static counts/hashes/order use zero tolerance. Static qualification does not establish numerical semantics, activation or runtime parity. Donor-derived claims require body/observation evidence; the limited unavailable-host-source disposition permits approved target-owned host contracts. Missing domain/runtime evidence still blocks dependent claims and release. |
| `DEC-HOST-P00-MODULE-HEADING` | Concrete Python tooling follows the five canonical module docstring sections, descriptive FR identities, explicit typed signatures and observable FR logs. |
| `DEC-HOST-SQX145-REFERENCE` | The sole reference is the downloaded 145-dev1 cohort under SQX_145_REFERENCE_ROOT. No alternate donor root, snapshot lookup, source backfill or compatibility fallback. Fresh record IDs use SQX145-EV-NNNNNN starting at 000132; preserve the allocation high-water mark. |
| `DEC-HOST-SQX145-BYTE-IDENTITY` | Fingerprint-bound published references serialize deterministically as UTF-8/LF with scoped Git attributes. Hash final bytes and reject unexplained drift; metadata shards remain bounded. |
| `DEC-HOST-P00-CLOSURE-BOUNDARY` | P00 accepts verified reference tooling/inventory, reconciled ownership proposals and explicit gap dispositions. Application registration, execution and applicable independent runtime comparisons belong to owning feature plans and release gates; P00 closure grants no runtime/parity authority. |
| `DEC-HOST-P00-UNAVAILABLE-HOST-SOURCE` | The audited MainApp/AppSettings/CpuInfo host-service bodies receive an accepted source limitation. HaruQuantAI may implement its own universal lifecycle/settings/path/CPU contracts, informed by directly inspected callers, through approved feature plans. Unsupported semantics are explicit normative target decisions. This exception covers no missing numerical, trading, AI or domain algorithm and grants no exact-translation/parity claim. |

## Ownership and release boundaries

- [Current P00 review](../../docs/dev/evidence/sqx145/p00-review.json) retains the earlier static observations unchanged. [Host-core research](../../docs/dev/evidence/p00-host-core-research.md) records the bounded packaging/caller audit and approved disposition.
- P00 closure qualifies reference readiness and disposition of known gaps. Application features, backend/UI execution and runtime comparisons remain their own approved delivery scopes.
- MainApp/AppSettings/CpuInfo bodies remain unavailable within the audited static boundary. Universal host services can follow approved HaruQuantAI contracts under the limited disposition; settings precedence, durability, CPU policy and lifecycle must be explicit target decisions and tested before delivery.
- The 23 selected AI gaps belong to phase 19.1. Other data/trading/engine gaps remain feature-level research obligations. Existing SC-02 limits blockers to declared dependencies.
- `manifest.py`, `fixtures.py` and `validate.py` map constructors/helpers to their documented FRs. Their imports configure no handlers or filesystem activity.
- All current JAR/resource application allocations remain proposed until owning feature plans ratify them. `FEAT-HOST-JRT-FS` is a proposed JVM-only disposition, not a Python implementation obligation.
- Missing domain bodies/independent observations cannot be replaced by guessed SQX behavior. Application tests do not establish donor parity; installed-product activation remains unverified.
- Persistence schemas/migrations/transactions/retention require a ratified host capability; plugins receive focused typed interfaces and never ad-hoc SQL authority.
- Reference tooling opens no operational database and never launches the donor. Live/irreversible effects retain distinct authorization.
