# 3. Deploy a strategy

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

To start trading a strategy on AlgoCloud you need to deploy it — deployment means you configure which strategy is traded, with what settings, and on which connected broker. The strategy is then executed in the cloud.

From then on (until stopped) it will trade autonomously — every bar the strategy rules are evaluated and trades are opened or closed using the connection to your broker.

# Prerequisites

Before you can deploy a strategy, you need:

-

A saved strategy in My strategies. Unsaved drafts cannot be deployed.

-

At least one connected broker — or you can deploy to the default AlgoCloud demo broker to trade with virtual money.

-

The strategy's traded symbols must be available at the selected broker (AlgoCloud checks this automatically in the deployment wizard — you'll see a green ✅ or red ❌).

# How to deploy a strategy

You can start trading a strategy from two places. In both cases the deployment wizard opens and leads you through the configuration in a few steps.

See Deploying your strategy for a full walkthrough of the wizard.

# 1. Start trading from Strategy Editor

If you have your strategy open in the Strategy Editor, click the Start trading button in the top-right.

[image]

Note: you need to save your strategy before it can be deployed.

# 2. Start trading from My strategies

The other way is from the My strategies screen. Find your strategy, open the Actions (⋮) menu and choose Start trading.

[image]

# Allocation budget

During deployment you set how much capital the strategy can use. This is the allocation budget — the maximum portion of your broker account the strategy is allowed to trade with. If you deploy multiple strategies on one account, each one gets its own budget, and AlgoCloud enforces the limit at the order level.

# Paper vs Live deployment

In the deployment wizard you select the target broker account. If you pick the AlgoCloud demo broker or your broker's paper account, the strategy runs on virtual money. If you pick a live account, it trades with real money. The behaviour is otherwise identical — same data feed, same rules.

# Troubleshooting

## I don't see the "Start trading" / Deploy button

Check that:

-

The strategy is saved (unsaved drafts have a different Action menu).

-

Your plan allows live/paper deployments. Free trial or expired plans may hide the button.

-

You have at least one connected broker (even the AlgoCloud demo broker).

## My symbols show a red ❌ in step 1 of the wizard

The symbol is not available at the selected broker. Either switch to a broker that supports it, or adjust the strategy to use supported symbols.

## "Cannot deploy — strategy exceeds account budget"

The allocation budget you selected is higher than your free broker balance. Lower the budget or deposit funds.
