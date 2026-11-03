# Backtest troubleshooting — stuck, slow or out of memory

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Backtests in AlgoCloud run on shared cloud infrastructure. Most backtests complete in seconds to a few minutes, but large data ranges or complex strategies can hit engine limits. This article covers the most common issues and how to get around them.

# Backtest "stuck" — running for an hour or more

If a backtest is still running long after you expected it to finish, try these steps in order:

-

Reduce the data range — the most common cause is a very long range (e.g. 2000 to today) with a large stock group. Try 2015 to today first.

-

Reduce the stock group — a Stockpicker strategy over S&P 500 is much heavier than one over a 20-symbol group.

-

Log out and log back in — if the backtest still hangs, this is a known workaround. The cloud engine occasionally keeps a stale session that blocks new backtests.

-

Try Quick backtest — it uses a shorter fixed range and is a good sanity check that the strategy itself is fine.

# Error: "my backtest is out of memory"

Meaning: The strategy is too heavy for the current cloud worker — typically a Stockpicker with a large universe, long range and many indicators.

Fix:

-

Reduce the data range (most effective).

-

Reduce the universe size (smaller stock group).

-

Simplify indicators — remove the heaviest ones first (high-lookback, multi-timeframe).

# Error: "Backtest communication error"

Meaning: The browser lost its connection to the backtest worker. The backtest may still be running or may have crashed.

Fix: Reload AlgoCloud. Check Backtest History (in Profile) to see if the backtest completed in the background. If it didn't, rerun it.

# Recommended data ranges

-

Single-asset strategy — 5 to 15 years is usually fine.

-

Stockpicker on a custom 20–50 symbol group — 5 to 15 years.

-

Stockpicker on S&P 500 — start with 5 years. Increase in steps.

-

Stockpicker on Russell 1000 — start with 2 years. This is the heaviest configuration.

# The backtest completes but results look wrong

-

Check the Backtesting article for common configuration issues (commissions, slippage, spread).

-

Check if the affected symbol had a stock split or delisting during your backtest range.

-

If you suspect a data quality issue, contact support with the symbol and the date of the suspect price — we'll check our data source.

# Still stuck?

Contact [email protected] with the strategy name, the backtest range you used, and (if possible) a screenshot of the error.
