<#-- Hull Moving Average -> the installed SqHullMovingAverage indicator. Mirrors
     HullMovingAverage.java (three AverageCalculator LWMAs), warm-up included.
     Output e.g.: SqHullMovingAverage(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqHullMovingAverage(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
