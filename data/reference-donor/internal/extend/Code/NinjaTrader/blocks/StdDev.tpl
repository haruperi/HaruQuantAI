<#-- Standard Deviation -> native NinjaScript StdDev(input, period)[barsAgo].
     Docs: https://ninjatrader.com/support/helpguides/nt8/standard_deviation_stddev.htm
     Uses the native overload StdDev(ISeries<double> input, int period).
     Output e.g.: StdDev(Close, 14)[0] -->
<@printSeriesAt block shift>StdDev(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>