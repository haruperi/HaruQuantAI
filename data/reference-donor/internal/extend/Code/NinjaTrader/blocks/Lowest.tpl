<#-- Lowest value over #Period# bars -> native NinjaScript MIN(input, period)[barsAgo].
     SQX rolling min = NT MIN. Input from #ComputedFrom#. See Lowest.java. -->
<@printSeriesAt block shift>MIN(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>
