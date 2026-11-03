<#-- Indicator Highest -> Nth-highest value of the child indicator over Period bars. Period is fixed
     at export, so the per-bar values are unrolled into an inline array and ranked by sqNthHighest.
     Period via getParamResolved: a variable-bound Period resolves to the variable's <value> at
     generation time (plain getParam would silently size the array with the default 5).
     Mirrors IndicatorHighest.java (sort + Nth). -->
<#assign ihPeriod = getParamResolved(block, "#Period#", "5")?number />
<#assign ihShift = shift?number />
<#global sqUsesNthValue = true>sqNthHighest(new double[] {<#list 0..(ihPeriod-1) as i><@printBlockChild block "#Indicator#" "${(ihShift+i)?c}"/><#sep>, </#list>}, <@printParam block "#NthValue#" "0" />)
