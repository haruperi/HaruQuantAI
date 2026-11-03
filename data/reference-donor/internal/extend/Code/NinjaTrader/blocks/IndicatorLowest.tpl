<#-- Indicator Lowest -> Nth-lowest value of the child indicator over Period bars. Period is fixed
     at export, so the per-bar values are unrolled into an inline array and ranked by sqNthLowest.
     Period via getParamResolved: a variable-bound Period resolves to the variable's <value> at
     generation time (plain getParam would silently size the array with the default 5).
     Mirrors IndicatorLowest.java (sort + Nth). -->
<#assign ilPeriod = getParamResolved(block, "#Period#", "5")?number />
<#assign ilShift = shift?number />
<#global sqUsesNthValue = true>sqNthLowest(new double[] {<#list 0..(ilPeriod-1) as i><@printBlockChild block "#Indicator#" "${(ilShift+i)?c}"/><#sep>, </#list>}, <@printParam block "#NthValue#" "0" />)
