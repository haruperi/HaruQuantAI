# AlgoWizard — Detailed Reference

**AlgoWizard (AW)** is a standalone visual strategy editor that is integrated into StrategyQuant X
(embedded as a Vue app in an iframe, backed by the `/algowizard/*` servlet). It is the **manual**
way to build or edit a strategy — you assemble the strategy as an XML rule tree by hand, instead of
letting the Builder generate it. AlgoWizard shares the same block catalog, strategy XML model, and
backtest engine as the Builder.

This folder breaks AlgoWizard down in detail. For the short functional summary see the module page
[../algowizard.md](../algowizard.md).

Parent: [AlgoWizard overview](../algowizard.md) · [Overview index](../README.md)
Integration (how the editor, SQX and the AI Chat are wired together):
[`algowizard-integration/`](../../algowizard-integration/README.md)

## Platforms & engines

A strategy targets a **platform** and a **trading engine**:

- **Desktop platform (`SQ`)** — the standard StrategyQuant target. Engines: **MetaTrader 4**,
  **MetaTrader 5 (netted / hedged)**, **Tradestation**, **MultiCharts**, **JForex**.
- **AlgoCloud platform (`CT`, "AC")** — the cloud target. Only two engines:
  **Stockpicker** and **Single-asset cloud strategy**. (Template strategies are not supported on
  AlgoCloud.)

> Note: there is **no engine literally called "Standard" or "AC"** — "Standard" here means the
> ordinary desktop engines, and "AC" means the **AlgoCloud** platform. Which blocks are offered for
> a given engine is controlled by the `forEngine` attribute in [config.xml](config-xml.md).

| Engine / type | Trades | Editor mode | Page |
|---------------|--------|-------------|------|
| **Standard (desktop)** | one symbol on MT4/MT5/TS/MC/JForex | Simple or Full | [engine-standard.md](engine-standard.md) |
| **Stockpicker** | a basket of symbols, ranked & picked | Picker | [engine-stockpicker.md](engine-stockpicker.md) |
| **Single-asset (cloud)** | one symbol on AlgoCloud | Simple | [engine-single-asset.md](engine-single-asset.md) |

Platform/engine background and the `forEngine` filter: [engines-and-platforms.md](engines-and-platforms.md).

## Editor modes

AlgoWizard opens a strategy in one of three editor modes ([editor-modes.md](editor-modes.md)):

- **Simple** — streamlined view; only for "simple-compatible" strategies (the canonical rule set,
  basic actions, no advanced SL features). Single-asset cloud strategies always open here.
- **Full** — the complete editor (arbitrary rules/events, advanced exits, variables).
- **Picker** — Stockpicker-specific (Long / Short / Position Score tabs).

## Rule tabs by engine

- **Standard / Full editor:** **Trading signals**, **Long entry**, **Short entry**, **Long exit**,
  **Short exit** (+ optional **Explore**). See [engine-standard.md](engine-standard.md).
- **Stockpicker / Picker editor:** **Long**, **Short**, **Position Score**. See [engine-stockpicker.md](engine-stockpicker.md).

## Templates, blocks & generation

AlgoWizard edits **strategy templates** — XML rule trees that can contain **random placeholders**
(`RandomCondition` / `RandomValue` / `RandomAction`, plus `Same…` and `Negated/Opposite…` variants)
that the Builder later fills randomly or genetically.

| Topic | Page |
|-------|------|
| Strategy templates & random placeholders | [templates-and-placeholders.md](templates-and-placeholders.md) |
| Custom blocks (build your own reusable block) | [custom-blocks.md](custom-blocks.md) |
| Random groups (per-placeholder block pools) | [random-groups.md](random-groups.md) |
| `config.xml` — the available-blocks catalog & its structure | [config-xml.md](config-xml.md) |
| How a strategy XML is generated (template → blocks → XmlStrategy) | [xml-generation.md](xml-generation.md) |

## Go deeper

- Concepts: [../concepts.md](../concepts.md)
- Builder (the automated counterpart): [../builder.md](../builder.md) · settings: [../settings/README.md](../settings/README.md)
- Export engines (how blocks render to platform code): [../export-engines/README.md](../export-engines/README.md)
- Developer/architecture: [../../onboard/07-algowizard/](../../onboard/07-algowizard/README.md) and
  [../../onboard/04-builder/04-strategy-creation.md](../../onboard/04-builder/04-strategy-creation.md)
