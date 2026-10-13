# Portfolio Composer Chart — Results tab

> Shows the combined equity curve of a portfolio assembled by the Portfolio Composer — the sum of its member strategies traded together.

## What it shows

The Portfolio Composer Chart tab displays the equity of a *portfolio* result rather than a single strategy. When several strategies are combined into a portfolio, this tab shows the aggregated equity curve for the whole set: how the combined account would have grown when all member strategies traded together over the shared period.

- **Combined portfolio equity** — the merged curve produced by summing the member strategies' trades into one account.
- Alongside it, the standard equity-chart machinery (markers, drawdown, zoom) applies to the combined curve.

## How it works

The Portfolio Composer builds a portfolio from selected strategies; the resulting `ResultsGroup` represents the portfolio as a whole (its result is flagged as a portfolio). This tab reads the portfolio's combined orders/equity and draws the aggregated curve, so diversification effects — a smoother combined curve than any single member, or correlated drawdowns that stack up — become visible.

It is the equity view within the Portfolio Composer's family of result tabs, which also includes the composition log (`/portfoliocomposerlog/`, how the portfolio was assembled) and the correlation matrix with overlapping-trades analysis (`/portfoliocorrelation/`). Together they let you assess both the combined performance and *why* the members work (or don't) as a portfolio.

## Options & settings

- **Chart controls** — zoom, drawdown overlay, and trade/period markers on the combined curve (shared with the equity-chart engine).
- **Portfolio context** — the tab reflects the current portfolio composition; changing membership in the Portfolio Composer updates the combined curve.

## Related

- Tab endpoint: `/portfoliocomposerchart/` (companions: `/portfoliocomposerlog/`, `/portfoliocorrelation/`)
- Portfolio Composer module overview: [../portfolio-composer.md](../portfolio-composer.md)
- Portfolio Master overview: [../portfolio-master.md](../portfolio-master.md)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Sibling tab: [Stockpicker Overview](stockpicker-overview.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
