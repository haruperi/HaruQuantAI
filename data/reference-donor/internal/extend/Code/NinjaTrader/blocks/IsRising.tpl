<#-- Is rising -> indicator strictly increasing over Bars bars (or non-falling + at
     least one rise when NotStrict). Bars is fixed at export time, so unroll the loop.
     Bars/Shift/NotStrict via getParamResolved: a variable-bound param resolves to the variable's
     <value> at generation time (plain getParam would silently unroll with the default).
     Mirrors SQ.Blocks.Comparisons.IsRising.java. -->
<#assign cs = (getParamResolved(block, "#Shift#", "0")?number) + (shift?number) />
<#assign bars = getParamResolved(block, "#Bars#", "2")?number />
<#assign notStrict = (getParamResolved(block, "#NotStrict#", "false") == "true") />
(<#list 0..(bars-2) as k><@printCmpOperand block "#Indicator#" "${(cs+k)?c}" "6" /> <#if notStrict>>=<#else>></#if> <@printCmpOperand block "#Indicator#" "${(cs+k+1)?c}" "6" /><#if k < bars-2> && </#if></#list><#if notStrict> && (<#list 0..(bars-2) as k><@printCmpOperand block "#Indicator#" "${(cs+k)?c}" "6" /> > <@printCmpOperand block "#Indicator#" "${(cs+k+1)?c}" "6" /><#if k < bars-2> || </#if></#list>)</#if>)
