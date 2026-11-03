# Trading log screen

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Trading log shows event logs for all strategy invocations. Each running strategy is triggered once on entry and once on exit, and the complete detailed log of every action performed during the invocation is visible here.

[image]

Open each log using the arrow in the first column to see the summary of the actions taken — evaluated signals, orders and open positions placed.

To see more, click the Log button next to the record to open the full event log:

[image]

Here you can see step-by-step what the trading engine does. Generally, it:

-

evaluates the entry or exit conditions to produce signals,

-

computes the position score for the signals,

-

optionally places or closes orders.

You can save a log to a file for more convenient reading.

# Understanding the columns

## Position score

Position score only applies to Stockpicker strategies — it's the numeric ranking the strategy uses to pick which symbol to trade when multiple signals fire at the same time.

-

Position score is empty / "no value" — expected for single-asset strategies (which don't rank candidates) or when the scoring formula evaluated to N/A (e.g. missing data for the scoring indicator). Not an error.

-

All scores are identical — your position scoring formula produces the same value for every candidate. Revisit the formula in the Stockpicker settings.

## Evaluated vs. ordered

The log distinguishes between signals that were evaluated (passed the entry rule) and orders that were placed (also passed money management and broker limits). If a signal evaluated but no order appeared, check:

-

Max open positions limit reached.

-

Allocation budget exhausted.

-

Symbol not available at the broker (red ❌).

-

Fractional shares not allowed for the order type.

# Exporting a log

Use the Save log button to export the full event log as a file — useful when sharing with support. Include the file when you email [email protected] with a trading question.
