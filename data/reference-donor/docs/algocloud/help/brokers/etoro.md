# eToro

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

✅ eToro is available in AlgoCloud

eToro is listed among supported brokers. To connect, go to Trading → Broker connections → Link account and select eToro. Both Demo (paper) and Real money accounts are supported.

eToro is one of the world's largest social investment platforms with over 40 million users, offering commission-free stock and ETF trading. Connecting eToro to AlgoCloud lets you deploy your algo strategies directly to your eToro account — both paper (demo) and real money.

## Link account for eToro

## Step 1: Get eToro API Keys

Login to your eToro account. If you don't have one yet, click Sign Up and create a free account.

[image]

Once logged in, click Settings in the left sidebar menu. On the Settings page, scroll down to the Trading section. You'll find API Key Management at the bottom of the page.

[image]

Click the green Create Your API Key button. Fill in the following fields:

-

Key Name — Enter a descriptive name, e.g. AlgoCloud Demo1

-

Environment — Select Demo for paper trading or Real for live trading

-

Access Permissions — Enable both Read Access and Write Access

-

IP Allowlisting — Leave empty (optional)

-

Expiration Date — Leave empty or set an expiration (optional)

Click Generate Key.

[image]

After generating, eToro displays your Private Key and Public Key:

[image]

⚠️ Important: Write down the Private Key and store it in a safe place. Once you close this dialog, the Private Key cannot be retrieved again. You will need private key in the next step.

## Step 2: Link to Broker in AlgoCloud

In AlgoCloud, navigate to Trading → Broker connections in the left sidebar and click the Link account button.

A wizard will guide you through the connection:

1. Select broker — Choose eToro from the list and click Next.

[image]

2. Connection details — Fill in:

-

Connection name — e.g. eToro Paper

-

Account type — Select Live trading (real money) or Demo trading (paper money)

-

Private key — Paste the Private Key from eToro

Click Next.

[image]

ℹ️ Note: The API key Environment (Real/Demo) you selected in eToro must match the Account type in AlgoCloud. A Demo key will not work for Live trading and vice versa.

3. Account protection — This optional feature protects your account from extreme losses. When enabled, AlgoCloud monitors your drawdown — if equity drops more than the set percentage from its peak, all trading stops and open positions are closed.

-

Toggle Turn on account protection to enable

-

Set the Maximum drawdown allowed (e.g. 50%)

⚠️Warning: The actual drawdown may exceed your set protection level. Account protection checks your equity periodically — not on every tick. In fast-moving markets, prices can gap beyond your threshold before the system triggers. Treat this as a safety net, not a guarantee of a precise stop level.

Click Submit.

[image]

Your eToro account is now connected. AlgoCloud will automatically retrieve your account data, including the available balance.

## Deploy a strategy to eToro

With the broker connected, you can deploy any strategy from My strategies. Click the ⋮ menu next to a strategy and select Start trading.

[image]

The deployment wizard has 4 steps:

## 1. Details

Set the deployed name, select your eToro account, and choose the traded instruments. For example, [[S&P 500]] as the main chart on D1 timeframe with SPY as the subchart. A green ✅ confirms the symbol is available on eToro.

Set execution settings: Entry at On Bar Open, Exit at On Bar Close.

[image]

Click the Main chart dropdown to select from available stock universes:

[image]

## 2. Money management

Configure how the strategy allocates capital:

-

Max open positions — e.g. Long: 5, Short: 0

-

Money management method — Risk fixed % of account (Stockpicker)

-

Risk in % — e.g. 20

-

Allow fractional shares — Enable if supported. Set Fractional decimals: 4, Fractional step: 0.01

[image]

## 3. Checks & verifications

Review the account protection settings.

## 4. Final review

Review the full strategy rules and deployment configuration. Read the risk disclaimer, then click Start Strategy.

[image]

## Monitoring

After deployment, go to Trading → Demo trading (or Live trading). The Deployed strategies tab shows your active strategy, its status, the connected eToro account, and capital allocation.

[image]

Use the additional tabs to monitor activity:

-

Open Trades — Currently open positions

-

Trade history — Completed trades with P&L

-

Trading Log — Entry triggers, orders, and trade executions

[image]

Expand individual entries to see trade details — stock symbols, order types, prices, quantities, and timestamps.

[image]

For the most detailed view, open the Strategy log to see the raw execution log with every signal and action.

[image]

## Setting up commissions for eToro

Before backtesting or deploying, make sure the commission settings match eToro's fee structure. In the Strategy Editor, click Settings and open the Commission dialog.

eToro offers commission-free stock trading, but there may be spread costs. Select the appropriate commission type based on your setup.

[image]

## Notes

-

eToro integration supports both Demo and Real (live) accounts in AlgoCloud.

-

Start with a Demo (paper) account to test before trading with real money.

-

To reset API key, go to Settings → Trading → API Key Management in eToro and generate the new one. Then update the connection in AlgoCloud.

-

The API key Environment (Real/Demo) must match the Account type in AlgoCloud.
