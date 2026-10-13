# Strategy templates & random placeholders

> A template is a strategy XML tree with special placeholder blocks that StrategyQuant fills in.

## What it is

A **strategy** in StrategyQuant X is an XML rule tree. A **strategy template** is that same tree
with certain parts left unspecified as **random placeholders** — special `<Item>` blocks that
StrategyQuant replaces with concrete blocks during generation. This is what lets you generate
strategies in your own custom "format": you define the skeleton and where the generated logic goes,
and the Builder (or the genetic engine) fills the placeholders.

AlgoWizard is the manual editor for these XML trees — you can build a full strategy by hand, or
leave placeholders in it and hand it to the Builder.

## The three placeholder families

Every placeholder is an `<Item>` with `categoryType="randomBlock"` and a `generate` attribute. The
`generate` value corresponds to the `GenerateTypes` enum: **normal / random / same / opposite**.
There is one placeholder per family for each generate mode:

| Family | Random (`generate="random"`) | Same (`generate="same"`) | Opposite (`generate="opposite"`) |
|--------|------------------------------|--------------------------|----------------------------------|
| **Conditions** | `RandomCondition` | `SameCondition` | `NegatedCondition` |
| **Values** | `RandomValue` | `SameValue` | `OppositeValue` |
| **Actions** | `RandomAction` | `SameAction` | `OppositeAction` |

- **Random** — generate brand-new content here (a condition tree, a value, or an action).
- **Same** — reuse whatever was generated for another placeholder (referenced by its id).
- **Opposite / Negated** — mirror/negate another placeholder for the short side.

## Placeholder parameters

A placeholder carries three parameters that identify and bind it:

- **`#Identification#`** — `controlType="randomId"`, a unique id such as `RandomConditionLong`.
  The `Same`/`Opposite` placeholders point at this id to know what to copy or negate.
- **`#Chart#`** — `controlType="dataVar"`, `defaultValue="Any"` — which chart/data the generated
  block runs on.
- **`#Group#`** — `controlType="randomGroupId"` with `randomGroupType="Conditions|Values|Actions"`
  — binds the placeholder to a **Random group** (a per-placeholder pool of allowed blocks).

A minimal condition placeholder from a template looks like this — note the `randomId` param that
gives it its name:

```xml
<signal>
  <Item returnType="boolean" ignoreInBuilder="true" randomTemplate="true" superType="condition">
    <Param key="#Identification#" name="Identification" type="string" controlType="randomId"></Param>
  </Item>
</signal>
```

A fully-formed value placeholder (from the Stockpicker Position Score template) shows all three
params together:

```xml
<Item key="RandomValue" name="RandomValue" returnType="pricenumber" ignoreInBuilder="true"
      display="RandomValue(#Identification#)" generate="random" superType="value"
      categoryType="randomBlock">
  <Param key="#Identification#" name="Identification" type="string" controlType="randomId">RandomPSValue</Param>
  <Param key="#Chart#" name="Chart" type="data" controlType="dataVar" defaultValue="Any">Any</Param>
  <Param key="#Group#" name="Random group" type="string" controlType="randomGroupId" randomGroupType="Values" />
</Item>
```

## Long ↔ short symmetry (worked example)

The classic use of the placeholder families is long/short symmetry. A template's **Long entry**
uses a `RandomCondition` with id `RandomConditionLong`; the **Short entry** uses a
`NegatedCondition` pointing at that same `RandomConditionLong`. StrategyQuant generates the long
condition and then puts a negated mirror of it in the short slot:

```
SIGNAL – LongEntrySignal:
CCI(14)[1] > 0 and RSI(20)[1] > 50

SIGNAL – ShortEntrySignal:
CCI(14)[1] < 0 and RSI(20)[1] < 50
```

The short side has the opposite comparison operators (`<` "Is Lower" instead of `>` "Is Greater") —
it is the negation of the long side. Exit signals work the same way.

## How RandomCondition content is generated

The condition(s) placed in a `RandomCondition` come from your **Building blocks** selection plus the
generation settings:

- the pool of **building blocks** you enabled (and their weights);
- the **condition count** (min/max number of conditions to combine into an AND/OR tree);
- the **Period** and **Shift** ranges used when drawing block parameters.

See [../settings/building-blocks.md](../settings/building-blocks.md) and
[../settings/parameter-ranges.md](../settings/parameter-ranges.md).

## Skeleton templates on disk

The built-in skeletons live under
`work_directory/StrategyQuant/internal/ctemplate/build/`:

| Folder | Purpose |
|--------|---------|
| `sq4/` | current SQ4 architecture |
| `sq3/` | legacy SQ3 architecture |
| `sp/` | Stockpicker |

Each folder holds the rule fragments assembled into a full template: `template.xml`,
`longentryrule.xml`, `shortentryrule.xml`, `longexitrule.xml`, `shortexitrule.xml`,
`signalentry.xml`, `signalexit.xml` (plus engine-specific variants). The Stockpicker
`template.xml` carries `pickerEditor="true"`, and its `positionscorerulelong.xml` embeds a
`RandomValue` placeholder named `RandomPSValue` (shown above).

## Placeholders in generated output

Once a placeholder is filled, the resulting block is marked `generated="random"` and keeps a
`randomId`. These markers let the genetic engine later find, mutate, and cross over exactly the
generated parts of the XML tree while leaving the fixed skeleton alone.

## Related

- [AlgoWizard detailed reference (index)](README.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [How a strategy XML is generated](xml-generation.md)
- [Editor modes](editor-modes.md) · [Engines and platforms](engines-and-platforms.md)
- Settings: [Building blocks](../settings/building-blocks.md) · [Parameter ranges](../settings/parameter-ranges.md) · [OppositeBlocks](../settings/oppositeblocks.md)
- Concepts: [../concepts.md](../concepts.md) · Builder: [../builder.md](../builder.md)
- Developer detail: [../../onboard/04-builder/04-strategy-creation.md](../../onboard/04-builder/04-strategy-creation.md)
