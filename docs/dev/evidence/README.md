# Clean-Room Evidence Ledger Procedure (`docs/dev/evidence`)

Authority: [AGENTS.md](../../../AGENTS.md), [PROJECT.md](../../PROJECT.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), and [app/host/README.md](../../../app/host/README.md).
Core rule: **Donor informs; specification owns.**

## 1. Logical Roots & Clean-Room Hygiene

- `SQX_REFERENCE_ROOT`: Logical root representing the read-only StrategyQuant X Build 145 reference installation.
- `HARUQUANTAI_ROOT`: Logical root representing this repository.
- **Zero Physical Paths:** Never commit machine-specific absolute paths (drive letters, home directories, or UNC paths) in repository evidence, schemas, manifests, or fixtures.
- **Clean-Room Flags:** Every ledger record in [`reimplementation.json`](reimplementation.json) must preserve:
  - `contains_proprietary_source: false`
  - `contains_sensitive_data: false`
  - `contains_personal_data: false`
  - `paraphrased_behavior_only: true`

## 2. Ledger Files

| File | Role |
| --- | --- |
| [`reimplementation.schema.json`](reimplementation.schema.json) | Draft 2020-12 JSON Schema (version 4) governing [`reimplementation.json`](reimplementation.json). |
| [`reimplementation.json`](reimplementation.json) | Canonical clean-room evidence ledger containing `source_catalog` and atomic `SQX145-EV-NNNNNN` records. |
| [`p00-inventory.json`](p00-inventory.json) | Fingerprinted donor & repository reference manifest reconciled by `tests/reference/manifest.py`. |
| [`p00-release-matrix.md`](p00-release-matrix.md) | Stage 0 (`P00`) qualification gates and runtime boundaries. |

## 3. Recording & Updating Evidence

1. Read both [`reimplementation.json`](reimplementation.json) and [`reimplementation.schema.json`](reimplementation.schema.json) before editing.
2. Record **one atomic, independently testable claim** per evidence record.
3. Allocate the next ID as `SQX145-EV-NNNNNN` using `allocation_high_water_mark + 1` and update `allocation_high_water_mark`. Never reuse an ID.
4. Use a stable dot-separated topic (e.g., `architecture.process.two_process_topology`, `simulator.execution.same_bar_precedence`).
5. Classify every claim as:
   - `observed`: directly supported by inspected evidence
   - `inferred`: reasoned from evidence with explicit reasoning limits
   - `normative`: a HaruQuantAI target architectural/design decision
   - `unverified`: an open hypothesis requiring validation
6. Assign calibrated confidence (`confirmed`, `high`, `medium`, `low`, `unverified`) and explicit `limitations`.
7. Map each record via `target_mapping` to its owning domain (`host`, `kernel`, `workspace`, `plugins`) and registered `FEAT-*`, `FR-*`, `DEC-*` IDs, or mark `registration_status: "proposed"` with `proposed_feature_id` / `proposed_requirement_ids` / `proposed_decision_ids` until the owning stage registers them.
8. Preserve historical findings: never silently overwrite a material prior claim. Add a new record and link both via `supersedes_records` and `superseded_by` (or `contradicts_records`).
9. Set `validation.state` to `"passed"` only when `actual_observation`, `artifact_paths`, and `executed_at` are recorded and all supporting local sources carry SHA-256 fingerprints.

## 4. Verification Commands

```powershell
uv run python -m tests.reference.validate
uv run python -m tests.reference.validate --check-donor
uv run pytest tests/unit/test_reference_manifest.py tests/unit/test_reference_fixtures.py tests/unit/test_reference_validation.py --no-cov
uv run python scripts/ci_check.py
```
