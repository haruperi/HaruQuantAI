<#-- Exponential Moving Average -> native NinjaScript EMA(input, period)[barsAgo].
     Docs: https://ninjatrader.com/support/helpguides/nt8/moving_average_-_exponential_e.htm
     Output e.g.: EMA(Close, 14)[0] -->
<@printSeriesAt block shift>EMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>