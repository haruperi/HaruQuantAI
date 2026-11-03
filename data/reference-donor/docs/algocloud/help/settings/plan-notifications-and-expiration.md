# Plan notifications &amp; expiration — what each email means

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

AlgoCloud sends email notifications when your plan status changes or is about to expire. This article explains what each notification means and what to do if the email contradicts your actual plan status.

# "Your Pro plan just upgraded but I got an expiration email"

This is a timing issue, not a billing bug. Expiration notifications are queued in advance — usually a few hours before the plan actually expires. If you upgrade to Pro right around that time, the sequence looks like this:

-

Your free plan is about to expire → notification is queued.

-

You buy Pro (plan is now active).

-

A few minutes later, the queued "your plan expired" email is delivered.

The expiration email does not reverse your Pro purchase. Go to Billing — if it says Current plan: Pro and shows the payment in Payment history, your plan is active. You can safely ignore the expiration email.

If Billing shows the plan as expired or not Pro, forward the email and the transaction details to [email protected].

# "Your strategies were disabled"

This email is sent when AlgoCloud stopped one or more of your deployed strategies. Common reasons:

-

Plan expired — free and paid plans have limits on the number of running strategies. When the plan downgrades, strategies over the limit are stopped.

-

Demo account inactivity — demo strategies are stopped after long periods of inactivity on the account. See Why my demo strategy stopped running.

-

Account protection triggered — the drawdown threshold you set during deployment was hit; AlgoCloud closed positions and stopped the strategy.

-

Broker disconnected — if the API key expired or was revoked, AlgoCloud cannot place orders and stops the strategy.

# "You are no longer interested in our platform"

This is sent when a demo (paper) strategy has been running on your account without you logging in for an extended period. It's a pre-deactivation reminder, not a final notice. To keep the strategy running, log in to AlgoCloud and redeploy it from My strategies.

# How to check your plan

Go to Billing. You'll see:

-

Current plan (Free / Basic / Pro)

-

Renewal date

-

Payment history — each charge with the date and amount

-

Usage — how many of the plan's strategy / backtest slots you're using

If anything there contradicts what you think you paid for, contact [email protected] with the transaction ID.
