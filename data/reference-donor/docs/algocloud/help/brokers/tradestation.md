# Tradestation

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Tradestation provides an easy to use Trading API.

Note

Tradestation is most suitable for AlgoCloud only with accounts over $25,000 USD!

​The problem is with their handling of Pattern Day Trading rule — if your account is smaller they don't allow you to open more than 3 trades in a 5 day rolling period.

# Link account for Tradestation

# Step 1 - Request Tradestation API credentials

You will need three things from Tradestation:

-

Account ID — the standard ID of your Tradestation account (visible on your account statements)

-

Client ID — issued by Tradestation on request

-

Client Secret — issued by Tradestation on request

Client ID and Client Secret are not self-serve — you must request them by email from Tradestation's API team. Follow the instructions here: How do I get an API Key?

⚠️ Important — callback URL whitelisting

Tradestation must whitelist the AlgoCloud callback URL for your credentials to work. When you email Tradestation to request API access, include this callback URL in your request:

app.algocloud.com/api/broker-api/ts/authorize

If the callback URL is not whitelisted, the OAuth authorization step will fail and the connection will not complete.

# Step 2 - Link to broker in AlgoCloud

Once Tradestation has given you the Account ID, Client ID and Client Secret, you can create the connection in AlgoCloud.

Go to the Connected accounts screen (Trading → Broker connections) and click Link account.

[image]

A wizard will guide you through the process. In the first step choose Tradestation from the list of supported brokers.

[image]

In the second step fill in the connection details:

-

Connection name — any name, used internally in AlgoCloud

-

Account ID — your Tradestation account ID (from your account statement)

-

Client ID — from the Tradestation email

-

Client Secret — from the Tradestation email

[image]

The third step is (optionally) to turn on Account protection.

[image]

After clicking Next, AlgoCloud redirects you to Tradestation to authorize the connection. Log in to Tradestation and approve the access. You'll be redirected back to AlgoCloud and the connection will be created.

[image]

AlgoCloud will then log in to the Tradestation API and retrieve basic information about your account — balance, equity and positions.

# Troubleshooting

## OAuth authorization fails / redirect does not complete

The most common cause is that Tradestation has not whitelisted the AlgoCloud callback URL for your credentials. Reply to the Tradestation API team and ask them to whitelist app.algocloud.com/api/broker-api/ts/authorize for your Client ID.

## "You are long 0 shares" error when the strategy tries to go short

Tradestation requires short selling to be explicitly enabled on the account. If your account is long-only, short trades will be rejected with this error. Contact Tradestation to enable short selling, or restrict your strategy to long-only in the deployment.

## Strategy hits the Pattern Day Trading limit

Tradestation enforces the PDT rule for accounts under $25,000: no more than 3 day trades in any 5 business day window. If you need high-frequency strategies, either fund the account above $25,000 or use a broker without the PDT rule (Alpaca, Robomarkets).
