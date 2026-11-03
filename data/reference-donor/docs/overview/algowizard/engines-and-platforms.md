# Platforms & Engines

> How a strategy declares its target platform and trading engine — and how that governs which blocks are available.

## What it configures

Every strategy built in AlgoWizard targets one **platform** and one **trading engine**.
The platform decides *where* the strategy runs; the engine decides *which trading
environment* it is compiled and backtested for. Together they determine the strategy's
capabilities and which building blocks the editor offers.

There is **no engine literally named "Standard" or "AC"**. "Standard" is shorthand for the
ordinary **desktop** engines; "AC" is what users loosely call the **AlgoCloud** platform.

## Platforms

Two platform types exist:

| Platform | Code | What it is |
|----------|------|------------|
| **Desktop** | `SQ` | The standard StrategyQuant desktop target. |
| **AlgoCloud** | `CT` | The cloud target (this is what users call "AC"). |

Conversion from a desktop strategy to a cloud one is done by the helper
`convertStrategyForAC`. AlgoCloud only accepts cloud engine types — attempting to move an
unsupported strategy over produces messages such as:

- *"Only Stockpicker or Single Asset strategies are supported in AlgoCloud"*
- *"Template strategies are not supported in AlgoCloud"*

## Engines

### Desktop (`SQ`) engines

These are the "Standard" (desktop) engines — the `Engines` enum:

- **MetaTrader 4**
- **MetaTrader 5 (netted)**
- **MetaTrader 5 (hedged)**
- **Tradestation**
- **MultiCharts**
- **JForex**

A desktop strategy trades a single symbol on the chosen platform. See
[engine-standard.md](engine-standard.md).

### AlgoCloud (`CT`) engines

The cloud target (`CloudAssetTypes`) exposes exactly two engines:

- **Stockpicker** — a multi-symbol basket that ranks candidates and picks the best. See
  [engine-stockpicker.md](engine-stockpicker.md).
- **Single-asset cloud strategy** — a single symbol on AlgoCloud. See
  [engine-single-asset.md](engine-single-asset.md).

## How the strategy element records this

The strategy element carries attributes that identify its engine and type:

- `engine="…"` — the target trading engine.
- `singleAsset="true"` — marks a single-asset cloud strategy.
- `pickerEditor="true"` — marks a Stockpicker strategy.

## The `forEngine` block filter

Which blocks the editor offers for a given engine is controlled by the `forEngine`
attribute on `<Item>` / `<ExitRule>` entries in the block catalog. It uses short engine
codes:

| Code | Engine |
|------|--------|
| `SP` | Stockpicker |
| `SA` | Single-asset |
| `MT4` | MetaTrader 4 |
| `MT5` | MetaTrader 5 (hedged + netted) |
| `TS` | Tradestation |
| `MC` | MultiCharts |
| `JF` | JForex |
| `*` | all engines |

Examples: `forEngine="*,-SP,-SA"` means *all except the cloud engines*;
`forEngine="SP,SA"` means *cloud engines only*. The full mechanics of the catalog live in
[config-xml.md](config-xml.md).

## Related

- [AlgoWizard reference index](README.md)
- [Standard (desktop) engines](engine-standard.md)
- [Stockpicker engine](engine-stockpicker.md)
- [Single-asset (cloud) engine](engine-single-asset.md)
- [Editor modes](editor-modes.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [AlgoWizard functional overview](../algowizard.md) · [Concepts](../concepts.md)
- [Developer/architecture onboarding](../../onboard/07-algowizard/README.md)
