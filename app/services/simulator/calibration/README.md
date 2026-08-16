# FEAT-SIM-17 — Empirical Execution Calibration

This feature partitions point-in-time eligible, checksummed evidence before fitting and publishes
immutable calibration artifacts. Calibration and validation code cannot access certification-holdout
records. Provider M1 spread parameters are labelled as end-of-minute lower bounds and use only
scheduled-event metadata for canonical regimes. Execution components without sufficient trace
evidence remain explicit exclusions; demo evidence never expands live applicability.

The sole public boundary is `app.services.simulator`. Internal artifact and partition classes are not
public contracts.
