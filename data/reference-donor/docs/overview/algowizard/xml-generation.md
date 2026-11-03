# How a strategy XML is generated

> From a template with placeholders to a finished, executable strategy XML.

## What it is

A strategy is **data, not code** — an XML rule tree. Generation is the process of taking a
**template** (a skeleton with random placeholders), filling those placeholders with concrete blocks
drawn from the catalog, and producing a complete `<Strategy>` XML that a runtime interpreter then
executes bar by bar. The same pipeline serves AlgoWizard (manual), the Random Builder, and the
Genetic Builder.

## Inputs

Generation combines three inputs:

- **What to build** — the strategy type, which selects a template.
- **Blocks panel** — the allowed blocks with their weights and the min/max condition count. At task
  start this is converted into a **`ReplacementsConfig`**: per placeholder id, a weighted list of
  candidate blocks.
- **Block catalog** — `config.xml`, parsed by **`BlocksConfig`** (helper `WizardConfigWorker`) into
  `BlockDefinition` objects. See [config-xml.md](config-xml.md).

## 1. Skeleton — pick a template

`StrategyTemplateGenerator` chooses a template based on the strategy type and produces an XML tree
whose generated slots are `<Item key="Random…">` placeholders:

| Strategy type | Template |
|---------------|----------|
| simple / multi-TF | `StrategyStandardTemplateSQ4` |
| improve an existing strategy | `StrategyImproveTemplate` |
| stockpicker | `StrategyStockpickerTemplate` |
| custom | a user XML file |

## 2. Assembly — `StrategyGenerator.generate()`

`StrategyGenerator.generate()` runs a fixed sequence of passes over a **clone** of the template.
The exact order (verified below) is:

1. **`modifyFuzzyPercentage()`** — for `sq4fuzzy` strategies only, randomize the fuzzy true-count.
2. **`findAndReplaceAndOrRndBlocks()`** — resolve template-level random/copied `AND`/`OR` join
   placeholders (distinct from the AND/OR nodes built inside a condition tree, see below).
3. **`findAndReplaceRandomBlocks()`** — for each `Random…` placeholder: select blocks by weight,
   build AND/OR condition trees (honoring the per-chart min/max condition count), and **recurse**
   through nested slots (comparison → value → …). Each generated block is marked `generated="random"`
   with a `randomId`.
4. **`findAndReplaceRandomParameters()`** — for each `Param generate="random"`, draw a value from
   that param's range (int, double, combo choice, …).
5. **`findAndReplaceSameBlocks()`** then **`findAndReplaceNegatedBlocks()`** — resolve `Same…` and
   `Negate…`/`Opposite…` placeholders (long ↔ short symmetry) by copying or negating the block that
   was already generated for the referenced `randomId`.
6. **`fillGeneratedElements()`** then **`findAndReplaceSameOrOppositeParameters()`** — resolve
   per-parameter `generate="same"` / `generate="opposite"` values.
7. **Cleanup** — `deleteMarkedRules()` / `deleteMarkedExits()`, `fixBlocksAndParams()`, fuzzy/formula
   fixers, `StrategyFixer.*` (strip the `generate`/`allowRandom` markers), optionally
   `generateATM()` (ATM exits/sizes, Ultimate-only), `FixStockpickerBlocks.fixSPStrategy()` for the
   Stockpicker engines, and `fixNumberOfExitTypes`.

