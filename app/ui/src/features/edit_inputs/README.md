# Edit Inputs (`FEAT-UI-EDIT_INPUTS`)

Owning README: `app/ui/README.md` (§4.4). Partial slice: FR-UI-PRESERVE_DRAFTS
implemented; RENDER_FIELDS, VALIDATE_INPUT, RESOLVE_CONFLICTS, and
CONFIRM_IMPACT are mock-build lines completing at the Stage 6 Data de-mock
gate (6.15).

## FR-UI-PRESERVE_DRAFTS

`draft_store.ts` persists non-secret drafts locally, scoped by
schema/workspace/actor identity and entity version (wire record R11):

- `load` discriminates `restored` / `mismatch` / `none` — mismatches
  (different identity scope, entity version, or corrupt storage) require
  explicit resolution via `clear` or a deliberate overwrite; never silent.
- `save` rejects payloads containing secret-shaped keys (recursive,
  case-insensitive heuristic: secret/password/token/credential/api_key/
  private_key). The authoritative non-secret policy is backend-side at
  de-mock; this is a bounded client guard.
- Storage never throws (quota/privacy failures degrade to no persistence).

## State decision (migration plan §8.3)

Module-level store only; no React context and no cross-feature state this
slice. Widget surfaces (`schema_form`, `selection_table`, `confirmation`)
arrive with the 6.15 de-mock.

## Bounded dev usage evidence

The mock fixture returns a non-null `DraftEnvelope` for the
`PRESERVE_DRAFT` operation; the store's refresh-restore semantics are
exercised in `__tests__/edit_inputs.test.tsx`.
