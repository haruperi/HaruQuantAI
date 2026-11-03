# Broker connection errors &amp; troubleshooting

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

When you connect a broker or your strategy tries to place orders, you may occasionally see an error from the broker's API. This article lists the most common errors, what they mean and how to fix them.

# Error: "Saving connected account failed - 401"

Broker: Trading212, Alpaca, any API-key broker.

Meaning: The broker rejected the API key during authentication — usually because the key is missing one or more required permissions.

Fix:

-

Log in to your broker (e.g. Trading212 → Settings → API).

-

Delete the existing API key.

-

Generate a new key and enable ALL permissions in the list.

-

Update the connection in AlgoCloud with the new key.

# Error: "403 - insufficient qty available for order"

Broker: Alpaca (most common), Tradestation.

Meaning: The broker refused to open or close the position because the account does not hold the required quantity. Common causes:

-

Short selling disabled — strategy tries to go short but the account is long-only. Enable short selling at the broker, or restrict the strategy to long-only.

-

Fractional shares limitation — Alpaca only allows market orders (not limit/stop) and DAY orders (not GTC) for fractional shares. See Fractional shares.

-

Position was already closed manually — if you manually closed the trade at the broker, the strategy no longer has the quantity it expected.

# Error: "You are long 0 shares" (Tradestation)

Meaning: Tradestation requires short selling to be explicitly enabled. By default, accounts cannot go short.

Fix: Contact Tradestation to enable short selling, or restrict the strategy to long-only.

# OAuth authorization fails / redirect does not complete

Broker: Tradestation, eToro.

Fix for Tradestation: Reply to the Tradestation API team and ask them to whitelist the AlgoCloud callback URL for your Client ID:

app.algocloud.com/api/broker-api/ts/authorize

Without this whitelisting, OAuth cannot complete. See Tradestation.

# "TA_SUCCESS" or other TA_* errors in the backtest log

Meaning: The backtest engine hit a data / indicator issue — typically missing historical bars or a corrupt symbol. Not a broker error; a data / backtest engine error.

Fix: Reduce the backtest range, exclude the problematic symbol, or see Backtest troubleshooting.

# Connection works in paper but not on live

-

The API key's environment (Real vs Demo) must match the Account type you selected in AlgoCloud.

-

Live accounts often have extra restrictions — short selling, margin, fractional orders — that demo accounts don't.

-

Some brokers restrict accounts by country (IBKR Canada personal vs business accounts behave differently).

If the behaviour still differs after checking these, contact AlgoCloud support — we can check the strategy log to see the exact reason the order was rejected.

# Pattern Day Trading limit

US brokers enforce the PDT rule for margin accounts under $25,000: no more than 3 day trades in any 5 business day window. If you need high-frequency strategies, use Alpaca (cash account, no PDT) or Robomarkets.

# Still stuck?

If the error doesn't match or the fix doesn't help, contact [email protected] and include:

-

Exact error message (copy/paste or screenshot).

-

Broker and account type (Demo / Live).

-

Deployed strategy name (so we can check the strategy log).