> Verified against: `StrategyGenerator.generate()` in
> `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/generator/`. The precise, sourced rules for
> each of these passes are in [Generation rules, verified from the Java engine](#generation-rules-verified-from-the-java-engine).

The output is a complete `<Strategy>` XML tree, for example:

```xml
<Strategy>
  <Variables>…</Variables>
  <Signals>
    <EntrySignal id="Main">
      <Rule><Condition key="IsGreater" generated="random" randomId="EntryCondition1">
        <Item key="ADX">…</Item> <Param key="#Period#">14</Param>
      </Condition></Rule>
    </EntrySignal>
    <ExitSignal id="StopLoss">…</ExitSignal>
  </Signals>
  <Orders>… SL/PT …</Orders>
</Strategy>
```

## 3. Execution — `XmlStrategy`

`StrategyBase.createXmlStrategy(elStrategy)` hands the generated XML to `XmlStrategy` — itself a
runtime-compiled snippet. At init it parses the XML **once** into an object tree:

```
StrategyEvent  →  Rule[]  →  IBlock[]
```

Blocks are resolved via `Blocks.getBlockObject(key)`, which maps each `<Item key="…">` to its
compiled snippet class. Per bar, the event tree is evaluated (conditions return true/false, actions
trade). The **same** `XmlStrategy` runs in the backtest and in live trading — only the execution
engine underneath differs.

## Two Builder paths that fill templates

AlgoWizard is the **manual** path to the same XML — you can also hand a template to the Builder via a
"startBuild" action. The Builder has two automated engines:

| Path | Engine → job | Character |
|------|--------------|-----------|
| **Random** | `RandomBuildEngine` → `BuilderJob` | each job independently generates and tests one strategy |
| **Genetic** | `GeneticBuildEngine` → `GPEngine` | genome = `Node` (the XML tree); evolves via mutation/crossover on the tree, preserving `randomId` links |

Because generated blocks keep their `generated="random"` + `randomId` markers (see
[templates-and-placeholders.md](templates-and-placeholders.md)), the genetic engine can locate and
recombine exactly the generated parts of the tree while leaving the skeleton intact.

## Block combination rules (what combines with what)

Not every block may be placed anywhere. Generation (and the AlgoWizard editor) is constrained by
two independent mechanisms: a **rule-Type whitelist** that decides which block *groups* a rule may
contain, and a **type system** (`superType` / `returnType`) that decides how blocks nest inside one
another.

### Rules and their `contains` whitelist

A strategy XML is organized as **Events → Rules → Blocks**. Each rule has a **Type**, and each Type
declares a `contains="…"` whitelist in the master `config.xml` `<Global>` section. That whitelist
restricts which block groups may be placed inside a rule of that Type. The verified rule Types and
their whitelists are:

| Rule Type | Label | `contains` whitelist |
|-----------|-------|----------------------|
| `Signal` | Signals | `MainComparisons,IndyComparisons` |
| `SignalFuzzy` | Fuzzy logic signal | `MainComparisons,IndyComparisons` |
| `IfThen` | If - Then | `MainComparisons,IndyComparisons,TradeActions,VariableActions,LogActions` (in the order/action context: `CreateOrder,ModifyOrder,CloseOrder,VariableActions,LoggingMessaging`) |
| `IfThenElse` | If - Then - Else | similar to `IfThen` |
| `ForEachTrade` | For Each Trade | `MainComparisons,IndyComparisons,TradeActions,VariableActions,LogActions,TradeComparisons` |
| `ActionOnly` | Action only | `CreateOrder,ModifyOrder,CloseOrder,VariableActions,LoggingMessaging` |

For example, a `Signal` rule's whitelist looks like this in the config:

```xml
<Type key="Signal" name="Signals" contains="MainComparisons,IndyComparisons" />
```

What this buys us:

- A **Signal rule** accepts only comparisons/conditions (`MainComparisons,IndyComparisons`) — no
  actions. This is exactly what stops, for example, an "open order" action from being placed inside
  a Signal: order actions live in the `CreateOrder` group, which is not in the Signal whitelist.
- An **Action-only rule** accepts only order/variable/logging actions
  (`CreateOrder,ModifyOrder,CloseOrder,VariableActions,LoggingMessaging`) — no comparisons.
- **If-Then / If-Then-Else / For-Each-Trade** accept both conditions and actions, so they can test
  something and then act on it in the same rule.

### Nesting by type: `superType` and `returnType`

Within a rule, blocks nest according to a type system. Every block carries:

- a **`superType`** — one of `condition`, `value`, `action`; and
- a **`returnType`** — the value kind the block yields. The most common return types in the catalog
  are `boolean` (~480 blocks), `number` (~148), `price` (~75), `pricenumber` (~37), plus `none`,
  `pricerange`, and `order`.

A parameter slot expects a particular type and only accepts a child block whose `returnType`
matches. For instance a comparison's `#Value#` slot expects a `number`/`value`-returning block (an
indicator), while the comparison itself returns `boolean`, so the comparison can legitimately sit
inside a Signal (which wants `boolean` conditions).

This is what produces the recursion:

```
Condition
  └─ Comparison            (superType=condition, returnType=boolean)
       ├─ Value / Indicator (superType=value, returnType=number/price)
       └─ Value / Indicator (superType=value, returnType=number/price)
```

