# Stock groups

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

## Data manager -> Stock groups

Stockpicker strategy trades on group of stocks, not individual assets, and Stock groups is the place where you can manage your groups.

It allows you to create groups of stocks, for example for indexes or sectors.

[image]

Stock groups already contain predefined standard indexes, and it enables you to create your own stock groups.

To distinguish stock groups from standard symbols, they are enclosed in [ ], for example [StockGroupName].

Default (uneditable) stock groups provided by us are enclosed in double quotes [[ ]].

## Adding stock group

Adding stock group is done in two steps. In first step you have to define name, exchange and optional description:

[image]

The next step is to define which stocks are in group:

[image]

You simply have to put there a list of stocks, separated by new line. Stocks must be defined by their correct tickers, and they can optionally have two more dates - date when stock was added to the group, and date when it was removed - all in DD.MM.YYYY format.

AAPL <- in case the stock is in group all the time

AAPL;1999.03.04 <- in case stock was added to group on 1999.03.04

AAPL;1999.03.04;2022.11.10 <- in case stock was added to group on 1999.03.04 and removed on 2022.11.10

The dates are important in order to support Survivorship bias – which is important for realistic backtests (more about this in another article) – so you can add also dates from – to when the stock belonged to index.
