<#-- Highest value over #Period# bars -> native NinjaScript MAX(input, period)[barsAgo].
     SQX HighestCalculator (rolling max) = NT MAX. Input from #ComputedFrom#. See Highest.java. -->
<@printSeriesAt block shift>MAX(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>