Each operand of a comparison is itself a value/indicator block, and those can in turn have their own
value slots — so the tree grows downward as **indicator → comparison → value**. This is exactly the
recursion `StrategyGenerator.findAndReplaceRandomBlocks()` builds when it fills a `Random`
placeholder: it picks a comparison, then fills that comparison's value slots with indicator/value
blocks whose `returnType` fits.

## Where blocks are added (the palette categories per tab)

In AlgoWizard, blocks are added into rule tabs from a **palette**, grouped into categories. The tab's
rule Type — and therefore its `contains` whitelist — determines which categories are offered.

- **Block (condition/value) categories:** Signals, CandlePatterns, BarAndTime, StrategyControl,
  Comparisons, Other, Functions, Price, Indicators, Random Conditions, Random Values, Custom blocks.
- **Action categories:** Close, OtherActions, Modify, Open, RandomActions.

So a Signal tab surfaces the comparison/indicator/value categories but not the action categories,
mirroring the `MainComparisons,IndyComparisons` whitelist; an Action-only tab surfaces the action
categories (Open, Close, Modify, …).

## Parameters

Each block `<Item>` carries one or more `<Param>` elements. The full attribute reference lives in
[config-xml.md](config-xml.md); in brief each param has:

- `key` — the `#Name#` token substituted into the snippet/template;
- `type` — `int` / `double` / `boolean` / `string` / `value` / `data` / `none`;
- `controlType` — how the editor renders it: `jspinnerVar`, `comboVar`, `dataVar`, `value`,
  `randomId`, `randomGroupId`, `SLPT`, `Price`, `Size`, …;
- `defaultValue`;
- editor ranges `minValue` / `maxValue` / `step`;
- generator ranges `builderMinValue` / `builderMaxValue` / `builderStep` and
  `genMinValue` / `genMaxValue`;
- `paramType` — e.g. `shift` or `symbol`.

During generation, each `generate="random"` param is drawn from these ranges. Note the actual
precedence (verified in `BlockParameter.initializeRanges()`): generation **starts** from the editor
`minValue`/`maxValue`/`step`, then **narrows** them with `builderMinValue`/`builderMaxValue`
(a `builderMinValue` only applies when it is *higher* than `minValue`, a `builderMaxValue` only when
it is *lower* than `maxValue`), and finally `genMinValue`/`genMaxValue`. `step` is replaced outright
by `builderStep`, then `genStep` if present. So — contrary to a common assumption — the builder/gen
range is a **subset of (or equal to)** the editor range, not a wider one; a `randomValue` attribute,
if present, overrides all of this. See the verified detail below.

## Generation rules, verified from the Java engine

Everything below was read directly from the generator sources under
`projects/libs/SQAppLib/src/com/strategyquant/tradinglib/`. Where the summary above simplified
something, the correction is noted here.

### Setup: template + replacements + catalog

`StrategyGenerator`'s constructor wires three things together before any generation runs:

- `BlocksConfig.getConfig()` loads the catalog **once** (a lazy singleton) from
  `SQPaths.wizardConfigPath` and parses every `<Item>` into a `BlockDefinition` (key, `superType`,
  `returnType`, `categoryType`, parameters). A block whose `categoryType="randomBlock"` is skipped
  (those are the placeholders themselves).
- The Blocks panel XML becomes a `ReplacementsConfig` — a `HashMap<identification → ReplacementConfig>`.
  Each `ReplacementConfig` holds the weighted candidate list for one placeholder id.
- `checkConfig()` then asserts that **every** `randomId` used in the template has a matching
  `ReplacementConfig`, and that every `Same`/`Opposite` id points at a real random id — otherwise
  generation throws before it starts.

> Verified against: `StrategyGenerator(...)` constructor, `checkConfig()`, and
> `BlocksConfig.getConfig()/parseBlocks()`.

### Exact pass order in `generate()`

`generate()` clones the template and runs these passes in this order (source line order):

1. `modifyFuzzyPercentage()` — only when `architecture == "sq4fuzzy"`; delegates to
   `StrategyStandardTemplateSQ4Fuzzy.ramdomizeFuzzyPercentags(...)` with `fuzzyMinTrue`/`fuzzyMaxTrue`
   (build-settings defaults **60 / 80**).
