<#-- Triple Exponential Moving Average -> native NinjaScript TEMA(input, period)[barsAgo].
     Docs: https://ninjatrader.com/support/helpguides/nt8/moving_average_-_triple_expone.htm
     Output e.g.: TEMA(Close, 30)[0] -->
<@printSeriesAt block shift>TEMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>