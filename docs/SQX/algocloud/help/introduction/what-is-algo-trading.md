# What is algo trading?

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Algo trading is the use of predefined trading rules (algos) to execute trades automatically, without the need for trader's manual work.

## What is a trading strategy?

Trading strategy is simply a set of exact trading rules - when to enter, when to exit, possibly when to move your protection stop etc.

If you have no previous experience with algo strategies it might be challenging at first that you must define exact rules for your trading strategy.

If you come from discretionary trading, you might struggle with this at first - you have to be able to formulate and define EXACTLY what the strategy should check and do.

But overcoming this it will open a whole new world of trading to you.

Your trading strategy definition could look like:

​When AAPL price today has risen more than 2% from its yesterday price, buy it.

it can also use indicators like:

​When Simple Moving Average (SMA) with period 5 of AAPL crosses above SMA with period 20, buy the stock.

​

​

AlgoCloud Strategy Editor allows you to define these rules like these in a simple way, you only have to construct them from the predefined blocks - conditions, values, comparisons, actions.

## Types of strategies supported by AlgoCloud

AlgoCloud currently supports two different types of strategies:

## Stockpicker strategy

This is a strategy that runs on a group of stocks, typically on index like S&P 500, or Russel 3000.

This means that this strategy trades on all 500 resp. 3000 stocks in a given group, picking a selected number of stocks to trade based on strategy rules.

​

​

An introductory video on the Learning academy: How stockpicking strategies work

It covers concepts like:

-

Introducing Stock groups

-

How Stockpicker strategy looks like

-

How Stockpicker engine works

-

Stockpicker strategy in AlgoCloud

## Single-asset cloud strategy

Single-asset cloud strategy trades on one stock symbol.

It can have additional subcharts attached - for example you can trade AAPL and look at MSFT and GOOG subcharts.

​

This is exactly a kind of strategy from our example earlier:

​When AAPL price today has risen more than 2% from its yesterday price, buy it.

​

It is a standard type of strategy that is supported by most common retail trading platforms such as MetaTrader, Tradestation, MultiCharts and so on.

​

AlgoCloud provides a way to export your AC strategy code to the code of your favorite supported trading platform where you can trade it.

## Other components of the straegy

## Money management

AlgoCloud comes with predefined Money management (position sizing) methods. Their usage is optional, you can also set the position size using a fixed value or compute it yourself and use it from variable. Money management configuration can be found on the top right panel:

By clicking on it it will open configuration dialog where you can choose between different Money management methods. Each method has its own parameters that can be configured.

Selected method is then used in strategy backtests and in the generated source code. However, you can choose to use a different management method when exporting the source code:

## Strategy charts

Strategy trades on the chart on which it is attached. Most of trading platforms allow strategy to access multiple charts / symbols, so for example strategy might be running on EURUSD/H1 chart but some of its indicators might be computed from different timeframe or even different symbol. AlgoCloud supprts this. Note that it supports accessing other subcharts to get price data and compute indicators, but it will trade only on the main chart. You can configure the charts that will be available to the strategy on the top right panel:

There you can add multiple subbcharts that can be used in your conditions and indicators:

To set indicator to use subchart instead of main chart all you only need to configure its Chart parameter, telling it that this particular indicator should be computed from subchart #1, and not from the main chart (on which the strategy is attached).

## Trading options

Trading options are additional options that are not directly a part of strategy rules, but they affect trading. An example might be limiting strategy to 1 trade per day, or automatically closing all trades at the end of Friday. Configuration of trading options are accessible from the top right panel:

By clicking on it it will open dialog where you can choose which of the available trading options should be active and their parameters.

## Variables

Trading strategy often has multiple parameters. Almost every indicator allows you to configure its period, you can configure for example Stop Loss or Profit Target size. It would be inconvenient to put these values there as fixed numbers, it makes it difficult to find them later when you want to change them. AlgoCloud allows you to create an unlimited number of variables - they can be used either internally in the strategy, or they can be external and be configurable as the strategy parameters. Configuration of variables is accessible from the top right panel:

By clicking on it it will open a dialog where you can manage all the variables the strategy uses. There already might be some variables created when you created new strategy from template. You can configure name, type and default value for every parameter.

An important option is the check on the first column - if turned on, it means this variable becomes a strategy parameter, which means it will be configurable in the trading platform - usually when you add the strategy to the chart. When unchecked, this variable is used only internally without need for configuration. The usage of the variables in your conditions is simple - see below:

Simply click on the [...] icon next to the parameter and there you'll see all the variables of that type that can be used. If you select the variable it will be assigned to this indicator parameter instead of number value that was there before:

To stop using this variable for this indicator parameter you can again click on [...] and choose Back to normal value.

​
