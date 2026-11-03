<#-- Simple Moving Average -> native NinjaScript SMA(input, period)[barsAgo].
     Docs: https://ninjatrader.com/support/helpguides/nt8/moving_average_-_simple_sma.htm
     Output e.g.: SMA(Close, 14)[0] -->
<@printSeriesAt block shift>SMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>