<#--
  ============================================================================
  MoneyManagement.inc - money-management subsystem (NinjaTrader).
  ============================================================================
  Loads the strategy's <MoneyManagement type="..."> section and emits, for the
  selected type, its C# variable declarations (into the class body) and its size
  expression (into the EnterLong/EnterShort quantity, when the Size formula is
  UseGlobalMM). Mirrors JForex/MoneyManagement.inc + Size.inc, rewritten to C#.

  Contract:
    - printMoneyManagementVariables : include MoneyManagement/<type>_variables.tpl
    - printMoneyManagementMethod    : include MoneyManagement/<type>_method.tpl
                                      (the bare size expression; lot->contract
                                       conversion is applied by printSizeMethod)
    - printMMSize                   : read a #key# value from <Method><Params>
                                      (3.9.129) or the flat <params> (3.9.133+)

  A MM type without its _variables/_method .tpl makes the include throw, so the
  export refuses instead of guessing a position size.
-->
<@moneyManagementLoad />

<#-------------------------------------------------------------->
<#-- Load the <MoneyManagement> section into `moneyManagement` (if present). -->
<#macro moneyManagementLoad>
  <#if doc.StrategyFile.Strategy.MoneyManagement[0]??>
    <#assign moneyManagement = doc.StrategyFile.Strategy.MoneyManagement />
  </#if>
</#macro>

<#-------------------------------------------------------------->
<#-- True when the strategy carries a <MoneyManagement> section. -->
<#function hasMoneyManagement>
  <#return doc.StrategyFile.Strategy.MoneyManagement[0]?? />
</#function>

<#-------------------------------------------------------------->
<#-- Read a parameter value (e.g. "#Size#") from <MoneyManagement>. Handles both XML shapes:
     <Method><Params><Param/> (through SQX 3.9.129, and always on the GUI-export path, which
     rebuilds this shape - StrategyXMLModifier.getMoneyManagement) and the flat <params><Param/>
     written into strategies by SQX 3.9.133+. A strategy carries exactly one shape, so the fallback
     can never double-print.

     A THIRD shape reaches here: neither. A strategy drawn in AlgoWizard and exported straight out
     carries no settings.xml at all - it has never been backtested, so nothing wrote one - and both
     lookups come back empty. Emitting nothing would leave `mmLots = ;` in the generated C#, which
     does not compile.

     So the size falls back to one unit, as on MetaTrader, JForex and EasyLanguage - their
     printMMSizeNumber ends in `<#if !found>1</#if>`. A missing size is not a missing TEMPLATE: that
     case refuses loudly a few lines below, because there the export cannot know what the method
     even computes. -->
<#macro printMMSize paramKey><@compress_single_line>
<#local found = false />
<#local mmParams = doc.StrategyFile.Strategy.MoneyManagement.Method.Params.* />
<#if mmParams?size == 0>
   <#local mmParams = doc.StrategyFile.Strategy.MoneyManagement.params.* />
</#if>
<#list mmParams as param>
   <#if param.@key == paramKey><#if param?ends_with(".0")>${param?replace(".0", "")}<#else>${param}</#if><#local found = true /></#if>
</#list>
<#if !found>1</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- Emit the selected MM type's C# variable declarations into the class body. -->
<#-- Bare include, like mt4Size.inc:156 / mt5Size.inc:105 / JForex Size.inc:154 / EasyLanguage
     Size.inc:32 / pseudoBlocks.inc:240 - all five let a missing MM template throw. Both callers
     refuse first (SourceCodeServlet.checkMMAllowed and SourceCode.generate), so the include is
     reached only for a type that HAS a template - and if that ever stops holding, a refusal beats a
     wrong position size. Every shipped type has both templates, same set as MetaTrader5. -->
<#macro printMoneyManagementVariables><#if hasMoneyManagement()>
<#include "/NinjaTrader/MoneyManagement/" + moneyManagement.@type + "_variables.tpl">
</#if></#macro>

<#-------------------------------------------------------------->
<#-- Emit the selected MM type's size expression (bare; converted by printSizeMethod). The action `block`
     is passed so risk-based MM types can read the entry's SL distance (printSLTicks), and `priceRef`, the
     price the order is sized at, reaches them as sqMMPriceRef. -->
<#macro printMoneyManagementMethod block priceRef="Close[0]"><@compress_single_line><#global sqMMPriceRef = priceRef><#if hasMoneyManagement()><#include "/NinjaTrader/MoneyManagement/" + moneyManagement.@type + "_method.tpl"><#else>1</#if></@compress_single_line></#macro>
