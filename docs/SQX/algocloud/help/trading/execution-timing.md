# Execution timing

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

It is important to understand what Execution timing is, how it works and how it affects your strategy.

Execution timing means when your strategy is triggered, evaluated and executed.

## When strategy can trade

Strategies running on daily (D1) timeframe can be triggered two times during a day - on:

## Entry

this is when entry conditions are evaluated and strategy places orders

## Exit

this is when (optional) exit conditions are evaluated and open orders are closed

​

[image]

## Timing options explained

[image]

## Before Bar Open

evaluates strategy before Bar open (it is before Market open for daily strategies).

Orders are entered in advance (market, stop or limit): calculations are based on previous days.

​Trades will be executed when market is opened.

Implications

​Block with Shift=0 with this trigger returns the current value of the last finished bar. So for example Close[0] returns Close price of previous market day. Open[0] returns Open price of previous market day.

## On Bar Open

evaluates strategy on bar open (when Market opens for daily strategies). We trigger this a few minutes AFTER the actual market opens to allow for accurate prices. Strategy will have access to current market open price.

​Trades will be executed immediately.

Implications

OnBarOpen Block with Shift=0 with this trigger returns the current value of the current open bar. So Open[0] returns current day Open price, Close[0] returns the last current price, very similar to Open[0]. Since the day didn't finish yet, Close[0] at Bar Open is NOT as same as final Close[0] at the end of the day.

Yesterday’s values then: Open[1], High[1], Low[1], Close[1]

## On Bar Close

evaluates strategy on bar close (when Market closes for daily strategies). We trigger this a few minutes BEFORE the actual market close to allow for correct executions.

​Trades will be executed immediately.

This timing is mostly used for closing of position because it actually does not make much sense to use it for limit or stop orders.

Market order is executed for the actual price at 3:58 PM.

Implications

OnBarClose Block with Shift=0 with this trigger returns the current value of the current open bar. So Open[0] returns current day Open price, Close[0] returns the last current price. Since we are very near to market close, it will be very similar to real market daily Close price.

The choice of your triggers will have impact on when and how the strategy trades, strategy can have different results when used with different timing.

You can backtest the strategy with the exact timing and you should use the timing that you used in your backtest.
