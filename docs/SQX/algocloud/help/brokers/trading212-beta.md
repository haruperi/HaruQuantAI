# Trading212 (Beta)

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Note

Trading212 is supported by AlgoCloud, but the Trading212 API is still in BETA — only Demo (paper) accounts are currently supported. Live (real money) trading via API is not yet enabled by Trading212.

# Link account for Trading212

# Step 1 - Generate your API key

Full instructions are available in Trading212 help: How can I generate an API key?

Log in to your Trading212 account and go to Settings → API, then click Generate API key.

⚠️ Important: Enable ALL permissions in the list. If any permission is missing, the connection to AlgoCloud will fail with a "Saving connected account failed - 401" error.

[image]

Copy the generated API key — you will paste it into AlgoCloud in the next step.

# Step 2 - Link to broker in AlgoCloud

In AlgoCloud, go to the Connected accounts screen (Trading → Broker connections). This is where you manage all connections to brokers.

Click the Link account button.

[image]

A wizard will guide you through the connection. In the first step, choose Trading212 from the list of supported brokers.

[image]

In the second step, fill in the connection details:

-

Connection name — any name (used internally in AlgoCloud, e.g. T212 Demo)

-

Account type — select Demo (only Demo is currently supported by the Trading212 API)

-

API key — paste the API key you generated in Step 1

The third step (optional) is to enable Account protection — AlgoCloud will stop trading if your drawdown exceeds the set threshold.

[image]

After clicking Submit, the connection is created and AlgoCloud will retrieve your account balance, equity and positions from Trading212.

[image]

# Troubleshooting

## Error: "Saving connected account failed - 401"

A 401 error means the API key does not have all required permissions. Return to Trading212 → Settings → API, delete the existing key, generate a new one and make sure all permissions in the list are enabled before confirming.

## I only see "Connection name", "Account type" and "API key" fields — no "Account ID" or "password"

That is the correct, current UI. The Trading212 connection uses only the API key — you do not need an Account ID or password. Older screenshots showing those fields are outdated.

## Can I connect my Trading212 real-money account?

Not yet. Trading212's API is in beta and currently supports Demo accounts only. Live trading via API will be added once Trading212 enables it on their side.
