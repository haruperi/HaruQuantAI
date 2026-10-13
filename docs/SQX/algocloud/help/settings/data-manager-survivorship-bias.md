# Survivorship bias

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Survivorship bias is a common and misleading error in stock trading that can lead to overly optimistic conclusions about market performance. It happens when only the “surviving” stocks - those that have done well or continue to exist - are analyzed, while those that failed or were delisted are ignored.

For example, many stock indexes, like the S&P 500, regularly remove poorly performing companies and replace them with stronger ones. When investors look at the historical performance of the index, they often forget that the current list of companies includes only the winners, not those that were dropped. This gives the impression that investing in the index is safer or more profitable than it actually was in the past.

Similarly, back-testing trading strategies on today’s market data can be flawed. If a trader tests a strategy using current stocks only—without including those that went bankrupt or were delisted - they may see unrealistically high returns.

To avoid survivorship bias, traders and analysts should use complete data sets that include both winners and losers over time. Recognizing this bias is key to developing realistic expectations and sound investment strategies.

Historical index constituents refer to the full list of companies that were included in a stock market index (like the S&P 500, Dow Jones, or NASDAQ-100) at various points in time - not just the ones that are currently in the index.

These records show:

-

When each company was added to or removed from the index

-

How long each company stayed in the index

-

Which companies were delisted, merged, or went bankrupt

This historical data is crucial for accurate backtesting, research, and performance analysis because it avoids survivorship bias. If you backtest a strategy using only current index members, you're only analyzing companies that survived - ignoring those that failed or were replaced, which can make a strategy look more successful than it actually would have been.

Example:

If you're backtesting an investment strategy on the S&P 500 from the year 2000 to 2025, using only the 2025 constituents, you're missing out on companies like Enron, Lehman Brothers, or Kodak, which were in the index but later failed or were removed.

Where to find historical constituents:

-

S&P Dow Jones Indices (official provider, paid data)

-

CRSP (Center for Research in Security Prices)

-

Bloomberg or FactSet (institutional access)

-

Some financial research platforms, academic databases, or GitHub repositories (limited free access)

-

Wikipedia

In summary, historical index constituents are essential for building realistic financial models and avoiding misleading results due to survivorship bias.
