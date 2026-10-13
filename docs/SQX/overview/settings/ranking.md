# Ranking — settings tab
> Defines the fitness that scores every generated strategy, the filters that discard bad ones, how many are kept in the databank, and when the build stops.

**Field-level controls (for UI tests):** [fields/ranking.md](fields/ranking.md)

**Applies to:** Build & Optimize.

## What it configures

When a strategy is generated it is backtested, and the result is used to compute its
**Fitness** — a number from 0 to 1 reflecting the strategy's "quality" for the criteria you
choose. This panel controls how that fitness is computed, which strategies are kept versus
thrown away, how many top strategies the databank holds, and the stop condition for the
build. In genetic mode the same fitness also drives which candidates survive and reproduce.

## Main options

- **Databank options**
  - **Maximum strategies to store in databank** — how many top strategies are remembered
    (e.g. top 100 or top 1000); once full, weaker strategies are replaced by better ones.
  - **Stop generation when** — the stop condition: terminate the build when the databank is
    full, or keep running until stopped manually. (Random generation otherwise runs until
    stopped; genetic evolution ends when its generations are exhausted or improvement
    stalls.)
- **Strategy quality ranking (fitness)**
  - **Use (main data backtest / cross checks / portfolio)** — from which results the fitness
    is computed. Portfolio (the sum of all trades across all symbols) is generally
    recommended when additional data is used; with no additional data it falls back to main
    data automatically.
  - **Determine best strategies by** — the Strategy Selection Criteria. Pick a predefined
    criterion (e.g. Profit Factor, Return/Drawdown, Net Profit) or build a custom fitness
    function combining several criteria, each with its own weight. Combining too many
    criteria can make them "fight" each other, so keep it focused.
- **Strategy filtering conditions** — rules that throw away strategies with bad properties:
  - **Automatic filters** — dismiss obviously invalid strategies (0 trades, no profit, no
    filled orders, etc.).
  - **Custom filters** — your own threshold rules; a strategy matching any of them is
    dismissed (e.g. too few trades, resulting in a loss). Separate values can be set for
    In-Sample and Out-of-Sample performance, and for Robustness Tests or Portfolio results.
    Abbreviations: **IS** (In Sample), **OOS** (Out of Sample), **RT** (Robustness Tests),
    **P** (Portfolio). Conditions can be evaluated in Money, Percent or Pips, for long, short
    or both directions.

## How it affects generation

Ranking is what tells the Builder which strategies are "good." The fitness criteria decide
the ordering of the databank and, in genetic mode, which individuals are selected for
crossover and mutation — so a poorly chosen fitness steers the whole search in the wrong
direction. The filtering conditions act as hard gates: strategies failing them never enter
the databank, keeping it clean and preventing the search from wasting slots on junk. The
databank size and stop condition determine how long the build runs and how large a pool of
survivors you end up with.

## Related

- Settings index: [README.md](README.md)
- Parent: [../builder.md](../builder.md) · [../optimizer.md](../optimizer.md)
- Concepts (fitness/ranking, key performance metrics, databank): [../concepts.md](../concepts.md)
- Robustness tests that can feed the fitness/filters: [cross-checks.md](cross-checks.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [building-blocks.md](building-blocks.md) · [data.md](data.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
