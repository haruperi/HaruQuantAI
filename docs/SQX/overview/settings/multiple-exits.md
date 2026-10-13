# Multiple exits generation (scale-out / ATM) — settings tab
> Generates multiple scale-out exits (ATM) randomly during a build, instead of using a fixed exit configuration.

**Field-level controls (for UI tests):** [fields/multiple-exits.md](fields/multiple-exits.md)

**Applies to:** Build (and Improver) — added in Build 131, **Ultimate edition only**.

## What it configures

Until Build 131, multiple exits for scaling out a trade (ATM, Advanced Trade Management) were
available only as **defined settings** — you specify the exact exit configuration and it is applied
to generated strategies or to existing strategies in the Retester (see [atm.md](atm.md)). This page
covers the Build 131 Ultimate addition: **generating multiple exits randomly** so the build searches
over different exit setups.

## Main options

- **Config source: Generate ATM** — you must switch the ATM config source to **Generate ATM** to see
  this configuration (as opposed to using fixed, defined exits).
- **Exit types to use** — choose which exit types the generator may use and their allowed ranges.
- **Exit scenarios** — exits are not generated fully randomly; you choose from **7** of the most-used
  scenarios that the generator picks from.
- **Use in Improver** — a new **ATM** entry in [Parts to improve](parts-to-improve.md) lets you
  improve only the ATM exits of an existing strategy, leaving the rest intact, or combine ATM
  improvement with improving the entry/exit rules.

## How it affects generation

When generating (or improving) a strategy, a scenario is first chosen randomly from the allowed
scenarios; depending on the scenario, 2 or 3 exits are then generated randomly from the allowed exit
types. This turns the exit structure itself into part of the search space, so the Builder can discover
scale-out configurations you wouldn't have specified by hand — while the scenarios keep the generated
exits within sensible, commonly used patterns rather than pure randomness.

## Related

- Settings index: [README.md](README.md)
- Fixed / defined ATM exits: [atm.md](atm.md)
- Improving only ATM on an existing strategy: [parts-to-improve.md](parts-to-improve.md)
- Multiple orders to the same direction (entries): [multi-orders.md](multi-orders.md)
- Concepts (exits, ATM, generation): [../concepts.md](../concepts.md)
- Tasks: [../builder.md](../builder.md) · [../retester.md](../retester.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