2. `findAndReplaceAndOrRndBlocks()` — resolves template-level `AND`/`OR` **join** placeholders
   (`RandomAndOr.Random` → `"random"`, `RandomAndOr.Copied` → `"copied"`). This is separate from the
   AND/OR nodes built inside a condition tree (pass 4).
3. `findAndReplaceRandomBlocks(…, RulePart.Unknown)` — the main block generator (details below).
4. `findAndReplaceRandomParameters(…, RulePart.Unknown, RuleType.Unknown)` — fills each
   `Param generate="random"`.
5. `findAndReplaceSameBlocks()` — resolves `Same…` placeholders.
6. `findAndReplaceNegatedBlocks()` — resolves `Negate…`/`Opposite…` placeholders.
7. `fillGeneratedElements()` — indexes any remaining generated `Item`s by `randomId` into the
   `generatedElements` map so later same/opposite passes can find them.
8. `findAndReplaceSameOrOppositeParameters()` — per-parameter `generate="same"` / `generate="opposite"`.
9. `deleteMarkedRules()` then `deleteMarkedExits()` — remove rules/exits tagged `<DeleteRule>`
   (a Signal rule is **not** deleted; its signal is replaced with a `Boolean=false` block instead;
   `deleteMarkedExits()` runs only for the Stockpicker engines).
10. `fixBlocksAndParams()` — re-stamps `categoryType`/`returnType` from the `BlockDefinition`, prunes
    unused action params, and trims trailing `.00` from numeric params.
11. Fuzzy/formula/custom-data fixers: `fixFuzzySignalRuleConditions()`, `FixUnusedDependentFormulas.fix()`,
    `fixValuesInCDataIndy()`, `fixIsFormula()`, `addCustomBlocksData()`.
12. `StrategyFixer.setCurrentVersion()`, `removeAllowRandom()`, `removeRandomGenerateAttributes()` —
    strip the generation-only markers.
13. `generateATM()` — adds an `<ATMs>` element; **guarded to Ultimate license** (logs and skips
    otherwise).
14. `FixStockpickerBlocks.fixSPStrategy()` — Stockpicker-only fixups.
15. `fixNumberOfExitTypes.fixStrategy()`.

> Verified against: `StrategyGenerator.generate()` (lines ~123–197).
> Note: same/negated **blocks** (passes 5–6) are resolved first; only afterwards does
> `fillGeneratedElements()` (7) index the remaining generated items so the same/opposite
> **parameter** pass (8) can copy or negate individual `<Param>` values.

### How a placeholder becomes a block

For every `<Item key="Random…">`, `findAndReplaceRandomBlocks()` looks up its `ReplacementConfig` and:

1. **Probability gate.** `shouldGenerate(rng)` returns `rng.probability(probability)`, where
   `probability = <probability attr, default 100> / 100`. If it fails and `deleteRule` is set, the
   slot becomes a `<DeleteRule>` marker; otherwise the placeholder is simply removed.
2. **Route by super-type.** A `Condition` placeholder goes to `generateRandomConditionBlock()`
   (builds a whole AND/OR tree); anything else (`Value`, `Comparison`, `Property`, `Action`) goes to
   `generateRandomSimpleBlock()` (a single block).
3. **Weighted pick.** The candidate pool is a `ReplacementBlocks` list; `chooseRandomly()` is a
   **roulette-wheel** by integer `weight`:

   ```java
   int index = rng.nextInt(cummulativeWeight);
   int weight = 0;
   for(ReplacementBlock block : blocks) { weight += block.weight; if(index < weight) return block; }
   ```

   Each block's `weight` is read straight from the config (`Integer.parseInt(elBlock.getAttributeValue("weight"))`).
   In the Blocks settings panel the default weight is **10 for Signal blocks and 1 for everything else**
   (`BlocksServlet`).
4. **Recursion brake.** If `currentDepth > 5` and the pool contains blocks with no `Block` children,
   selection is restricted to those childless blocks so the tree terminates; `currentDepth > 10`
   throws. There is also a **retry loop** (up to 1000 for a block, 100 for a boolean super-type):
   a candidate is discarded and re-drawn if `checkersList.check(elBlock)` rejects it.

