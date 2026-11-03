# Single-asset strategies explained

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

This is a type of strategy that trades one stock symbol.

It can have additional subcharts attached - for example you can trade AAPL and look at MSFT and GOOG subcharts.

​

This is an example of strategy looking at the condition like this:

​When AAPL price today has risen more than 2% from its yesterday price, buy it.

In Editor the strategy looks as simple as it gets. There are only two sections - one for configuring Buy (Long) orders, and the other for Sell (Short) orders.

## Layout

[image]

Orientation on the screen:

-

Long/Short section - Sell section is identical to Buy section, with one additional possibility - you can configure Short rules to be symmetrical to Long. If enabled, Short section will be not editable and instead of that AlgoCloud automatically creates all its conditions to be symmetrical with the Buy conditions and exits. So for example, if your Buy condition is "CCI(20) crosses above 0" then your symmetrical Short condition will be "CCI(20) crosses below 0". AlgoCloud saves a lot of duplicate work of specifying the Short conditions yourself, and you should use it if you don't have some special strategy that uses Sell orders that are not symmetrical to Buy orders. It is not turned on by default.

-

When condition(s) - here is where you can specify conditions that have to be valid to open the Buy trade. The condition can be simple, for example "CCI(20) crosses above 0" or it can be more complex.

-

Order type - You can use Market, Stop or Limit orders. For Stop/Limit orders you will also have to specify its stop/limit price level.

-

Exit types (optional) - you can optionally use any of the predefined exit types - Stop Loss, Profit Target or exit after given number of bars or at End of day.

-

Exit when conditions (optional) - you can additionally enter another set of conditions that have to be valid to close the trade, for example "CCI(20) crosses below 0".
