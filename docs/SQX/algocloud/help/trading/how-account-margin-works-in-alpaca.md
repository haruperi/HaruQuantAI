# How account margin works in Alpaca

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Alpaca offers 3 types of accounts:

-

Cash 1:1

-

Overnight - margin 2:1

-

Intraday - margin 4:1

## 1) Cash account

-

trading with your own money, no leverage, no borrowing

-

cannot be traded short

Buying power = cash in the account

Cash 1:1

Example

Equity

Buying power

Used equity

Used margin

Remaining Cash

75% of account

100000

100000

75000

0

25000

150% of account

100000

100000

❌ ERROR (limit 100 %)

0

100000

## 2) Overnight account

-

possible to hold double the position of cash even overnight

-

minimum deposit = $2000

-

possible to trade short

Buying power = 2 x cash

Overnight 2:1

Example

Equity

Buying power

Used equity

Used margin

Remaining Cash

75% of account

100000

200000

75000

0

25000

150% of account

100000

200000

100000

50000

-50000

## 3) Intraday account

-

during the trading day it is possible to hold a position up to 4 times larger than the equity

-

minimum deposit = 25000 USD (Pattern Day Trader rule)

Buying power = 4 x cash

Intraday 4:1

Example

Equity

Buying power

Used equity

Used margin

Remaining Cash

75% of account

100000

400000

75000

0

25000

150% of account

100000

400000

100000

50000

-50000

Notice:

-

For example, if you want to trade 75% of your account and use 2:1 leverage to trade a double position, you need to enter a double risk percentage (i.e. 150%) in AlgoCloud's strategy settings. Alpaca then blocks 100% cash and 50% margin.

Example with 125% - log detail in AlgoCloud

[image]

Account Detail in Alpaca

[image]

-

if the account is not leveraged and you try to trade more than 100%, the trade will not be executed

[image]
