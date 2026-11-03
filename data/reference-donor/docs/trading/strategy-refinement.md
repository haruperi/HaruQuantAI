# Refining strategies: templates, improvement, exits, parametrization

Between "generate candidates" and "assemble a portfolio" sits a set of SQX tools that let a
trader *shape* and *iterate* strategies instead of taking whatever the generator produces.
All controls below are exercised by the scenario corpus (`tests/ui/scenarios/SQX-Build`,
`SQX-Optimize`, `SQX-AlgoWizard`) and map to catalog refs.

## Strategy styles: how the rules are wired

Before blocks and templates comes the **strategy style** — how the IF-THEN rules are
structured ([concepts → Strategy style](../overview/concepts.md#strategy-style)):

- **SQ3 (old) style** — four independent rules (long/short entry, long/short exit). Simple,
  but long and short conditions firing together conflict.
- **SQ X new style** — one dedicated **Signal rule** computes `LongEntrySignal` /
  `ShortEntrySignal` / exit signals; entry/exit rules then act only on non-conflicting
  combinations (`LongEntrySignal && !ShortEntrySignal && !LongExitSignal`). The default.
- **SQ X with Fuzzy Logic** — the signal becomes a **vote**: N conditions are all evaluated
  and the signal fires when a configured share (e.g. 70 %) is true, no AND/OR chain. Only
  worth it with many sub-conditions (with 10 conditions, "7 of 10 agree" is a genuinely
  different — and more gradual — edge than a strict conjunction).

Style is orthogonal to the *trading* style (mean reversion vs momentum): the trading style
comes from the blocks; this section is about rule plumbing and conflict handling.

## Control the architecture: templates, random groups, custom blocks

A **template** is a strategy skeleton with placeholders the Builder fills randomly:

- **Random condition / Random value** placeholders draw from **random groups** — named pools
  of interchangeable blocks you curate in AlgoWizard. Instead of "any of 401 signal blocks",
  the Builder chooses from *your* shortlist (e.g. only band-reversal entries).
- **Same / Negated / Opposite** placeholders reference an earlier placeholder's identification
  (`RC1`, `RV1`…), which is how you force the short side to mirror or invert the long side.
- **Custom blocks** are your own composite conditions (built visually, with parameters and an
  optional *opposite block*); once imported they appear in Builder → Building blocks like any
  native block, and numeric parameters can be marked **Generate randomly** over `min:max:step`.

This is the precision tool behind the [style pages](README.md): a style page narrows block
*families*; a template + random groups narrows to exact structures.

## Improve an existing strategy

Builder's **Improve existing strategy** mode seeds generation from strategies you already have
(a picked `.sqx` file or the whole *Strategies to improve* databank) and mutates only the
**Parts to improve** you allow — entry rules, exit rules, order types, ATM exits — each either
**Replace** (swap the part) or **Add** (AND-extend it). Typical trader loop: build broadly →
keep the 10 best → improve with only *exit rules* unlocked → retest.

## Exits and trade management (ATM)

**Advanced Trade Management** adds staged partial exits on top of the strategy's own SL/PT:

- Split the position by **exit scenarios** (50/50, 33/66, 33/33/33, 50/25/25 …); each stage
  closes at its own level — multiple of the original SL/PT, fixed profit (pips or ATR-based),
  or a trailing stop. In results, staged closes show up as `Exit#1`/`Exit#2` in the *Close
  type* column of the trade list.
- Config sources: use the ATM stored in the strategy, define one config for all strategies, or
  let the Builder **generate ATM** (Ultimate edition): a scenario is drawn from the allowed
  set, then 2–3 exits are generated within your allowed types/ranges — and ATM can be the
  *only* part unlocked in Parts to improve, so exits are iterated while the entry logic stays
  intact ([overview/settings/multiple-exits.md](../overview/settings/multiple-exits.md)).
- Trading-options guardrails belong to the same conversation: **Maximum SL / Maximum PT** caps,
  **Exit at end of day / on Friday**, **Don't trade on weekend**, **Limit time range** with
  exit at range end, and **Market open sessions** synced from the Data Manager.

## What to parametrize (Optimizer)

Optimization is only meaningful over parameters you *choose* to expose. The Optimizer's
**What to parametrize → Your own settings** switches select which element categories (periods,
levels, …) become optimizable; the parameter table shows the resulting ranges. Constraining a
parameter tightly makes it identical across all optimized results — the standard trick to
optimize one dimension at a time. Guard against overfitting with the walk-forward types and
the databank's **Don't save original strategy** switch off, so the untouched original stays in
the results for comparison.

## Equities: the Stockpicker mode

For stock baskets SQX offers **Stockpicker** strategies: one strategy trades a whole **stock
group**, ranking candidates each bar by a **Position score** expression under **max open
positions** limits, with equity-specific money management (risk % of account, fixed amount,
fractional shares) and a per-bar **Stockpicker log** explaining what was picked and why.
Stockpicker builds skip ATM and robustness cross-checks — validate them with multi-group and
broker-filtered retests instead.

## Packaging for sale (Business Module)

A finished strategy can be productized: the **Business Module** packages a `.sqx` into a
MetaTrader EA — choose which parameters stay **configurable (external)**, attach resources and
a logo, and build **unlocked / demo-locked / fixed-size-locked** variants for the MQL market.
That is the last mile of the workflow when the goal is selling the system rather than trading it.
