# Alpaca Markets

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Alpaca.Markets provides an easy to use API for trading, and connecting this broker to AC is simple.

## Link account for Alpaca

## Step 1 - Get Alpaca API keys

First of all, log in to your account at Alpaca.markets.

Once logged, select your account from the left main menu. We'll use Alpaca paper trading account in this example, but the method is the same also for live trading account.

[image]

Choosing an account gets you to the account screen. There you see API keys mentioned on the right.

[image]

If you didn't do it before you don't have API key yet, so click on Generate New Keys.

[image]

Keys will be generated and you'll immediately see your keys:

[image]

You will need to enter both API Key ID and Secret key in AC cloud in order to connect to this Alpaca account.

Note

Write down the secret key and store it in a safe place. Once you'll refresh the page the secret key will be lost and you will be not able to view it again.

​

​

## Step 2 - Link to broker in AC cloud

Once you have your Alpaca keys you can create a connection in AlgoCloud.

Go to Connected accounts screen. This is where you manage all your connections to brokers.

Click on Link account button.

[image]

This will open wizard that will lead you through the process.

The first step is to choose your broker from the list of supported ones.

[image]

The second step is specifying the connection.

Name your connection - you can give your new connected account any name - it will be used internally in AlgoCloud.

Put your Alpaca Api Key ID as Client ID and Alpaca Secret key as Client Secret.

[image]

The third step is (optionally) turn on Account protection.

[image]

After clicking Next the connection is created.

[image]

AlgoCloud will then try to log in to Alpaca API and retrieve basic information about your account like balance, equity, positions.

## Resetting accounts, regenerating keys

This applies to paper trading or demo accounts - brokers usually allow you to reset your paper trading accounts, so you can start anew. The exact features and functionality of a reset depends on the broker.

##
