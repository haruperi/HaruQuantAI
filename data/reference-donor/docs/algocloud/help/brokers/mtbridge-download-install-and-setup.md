# AlgoCloud / MTBridge - download, install and setup

> Offline copy of the AlgoCloud help article (fetched 2026-08-07).

## Download script

Below you can find link for the MetaTrader part of the bridge. (we will install this file later in MetaTrader)

Last version released 26.02.2026

MT5 Bridge download link

## Order Type Limitations in MTBridge

MTBridge currently supports only market orders.

Stop or limit orders are not supported due to technical and policy limitations imposed by Darwinex Zero and some other connected brokers.

This means that any strategy relying on pending orders (such as Buy Stop, Sell Stop, Buy Limit, or Sell Limit) will not function as intended when executed through MTBridge.

If your strategy uses these order types, you will need to rewrite or adapt the logic so that it opens positions directly using market orders instead. For example:

-

Replace entry conditions that trigger a pending order with a market execution at the moment the condition is met.

-

Recalculate entry prices and risk management accordingly.

-

Use internal logic or virtual stop levels to simulate pending order behavior if needed.

This limitation applies to both StrategyQuant X-generated strategies and custom-coded systems that rely on MTBridge for order execution.

We are continuously evaluating options for broader broker compatibility and potential support for additional order types in future releases. However, at this stage, market orders are the only supported execution type.

# AlgoCloud setting

-

log in to your AlgoCloud account

-

open the tab in the left menu Live trading → Connected brokers

-

for connected accounts in the Publishing column, click the link Manage

[image]

## Channel settings

4. click the Add new channel link below

[image]

5. click on the word New channel and name the channel as you like (e.g. DarwinexZero) and continue with the next arrow

[image]

6. in the window Your channel ID is the code you will need to connect to MetaTrader5

[image]

7. Next, check which information you want to share

a) open and closed positions

b) history of closed stores

[image]

8. check which strategies you want to copy to MT5

a) select all strategies

[image]

b) or select only certain strategies and click the button + Add

[image]

9. save the settings with the Update button and close with the Close button

[image]

# Installation in MetaTrader5

-

extract the ZIP file you downloaded in the previous step. You will see a folder (eg mtbridge-20250926). There are 3 more folders - Experts, Images, Libraries

[image]

2. in MetaTrader5 open the main folder of the program. You can find it in the main menu File → Open Data folder and open the folder MQL5, where there are other folders

[image]

[image]

3. Copy all 3 components (Experts, Images, Libraries) from the unzipped archive to MQL5 folder

[image]

4. restart MetaTrader5. Then you will see the new ACBridge script

[image]

5. load this script into any chart. In the following window, it is necessary to check the option of loading DLL libraries

[image]

6. in AlgoCloud, click Copy ID to copy the Channel ID, then paste it into the AC Channel ID input field in Inputs bookmark

AlgoCloud

[image]

MetaTrader5

[image]

7. variable Max Trade Size is the maximum number of purchased shares per 1 position. Set according to your broker. The default setting for DarwinexZero is 1000.

8. variable Production version leave on the value True

9. confirm everything with the OK button. In the window Navigator the script is loaded ACBridge

[image]

10. in the graph window you will see the current version of the script and the connection status Connected

[image]

11. you will see the status Connection failed if ACBridge is set incorrectly

[image]

12. now ACBridge is connected to AlgoCloud and orders will be copied

13. as a confirmation that the order has been sent from AlgoCloud, you will see a mark next to each position in the Comment column AC Trade + transaction number

[image]

NOTE:

-

For the script to work properly, you must have Algorithmic Trading and DLL import enabled in the MT5 options. Path from the main menu:

Tools→ Options → Expert Advisors bookmark

[image]
