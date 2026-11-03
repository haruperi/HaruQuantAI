# OppositeBlocks / negation — field reference (for UI tests)

> No web-plugin UI exists for this feature — it is a global CSV config file, confirmed by both source
> and the existing prose page. Documented here as instructed: what the mechanism is instead of invented
> fields.

Places searched for a UI (none found):
- `internal/plugins/**` — grep for `opposite`/`Opposite` (case-insensitive) across all plugin
  `.js`/`.html` returns zero matches anywhere in `internal/plugins`.
- `internal/web/app/**` — same grep, zero matches outside of unrelated minified vendor libs.
- `internal/web/AlgoWizard/assets/*.js` (minified Vue bundle) — grep for `data-testid` near
  `custom`/`opposite`/`block` only turns up `editor-custom-resources-*` (an unrelated "custom
  resources" conflict-resolution dialog, not this feature).

Backend confirmation:
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/blocks/OppositeBlocksConfig.java` — loads
  `user/settings/OppositeBlocks.csv` (format `Block;OppositeBlock`, one pair per line; falls back to
  each block's `@OppositeBlock` Java annotation when the CSV doesn't cover it).
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/Blocks.java` (`_generateOppositeBlocksMap`,
  `_getOppositeBlock`) — consumer of the cache built by `OppositeBlocksConfig`.

## What actually configures this

| Mechanism | Where | UI control? |
|---|---|---|
| Global negation override for **standard** blocks | `user/settings/OppositeBlocks.csv` (`Block;OppositeBlock` per line, block **snippet code names**) | **No** — hand-edited file; doesn't exist by default (an `OppositeBlocks_example.csv` documents the default list); requires an app restart to take effect. |
| Per-block negation for **custom** blocks | AlgoWizard → Customize → Custom blocks → "Opposite block" field | Exists as a UI control in AlgoWizard (see [custom-blocks.md](custom-blocks.md)) but that app's compiled bundle has no extractable ng-model/data-testid for it in this repo. |
| Default negation (no override) | Each block's `@OppositeBlock` Java annotation | **No** — compiled into the block's snippet code, not runtime-configurable. |

## Why there's nothing to enumerate in Building blocks

The Building-blocks panel (`SettingsBlocks/views/blocks.html`) has no negation-related control at all —
confirmed by grep across its `BlocksCtrl.js` and `services/BlocksService.js` (no `invert`, `negat`,
`opposite`, or standalone `not` toggle). Long/Short symmetry is instead driven by the **Entry
Symmetry** / **Exit Symmetry** checkboxes on the **Trading directions** panel
(`SettingsWhatToBuild/views/settings/tradingDirections/tradingDirections.html`,
`ng-model="config.entrySymmetry"` / `config.exitSymmetry`, both disabled unless
`config.type == constants.buildStrategyDirections.both`) — those checkboxes turn symmetric generation
on/off; they do not expose the negation mapping itself.

If a UI test needs to exercise this feature end-to-end, it has to go through the file system (creating
`user/settings/OppositeBlocks.csv`) plus a restart, not through any web control.

## Related

- Prose page: [../oppositeblocks.md](../oppositeblocks.md)
- Fields hub: [README.md](README.md)
- Parent panel: [../building-blocks.md](../building-blocks.md)
- Per-custom-block opposite field: [custom-blocks.md](custom-blocks.md)
- Symmetry checkboxes (related but distinct control): see Trading directions panel in
  `internal/plugins/SettingsWhatToBuild/views/settings/tradingDirections/tradingDirections.html`
