<#-- Moving Average with a method selector (#MAMethod#): 0=Simple, 1=Exponential, 2=Smoothed, 3=Linear
     weighted. Simple and Exponential map to native NT SMA/EMA, Smoothed and Linear weighted to the
     installed SqSMMA/SqLWMA indicators, like printMAValueAt but reading #MAMethod#. Mirrors
     MovingAverage.java (AverageCalculator method 0-3).
     Output e.g.: SqSMMA(Close, 14).Values[0][0] -->
<#assign maMethod = getParam(block, "#MAMethod#", "0") />
<#if maMethod == "2" || maMethod == "3"><#global sqUsesIndicatorPackage = true></#if><#if maMethod == "1"><@printSeriesAt block shift>EMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt><#elseif maMethod == "2"><@printSeriesAt block shift>SqSMMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt><#elseif maMethod == "3"><@printSeriesAt block shift>SqLWMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt><#else><@printSeriesAt block shift>SMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt></#if>
