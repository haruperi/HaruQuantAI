# Reimplementation evidence procedure

Current ledger: `reimplementation.json`, strict Draft 2020-12 schema version 2 in
`reimplementation.schema.json`. Read both in full before any edit. Do not allocate
an ID from a roadmap seed or missing registry. Only the current owner-approved plan
and owning README confer target authority.

## History and ID allocation

`history/3ede688/reimplementation.json` and its schema are byte-identical historical
Git blobs at `3ede688544b1c161984573cdc25e7a36b01d4a37`. They preserve 88 identities,
relationships, review states and historical execution timestamps. Their 41 passed
states are historical, not current validation. The current envelope records both
hashes and maximum ID 88. Allocate global highest ID + 1 across both generations;
P00 starts at SQX144-EV-000089. Never reuse an identity. Allocate source catalog IDs
by highest existing suffix in each namespace plus one, checking collisions.

## Atomic claims

Record one independently testable claim per ID. Include question, topic, scope,
classification (observed/inferred/normative/unverified), confidence and limitations.
A normative decision is target authority; an observation describes the donor.
Missing behavior remains unverified, not an invented default or successful fallback.

Sources carry catalog identity, logical root, exact artifact locator, SHA-256,
access date, narrow symbol/offset/line/JSON/XML location, inspection method and
support/contradiction/context relation. Method declarations do not prove bodies;
bytecode references do not prove callers' runtime reachability. Never publish
proprietary source/decompiled text, credentials, user values or private endpoints.

Target mappings resolve registered FEAT/FR/DEC identities and owning README.
Roadmap proposals are mapped separately in p00-ownership.json and remain
unratified. Retain legacy identifiers only inside history; new IDs are descriptive.

## Validation and supersession

Before recording passed, execute the exact procedure, record expected and actual
observations, UTC timestamp and repository-relative durable artifact. Classify
validation as static, runtime or authority. Static ZIP/body inspection never
satisfies runtime or numerical parity. Runtime passes require actual black-box
source observations. Snapshot restoration alone cannot promote historical passes.

Check the full schema with format validation, source IDs, all relationships, unique
identities, fingerprints, registered mappings, paths and clean-room flags. Reject
absolute/UNC/drive/traversal/escaped roots, duplicate JSON keys and nonfinite JSON.
The reference JSON input limit is 4 MiB, approved as a target tooling boundary.

Conflicting claims are preserved with linked contradiction/supersession records;
reciprocal supersedes/superseded_by links must resolve and be acyclic. No deletion,
silent rewrite or retroactive review-state upgrade. A historical record's original
schema remains available and unchanged. New records start unreviewed even when the
owner approved the target decisions; source-observation review is separate.

## Repeatable checks

```powershell
uv run python -m tests.reference.validate
uv run python -m tests.reference.validate --check-donor
```

The explicit donor check reads only the configured SQX_REFERENCE_ROOT. Offline
checks need no installation. Actual product version/activation remains unverified.
Integer/hash/order facts compare exactly; numerical tolerances must be ratified per
future feature. CI and log/negative-case tests are documented in tests/reference.
