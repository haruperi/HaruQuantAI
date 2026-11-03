# Why my demo strategy stopped running

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Demo (paper) strategies in AlgoCloud can stop running on their own in a few situations. This article explains each one and how to get back to a running state.

# Reasons a demo strategy stops

## 1. Account inactivity

If you don't log in to AlgoCloud for an extended period while you have a demo strategy running, AlgoCloud stops the strategy to free up cloud resources. Before that happens, we send a reminder email with the subject "You are no longer interested in our platform". It's a pre-deactivation reminder — not a cancellation of your account.

Fix: Log in, go to My strategies and redeploy the strategy.

## 2. Plan expired or downgraded

Free and paid plans have a cap on the number of running strategies. When your plan ends (free trial, Pro, etc.), strategies over the cap are stopped first — and you'll get a "your strategies were disabled" email.

Fix: Renew or upgrade your plan, then redeploy the strategy.

## 3. Account protection triggered

If you enabled account protection during deployment and the account's drawdown exceeded the threshold you set, AlgoCloud closes all open positions and stops the strategy. The Strategies screen will show "Stopped — account protection".

Fix: Review the losses, decide whether to redeploy with a higher threshold or revised strategy rules.

## 4. Error during order placement

If the broker repeatedly rejects orders (auth failed, insufficient qty, etc.), AlgoCloud stops the strategy to prevent runaway errors.

Fix: Open the Trading log, find the last error, and fix the root cause — typically a broker permission or symbol availability issue.

# How to restart a stopped strategy

-

Go to My strategies.

-

Open the Actions (⋮) menu next to the stopped strategy.

-

Choose Start trading and walk through the deployment wizard again.

# Resetting a paper account

If the paper account's balance or history is a mess and you want a clean slate:

-

Stop all strategies deployed to that account (from the Strategies screen).

-

Go to Live trading → Connected brokers.

-

Open the AlgoCloud demo broker (or your broker's paper account) and click Reset.

Resetting deletes all open and historical trades and restores the starting balance.
