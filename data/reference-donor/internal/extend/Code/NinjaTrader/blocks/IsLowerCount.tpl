<#-- Is lower for X bars -> left < right at every one of Bars consecutive shifts
     (or left <= right everywhere + at least one strict < when NotStrict). Bars is fixed
     at export -> unroll. Bars/Shift/NotStrict via getParamResolved: a variable-bound param resolves
     to the variable's <value> at generation time (plain getParam would unroll with the default).
     Mirrors SQ.Blocks.Comparisons.IsLowerCount.java. -->
<#assign cs = (getParamResolved(block, "#Shift#", "0")?number) + (shift?number) />
<#assign bars = getParamResolved(block, "#Bars#", "2")?number />
<#assign notStrict = (getParamResolved(block, "#NotStrict#", "false") == "true") />
(<#list 0..(bars-1) as i>(<@printCmpOperand block "#IndicatorLeft#" "${(cs+i)?c}" "5" /> <#if notStrict><=<#else><</#if> <@printCmpOperand block "#IndicatorRight#" "${(cs+i)?c}" "5" />)<#if i < bars-1> && </#if></#list><#if notStrict> && (<#list 0..(bars-1) as i>(<@printCmpOperand block "#IndicatorLeft#" "${(cs+i)?c}" "5" /> < <@printCmpOperand block "#IndicatorRight#" "${(cs+i)?c}" "5" />)<#if i < bars-1> || </#if></#list>)</#if>)