Property/Comparison placeholders are patched in place (their attributes are applied to the existing
`<Item>`) rather than swapped wholesale, so the sub-value tree the template already carries is kept.
Every generated block is stamped `generated="random"` and `randomId="<id>"`.

> Verified against: `ReplacementConfig.generateRandomBlock()/shouldGenerate()`,
> `ReplacementBlocks.chooseRandomly()/choose()`, and `StrategyGenerator.findAndReplaceRandomBlocks()`.

### Condition trees: how many conditions, and AND vs OR

`generateRandomConditionBlock()` decides a **conditions-to-generate count per chart** from that
chart's `minConditions`/`maxConditions` (or `minExitConditions`/`maxExitConditions` when the rule is
an Exit — the rule type is recognized from parent `signal`/`Rule` names by
`RuleType.recognizeRuleTypeFromParents()`):

- `min == max` → that fixed count.
- otherwise `getConditionsToGenerate()` biases **toward the minimum on a logarithmic scale**: it sums
  `2^i` over the range width, draws a uniform index into that sum, and returns the count where the
  cumulative crosses — so smaller counts are exponentially more likely. Both bounds are capped at 30.

Then:

- **0** total conditions → `createAlwaysTrue()` (entry) or `createAlwaysFalse()` (exit).
- **1** → a single boolean block, no AND/OR wrapper.
- **>1** → a **left-deep** binary tree of AND/OR `Item`s: it seeds one AND/OR node, adds a boolean
  block, and for each further condition wraps the whole accumulated tree in a *new* AND/OR node
  (`elAndOr.addContent(elGenerated); elGenerated = elAndOr;`).

Each AND-vs-OR choice is an independent weighted coin:

```java
int index = rng.nextInt(andWeight + orWeight);
if(index < andWeight) return "AND";
return "OR";
```

`andWeight`/`orWeight` come from the placeholder config and **default to 1 each (50/50)**. Each leaf
boolean block is chosen by `generateBooleanBlock()`, which randomly picks among the available boolean
super-types present in the pool (`Comparison`, `Condition`, `Property`) with up to 100 verification
retries.

> Verified against: `ReplacementConfig.generateRandomConditionBlock()`, `getConditionsToGenerate()`,
> `getAndOrNameByWeight()`, `generateBooleanBlock()`; `RuleType`.

### Type constraints and the indicator → comparison → value recursion

Slot filling is filtered by `createReplacementBlocks(superType, returnType, isFirstValue, …)`:

- a candidate must have `block.blockDef.superType == superType`;
- if a `returnType` is requested (`> 0`), the block's `returnType` must match it;
- its `#Chart#` param must be compatible with the target chart index (`checkChartGeneration()`).

The comparison operand recursion lives in `addValueParamInComparison()`:

