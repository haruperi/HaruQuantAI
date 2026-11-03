<#-- Logical AND of all child conditions -> (c1&&c2&&...). Multi-child: iterates the block's operands
     (like JForex And, && instead of nothing). compress_single_line collapses the spaces around && (the
     child templates carry trailing newlines), so the operator renders compact - valid C#. -->
<@compress_single_line>(<#list block.* as child><#if !child?is_first> && </#if><@printBlock child /></#list>)</@compress_single_line>
