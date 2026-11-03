# config.xml — the available-blocks catalog

> The XML that declares which building blocks and parameters are offered, and with what ranges.

## What it is

`config.xml` is the **block catalog**: it lists the building blocks available to AlgoWizard and the
Builder, their parameters, the control types the editor uses, and the value ranges the generator
draws from.

> **Important caution:** `config.xml` declares *which* blocks and params are offered and *what*
> ranges they use — it does **not** define what a block computes. The computation lives in annotated
> Java snippets (`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/.../*.java`, with
> `@BuildingBlock` / `@Parameter` / `@OppositeBlock`), compiled at runtime and registered by
> `Blocks.java`. There are therefore two layers: **catalog XML** (what is offered) and **snippet
> code** (what it does). See [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md).

## Two files named config.xml

There are two distinct files — do not confuse them:

| File | Size | Role |
|------|------|------|
| `work_directory/StrategyQuant/internal/web/SQWIZARD/branding/global/config.xml` | ~965 KB | **Master catalog.** Parsed by the Java `BlocksConfig`; the authoritative list of available building blocks for **AlgoWizard and the Builder**. |
| `work_directory/StrategyQuant/internal/ctemplate/config.xml` | ~18 KB | **Classic-editor aggregator.** XIncludes sibling `ctemplate/*.xml` files and defines the random-placeholder families plus a short `UsedBlocks` whitelist. |

Both files root as `<StrategyEditor version="2.0">`.

The small `ctemplate/config.xml` pulls in its siblings via XInclude: `events.xml`,
`datasTimeframes.xml`, `moneyManagement.xml`, `parameterSets.xml`, `wizard.xml`.

## Master catalog structure

The master `config.xml` is organized as:

```
<StrategyEditor version="2.0">
  <Global>
    Events        — rule Types (Signal, IfThen, IfThenElse, ForEachTrade, ActionOnly),
                    each with a `contains` whitelist
    Datas
    Timeframes
    Colors
    Engines
    MoneyManagement
    Formulas
    ExitRules
    UsedBlocks
  <ParameterSets>
  <Blocks>
    <Comparisons> <Values> <Conditions> <Actions>
      each holds <Category name= key=>   (e.g. "Bar And Time",
                                           "Custom Indicators" (ci="true"),
                                           "Random Conditions")
        each Category holds <Item>s
  <Wizard>        — guided Steps
```

## `<Item>` attributes

An `<Item>` is one building block. Key attributes:

| Attribute | Meaning |
|-----------|---------|
| `key` | unique block id — equals the snippet class name |
| `name` | display name in the palette |
| `display` | signature shown to the user, with `#Param#` tokens (e.g. `#Indicator# is rising`) |
| `returnType` | `boolean` / `number` / `pricenumber` / `none` |
| `mI` | menu grouping |
| `categoryType` | `operators` / `simpleRules` / `randomBlock` / `other` |
| `customSnippet` | marks a custom snippet block |
| `ignoreInBuilder` | block is hidden from the Builder |
| `generate` | placeholder mode (`random` / `same` / `opposite`) — see [templates-and-placeholders.md](templates-and-placeholders.md) |
| `superType` | broad kind (`condition` / `value` / …) |
| `forEngine` | per-engine availability — codes `SP` / `SA` / `MT4` / `MT5` / `TS` / `MC` / `JF` / `*` (e.g. `*,-SP,-SA` = all engines except Stockpicker and Single-asset) |

## `<Param>` attributes

Each `<Param>` is one editable parameter of a block:

| Attribute | Meaning |
|-----------|---------|
| `key` | the `#Name#` token used in `display` |
| `name` | label |
| `type` | `int` / `double` / `boolean` / `string` / `value` / `data` / `none` |
| `controlType` | UI control: `jspinnerVar` / `booleanVar` / `comboVar` / `dataVar` / `value` / `randomId` / `randomGroupId` / `SLPT` / `Price` / `Size` / `RangeLevel` |
| `defaultValue` | default |
| `minValue` / `maxValue` / `step` | range used in the **editor** |
| `builderMinValue` / `builderMaxValue` / `builderStep` | range used by the **generator** |
| `genMinValue` / `genMaxValue` | generator bounds |
| `paramType` | `shift` or `symbol` |
| `help` | tooltip text |
| `dependentOn` | another param this one depends on |

The split between editor ranges (`minValue`/`maxValue`/`step`) and generator ranges
(`builderMinValue`/`builderMaxValue`/`builderStep`, `genMinValue`/`genMaxValue`) lets the manual
editor allow a wide range while the generator draws from a narrower one. See
[../settings/parameter-ranges.md](../settings/parameter-ranges.md).

## A representative Item

The "Is rising" comparison, trimmed:

```xml
<Item key="IsRising" name="Is rising" display="#Indicator# is rising" returnType="boolean" mI="Comparisons" categoryType="operators">
  <paramCategory name="Properties" expanded="true">
    <Param key="#Bars#" name="Bars rising" type="int" defaultValue="2" controlType="jspinnerVar" minValue="2" maxValue="100" step="1" builderMaxValue="50"/>
    <Param key="#Shift#" name="Shift" type="int" defaultValue="1" controlType="jspinnerVar" minValue="0" maxValue="1000" paramType="shift"/>
  </paramCategory>
  <paramCategory name="Default" expanded="true">
    <Param key="#Indicator#" name="Indicator" type="value" controlType="value"/>
  </paramCategory>
</Item>
```

Params here are grouped into `<paramCategory>` sections. `#Bars#` has a separate `builderMaxValue`
(50) so the generator uses a tighter upper bound than the editor's `maxValue` (100). `#Shift#` is
tagged `paramType="shift"` so it participates in the global Shift range. `#Indicator#` is a nested
value slot (`type="value"`, `controlType="value"`) that another block plugs into.

## Related

- [AlgoWizard detailed reference (index)](README.md)
- [Strategy templates & random placeholders](templates-and-placeholders.md)
- [How a strategy XML is generated](xml-generation.md)
- [Engines and platforms](engines-and-platforms.md) (the `forEngine` filter)
- Settings: [Building blocks](../settings/building-blocks.md) · [Parameter ranges](../settings/parameter-ranges.md) · [Custom blocks](../settings/custom-blocks.md)
- Concepts: [../concepts.md](../concepts.md) · Builder: [../builder.md](../builder.md)
- Developer detail: [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md)
