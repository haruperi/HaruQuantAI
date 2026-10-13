# Backtesting

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

AlgoCloud allows you to use backtesting engine with built-in high quality historical data. You can configure the backtests extensively using the Backtests toolbar settings:

[image]

There are few main concepts you should familiarize with when working with AlgoCloud:

-

Backtest is a result of strategy test on historical data. The exact backtest configuration can be done in backtest setting. There you can configure symbol, timeframe, date range, spread and many other things.

-

Backtest precision is Selected Timeframe, which means the backtest is simulated on the candles of your timeframe. So if you have D1 (daily) bars, backtest engine will simulate OHLC prices of every day bar.

-

Full / Quick backtest there are also two backtest types:

-

Quick backtest makes a very quick backtest on last year of data with Selected Timeframe precision.

-

Full backtest is a backtest on the defined history, which includes over 30+ years of historical stock data.

Note that some options might be enabled only in higher plans.

## Backtest settings

#### Data tab:

You can configure symbol, timeframe, date range, spread:

[image]

#### Trading Options:

You can turn on logging in Trading Options - you can use it for debugging. After running backtest, additional tab is displayed in results, which shows all signals as a text:

[image]

[image]

#### Money Management

Here you can setup money management for your strategy:

[image]

Money management methods:

Risk fixed % of account

Fixed amount

Both methods allow to use fractional shares.

More about costs in this article.

## Backtest results

Backtest results are previewed on the main editor screen on the bottom right section:

[image]

By clicking on it you can switch to full Results view with more detailed analysis of strategy performance.

#### Overview screen

You can choose from different templates for views of statistics:

[image]

#### SP Overview

Overview of traded stocks:

[image]

[image]

#### List of trades

[image]

#### Equity chart

[image]

You can compare strategy performance with benchmark. To turn it on, change X Axis to Time.

Choose Benchmark asset and normalization type.

Normalization means that we’ll recompute real performance of benchmark asset as if it would have the same exposure / drawdown as your strategy.

This allows you to compare how would the benchmark look like with the same risk or invested capital in time.

More information in this article.

#### Trade analysis

[image]

#### Strategy config

[image]

#### Source code

Contains source code, logic of strategy written in human readable form

[image]

​
