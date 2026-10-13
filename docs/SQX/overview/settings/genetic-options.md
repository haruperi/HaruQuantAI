# Genetic options — Builder settings panel
> Tunes the genetic evolution engine — how large the population is, how many generations it runs, and how individuals are mixed, mutated, migrated and refreshed.

**Field-level controls (for UI tests):** [fields/genetic-options.md](fields/genetic-options.md)

## What it configures

This panel controls the parameters of **genetic evolution**, the guided build mode where
strategies are treated as individuals in a population that is bred and mutated over
successive generations toward better fitness. The panel is only visible when the build mode
in **What to build** is set to **Genetic evolution** — it has no effect in Random
generation mode. Here you decide how big the population is, how long it evolves, how genetic
operators behave, whether to use islands, where the starting population comes from, and how
the engine keeps the population diverse and avoids stagnation.

## Main options

- **Max # of Generations** — how many generations the population is evolved for. Typical
  values are 5–100; very high counts rarely help — restarting from scratch is usually better.
- **Population size** — number of strategies on a single island (typical 10–100+). With more
  than one island the total population is `islands × population size`, so keep it reasonable.
- **Crossover and Mutation probability** — the probability of the basic genetic operations.
  Raising mutation tends to produce more diverse strategies.
- **Islands** — the number of separate, independently evolving sub-populations. Islands run
  in isolation with occasional migration between them; 1–10 is the recommended range.
- **Migrate every Xth generation** — how often individuals migrate between islands. Migration
  can "unlock" an island stuck in a local minimum; too-frequent migration loses island
  diversity (around every 10 generations is a sensible default).
- **Population migration rate** — how many strategies migrate at each migration event
  (roughly 1–5 individuals; use a higher % for small populations, a lower % for large ones).
- **Use strategies from Initial population databank** — seeds evolution from existing
  strategies loaded into a separate *Initial population* databank instead of a purely random
  start; any shortfall is filled with randomly generated strategies. This seed population is
  **not** run through the initial-population filter.
- **Generated decimation coefficient** — generate this many times more initial strategies
  than needed and keep only the best (e.g. `3` = 3× oversampling). Improves initial-population
  quality but greatly increases the time before evolution starts.
- **Filter generated initial population** — a light filter for the randomly generated initial
  generation. Keep it lenient (filtering only e.g. by minimum number of trades) — evolution
  should be able to improve a weak population, so an over-strict filter is counterproductive.
- **Start again when finished** — automatically restart the whole build when it finishes, so
  it keeps evolving new populations autonomously until you stop it.
- **Restart evolution fitness if…** — restart evolution when overall fitness stagnates
  (the population as a whole stops improving).
- **Detect same strategies and replace them** ("fresh blood") — each generation, detect
  duplicate strategies and replace them with newly generated ones to keep diversity.
- **Replace X % of the weakest strategies** — replace the worst strategies each generation
  with freshly generated ones.
- **Show last generation databank** — displays a databank with the current generation (first
  island only) for inspection.

## How it affects generation

These settings shape the search itself, not the strategies' trading behaviour. Population
size and generation count set how much of the enormous strategy space is explored;
crossover/mutation rates balance exploiting good solutions against exploring new ones;
islands plus migration preserve diversity so evolution doesn't collapse into a single local
optimum; and the initial-population, restart and fresh-blood options keep the run productive
by giving it a good start and rescuing it from stagnation. Fitness itself — what "better"
means — is defined on the Ranking panel and evaluated on the In-Sample Training data.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (genetic programming, fitness, data parts): [../concepts.md](../concepts.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [data.md](data.md) · [ranking.md](ranking.md) · [trading-options.md](trading-options.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md) · [../../onboard/04-builder/02-start-flow.md](../../onboard/04-builder/02-start-flow.md)
