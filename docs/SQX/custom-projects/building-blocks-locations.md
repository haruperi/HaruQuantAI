# Where building blocks live

Building blocks exist in **three places** with three different roles. Confusing them is the most
common mistake when editing block-related configuration by hand.

## 1. The built-in catalog — Snippets (source of truth for what CAN exist)

`internal/extend/Snippets/SQ/Blocks/<Category>/*.java` (+ user additions in
`user/extend/Snippets/SQ/Blocks/`) — annotated Java classes (`@BuildingBlock`, `@Parameter`,
`@ParameterSet`, `@OppositeBlock`), compiled at startup by SnippetsCompiler into `Snippets.jar`
and registered in the `Blocks` singleton. **A block's identity everywhere else is this class's
simple name** (`RSICrossUp`) or a dotted family path (`Indicators.RSI`,
`Stop/Limit Price Levels.Highest`).

Catalog reference: [`../overview/snippets/building-blocks/`](../overview/snippets/building-blocks/README.md) ·
dev internals: [`../onboard/04-builder/05-blocks-catalog.md`](../onboard/04-builder/05-blocks-catalog.md).

## 2. Per-task selection — the `<Blocks>` section of a Build task (what IS USED in a build)

Inside `Build-Task<N>.xml` (in `project.cfx`): `<Blocks><BuildingBlocks><Block key="…" use="…"
weight="…">` — which blocks the generator may pick, with parameter generation ranges. This is what
the Builder's Building Blocks tab edits, and the style lever described in
[strategy-styles.md](strategy-styles.md). Shipped defaults:
`internal/plugins/TaskBuild/task_forex.xml` and the style templates in
`internal/web/BUILDER/simpleTemplates/*.xml`.

## 3. AlgoWizard custom blocks — `user/settings/` (user-created blocks)

Custom blocks built visually in the **AlgoWizard editor** (the web app deployed at
`internal/web/AlgoWizard/` — see [`../algowizard-integration/`](../algowizard-integration/README.md))
are NOT Java snippets. They are stored as XML in the user's settings folder (paths from
`SQPaths.java`):

| File | Constant | Content |
|---|---|---|
| `user/settings/customBlocks.xml` | `algoWizardCustomBlocksPath` | The custom block definitions. Managed by `CustomBlocks` (`SQAppLib/…/blocks/CustomBlocks.java`); served/edited through `AlgoWizardServlet` (`customBlocksXML` payloads). Timestamped backups are kept next to it (up to 50). |
| `user/settings/blockGroups.xml` | `algoWizardBlockGroupsPath` | Block/random groups (`RandomGroups`), served as `blockGroupsXML`. |
| `user/settings/customDataIndys.xml` | `algoWizardCustomDataIndysPath` | Custom data indicators. |

How they meet the Builder:

- Custom blocks get keys prefixed **`CBlock_`** and appear in the Build task's
  `<Blocks><BuildingBlocks>` like any other block
  (`<Block key="CBlock_MySignal" use="true" …>`).
- On every settings load, `BlocksSettingsPlugin.fixCustomBlocks()` reconciles the task's
  `CBlock_*` entries against `user/settings/customBlocks.xml` (parameters may have changed in
  AlgoWizard since the task was saved).
- A project that uses custom blocks also carries them in the task's
  `<Resources><CustomBlocks>` element, so the project stays portable to a machine where the
  block isn't installed.

## File formats (for the AI tools)

- **customBlocks.xml** — root `<CustomBlocks>`, one `<Item name="…" key="CBlock_…">` per block,
  each with a `<Contents>` child holding the block definition the AlgoWizard editor produced.
  In-memory model: `CustomBlocks` (load/save/findByKey/findByName).
- **blockGroups.xml** — root `<Groups>` (legacy files may say `<RandomGroups>` — normalized on
  load), `<Group id="…" name="…">` children. In-memory model: `RandomGroups`.
- Both `save()` paths keep **50 timestamped backups** next to the file and push a refresh message
  to the Builder/TaskManager UIs, so a programmatic edit behaves exactly like an editor edit.

## Practical rules for config authors (and the AI skill)

1. Never invent a `key` — it must exist in the Snippets registry (built-ins) or in
   `user/settings/customBlocks.xml` (`CBlock_*`).
2. When enabling custom blocks in a Build task, verify the block exists first:
   `get_custom_blocks()` lists them (name, key, empty flag); `get_custom_blocks(name)` returns
   one block's XML.
3. Change these files ONLY through the dedicated tools — `update_custom_blocks(xml, name?)`
   (single-block upsert or whole-document replace) and `update_block_groups(xml)`. They reuse the
   AlgoWizard save path (backups + live Builder refresh); raw `write_file` on both files is
   refused by the sandbox.
4. The AlgoWizard editor app folder (`internal/web/AlgoWizard/`) holds the editor itself and its
   assets (`assets/InitialStrategy.xml`, `examples/*.sqx`), not the user's blocks — those are
   always in `user/settings/`.
