# Walk-Forward — Results tab

> Shows how a strategy holds up when it is periodically re-optimized: per-period optimization/run results, the Walk-Forward Matrix, and a robustness verdict.

## What it shows

The Walk-Forward tab appears only for results produced by a Walk-Forward (WF) task — the `containsResult(rg)` check requires the result to carry `SettingsKeys.WalkForwardResult`. It presents:

- **Walk-Forward periods** — the sequence of optimization (In-Sample) parts each followed by a run (Out-of-Sample) part. Data is split into a configurable number of periods; each period is optimized, then traded forward with the parameters found. The table lets you inspect the results for each optimization and run period side by side.
- **Robustness score** — a customizable set of score components, each with a boundary value, plus a main threshold saying how many components must pass for the WF result to count as successful. This drives the pass/fail verdict shown in the tab.
- **Walk-Forward Matrix** (when the task ran in Matrix mode) — a grid of WF optimizations across different numbers of reoptimization periods (runs) and different Out-of-Sample percentages. Each matrix cell is a full WF optimization scored pass/fail; the tab highlights clusters of successful combinations and the suggested optimal reoptimization period.

## How it works

Standard Walk-Forward optimization simulates working with a strategy in real trading: optimize on recent history, trade forward with those values, then reoptimize after some time and repeat. If the reoptimized strategy beats the original non-optimized version on the same data, the strategy both benefits from reoptimization and shows resilience to changing market conditions.

The **Walk-Forward Matrix** answers "what is the best reoptimization period?" by running the whole WF optimization for every combination of runs × OOS %. A robust strategy shows gradual (not abrupt) changes across the surface. The tab's success rule looks for a cluster (for example a 3×3 group where at least 7 of 9 single WF tests pass); finding such a cluster indicates the strategy stays profitable under different reoptimization settings — a sign of robustness — and the center of the cluster is offered as the recommended reoptimization period.

Each individual WF optimization is judged with the customizable Robustness score described above. WF matrix per-combination results, matrix layout, and stability values are carried on the `ResultsGroup` and rendered through the tab's WF views (`WFViews`/`WFViewsManager`); parameters can be exported (`WFParamsExport`).

## Options & settings

- **Period/combination selector** — pick any single WF optimization (or matrix combination such as "7 runs / 20% OOS") to drill into its detailed per-period results; the Equity Chart tab then reflects that selection.
- **3D matrix charts** — display any value (Net Profit, Drawdown, Stagnation, Profit Factor, Stability, etc.) across all matrix combinations as a surface, bar chart, or heatmap.
- **Configure (success criteria)** — set the cluster size and how many tests within it must pass for the strategy to be considered robust, and let the tool auto-select the optimal reoptimization period.
- **Robustness score components** — add/remove watched conditions, set their boundary values, and set the main pass threshold.
- **Export** — export WF parameters/values for use in databank columns and filters.

## Related

- Tab endpoint: `/walkforward/`
- Optimizer module overview: [../optimizer.md](../optimizer.md)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Sibling tab: [Optimization Profile](optimization-profile.md) · [Robustness Tests](robustness-tests.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
