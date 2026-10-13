# Deploying your strategy

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Note

If you want to trade live, you need to connect your broker account first. If you have no connected account then only AlgoCloud paper trading will be available for you.

Trading on the cloud is available for Single-asset and Stockpicker type of strategies.

To deploy your strategy, find it in My strategies list and click on the Deploy icon:

[image]

This will start a deployment wizard that will lead you through the deployment process in 4 simple steps.

Note

Although the deployment wizard might look complex it is preset with the settings you used in the latest strategy backtest. You won't need to change too much in any of these steps if you want it to trade like in the backtest.

## Step 1 - Details

[image]

## Start details

Deployed name - is simply a name you give to your deployed strategy to recognize it. It can be as same as name of your saved strategy, but you can also change it.

Account - perhaps the most important option here, select the connected account on which you want to trade this strategy.

## Traded instruments

Main chart - preset from the last backtest - it is the stock group or symbol on which the strategy trades.

Subcharts (optional) - some strategies use multiple subcharts, they are specified here.

## Execution settings

Here you set when to trigger strategy entry and exit signals. Again, this is preset from the last backtest.

You can find more details about execution settings here

## Step 2 - Money management

[image]

This is the screen where you can configure position sizing of your strategy - how much money it has allocated for trading.

You can either allocate fixed amount, or % of the current account balance.

There is also a configuration of maximum open positions for stockpicker type of strategy.

## Step 3 - Checks & verifications

[image]

There are different checks and verifications made in this step, depending on your strategy and configuration.

If there is a possible problem you are notified by warning or error.

## Step 4 - Final review

[image]

This is the last step where you should review the strategy with complete rules and configuration summarized in an easy-to-understand Pseudo code.

When everything looks ok you can finish strategy deployment by confirming it with Start Strategy button.

## Managing deployed strategies

Once strategy is deployed and running it will trade autonomously - every day the strategy rules are evaluated and trades are opened or closed according to them using a connection to your broker.

You can see it in the Live trading section - depending on the type of broker account you used you'll see it either under Demo accounts or Real money accounts:

[image]

This is the place where you can manage all your running strategies - watch what they are doing, which trades they opened or closed and you can of course also stop every strategy.
