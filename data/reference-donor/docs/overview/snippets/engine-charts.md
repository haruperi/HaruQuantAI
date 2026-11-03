# Engine Charts — full catalog

> Reference enumeration of the built-in charts/panels shown live in the **engine monitor** while a
> Builder, Optimizer, or other project is running (progress dashboard).

## How the set is assembled

Each chart is a snippet class extending `com.strategyquant.tradinglib.EngineChart`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/EngineCharts/`). Its constructor calls
`super(displayName, type)`, where `type` is one of:

- `TYPE_GLOBAL` (`10`) — application-wide, always available (e.g. JVM memory), not tied to a
  running project.
- `TYPE_PROJECT_BASED` (`50`) — only meaningful while a project (Builder/Optimizer run) is active;
  reads data from `project` (`ProjectRunInfo`, `Databank`, `GeneticInfo`).

Each chart implements `addNextValue()` (called periodically to sample new data into its internal
series) and `print()` (returns the JSON payload the UI polls — a `DATA_TYPE_CHART` time-series
chart, `DATA_TYPE_ROWS` label/value list, or `DATA_TYPE_GRID` key/value grid). Charts have no
`@Parameter`-style user settings; they are fixed instruments the user picks from a list to display
in the monitor.

## The 14 engine charts

| Display name | Class | Type | What it plots |
|---|---|---|---|
| Accepted strategies per hour | `AcceptedStrategiesPerHour` | Project | Time-series line of `projectRunInfo.acceptedStrategiesPerHour` (strategies passing acceptance criteria per hour), refreshed only when `totalJobsDone` changes (or every 10 checks). |
| Average strategies per hour | `AverageStrategiesPerHourChart` | Project | Time-series line of `projectRunInfo.strategiesPerHour` (average throughput), same refresh logic as above. |
| Databank Fitness - IS | `DatabankFitnessIS` | Project | 3 time-series lines (Top Strategy / Top 10 Avg / All Avg) of in-sample fitness (`bestFitnessIS`, `topAvgFitnessIS`, `avgFitnessIS`) from the project's `Databank.getFitnessData()`. Y-axis fixed 0–1. |
| Databank Fitness - IS Training | `DatabankFitnessIST` | Project | Same 3-series layout, using `*FitnessIST` (in-sample training fold) values. |
| Databank Fitness - IS Validation | `DatabankFitnessISV` | Project | Same 3-series layout, using `*FitnessISV` (in-sample validation fold) values. |
| Databank Fitness - OOS | `DatabankFitnessOOS` | Project | Same 3-series layout, using `*FitnessOOS` (out-of-sample) values. |
| Island #1 - Fitness IS | `GenEvoFitnessIS` | Project | 3 time-series lines (Top Strategy / Top Ten Avg / All Avg) sourced from genetic-evolution island #1's per-generation `FitnessCollectionData` (`bestFitnessIS`, `topAvgFitnessIS`, `avgFitnessIS`); only populated during a genetic build. |
| Island #1 - Fitness IS Training | `GenEvoFitnessIST` | Project | Same, using `*FitnessIST`. |
| Island #1 - Fitness IS Validation | `GenEvoFitnessISV` | Project | Same, using `*FitnessISV`. |
| Island #1 - Fitness Out of Sample | `GenEvoFitnessOOS` | Project | Same, using `*FitnessOOS`. |
| Genetic Evolution info | `GeneticEvolutionInfo` | Project | `DATA_TYPE_ROWS` list, one row per island (up to 7): `Generation: N, Population: N`; shows "No genetic evolution running" if the current build isn't genetic. |
| Heap memory chart | `HeapMemoryChart` | Global | Area chart of JVM heap: "Memory Usage" (`heapUsage.getUsed()`) vs. "Heap Size" (`heapUsage.getCommitted()`), in MB; periodically triggers `System.gc()` (every ~5000 samples) as a side effect. |
| Off-heap memory chart | `OffHeapMemoryChart` | Global | Area chart, single series "Off-Heap Size" — SQX's off-heap allocator usage (`OffHeapMemory.getInfo()`), in MB. |
| Off-heap memory info | `OffHeapMemoryInfoChart` | Global | `DATA_TYPE_GRID` key/value pair: "Allocated objects" and "Allocated memory" (human-formatted bytes) from `OffHeapMemory.getInfo()`. |

## Related

- Databank / results overview: [`../results-databank.md`](../results-databank.md)
- Builder overview: [`../builder.md`](../builder.md) · Optimizer overview: [`../optimizer.md`](../optimizer.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/EngineCharts/`
