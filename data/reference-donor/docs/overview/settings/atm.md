# ATM (Advanced Trade Management) — settings tab
> Configures multiple / scale-out exits so a strategy can close a position in parts at different targets.

**Field-level controls (for UI tests):** [fields/atm.md](fields/atm.md)

**Applies to:** Build, Optimize, Retest (shared) — can also be applied to already existing strategies in the Retester.

> Note: in early builds this feature was marked **EXPERIMENTAL** (introduced around Build 130).

## What it configures

ATM enables an easy configuration of **multiple exits** for a strategy. The logic is simple: you
enter the trade, close part of the position quickly on a small profit to cover costs and risk, then
let the rest run to a more distant target (or targets) — now effectively risk-free. This can be done
manually by editing a strategy (code or AlgoWizard), but ATM makes it a simple switch that can even
be applied to existing strategies.

## Main options

- **Enable ATM** — turn multiple exits on, then define your exits and the size constraints.
- **Exits** — define each exit's size (percentage of position) and type. Each exit can use:
  - a multiple of the original **Stop Loss** or **Profit Target** (e.g. 0.5× or 2× the original PT),
  - a fixed profit target,
  - a **trailing stop**, or
  - a **time-based** target by number of bars.
- **ATM size constraints** — tell ATM how to split the position between exits: the number of decimal
  places and the minimum size (e.g. one decimal place, minimum size 0.1). ATM uses only as many exits
  as fit the Money Management size and these constraints — if the computed size cannot be divided
  while keeping every exit at least the minimum size, only the first exit(s) are used.
- **ATM config source** — either use the **ATM saved in the strategy** (if any) or the **ATM settings
  defined on this screen** (in which case they are saved into the strategy). To generate exits
  randomly instead of fixing them, see [multiple-exits.md](multiple-exits.md).

> Important: ATM **overrides all other exits except the Stop Loss**. The strategy will not use its
> original Profit Target, Trailing Stop or Exit-after-X-bars — only the original Stop Loss plus the
> exits you define in ATM.

## How it affects generation

ATM changes how a strategy exits its trades: instead of a single exit, the position is closed in
parts across several targets, which can smooth the equity curve and reduce risk once the first part
is banked. It is not a magic bullet — multiple exits do not always improve a strategy — but on many
strategies a simple ATM configuration can help. Because it can be applied to existing strategies, it
is useful both during a build and as a post-processing step in the Retester.

## Related

- Settings index: [README.md](README.md)
- Generate exits randomly instead of fixing them: [multiple-exits.md](multiple-exits.md)
- Multiple orders to the same direction (scaling in): [multi-orders.md](multi-orders.md)
- Sibling panels: [money-management.md](money-management.md) · [trading-options.md](trading-options.md)
- Concepts (exits, money management, backtest): [../concepts.md](../concepts.md)
- Tasks: [../retester.md](../retester.md) · [../builder.md](../builder.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
