# Multiple orders to the same direction — reference
> Explains why StrategyQuant doesn't generate multiple same-direction entries by default, and the platform limits if you add them manually.

**Field-level controls (for UI tests):** [fields/multi-orders.md](fields/multi-orders.md)

**Applies to:** manual strategy building / editing the default strategy template in AlgoWizard (not a generator setting).

## What it configures

This topic relates to manually creating a strategy or editing the default strategy template in
AlgoWizard. By default StrategyQuant **does not** use multiple orders to the same direction in one
strategy, but you can add several `EnterAtMarket` or `EnterAtStop`/`EnterAtLimit` actions to a
strategy yourself in the AlgoWizard editor. The reason it isn't used automatically is that it is
complicated to make work correctly and is not fully supported on all trading platforms.

## Main options

- **MetaTrader 4/5** — uses **MagicNumbers** to uniquely identify orders. Multiple same-direction
  entries work correctly **only if each `EnterAtXXX` order uses a unique MagicNumber**. If they share
  a MagicNumber, the EA cannot tell which order an exit belongs to, so exits are applied to all orders
  and behave incorrectly.
- **TradeStation / MultiCharts** — **does not** support multiple independent same-direction orders
  with independent exits. You can name an entry, but exits cannot be managed independently per entry,
  so exits of different orders in the same direction are applied to all of them. Avoid multiple
  same-direction entries here unless you know exactly what you are doing.
- **Scaling In** — opening multiple orders in the same direction. This is a feature planned for later
  builds with special handling to manage the platform restrictions above.

## How it affects generation

The generator keeps strategies to a single order per direction to guarantee correct, portable exit
behavior across platforms. If you add multiple same-direction entries manually, the behavior depends
entirely on the target platform's order model — correct on MetaTrader with unique MagicNumbers, but
unreliable on TradeStation/MultiCharts — so this is a manual, advanced technique rather than something
the Builder produces on its own.

## Related

- Settings index: [README.md](README.md)
- Multiple / scale-out exits (the exit-side counterpart): [multiple-exits.md](multiple-exits.md) · [atm.md](atm.md)
- The AlgoWizard editor: [../algowizard.md](../algowizard.md)
- Order sizing: [money-management.md](money-management.md)
- Concepts (order types, entries/exits, platform code): [../concepts.md](../concepts.md)
