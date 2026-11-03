# What markets does AlgoCloud support?

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

AlgoCloud is built for US stocks and ETFs. Here's a quick answer to the most common "does AlgoCloud support X" questions.

# Supported

-

US stocks — individual tickers traded on NYSE / NASDAQ / AMEX.

-

US ETFs — sector ETFs, index ETFs (SPY, QQQ, IWM, sector XL*), leveraged ETFs.

-

Stock groups — S&P 500, Russell 1000, custom lists. See Stock groups.

-

Daily (D1) timeframe — the primary timeframe supported natively.

-

Weekly / monthly — supported for backtesting; live deployment depends on broker.

-

European stocks / global markets via Interactive Brokers (Beta).

# Not natively supported

-

Futures — AlgoCloud does not trade futures directly. Tradestation supports them but AlgoCloud's strategy templates target equities. Futures via MT5 broker is possible through MTBridge.

-

Forex — not in native brokers (Alpaca, Tradestation, eToro stocks, Trading212). Use MTBridge to connect any MT4 / MT5 forex broker.

-

Options — not currently supported.

-

Crypto — not currently supported.

-

Intraday timeframes (1-minute, 5-minute) — AlgoCloud's engine is optimised for D1 and above. 1-minute strategies are not the primary use case; some users run them via MT4/MT5.

# Country availability

Which broker you can connect depends on where you live:

-

US — all supported brokers work (Alpaca, Tradestation, IBKR, eToro).

-

EU — Trading212 (Demo), eToro, XTB, IBKR, Robomarkets, MT4/MT5.

-

Canada — IBKR (with notes — personal vs business accounts differ), eToro.

-

India / LATAM / Asia / rest of world — eToro and IBKR are usually the options; check each broker's country list.

If your country or broker isn't listed, contact [email protected] — we can check if one of the supported brokers accepts clients from your region.
