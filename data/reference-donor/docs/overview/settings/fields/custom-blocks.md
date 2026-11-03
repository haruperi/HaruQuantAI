# Custom blocks — field reference (for UI tests)

> Custom blocks are authored in the separate embedded **AlgoWizard** app, not in the Builder's Building
> blocks panel — that panel only *displays* them once created.

Source checked:
- `internal/plugins/SettingsBlocks/services/BlocksService.js` (lines ~100-113: loads
  `result.customBlocks` from the server and merges them into the standard grids by `groupKey`) and
  `internal/plugins/SettingsBlocks/views/blocks.html` (the grids they land in).
- `internal/web/AlgoWizard/` — where custom blocks are actually created/edited. This is a **compiled,
  minified Vue SPA** (`assets/index-*.js`); no Angular-style `.html`/`ng-model` source exists in this
  repo to extract exact field bindings from, and grepping the bundle for `data-testid` finds only
  generic/dynamic props (`__props.testid`, `_ctx.buttonTestId`) — no static per-field test ids for the
  Custom blocks screen.
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/blocks/CustomBlocks.java` (backend load/save
  of `algoWizardCustomBlocksPath`, confirms these are an AlgoWizard concept, not a SettingsBlocks one).
- Existing prose page `../custom-blocks.md` (already vetted against the backend/AlgoWizard behavior).
- `tests/ui/scenarios/SQX-AlgoWizard/TC-070..TC-085` (TS14 suite) — existing manual test-case titles for
  add/duplicate/rename/delete/category/opposite/parameters/import-export of custom blocks; useful as
  scenario names, but they are prose test-case files, not element identifiers.

## Where custom blocks are actually configured

**AlgoWizard → Customize → Custom blocks.** No ng-model/data-testid source is available in this repo
for that screen. Per the existing prose page (`../custom-blocks.md`), the editor exposes, per block:

| Field (prose name) | Notes |
|---|---|
| Block key | Unique ID, letters/numbers only. |
| Block name | Display name shown in Building blocks selection. |
| Block type | `Condition` (signal) or `Price level` (stop/limit). |
| Conditions / content | Built via the standard block-picker dialog. |
| Parameters | Chart (mandatory) + user-added params of type chart / period / shift / int / double / bool. |
| Opposite block | Link to the block used for the Short direction; "Not set" until created; "Negate from opposite block" re-applies negation after edits. |

These are **not** verifiable ng-model bindings from source in this pass — treat as unconfirmed until
cross-checked against the actual AlgoWizard DOM (e.g. via a live capture) before writing selectors.

## What appears inside Building blocks (SettingsBlocks) itself

No distinct controls of its own. `BlocksService.js` loads `result.customBlocks` from the server and
merges each entry into the existing grids by `groupKey`:

| Custom block `groupKey` | Merged into |
|---|---|
| `"Custom conditions"` | `blocksGrid` (Signals section) |
| `"Custom price levels"` | `priceBlocks` → `stopLimitBlocksGrid` (Stop/Limit entry blocks section) |

Once merged, a custom block is just another row in `blocksGrid` / `stopLimitBlocksGrid` — same
columns (ID, Use checkbox, Name, Weight, Parameters link) and same `block-config` Parameter-ranges
popup as built-in blocks. See [parameter-ranges.md](parameter-ranges.md) for that popup's fields, and
[../../fields/README.md](README.md) → the Building-blocks grids for the shared grid column layout.

## Related

- Prose page: [../custom-blocks.md](../custom-blocks.md)
- Fields hub: [README.md](README.md)
- Parameter ranges popup shared with standard blocks: [parameter-ranges.md](parameter-ranges.md)
- Global negation file (distinct from per-block "Opposite block"): [oppositeblocks.md](oppositeblocks.md)
