# Robomarkets (Beta)

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

Connection to Robomarkets is available for beta testing.

Robomarkets provides an easy to use API for trading, and connecting this broker to AC is simple.

Important Note

AlgoCloud works only with Robomarkets NETTING accounts!

If you have HEDGING account it will not work with AlgoCloud.

## Link account for Robomarkets

## Step 1 - Prepare your Robomarkets credentials

You will need Robomarkets Account ID and Access token.

Log in to your Robomarkets Stockstrader.

Account ID is visible on the top left corner - you should use only the number, without "-demo" or "-real" postfic.

Access token can be requested by clicking on the API integration menu on the top right.

[image]

​

​

## Step 2 - Link to broker in AC cloud

Once you have your Robomarkets credentials keys you can create a connection in AlgoCloud.

Go to Connected accounts screen. This is where you manage all your connections to brokers.

Click on Link account button.

[image]

This will open wizard that will lead you through the process.

The first step is to choose your broker from the list of supported ones. You can give your new connected account any name - it will be used internally in AlgoCloud.

[image]

The second step is specifying the connection.

Put your Robomarkets Account ID and Access token there.

[image]

The third step is (optionally) turn on Account protection.

[image]

After clicking Next the connection is created.

[image]

AlgoCloud will then try to log in to Robomarkets API and retrieve basic information about your account like balance, equity, positions.

​
