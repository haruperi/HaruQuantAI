# Portfolio construction in SQX

Deep dive for Step 4 of the [trader workflow](workflow.md): turning a databank of robust
strategies into a portfolio that is more than the sum of its parts. Everything here maps to
concrete SQX controls (verified against the scenario corpus in `tests/ui/scenarios/`).

## Diversify by design, not by accident

Two individually great strategies that draw down together add almost nothing. SQX gives three
levers to force real diversification:

1. **Correlation constraints** (Portfolio Master → Correlation settings): set a *maximum
   allowed correlation* of Profit/Loss series per period — **Day, Week, Month, Year** can each
   carry their own threshold (e.g. 0.03 daily/weekly/monthly, 0.1 yearly). Candidate
   combinations that violate any threshold are rejected; the **Strategy dismissal stats**
   window shows why candidates were dropped, and the **Portfolio correlation** result tab shows
   the final pairwise matrix (Compute button).
2. **Sectors via strategy notes**: the databank's *Set note* action doubles as a sector tag
   (e.g. `Sec1`, `Sec2`). Portfolio Master's **"Max allowed strategies from the same sector"**
   then caps same-sector members per portfolio — a cheap way to enforce spread across symbols,
   timeframes or styles.
3. **Fit to existing portfolio** (Builder!): diversification can start *before* the portfolio
   stage — load your live strategies into the **Existing portfolio** databank and the Builder
   offers two mechanisms (field-level detail:
   [`overview/settings/fields/ranking.md`](../overview/settings/fields/ranking.md)):
   - a **correlation dismissal filter** — reject any new strategy whose P/L correlation with
     *any* existing strategy exceeds a limit (e.g. 0.05, per chosen period);
   - **fitness computed on the combined portfolio** (`Use = Existing portfolio` in the
     Fitness configuration) — each candidate is scored by simulating *existing + candidate*
     together, so the build prefers strategies that improve the portfolio as a whole, not
     the best standalone performers.

## Portfolio Master mechanics

- Input pool = the **Simple strategies** databank (optionally narrowed by the *Only selected*
  switch). At least 2 strategies are required to start.
- **Min/max strategies per portfolio** bound the combination size; the **"number of possible
  portfolios"** readout is the combinatorial count (Σ C(n,k) for k = min..max) — sanity-check
  it before long runs. Brute-force search is used for small spaces, genetic search for large.
- **Max portfolios to store in databank** caps retained results; each result row is itself a
  *portfolio strategy* that can be **split** back into members from the databank.
- Constraints compound: with min=3, max-per-sector=1 and three sectors, every result has
  exactly 3 members — one per sector.

## Weights: Portfolio Composer

Portfolio Master picks *which* strategies; **Portfolio Composer** decides *how much* of each:

- Loaded strategies should share a money-management type — the Configuration tab states
  "Strategies use the same / different types of Money Management" and lists each strategy's
  sizing (e.g. `Fixed size: 0.10 lots / $10000`).
- Assign **weights** per strategy and *Recompute portfolio* (needs ≥ 2 selected), or run
  **Automatic computation** — a search over weightings driven by a fitness criterion:
  **sharpeRatio**, **ReturnDrawdownRatio** or **CAGRMaxDrawdownRatio**, with a cap on
  simulations.
- Compare weighted variants in the Overview/Equity chart before committing.

## Databank operations that support the loop

- **Merge strategies** → one portfolio strategy row; **Split** → back to members.
- **Filter by correlation** works directly in the databank too (per-period max), useful to
  thin a pool before Portfolio Master.
- **Copy/Move to Portfolio Master / Portfolio Composer / Retester** moves candidates between
  stages; "Apply current config" decides whether the source module's settings travel along.
- Final check: retest the *portfolio strategy itself* (single databank row) so slippage,
  sessions and data settings apply to the combined trade stream.
