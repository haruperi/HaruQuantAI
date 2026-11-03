<#-- Ichimoku line value from the installed SqIchimoku indicator. #Line# selects the output: 0=Tenkan,
     1=Kijun, 2=SenkouA, 3=SenkouB (Chikou is not produced; it reads SenkouB). NinjaTrader has no native
     Managed Ichimoku. See printIchimokuValueAt (Parameters.inc). -->
<@printIchimokuValueAt block getParam(block, "#Line#", "0") shift />