- the **first** value operand is drawn from the `Value` pool with `isFirstValue = true`, which
  **excludes blocks flagged `notFirstValue`** (e.g. a bare `Number` can't be the left side);
- the **second** operand is drawn with `returnType = leftValueBlock.returnType`, so both operands of a
  comparison must return the **same** value kind;
- special case: if the left operand is an indicator and the right is `Number`,
  `generatorIndicatorComparisonValue()` draws the number from the *left indicator's* own
  `indicatorMin/indicatorMax/indicatorStep` range, so the constant is meaningful for that indicator.

A `Property` or `Value` block's own `#Indicator#` slot recurses via
`generateRandomBlock(BlockSuperTypes.Value, …)`. Note one structural rule set at parse time:
`BlockDefinition.parseParameters()` **re-classifies a `Comparison` that has exactly one value
parameter as a `Property`** — that is what distinguishes single-operand tests (IsRising, IsAbove-style)
from two-operand comparisons in the recursion.

> Verified against: `ReplacementConfig.createReplacementBlocks()`, `addValueParamInComparison()`,
> `generatorIndicatorComparisonValue()`, `addValueParam()`; `BlockDefinition.parseParameters()`.

### Parameter value drawing

Each parameter carries a `generation` mode — `Fixed`, `Random`, or `Formula`.

- **Fixed** uses the parsed default (`iDefaultValue`/`dDefaultValue`/`bDefaultValue`); a value that
  isn't numeric marks the param `couldBeVariable`, and if a build-settings variable of that name
  exists the param is emitted as `variable="true"`.
- **Random int/double** (`getIntParam()` / `getDoubleParam()`):
  - `combo` control type → uniformly pick one entry from `values="Name=idx,…"`.
  - if a `randomValue` range is present (per-item override `rvr`, or the param's own `rvConfig`), draw
    from it via `RandomValueConfig`.
  - otherwise, for `jspinnerVar`/`jspinner`: `steps = (max - min) / step + 1;
    value = min + rng.nextInt(steps) * step`. `min`/`max` first pass through `fixValue()`, which
    resolves symbolic bounds (`Value.MinPeriod`/`MaxPeriod` → the chart's period range;
    `MinSL…`/`MaxPT…` → the build-settings SL/PT bounds).
  - `#TimeFrom#`/`#TimeTo#` are special-cased to an `HHMM` integer.
  - boolean params flip 50/50 (`rng.nextInt(2)`); `data` params emit the chart index; string params are
    left empty.
- **Ranges are a subset of the editor range**, confirming the note in [Parameters](#parameters):
  `BlockParameter.initializeRanges()` starts from `minValue`/`maxValue`/`step`, then applies
  `builderMinValue` **only if higher** than `minValue`, `builderMaxValue` **only if lower** than
  `maxValue`, then `genMinValue`/`genMaxValue` (which also apply when they are "predefined" symbolic
  constants); `step` is replaced outright by `builderStep`, then `genStep`. A `randomValue` attribute
  builds an `rvConfig` that overrides all of this.
- **`randomValue` formats** (`RandomValueConfig.parseRandomValue()`): new form `min:max` or
  `min:max:step` (colon-separated); legacy form `min-max` or `min-max;step`; or a bare fixed value.
  Decimal count is inferred from the operand scales, capped at 6.
- **Formulas** (SL/PT exits) are generated last and in dependency order: the `#ProfitTarget#` formula
  first, then non-dependent formulas, then dependent ones; `fixParametersOrder()` restores XML order
  afterwards. When `LimitSLPTRRR` is enabled, StopLoss/trailing values are bounded relative to the
  already-drawn ProfitTarget via the RRR coefficients. A formula is set-vs-`none` by
  `formulaProbability` (default 0.5), and among real values chosen by weight.

> Verified against: `ReplacementParameter.getIntParam()/getDoubleParam()/addBooleanParam()`,
> `BlockParameter.initializeRanges()/recognizeDecimals()`, `RandomValueConfig.parseRandomValue()`,
> `ReplacementConfig.generateBlockParameters()/generateProfitTargetParam()`.

### Same, Negated / Opposite (long ↔ short symmetry)

The generator keeps `generatedElements`, a `HashMap<randomId → generated Element>`, so copies and
negations reuse the exact block that was generated for the referenced id:

- **`Same…`** (`findAndReplaceSameBlocks()`): clone `generatedElements.get(id)`, mark
  `generated="same"`. If the referenced block was deleted, the copy becomes a `<DeleteRule>` too.
- **`Negate…`/`Opposite…`** (`findAndReplaceNegatedBlocks()`): rebuild the source as an `IBlock` via
  `Blocks.getBlockObject(...)`, then `replacements.negateBlock(block)` produces the opposite; the result
  is cached under `"_Negated_" + id`, stamped `generated="negated"`, and keeps the original
  `returnType`. If the source id was never generated, the placeholder is removed.
- **Per-parameter** `generate="same"` copies a single param from the stored block;
  `generate="opposite"` negates on demand (reusing the `_Negated_` cache). There is an explicit fix
  for `#Price#` when a market vs stop/limit mismatch means the negated block has no price param.

Negation itself is pluggable: `Negaters` loads user-extensible `Negater` snippet classes (the
`@OppositeBlock` mechanism) sorted by order into a `NegatersList`; `negateBlock()` just delegates to
`NegatersList.negate(block, strategy)`. This is how a long entry rule is turned into the mirror-image
short rule while preserving the `randomId` link.

> Verified against: `StrategyGenerator.findAndReplaceSameBlocks()`, `findAndReplaceNegatedBlocks()`,
> `findAndReplaceSameOrOppositeParameters()`; `ReplacementsConfig.negateBlock()`; `Negaters`.

### Stockpicker & ATM fixups

- `generateATM()` calls `atmGenerateConfig.generate(rng)` and appends an `<ATMs>` element, but only
  under an Ultimate license — otherwise it logs and returns.
- `FixStockpickerBlocks.fixSPStrategy()` runs only when the strategy `engine` is `Stockpicker` or
  `StockpickerSingleAsset`. It walks every `Item` and fixes TA-Lib block params, and forces the
  `#Shift#` of daily/weekly/monthly `Open/High/Low/Close` blocks to be **≥ 1** (a shift of `0` is
  rewritten to `1`) — but only for blocks that were actually `generated`, leaving template blocks
  untouched.

> Verified against: `StrategyGenerator.generateATM()`; `FixStockpickerBlocks.fixSPStrategy()/
> fixDWMBlockShift()`.

### Template selection (correction)

`StrategyTemplateGenerator.generate()` chooses the skeleton by **strategy type *and* engine**, which
is more nuanced than the table in [1. Skeleton](#1-skeleton--pick-a-template):

- `simple` / `multi-tf`: `Stockpicker` engine → `StrategyStockpickerTemplate`;
  `StockpickerSingleAsset` → `StrategyStockpickerSingleAssetTemplate`; otherwise by architecture —
  `sq3` → `StrategyStandardTemplateSQ3`, `sq4` → `StrategyStandardTemplateSQ4`, `sq4fuzzy` →
  `StrategyStandardTemplateSQ4Fuzzy`.
- `improve`: architecture is *detected* from the existing strategy's first rule type
  (`Signal` → sq4, `SignalFuzzy` → sq4fuzzy, else sq3) and then `StrategyImproveTemplateSQ3`/`SQ4`
  is used. Improver is not implemented for Stockpicker engines.
- `template`: load the user file (`.sqw` / `.sqx` / `.sq4`) and normalize it (`fixXmlns`,
  `fixCharts`, `fixRandomGroups`, `fixGeneratedBlocks`).

> Verified against: `StrategyTemplateGenerator.generate()`, `recognizeArchitectureFromStrategy()`,
> `getConfiguredTemplate()`.

### `forEngine` (not confirmed in the generator)

The block pool the panel offers per engine is filtered by a `forEngine` attribute that **defaults to
`"*"`** (all engines) — see `WizardConfigWorker` (`XMLUtil.getAttr(itemElem, "forEngine", "*")`). This
filtering happens when building the settings/replacements config, not inside `StrategyGenerator`
itself; the generator only ever sees the already-filtered candidate list.

> Verified against: `WizardConfigWorker.blockToJSON()`. (The generator classes do not read
> `forEngine` directly — not confirmed in the generation engine.)

## Two layers behind every block: Java snippet + engine templates

A block is not a single artifact — it exists in **three** places that must be kept consistent:

1. **Catalog entry** in `config.xml` (`<Item>`) — declares the block, its params, ranges,
   `forEngine` availability, and its `returnType` / `superType`. This is what the editor and the
   generator offer. See [config-xml.md](config-xml.md).
2. **Java snippet** in
   `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/.../<Block>.java` — annotated
   with `@BuildingBlock` / `@Parameter` / `@OppositeBlock` and compiled at runtime. This holds the
   block's **logic**, used for backtesting.
3. **Per-engine FreeMarker template** in
   `work_directory/StrategyQuant/internal/extend/Code/<Engine>/blocks/<Block>.tpl` — how the block
   renders to platform source (MT4 / MT5 / JForex / EasyLanguage / PseudoCode). A block with **no
   `.tpl` for a given engine cannot be exported to it.**

So the catalog decides *whether/where* a block can be used, the Java snippet decides *what it does in
a backtest*, and each engine template decides *how it becomes code* on that platform. See the
per-engine export reference: [../export-engines/README.md](../export-engines/README.md).

## Related

- [AlgoWizard detailed reference (index)](README.md)
- [Strategy templates & random placeholders](templates-and-placeholders.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [Export engines & per-engine templates](../export-engines/README.md)
- [Editor modes](editor-modes.md) · [Engines and platforms](engines-and-platforms.md)
- Concepts: [../concepts.md](../concepts.md) · Builder: [../builder.md](../builder.md)
- Settings: [Building blocks](../settings/building-blocks.md) · [Parameter ranges](../settings/parameter-ranges.md)
- Developer detail: [../../onboard/04-builder/04-strategy-creation.md](../../onboard/04-builder/04-strategy-creation.md) · [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md)
