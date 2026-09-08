# Phase 0 specification drift reconciliation

**Repository baseline:** `34edd2b3c8164b59ed9b2b2964c0d79f7c2d399a`

**Original historical blob:** `7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd`

**Inspected historical blob:** `d69bef59cb981350cd6f2ebdccc31b231a4e0950`

The live authoritative inputs are
`docs/dev/Feature_Requirement_Traceability_Register.md` and
`docs/dev/Phased_Feature_Implementation_Plan.md`. Their working-tree SHA-256 and
Git blob identities are recorded by `baseline-manifest.json`. The normalized
register and complete capability graph are retained under `evidence/source/`;
the absent legacy `docs/dev/inputs/*` paths are not cited as if they existed.

## Historical blob comparison

The exact command was:

```powershell
git diff --no-ext-diff --unified=3 7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd d69bef59cb981350cd6f2ebdccc31b231a4e0950
```

It reports six removed whitespace-only blank lines and six corresponding clean
blank lines in the `SQXArchiveHandler.parse_orders_bin` and
`SQXArchiveHandler.export_orders_parquet` code examples. No executable repository
file, feature identity, requirement, capability edge, ownership boundary,
catalogue entry, workflow or acceptance oracle changes between those blobs.

## Clause disposition

| Changed clause | Disposition | Scope effect |
| --- | --- | --- |
| Blank lines in `parse_orders_bin` example | retained semantics; formatting normalized | none |
| Blank line in `export_orders_parquet` example | retained semantics; formatting normalized | none |

No clause is classified `changed` or `scope-impacting`. The feature set therefore
remains exactly 205. Any future added/removed feature is a scope change requiring
owner approval and regeneration; it cannot appear as an implicit 206th task.

## Current-source reconciliation

The source register contains 205 unique cards, 575 FRs, 276 local NFRs, 477
required edges and 233 operation-gated edges. The phased plan contains the same
205 feature IDs exactly once plus eight non-feature preparations. The generated
Phase 0 validator checks those sets and counts directly; timestamps and narrative
claims do not establish freshness.
