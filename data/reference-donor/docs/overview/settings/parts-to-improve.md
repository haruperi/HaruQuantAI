# Parts to improve — settings tab
> Chooses which parts of an existing strategy the generator should regenerate, and whether to add to or replace them.

**Field-level controls (for UI tests):** [fields/parts-to-improve.md](fields/parts-to-improve.md)

**Applies to:** Build only — visible only when you chose to improve an existing strategy in [What to build](what-to-build.md).

## What it configures

When you build in "improve an existing strategy" mode, this panel decides **which parts** of the
strategy are worked on and **how**. The generator takes your strategy, recognizes its entry and exit
rules, and then either adds new conditions to them or replaces existing ones with newly generated
conditions, according to your choices here.

## Main options

- **Which parts to improve** — choose any of:
  - **Entry rule**
  - **Exit rule**
  - **Order type**
  - **ATM** — improve only the multiple-exit (scale-out) configuration; see
    [multiple-exits.md](multiple-exits.md).
- **How to modify each part** — for each chosen part, one of:
  - **Add** — add new conditions to the existing ones.
  - **Replace** — delete the existing conditions and generate new ones.
  - **Add or Replace** — randomly decide between Add and Replace.

## How it affects generation

Instead of building strategies from scratch, the generator starts from your strategy and mutates only
the parts you selected, leaving the rest intact — for example, generating and trying different ATM
exits while keeping the entry and exit rules unchanged. This is a quick way to iterate on a strategy
you already like. For a more flexible approach, you can instead open the strategy in AlgoWizard, place
generation placeholders on the parts you want to change, and build from that strategy template — this
produces new strategies based on your original with the placeholders filled by newly generated
conditions or actions.

## Related

- Settings index: [README.md](README.md)
- Prerequisite panel (choose to improve a strategy): [what-to-build.md](what-to-build.md)
- Improve ATM exits: [multiple-exits.md](multiple-exits.md) · [atm.md](atm.md)
- Building the strategy template in AlgoWizard: [../algowizard.md](../algowizard.md)
- Concepts (template placeholders, entry/exit rules): [../concepts.md](../concepts.md)
- Tasks: [../builder.md](../builder.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
