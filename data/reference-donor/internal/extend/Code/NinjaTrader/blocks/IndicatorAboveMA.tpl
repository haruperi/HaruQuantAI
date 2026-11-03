<#-- IndicatorAboveMA -> sqIndicatorAboveMA (SQIndicators.inc). The nested #Indicator# is above its own moving average.
     The child is passed as a C# lambda over the bar offset, because the Java evaluates it at
     shift + i for i = 0..#Period#-1 (IndicatorMAComparisonBlockAbstract.calculateMA) - a shift
     that is only known at runtime. See printIndicatorLambda in Parameters.inc.
     #MAType#: 1 = Simple, 2 = Exponential, 3 = Weighted, 4 = Hull. -->
<#global sqUsesBlockMA = true>(sqIndicatorAboveMA(<@printIndicatorLambda block />, <@printParam block "#Period#" "14" />, <@printParam block "#MAType#" "1" />, <@printCIShift block shift />))