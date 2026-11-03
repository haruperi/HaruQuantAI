<#-- Rate of Change -> the installed SqROC indicator. Mirrors ROC.java: Close
     only, 0 before bar period.
     Output e.g.: SqROC(Close, 14).Values[0][0] -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqROC(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>