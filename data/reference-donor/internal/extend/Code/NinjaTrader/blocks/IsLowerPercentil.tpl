<#-- Is lower percent rank -> share of past Bars values that the current value is
     below is above Percentile %. count = 1 + sum over i=1..Bars-1 of
     (val[Shift] < val[Shift+i]). Bars fixed at export -> unroll (Bars/Shift via
     getParamResolved so a variable binding resolves to the variable's <value>).
     Percentile is a pure runtime comparison operand, so it stays variable-aware via
     printParam (a bound variable is referenced by name at runtime).
     Mirrors SQ.Blocks.Comparisons.IsLowerPercentil.java. -->
<#assign cs = (getParamResolved(block, "#Shift#", "0")?number) + (shift?number) />
<#assign bars = getParamResolved(block, "#Bars#", "10")?number />
(((1<#list 1..(bars-1) as i> + (<@printCmpOperand block "#Indicator#" "${cs?c}" "5" /> < <@printCmpOperand block "#Indicator#" "${(cs+i)?c}" "5" /> ? 1 : 0)</#list>) * 100.0 / ${bars?c}) > <@printParam block "#Percentile#" "50" />)
