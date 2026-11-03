# 1. Connect a broker

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

You need to create a connection between your AlgoCloud account and your broker(s) in order to trade — so that AlgoCloud can send orders, check positions, etc. to your broker account.

The way of creating this connection is different for each broker, and we provide a simple step-by-step wizard for all the supported brokers.

Note

Most brokers allow you to have a demo or paper trading account with them, in addition to your real account. Paper/demo accounts use virtual money, so you will not risk your real money.

You can have multiple connected accounts in AlgoCloud, so you can create connections to both your paper and live accounts of the same broker.

You can run your strategy against your paper account to trade with demo money before going live.

# Supported brokers

AlgoCloud currently supports the following brokers. Click a broker for setup instructions:

-

Alpaca Markets — US stocks & ETFs, fractional shares, commission-free. Good for small accounts (no PDT restriction on cash accounts).

-

Tradestation — US stocks, options, futures. Best for accounts over $25,000 USD (Pattern Day Trading rule).

-

Interactive Brokers (Beta) — global markets, professional platform.

-

eToro — commission-free stocks & ETFs, Demo and Real accounts supported.

-

Trading212 (Beta) — Demo accounts only (Trading212 API is still in beta).

-

Robomarkets (Beta) — no PDT restriction, good for small accounts.

-

XTB — European broker.

-

MetaTrader 4 / 5 (via MTBridge) — connect any MT4/MT5 broker using the AlgoCloud MTBridge.

Not sure which broker to choose? See Brokers overview for a comparison.

# Connected brokers

Manage connections to your brokers in the menu Live trading → Connected brokers.

[image]

Click the + Link account button and follow the wizard to create a connection to your broker.

[image]

You will also see the default AlgoCloud demo broker in the list — this demo broker can be used to run strategies in demo mode. You can reset your paper trading account, which will delete all open and historical trades and reset the account balance.

You need to stop all strategies before resetting the account. You can stop strategies from the Strategies screen.

# Difference between Live and Demo accounts

AlgoCloud clearly separates demo and real accounts:

Live accounts (real money)

Real money accounts at your broker. If you deploy your strategy on a live connected account, it will trade real stocks with real money through your broker.

Paper accounts (demo money)

Paper/demo accounts — you can get a demo account from your broker, or use the built-in AlgoCloud demo broker simulation. Your strategy will still use real data feeds and real prices, but trades are settled with virtual (paper/demo) money.

# Troubleshooting connection errors

If your broker connection fails with an error code (401, 403, OAuth failed, etc.), see the broker-specific troubleshooting section in each broker's article:

-

401 "Saving connected account failed" → your API key is missing permissions. Regenerate it with all permissions enabled.

-

403 "insufficient qty available" → the broker does not allow the order (fractional-shares limitation, short-selling disabled, margin exhausted).

-

OAuth redirect fails → for Tradestation, the callback URL must be whitelisted by the broker.
