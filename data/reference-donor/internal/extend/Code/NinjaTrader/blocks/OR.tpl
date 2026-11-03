<#-- Logical OR of all child conditions -> (c1||c2||...). Multi-child, mirrors JForex Or (||).
     compress_single_line collapses spaces around || (compact, valid C#) - see And.tpl. -->
<@compress_single_line>(<#list block.* as child><#if !child?is_first> || </#if><@printBlock child /></#list>)</@compress_single_line>
