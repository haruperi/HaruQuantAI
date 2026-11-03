<#-- Volume Weighted Average Price from the installed SqVWAP indicator; NinjaTrader has no native
     Managed VWAP. Rolling sum((O+H+L+C)/4 * Vol)/sum(Vol). See printVWAPValueAt. -->
<@printVWAPValueAt block shift />
