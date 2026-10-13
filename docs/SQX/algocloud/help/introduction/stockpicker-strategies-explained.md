# Stockpicker strategies explained

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Quick explanation - Stockpicker strategy is a strategy that runs on a group of stocks, typically on index like S&P 500, or Russel 3000.

This means that this strategy trades on all 500 resp. 3000 stocks in a given group, picking a selected number of stocks to trade based on strategy rules.

There are many ways to trade equities (stocks, ETFs, etc.). A simple approach is to trade an individual stock, or an ETF. But the nature of stocks allows many other trading styles:

-

Asset rotation / rebalancing – where you rebalance the weight of different assets in your portfolio

-

Pair trading and similar – where you trade the differences between correlated or cointegrated pair of stocks

-

Stocks picking – where you trade a whole group of stocks. There are even multiple different styles of stocks picking.

-

… and there are other more “exotic” styles

The common thing with these different styles of stock-trading algorithms is that they usually trade groups of stocks – either several stocks in a group, several pairs of stocks, or hundreds of stocks that constitute indexes like S&P 500.

AlgoCloud Stockpicker engine was made to allow you to use the third mentioned style of trading stocks – algo strategies that trade on a big group of stocks, for example all 500 stocks in the S&P 500, or 2000 stocks in Russel 2000 - but pick only a smaller number of stocks to trade depending on the strategy rules.

## Why would you want to trade stock indexes this way instead of trading the S&P 500 as a single ETF ?

Well, it can be more profitable and with less risk. By buying S&P 500 ETF (for example SPY) you are buying the whole index. By using a smart algorithm that uses some set of rules that trade only a portion of stocks in this index you can limit your exposure and risk, and get better profit.

Note that profits are NOT guaranteed in any way – they depend on your particular algo strategy.

According to our best knowledge our AlgoCloud is the world’s first and only NO CODE platform that offers research and live trading of this type of strategies.

## So how Stockpicker strategy looks like

An example Stockpicker strategy in pseudo code:

//--------------------------------------------------------------------

// Trading options logic

//-------------------------------------------------------------------- Entry type: On Bar Open Order place type: Immediately

//--------------------------------------------------------------------

// Trading rule: Long (On Bar Open)

//-------------------------------------------------------------------- Entry Condition: (Kaufman Adaptive Moving Average(Main chart, PRICE_TYPICAL, 146)[2] is rising for 2 bars at 3 bar ago)

Order: Open Long order at Market;

Exit: At end of day (DayClose)

//--------------------------------------------------------------------

// Trading rule: Short (On Bar Open)

//-------------------------------------------------------------------- Entry Condition: (Kaufman Adaptive Moving Average(Main chart, PRICE_TYPICAL, 146)[2] is falling for 2 bars at 3 bar ago)

Order: Open Short order at Market;

Exit: At end of day (DayClose)

//--------------------------------------------------------------------

// Trading rule: Position Score (On Bar Open)

//-------------------------------------------------------------------- Position Score = LowDaily(Main chart)[2];

Max positions: 5

Stockpicker strategy consist of Long + Short rule and Position score rule. It trades on a Daily timeframe only.

Long and Short rules define:

-

Entry condition(s) – when should the strategy open trade

-

Order – type of order – Market, Stop, Limit

-

Exit – when it should close the trade

In our example the strategy will have a long entry signal when:

(Kaufman Adaptive Moving Average(Main chart, PRICE_TYPICAL, 146)[2] is rising for 2 bars at 3 bar ago), and it will close it ad the end of day

Position score rule is a specialty of Stockpicker strategies. Because Stockpicker strategy trades on a group of stocks (for example 500 stocks in S&P 500 index), it must determine how many positions should be open in parallel as well as the criterium on how to sort signals from different stocks:

-

Max positions = 5 means that this strategy will open positions in maximum 5 different stocks in parallel

-

Position score formula is the criterium by which to sort which stocks to choose if there is more than 5 stocks that could be opened at a given day.

[image]

## How Stockpicker engine works:

This kind of engine is different because remember – it trades on 500 stocks in the group.

-

At the entry – typically at market open – it will check the Long & Short rules on all stocks in the group that it is trading, for example on all 500 stocks in S&P 500.This could produce for example 12 different entry signals for 12 different stocks – AAPL, TSLA, …, AMZN, GOOG etc.

-

It then uses the specified Position score formula to compute a score value for each of these 12 stocks. If there are no open positions, it will then choose Max positions of these stocks by the biggest score. Our example algorithm selects 5 stocks with the biggest position score and opens them at market.

-

The trades are closed according to the exit rule – for example at the end of day, and a new evaluation is again made the following day and so on.

The trading result of this strategy applied on S&P 500 stock group could look as follows:

[image]

You can see that it opened 5 different stocks on day 1, and then another 5 stocks on day 2.

It can happen that less than 5 or even no trades are opened on a particular day – it depends in the entry conditions, etc.

Strategy can also use a different entry rule than Close at end of day – the trades can last for more than one day, but there will be never more than 5 stocks opened at the same time.

Related resources:

Introduction to Stockpicker strategies (videos)
