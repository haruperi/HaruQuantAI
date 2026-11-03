<#--
  COT symbol inputs, shared by the MetaTrader 4, MetaTrader 5, NinjaTrader and EasyLanguage exports.

  Every COT market a strategy reads becomes one string input COTSymbol1, COTSymbol2, ... numbered in the
  order the markets first appear in the strategy. Its default is the market SQX resolved at export, and the
  trader can type any other COT market. The exported code builds the COT data identifier from the input:
  COTSymbol1 + "_52W" instead of "ES_52W".

  cotSymbols         every market, in input order
  cotCheckedSymbols  markets read through the SqCOT data files (COT blocks, SqCOT / SQ_COT_GetValue custom
                     data). The strategy checks at start-up that the data file of each of them exists.
                     Markets read only through sqCOTData() are left out: that runtime downloads its own data
                     and reports a market the server does not know.

  Each Main.tpl calls cotCollectSymbols before it prints the inputs or any block.
-->
<#global cotSymbols = []>
<#global cotCheckedSymbols = []>

<#-- A COT data identifier inside a custom-data source code: "ES_52w", "6A_156w" -->
<#assign cotIdentifierPattern = '"([A-Za-z0-9]+)_(?:52|156)[wW]"'>

<#--
  Walk the strategy and collect the COT markets.
  @param node      the subtree to scan, normally doc.StrategyFile.Strategy
  @param codeAttr  the custom-data source code attribute of this platform ("mt4", "mt5", "el"), or "" when the
                   platform exports no COT custom data
-->
<#macro cotCollectSymbols node codeAttr>
<#list node?children as c><#if c?node_type == 'element' && c?node_name != "CustomIndicators">
  <#if (c.@mI[0]!"") == "COT" && !c.@cdataIndyName[0]?? && cotHasSymbolParam(c)>
    <#local sym><@printParam c "#CotSymbol#" /></#local>
    <#local sym = sym?trim>
    <#-- the VixProxy templates read VX when the block carries no symbol -->
    <#if sym == "" && (c.@key[0]!"")?contains("VixProxy")><#local sym = "VX"></#if>
    <@cotAddSymbol sym true />
  <#elseif c.@cdataIndyName[0]?? && codeAttr != "">
    <#local code = "" + (c["@" + codeAttr][0]!"")>
    <#local readsDataFiles = !code?contains("sqCOTData(")>
    <#list code?matches(cotIdentifierPattern) as m>
      <@cotAddSymbol m?groups[1] readsDataFiles />
    </#list>
  </#if>
  <@cotCollectSymbols c codeAttr />
</#if></#list>
</#macro>

<#-- A COT block without a COT Symbol setting reads no COT market -->
<#function cotHasSymbolParam block>
  <#list block.* as param>
    <#if (param.@key[0]!"") == "#CotSymbol#"><#return true></#if>
  </#list>
  <#return false>
</#function>

<#macro cotAddSymbol sym checked>
<#if sym != "">
  <#if !cotSymbols?seq_contains(sym)><#global cotSymbols = cotSymbols + [sym]></#if>
  <#if checked && !cotCheckedSymbols?seq_contains(sym)><#global cotCheckedSymbols = cotCheckedSymbols + [sym]></#if>
</#if>
</#macro>

<#--
  The input that holds a COT market, e.g. COTSymbol2. A market that was not collected (a template rendered
  outside Main.tpl) stays a string literal, exactly as before the inputs existed.
-->
<#function cotSymbolInput sym>
  <#if (cotSymbols??) && cotSymbols?seq_contains(sym?trim)>
    <#return "COTSymbol" + (cotSymbols?seq_index_of(sym?trim) + 1)>
  </#if>
  <#return "\"" + sym + "\"">
</#function>

<#-- The COT data identifier of a market and period: COTSymbol1 + "_52W", or "ES_52W" for a market that was not collected -->
<#function cotIdentifier sym period>
  <#if (cotSymbols??) && cotSymbols?seq_contains(sym?trim)>
    <#return cotSymbolInput(sym) + " + \"_" + period + "\"">
  </#if>
  <#return "\"" + sym + "_" + period + "\"">
</#function>

<#--
  The error of a COT input whose market has no COT data file, as a string expression. MQL, C# and EasyLanguage
  all join strings with +. The 52W file stands for the market: the COT download always writes 52W and 156W.
-->
<#function cotMissingSymbolMessage input>
  <#return '"' + input + ': COT symbol \'" + ' + input + ' + "\' does not exist. No COT data file " + ' + input
    + ' + "_52W was found. Check the symbol, or download the COT data. The strategy will not trade."'>
</#function>

<#--
  MQL4 / MQL5: sqCOTCheckSymbols() refuses a COT input that names a market without a data file - a
  mistyped symbol would otherwise read empty COT values and trade on them. COT_IsAvailable() comes from
  SqCOTReader.mqh, which SqCOTHelper.mqh includes, and answers from the files the SqCOT indicator reads.
  OnInit runs the check when the data is already there (a missing market stops the EA); otherwise
  sqCOTTradingAllowed() runs it once on the first tick after the data arrives, and a missing market keeps
  the OnTick gate closed.
-->
<#macro printCotSymbolCheckMql>
bool sqCOTCheckSymbols() {
<#list cotCheckedSymbols as cotSymbol>
<#local input = cotSymbolInput(cotSymbol)>
   if(!COT_IsAvailable(${input} + "_52W")) {
      Alert(${cotMissingSymbolMessage(input)});
      return(false);
   }
</#list>
   return(true);
}

bool sqCOTSymbolsChecked = false;
bool sqCOTSymbolsInvalid = false;

// OnTick gate: true once the COT data is loaded and every COT symbol input has its data file
bool sqCOTTradingAllowed() {
   if(sqCOTSymbolsInvalid || !SqCOT_DataReady()) {
      return(false);
   }
   if(!sqCOTSymbolsChecked) {
      if(!sqCOTCheckSymbols()) {
         sqCOTSymbolsInvalid = true;
         return(false);
      }
      sqCOTSymbolsChecked = true;
   }
   return(true);
}
</#macro>

<#-- A custom-data source code with each "ES_52w" identifier read from its input: COTSymbol1 + "_52w" -->
<#function cotRewriteCode code>
  <#if !(cotSymbols??)><#return code></#if>
  <#local out = code>
  <#list cotSymbols as sym>
    <#if sym?matches("[A-Za-z0-9]+")>
      <#local out = out?replace('"' + sym + '_(52|156)([wW])"', cotSymbolInput(sym) + ' + "_$1$2"', 'r')>
    </#if>
  </#list>
  <#return out>
</#function>
