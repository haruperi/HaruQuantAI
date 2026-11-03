<#--
  ============================================================================
  Parameters.inc - per-platform parameter-printing macros (NinjaTrader).
  ============================================================================
  Macros that block templates (blocks/*.tpl) call to emit block parameters as
  NinjaScript C#. The same call site produces different output per platform
  because each platform defines its own printParam/printInput/printShift; this
  file is the NinjaScript flavour.

  Key NinjaScript adaptations vs. the EasyLanguage/JForex source:
    - bar offset is the C# indexer [barsAgo]  (SQX shift == NinjaScript barsAgo);
    - native NT indicators take a price series (Close/Open/...), so printInput
      returns a NinjaScript price series rather than a data handle;
    - a block's #Chart# selects the data series (primary = 0, subcharts = 1+).
-->

<#-------------------------------------------------------------->
<#--
  Emit the value of a named parameter (variable name, formula key, or literal).
  @param block         the block whose <Param> children are scanned.
  @param paramName     the parameter key to print (e.g. "#Period#").
  @param defaultValue  fallback printed when the parameter is absent ("NULL" = none).
  Generates: e.g. "14"  (or a variable name / formula key).
-->
<#macro printParam block paramName defaultValue="NULL"><@compress_single_line>
<#local found=false />
<#-- Find the matching <Param> and delegate its value formatting. -->
<#list block.* as param>
	<#if param.@key == paramName>
      <@printParameterValue param />
      <#local found=true />
   </#if>
</#list>
<#--
  Parameter not present. With a default, emit it - that has to be the value the block itself
  holds when the strategy carries none: an emitted value the StrategyQuant side does not use is
  a silent divergence.

  Without one, emit a marker rather than nothing. Nothing ends the call in a comma and the user
  meets it as "error CS1525: Invalid expression term ')'" at a column of one long line. The
  marker does not compile either, but it names the parameter, it greps, and the codegen suite
  fails on it before any of this reaches a customer.
-->
<#if found==false && defaultValue != "NULL">${defaultValue}<#elseif found==false>SQ_MISSING_PARAM_${paramName?replace("#", "")}</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Format a single <Param> value: strategy variable, formula key, or literal.
  @param param  the <Param> XML node.
  Generates: the variable name (when @variable="true"), the formula key (when a
  <Formula> child is present), or the literal value (trailing ".0" stripped).
-->
<#macro printParameterValue param><@compress_single_line>
<#if param.@variable[0]?? && param.@variable == "true">
   <#-- Parameter is bound to a strategy variable -> emit its name. -->
   <@printVariableName param />
<#elseif param.Formula[0]?? >
   <#-- Parameter holds a formula -> emit the formula key. -->
   <@printFormulaKey param.Formula[0] />
<#else>
   <#-- Plain literal: drop a redundant ".0" so ints stay ints. -->
   <#if param?ends_with(".0")>${param?replace(".0", "")}<#else>${param}</#if>
</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit a strategy variable's C# name by its id (csVariableName: a valid C# identifier, unique in the class).
  @param variableName  the variable id referenced by a parameter.
  Generates: the variable's C# name (e.g. "My Var" -> "My_Var").
-->
<#macro printVariableName variableName><@compress_single_line>
<#list doc.StrategyFile.Strategy.Variables.* as var>
	<#if var.id == variableName>${csVariableName(var)}</#if>
</#list>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Whether the AssignVariable target variable of a block is declared as an int.
  Scans the block for its #Variable# parameter, then resolves that variable's <type>. Used by
  AssignVariable.tpl to cast the double-typed formula RHS to (int) for an int target (C# has no
  implicit double->int conversion; mirrors the MT5 AssignVariable cast). Returns false when the
  target is not int (double/other) or cannot be resolved.
  @param block  the AssignVariable block whose #Variable# target type is checked.
  @return true when the target variable's declared type is int.
-->
<#function assignTargetIsInt block>
<#list block.* as param>
	<#if param.@key == "#Variable#">
		<#list doc.StrategyFile.Strategy.Variables.* as var>
			<#if var.id == param><#return var.type == "int" /></#if>
		</#list>
	</#if>
</#list>
<#return false />
</#function>

<#-------------------------------------------------------------->
<#--
  Emit the key of a <Formula> element verbatim.
  @param Formula  the <Formula> XML node.
-->
<#macro printFormulaKey Formula><@compress_single_line>${Formula.@key}</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Return the raw literal value of a parameter (helper, not a printer).
  @param block         block whose <Param> children are scanned.
  @param paramName     parameter key to read.
  @param defaultValue  returned when absent or when the value is a variable/formula.
  @return the literal string value, or defaultValue.
-->
<#function getParam block paramName defaultValue="NULL">
<#list block.* as param>
	<#-- children without a @key attribute (e.g. nested <Block>/<data> elements) are not params;
	     an empty NodeList must not reach the == (printBlock calls getParam on EVERY leaf item,
	     including comparison items whose children are operand Blocks). -->
	<#if param.@key[0]?? && param.@key == paramName>
      <#if param.@variable[0]?? && param.@variable == "true">
      <#elseif param.Formula[0]?? >
      <#else>
        <#return param>
      </#if>
   </#if>
</#list>
<#return defaultValue>
</#function>

<#-------------------------------------------------------------->
<#--
  Like getParam, but a VARIABLE-BOUND parameter is RESOLVED to the referenced strategy variable's
  <value> at generation time instead of silently falling back to the default.
  Required by the loop-UNROLLING templates (IsRising/IsFalling, IsGreaterCount/IsLowerCount,
  IsGreaterPercentil/IsLowerPercentil, IndicatorHighest/IndicatorLowest): their #Bars#/#Period#/#Shift#
  drive how many terms are emitted, so the value must be a literal at generation time - a runtime
  variable reference cannot size an unrolled expression. The builder binds these optimizable params to
  variables, so plain getParam would silently unroll with the default (e.g. "rising over 10 bars" degrading to "rising over 2 bars").
  Caveat: if the strategy REASSIGNS the bound variable at runtime (AssignVariable), the unrolled shape
  stays at the initial <value> - acceptable: builder optimization variables are not runtime-assigned,
  and the SQX backtest itself sizes the window from the value the variable holds when evaluated.
  Formula-bound params still fall back to the default (cannot be resolved statically).
  @param block         block whose <Param> children are scanned.
  @param paramName     parameter key to read.
  @param defaultValue  returned when absent, formula-bound, or the variable id cannot be resolved.
  @return the literal string value (own or the bound variable's <value>), or defaultValue.
-->
<#function getParamResolved block paramName defaultValue="NULL">
<#list block.* as param>
	<#if param.@key == paramName>
      <#if param.@variable[0]?? && param.@variable == "true">
        <#list doc.StrategyFile.Strategy.Variables.* as var>
          <#if var.id == param><#return var.value[0]!defaultValue></#if>
        </#list>
        <#return defaultValue>
      <#elseif param.Formula[0]?? >
        <#return defaultValue>
      <#else>
        <#return param>
      </#if>
   </#if>
</#list>
<#return defaultValue>
</#function>

<#-------------------------------------------------------------->
<#--
  Emit the input price series for a NinjaScript indicator.
  @param block        the indicator block.
  @param quoteSymbol  unused (kept for signature parity with other platforms).
  Generates: a NinjaScript price series (e.g. "Close", or "Closes[1]" for a subchart);
  see printComputedFrom.
-->
<#macro printInput block quoteSymbol=false><@compress_single_line>
<@printComputedFrom block />
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Map the #ComputedFrom# parameter to a NinjaScript price series.
  @param block  the indicator block.
  Generates Close/Open/High/Low/Volume and Median/Typical/Weighted - all built-in NinjaScript
  ISeries<double>. Median/Typical/Weighted use the same formulas as SQX
  (MedianDataSeries (H+L)/2, TypicalDataSeries (H+L+C)/3, WeightedDataSeries (H+L+2C)/4), so the
  native series is used directly (no helper).
  Default: Close.
-->
<#--
  Which chart series the block reads.
  Blocks carry a `#Chart#` parameter (controlType="dataVar") holding the `<data><id>` of the chart
  chosen in the strategy: "0" is the primary series, "1"+ are the extra AddDataSeries added in
  State.Configure. Missing parameter -> primary, which is what every single-chart strategy has.
-->
<#macro printComputedFrom block><@compress_single_line>
<#local cf = getParam(block, "#ComputedFrom#", "0") />
<#local ci = getParam(block, "#Chart#", "0") />
<#-- Primary series uses the scalar accessors (Close, High, ...); a secondary series MUST use the
     indexed collection (Closes[n], Highs[n], ...), otherwise the indicator silently computes from
     the primary chart - it compiles and runs, it is just the wrong data. -->
<#if ci == "0">
  <#switch cf>
    <#case "0">Close<#break>
    <#case "1">Open<#break>
    <#case "2">High<#break>
    <#case "3">Low<#break>
    <#case "4">Median<#break>
    <#case "5">Typical<#break>
    <#case "6">Weighted<#break>
    <#case "7">Volume<#break>
    <#default>Close
  </#switch>
<#else>
  <#switch cf>
    <#case "0">Closes[${ci}]<#break>
    <#case "1">Opens[${ci}]<#break>
    <#case "2">Highs[${ci}]<#break>
    <#case "3">Lows[${ci}]<#break>
    <#case "4">Medians[${ci}]<#break>
    <#case "5">Typicals[${ci}]<#break>
    <#case "6">Weighteds[${ci}]<#break>
    <#case "7">Volumes[${ci}]<#break>
    <#default>Closes[${ci}]
  </#switch>
</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit a concrete price/time series honouring the block's #Chart#.
  @param block  the block carrying an optional #Chart# dataVar.
  @param name   scalar series name ("Close", "High", "Low", "Open", "Volume", "Time").
  Primary chart -> the scalar accessor (Close); a secondary chart MUST use the indexed
  collection (Closes[n]) - the scalar compiles and runs on the WRONG data otherwise
  (same rule as printComputedFrom). Plural form is name + "s" for every
  supported series.
-->
<#macro printSeries block name><@compress_single_line>
<#local ci = getParam(block, "#Chart#", "0") />
<#if ci == "0">${name}<#else>${name}s[${ci}]</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit the block's data-series index as a bare integer.
  @param block  the block carrying an optional #Chart# dataVar.
  Generates: "0" for the primary chart, "1"+ for a subchart.

  This is the runtime counterpart of printSeries. Where printSeries picks the right ACCESSOR for an
  expression the template writes itself (Closes[1][3]), a block whose calculation lives in an sq*
  helper cannot do that - the helper reads the bars internally - so it is handed the index instead
  and uses the sqHigh/sqLow/... accessors and sqBarCount(ci) clock from SQ.inc.

  Emitted as the LEADING argument of a series-aware helper, so the reader sees which chart the call
  computes over before anything else.
-->
<#macro printChartIndex block><@compress_single_line>
<#local ci = getParam(block, "#Chart#", "0") />
${ci}
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit the NinjaScript bar indexer for a block's shift.
  @param block  the block carrying an optional #Shift# parameter.
  @param shift  extra offset added on top of the block's own shift.
  Generates: "[<offset>]", e.g. "[0]" or "[1]".
  SQX shift maps 1:1 to NinjaScript barsAgo (0 = current bar).
  Used by the COT templates only: their StrategyQuant blocks look COT values up by time rather than
  reading a data series, so what they return before the first bar is not the 0 that printSeriesAt
  gives. Every other read goes through printSeriesAt.
-->
<#macro printShift block shift><@compress_single_line>[<@printCIShift block shift />]</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Compute the bar offset that printSeriesAt and printShift read at.
  @param block  block whose #Shift# parameter is read (may be absent).
  @param shift  caller-supplied extra offset.
  Generates: the offset, combining the block's #Shift# with the extra shift
  (e.g. block shift 0 + extra 1 -> "1"; variable/formula shift -> "<name>+1").
  When the block has no #Shift#, the extra shift alone is emitted.
-->
<#macro printCIShift block shift><@compress_single_line>
<#local found = false />
<#list block.* as param>
	<#if param.@key == "#Shift#">
      <#local found = true />
      <#if param.@variable[0]?? && param.@variable == "true">
         <#-- shift bound to a variable: name (+ extra offset). -->
         <@printVariableName param /><#if shift != "0">+${shift}</#if>
      <#elseif param.Formula[0]?? >
         <#-- shift from a formula: key (+ extra offset). -->
         <@printFormulaKey param.Formula[0] /><#if shift != "0">+${shift}</#if>
      <#else>
         <#-- literal shift: if zero use the extra offset, else sum them. -->
         <#if param == "0"><#if shift != "0">${shift}<#else>0</#if><#else>${param}<#if shift != "0">+${shift}</#if></#if>
      </#if>
   </#if>
</#list>
<#-- No #Shift# parameter on this block: the extra offset is the whole index. -->
<#if found == false>${shift}</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit a read of a series at the block's shift.
  @param block  the block carrying an optional #Shift# and #Chart#.
  @param shift  extra offset added on top of the block's own shift (as printCIShift).
  Nested content: the series expression, e.g. "Close" or "SqCCI(Close, 14).Values[0]".
  Generates: "Close[1]", or "sqAt(0, Close, 30)" when the offset can reach past the first bar.
  Every template reads a series through this macro (or printSeriesAtOffset), so the decision of
  sqReadNeedsGuard is made in one place.
-->
<#macro printSeriesAt block shift><#local series><#nested></#local><#local offset><@printCIShift block shift /></#local><@sqEmitRead block series offset /></#macro>

<#-------------------------------------------------------------->
<#--
  Emit a read of a series at an offset the caller has already written out.
  @param block   the block whose #Chart# names the series the offset counts bars of.
  @param offset  the offset text, e.g. "3", "1+1", "shiftVar+1".
  @param chart   the chart index when the series is fixed to one chart whatever the block says, e.g.
                 "0" for the ATR of a price formula, which always reads the primary chart; empty to take
                 it from the block.
  Nested content: the series expression.
  Generates: e.g. "SMA(Close, 200)[1]", or "sqAt(0, SMA(Close, 200), 1)" in an OnInit rule.
-->
<#macro printSeriesAtOffset block offset chart=""><#local series><#nested></#local><@sqEmitRead block series offset chart /></#macro>

<#-------------------------------------------------------------->
<#--
  Mark the strategy as calling the ATR runtime of SQ.inc (sqAtrTicks, sqMMAtrRisk).
  Called on the line of every caller. Those helpers read the installed SqATR through sqAt, so the
  indicator package guard and sqAt are needed with them.
  Generates: nothing.
-->
<#macro useAtrRuntime><#global sqUsesAtrRuntime = true><#global sqUsesIndicatorPackage = true><#global sqUsesGuardedRead = true></#macro>

<#--
  The read itself, shared by printSeriesAt and printSeriesAtOffset.
  @param block   the block whose #Chart# names the series the offset counts bars of.
  @param series  the series expression.
  @param offset  the offset text.
  @param chart   an explicit chart index, or empty to read #Chart# from the block.
  Generates: "<series>[<offset>]", or "sqAt(<chart>, <series>, <offset>)" when sqReadNeedsGuard says
  so, e.g. "Close[1]" / "sqAt(0, Close, 30)". A guarded read sets sqUsesGuardedRead, which makes
  SQ.inc emit sqAt.
-->
<#macro sqEmitRead block series offset chart=""><@compress_single_line>
<#local s = series?trim />
<#local o = offset?trim />
<#local ci = chart?has_content?then(chart, getParam(block, "#Chart#", "0")) />
<#local dayPrice = dailyChartPrice(ci, s) />
<#local dayMa = dailyChartMA(ci, s) />
<#local native><#if sqReadNeedsGuard(o)><#global sqUsesGuardedRead = true>sqAt(${ci}, ${s}, ${o})<#else>${s}[${o}]</#if></#local>
<#if dayMa != ""><#global sqUsesIndicatorPackage = true>(${isDayRead(ci)} ? SqHigherTimeframeMA(${dayBarsSeries(ci)}, ${dayMa}, ${completedDayShift(o)}).Values[0][0] : ${native?trim})
<#elseif dayPrice != "-1"><#global sqUsesIndicatorPackage = true>(${isDayRead(ci)} ? SqCalendarDayOHLC(${dayBarsSeries(ci)}, ${completedDayShift(o)}).Values[${dayPrice}][0] : ${native?trim})
<#else>${native?trim}</#if>
</@compress_single_line></#macro>

<#--
  A price read of a Day subchart, on StrategyQuant's calendar day. NinjaTrader's Day bar rolls at the
  session close; StrategyQuant's at midnight of the data's own stamps. The installed SqCalendarDayOHLC groups
  intraday bars (the primary bars, or the companion series of a Day subchart on another symbol - dayBarsSeries)
  by the calendar day of their start, a Sunday included, and its DayShift counts days
  back from the day in progress. Returns the Values index of the price (0 Open, 1 High, 2 Low, 3 Close), or
  "-1" when the read is not a plain price of a Day subchart.
-->
<#function dailyChartPrice ci series>
  <#if ci == "0" || !isSubchart(ci)><#return "-1" /></#if>
  <#if series == "Opens[" + ci + "]"><#return "0" /></#if>
  <#if series == "Highs[" + ci + "]"><#return "1" /></#if>
  <#if series == "Lows[" + ci + "]"><#return "2" /></#if>
  <#if series == "Closes[" + ci + "]"><#return "3" /></#if>
  <#return "-1" />
</#function>

<#--
  A moving average of a Day subchart, on StrategyQuant's calendar day: the installed SqHigherTimeframeMA
  builds the days from intraday bars (dayBarsSeries) and runs StrategyQuant's AverageCalculator over them, where
  NinjaTrader's own Day series would average its session days.
  Returns the "minutes, maType, period, priceType" arguments, or "" when the read is not an SMA, EMA, SMMA
  or LWMA of a Day subchart, e.g. "1440, 0, 20, 0" for "SMA(Closes[1], 20)".
-->
<#function dailyChartMA ci series>
  <#if ci == "0" || !isSubchart(ci)><#return "" /></#if>
  <#local m = series?matches("(SMA|EMA|SqSMMA|SqLWMA)\\((Closes|Opens|Highs|Lows|Medians|Typicals|Weighteds|Volumes)\\[" + ci + "\\],\\s*([^()]+)\\)(\\.Values\\[0\\])?") />
  <#if !m><#return "" /></#if>
  <#local fn = m?groups[1] />
  <#if (fn == "SqSMMA" || fn == "SqLWMA") != (m?groups[4] != "")><#return "" /></#if>
  <#local type = {"SMA": "0", "EMA": "1", "SqSMMA": "2", "SqLWMA": "3"}[fn] />
  <#local price = {"Closes": "0", "Opens": "1", "Highs": "2", "Lows": "3", "Medians": "4", "Typicals": "5", "Weighteds": "6", "Volumes": "7"}[m?groups[2]] />
  <#return "1440, " + type + ", " + m?groups[3]?trim + ", " + price />
</#function>

<#--
  The days back of a Day subchart read. A secondary chart holds its last COMPLETED bar at shift 0 in
  StrategyQuant as in NinjaTrader, while SqCalendarDayOHLC and SqHigherTimeframeMA count 0 as the day in
  progress, so StrategyQuant's shift k is their k + 1.
  @param offset  the offset text, e.g. "0", "2", "ReadShift+1".
  Returns: e.g. "1" for "0", "(ReadShift+1)+1" for "ReadShift+1".
-->
<#function completedDayShift offset>
  <#if offset?matches("\\d+")><#return (offset?number + 1)?c /></#if>
  <#return "(" + offset + ")+1" />
</#function>

<#-- True when the chart with this index is a subchart with a timeframe, i.e. one whose Subchart<N>Timeframe input
     can ask for a calendar day at run time. -->
<#function isSubchart ci>
  <#list doc.StrategyFile.Strategy.Datas.* as data>
    <#if data.id?string == ci><#return ci != "0" && barsPeriodOf(data.timeFrame) != "" /></#if>
  </#list>
  <#return false />
</#function>

<#--
  Whether a read at this offset needs sqAt (SQ.inc). StrategyQuant reads 0 before the first bar of a
  chart; NinjaTrader's indexer throws there and terminates the strategy.
  The rules run only once every series has BarsRequiredToTrade bars (printBarsGuard), so an offset that
  is a sum of integer literals not larger than the Reserved bars is always in range - the plain indexer
  stays. Guarded: a larger literal offset, one that is not literal (a variable, a formula, a lambda
  parameter), and any non-zero offset in an OnInit rule, which runs on the first bar (sqReadsOnInit,
  Main.tpl).
  @param offset  the offset text, e.g. "21", "19+1", "ReadShift+1".
  Returns: true when the read must go through sqAt, e.g. "21" with 20 Reserved bars.
-->
<#function sqReadNeedsGuard offset>
<#local total = 0 />
<#list offset?split("+") as term>
	<#local t = term?trim />
	<#if !t?matches("[0-9]+")><#return true></#if>
	<#local total = total + t?number />
</#list>
<#if total == 0><#return false></#if>
<#if sqReadsOnInit!false><#return true></#if>
<#return total gt sqReservedBars()>
</#function>

<#-------------------------------------------------------------->
<#--
  The nested #Indicator# of the four Indicator*MA comparison blocks, rendered as a C# lambda over
  the bar offset.

  Those blocks average their nested block over period bars - Indicator.evaluateBlock(shift + i) -
  so the child has to be evaluatable at a shift that is only known at RUNTIME. Every other template
  bakes the shift in as a literal at generation time, which cannot express this. A lambda can, and
  it needs no new machinery: printCIShift already renders a shift as an IDENTIFIER rather than a
  number (that is how a shift bound to a strategy variable works), and it never does arithmetic on
  it - it concatenates - so passing the lambda parameter name straight through yields valid C#
  such as "1+__sqK0".

  The parameter name is numbered, because C# 7.3 forbids a nested lambda from shadowing an outer
  lambda's parameter - which is exactly what an Indicator*MA block nested inside another would do.
-->
<#assign sqLambdaSeq = 0 />
<#macro printIndicatorLambda block><@compress_single_line>
<#assign sqLambdaSeq = sqLambdaSeq + 1 />
<#local v = "__sqK" + sqLambdaSeq />
${v} => <@printBlockChild block "#Indicator#" v />
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     ORDER / ACTION macros
     ============================================================ -->

<#-------------------------------------------------------------->
<#--
  Pick a per-direction value based on a block's #Direction# parameter.
  @param block      the action block.
  @param paramName  the direction parameter key (usually "#Direction#").
  @param longVal    value emitted when direction is Long (1).
  @param shortVal   value emitted when direction is Short (-1).
  Generates: longVal or shortVal. Only a literal direction is resolved; a variable
  or formula direction defaults to Long.
-->
<#macro printDirectionValue block paramName longVal shortVal><@compress_single_line>
<#local dir = getParam(block, paramName, "1") />
<#if dir == "-1">${shortVal}<#else>${longVal}</#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit the managed exit call(s) for an exit block's #Direction# parameter.

  Unlike an entry, an exit direction has THREE values - the SQX exit blocks declare
  values="Long=1,Short=-1,Any=0" with defaultValue="0". printDirectionValue is binary
  ("-1" -> short, anything else -> long), so it would map Any onto ExitLong() and never
  close a short; this macro handles all three.

  @param block      the exit action block.
  @param paramName  the direction parameter key (usually "#Direction#").
  Generates: ExitLong(); / ExitShort(); / both (Any), the continuation line indented to
  match the surrounding emitted statements.
-->
<#macro printExitByDirection block paramName>
<#local dir = getParam(block, paramName, "0") />
<#if dir == "1">
ExitLong();<#rt>
<#elseif dir == "-1">
ExitShort();<#rt>
<#else>
ExitLong();
			ExitShort();<#rt>
</#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  Emit the NinjaScript signal name (a C# string literal) for an action.
  @param block  the action block.
  Generates: "LE" for long, "SE" for short (per-direction signal, not a magic
  number). NinjaScript Managed pairs SetStopLoss/SetProfitTarget/Exit
  with the entry via this signal name.
-->
<#-- suffix: optional signal-name suffix - "F" marks the already-crossed market FALLBACK entry of
     EnterAtStop/EnterAtLimit, which must run under its OWN signal name (with a same-name pending
     still working, NinjaTrader's Managed rules silently ignore both a different-type entry AND
     CancelOrder in the same OnBarUpdate; a distinct name under EntryHandling.UniqueEntries is
     accepted immediately). -->
<#macro printSignalName block suffix=""><@compress_single_line>"<@printDirectionValue block "#Direction#" "LE" "SE" />${suffix}"</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Render the #Price# formula's child block as a NinjaScript price expression - the stop/limit
  price level for pending entry orders (EnterAtStop / EnterAtLimit).
  @param block           the action block carrying the price parameter.
  @param priceParamName  the price parameter key (usually "#Price#").
  Mirrors JForex printPrice: SQ.Formulas.Price.UseFormula -> printBlock on the formula's child block
  (e.g. Close[0], (High[0] + ...)). Falls back to 0 when no formula/child is present.
-->
<#macro printPrice block priceParamName><@compress_single_line>
<#list block.* as param>
	<#if param.@key == priceParamName>
		<#-- Indicator values enter an order price rounded to 6 decimals, as IndicatorBlock.evaluateBlock
		     returns them; the caller rounds the whole level as SQUtils.fixPrice does. -->
		<#if param.Formula[0]?? && param.Formula[0]?children[0]??><#global sqRound6Indicators = true><@printBlock param.Formula[0]?children[0] /><#global sqRound6Indicators = false><#else>0</#if>
	</#if>
</#list>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit the order quantity for EnterLong/EnterShort.
  @param block          the action block.
  @param sizeParamName  the size parameter key (usually "#Size#").
  Generates: the quantity expression.
    DefineOwnSize   -> literal value
    UseFromVariable -> variable name
    UseGlobalMM     -> Math.Max(1, (int)Math.Round(<money management size>))
  Note: SQX size is in lots/units; NinjaScript quantity is an integer contract count.
  UseGlobalMM applies the lot->contract conversion (round, min 1)
  to the MM type's size expression (MoneyManagement.inc / MoneyManagement/<type>_method.tpl).
-->
<#-- priceRef: the price the order is sized at - the decision close, or a pending entry's level. -->
<#macro printSizeMethod block sizeParamName priceRef="Close[0]"><@compress_single_line>
<#-- Instrument order-size multiplier (InstrumentInfo.orderSizeMultiplier, put into the root by
     SourceCodeGenerator.getSource). Applied to the size before the lot->contract rounding, mirroring
     MT5 (LotSize = LotSize * multiplier). Emitted ONLY when non-default (!= 1) so the common case stays
     clean "Math.Round((double)(1))". orderSizeStep is intentionally NOT applied: NinjaScript trades whole
     contracts, so the final (int)Math.Round already quantizes the size (lot->contract), which
     subsumes a sub-contract step. -->
<#local mult><#if (orderSizeMultiplier??) && orderSizeMultiplier?number != 1> * ${orderSizeMultiplier}</#if></#local>
<#-- The size above is a LOT count, which is what StrategyQuant sizes in; NinjaTrader counts forex in
     units, where a full lot is a quantity of 100 000. SqContractSize carries the conversion
     (InstrumentInfo.pointValue / Instrument.MasterInstrument.PointValue, computed in State.DataLoaded)
     and is 1 where the instrument already counts per contract; with an unresolved instrument it is
     not emitted at all (see below). Applied
     after the instrument multiplier and before the whole-quantity rounding, which is the only place a
     lot count becomes the integer NinjaScript takes. -->
<#-- Emitted ONLY when the instrument resolved, the same rule the multiplier above follows: with no
     instrument pointValue is 0 and SqContractSize is not declared, so the size carries no factor. -->
<#if (pointValue??) && pointValue?number gt 0><#local mult>${mult} * SqContractSize</#local></#if>
<#list block.* as param>
	<#if param.@key == sizeParamName>
		<#switch param.Formula[0].@key>
			<#-- All three size sources round to whole contracts, min 1 (NinjaScript EnterLong/Short take an int
			     quantity). Without the wrapper DefineOwnSize (e.g. 0.1) and
			     UseFromVariable (a double field) would emit a double into EnterLong(int, ...) = CS1503.
			     The (double) cast is REQUIRED: a literal int size (e.g. 1) or an int-typed size variable would
			     make Math.Round(...) ambiguous between Math.Round(double)/Math.Round(decimal) = CS0121. -->
			<#case "SQ.Formulas.Size.DefineOwnSize">Math.Max(1, (int)Math.Round((double)(<@printParameterValue param.Formula[0].Param />)${mult}))<#break>
			<#case "SQ.Formulas.Size.UseFromVariable">Math.Max(1, (int)Math.Round((double)(<@printVariableName param.Formula[0].Param />)${mult}))<#break>
			<#case "SQ.Formulas.Size.UseGlobalMM">Math.Max(1, (int)Math.Round(<@printMoneyManagementMethod block priceRef />${mult}))<#break>
			<#default>1
		</#switch>
	</#if>
</#list>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit a full SetStopLoss / SetProfitTarget call for an entry (or nothing when
  the formula is None). Must be called BEFORE the Enter* method (NinjaScript
  submits the SL/PT upon entry fill).
  @param block          the action block.
  @param slptType       "SL" or "PT".
  @param slptParamName  the SL/PT parameter key (e.g. "#StopLoss.StopLoss#").
  Generates one NinjaScript statement:
    None        -> (nothing)
    FixedValue  -> CalculationMode.Ticks, <pips> * SqPipFactor  (SQX pips -> ticks)
    PctValue    -> CalculationMode.Percent, <value>
    ATRBasedValue -> CalculationMode.Ticks, sqAtrTicks(mult, period)
    PriceLevel  -> CalculationMode.Price, <price expression>
  SetStopLoss takes a trailing isSimulated flag (false); SetProfitTarget does not.
-->
<#--
  Emit the entry's StopLoss + ProfitTarget, honouring the UseInitialSLPT trading option.

  Without the option the two calls are emitted unconditionally.

  With the option present the calls go under `if (UseInitialSLPT)`, and the deferred counterpart is
  emitted per bar by printDeferredSLPTManage (ExitMethods.inc). The branch is a RUNTIME if, not a
  FreeMarker one, because the option's value is already emitted as a field
  (UseInitialSLPT_variables.tpl) - so both paths exist in the generated source.
-->
<#--
  anchor="close" (market entries): emit tick-distance SL/PT as ABSOLUTE prices anchored to the
  decision bar close instead of CalculationMode.Ticks. SQX core stores initial SL/PT as absolute
  levels computed from the close of the decision bar, while CalculationMode.Ticks offsets from the
  entry FILL (the next bar's open) - the close->open gap would shift every level. Pending
  entries (stop/limit) keep the tick offset: there the fill price IS the order price SQX
  anchored to, so the offset is already equivalent.
-->
<#-- atrBarsAgoSL / atrBarsAgoPT: per-type ATR shift overrides. SQX's ATRBasedValue caches the
     shift-1 ATR keyed to chartData.Bars() (ATRBasedValue.getCachedATR): the STOP LOSS formula is
     evaluated when the order is CREATED (the submit eval, Bars() = N -> the decision-frame ATR),
     while the PROFIT TARGET is evaluated at the FILL, and a pending fills MID-BAR when Bars() has
     already advanced - its cache recomputes one bar fresher. So SL distances correspond to shift 1
     at the submit eval and PT distances to shift 0, for the plain pending and the F-name market
     fallback alike. Pending blocks therefore pass atrBarsAgoPT="0" and leave SL at the default. -->
<#macro printEntrySLPT block anchor="" suffix="" atrBarsAgoSL="" atrBarsAgoPT="">
<#if anchor == "close"><@printLevelTargetReset block suffix /></#if>
<#if tradingOptionUsed("UseInitialSLPT")>if (UseInitialSLPT)
				{
					<@printSetSLPT block "SL" "#StopLoss.StopLoss#" anchor suffix atrBarsAgoSL />
					<@printSetSLPT block "PT" "#ProfitTarget.ProfitTarget#" anchor suffix atrBarsAgoPT />
				}
				<#else><@printSetSLPT block "SL" "#StopLoss.StopLoss#" anchor suffix atrBarsAgoSL />
				<@printSetSLPT block "PT" "#ProfitTarget.ProfitTarget#" anchor suffix atrBarsAgoPT /></#if>
<#if anchor == "close"><@printLevelSLRecord block /></#if>
</#macro>

<#--
  A market entry whose stop loss is a price level records that level, so the entry's fill can tell whether
  the stop is on the wrong side of it (OnExecutionUpdate in Main.tpl). StrategyQuant fills such a stop at once,
  at the market, which closes the trade at its entry price.
  @param block  the EnterAtMarket block.
-->
<#macro printLevelSLRecord block><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"><#global sqUsesWrongSideLevelSL = true><#if getParam(block, "#Direction#", "1") != "-1">sqLongLevelSL<#else>sqShortLevelSL</#if> = ${slptVal};</#if></#macro>

<#--
  A market entry whose stop loss is a price level on the close of the decision bar does not enter: StrategyQuant
  refuses a stop on the price it anchors the entry to (EnterAtMarket.marketEntry). Emits the extra condition of
  the entry's if, or nothing for any other stop.
  @param block  the EnterAtMarket block.
-->
<#macro printLevelSLGuard block><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"> && sqRoundPrice(${slptVal}) != Close[0]</#if></#macro>

<#--
  A reversing market entry whose price-level stop loss is the close of the decision bar enters without a stop:
  EnterReverseAtMarket has no refusal of its own, and StrategyQuant sets the level only at the fill, from the next
  bar (printDeferredLevelSLArm, ExitMethods.inc). The entry's stop moves out of reach (one tick for a long, 1e9 for
  a short), the level is recorded for that arming and not for the wrong-side check of the fill. Emitted after
  printEntrySLPT, or nothing for any other stop.
  @param block   the EnterReverseAtMarket block.
  @param suffix  the signal name suffix, as printEntrySLPT takes it.
-->
<#macro printLevelSLAtCloseOff block suffix=""><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"><#global sqUsesDeferredLevelSL = true><#local side = (getParam(block, "#Direction#", "1") != "-1")?then("Long", "Short") />if (sqRoundPrice(${slptVal}) == Close[0])
				{
					SetStopLoss(<@printSignalName block suffix />, CalculationMode.Price, <#if side == "Long">TickSize<#else>1e9</#if>, false);
					sq${side}LevelSL = double.NaN;
					sq${side}DeferSL = sqRoundPrice(${slptVal});
					sq${side}DeferSLName = <@printSignalName block suffix />;
				}</#if></#macro>

<#--
  A market entry with a price-level stop loss and no profit target of its own sets a target out of reach before
  it enters. A wrong-side stop closes a trade through a target at the fill price (OnExecutionUpdate in Main.tpl),
  and NinjaTrader keeps a signal name's target for the next entry under that name; an entry that sets no target
  would otherwise inherit that one. Out of reach is 1e9 for a long, one tick for a short.
  @param block   the EnterAtMarket block.
  @param suffix  the signal name suffix, as printEntrySLPT takes it.
-->
<#macro printLevelTargetReset block suffix=""><@resolveSLPT block "SL" "#StopLoss.StopLoss#" /><#if slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"><@resolveSLPT block "PT" "#ProfitTarget.ProfitTarget#" /><#if slptFkey == "" || slptFkey == "SQ.Formulas.SLPT.None">SetProfitTarget(<@printSignalName block suffix />, CalculationMode.Price, <#if getParam(block, "#Direction#", "1") != "-1">1e9<#else>TickSize</#if>);</#if></#if></#macro>

<#-------------------------------------------------------------->
<#-- atrBarsAgo: optional ATR shift override for ATRBasedValue distances - "0" for pending entries
     (SQX computes a pending's SL/PT at the FILL tick; see sqAtrTicks(mult, period, barsAgo) in
     SQ.inc). Empty keeps the market-entry default (barsAgo 1). -->
<#-- Shared SL/PT resolver: computes the CalculationMode + value expression for one SL/PT slot and
     leaves them in the GLOBALS slptFkey / slptMode / slptVal / slptMmNote (FreeMarker macros cannot
     return values; rendering is single-threaded, so sequential assigns are safe). Used by
     printSetSLPT (immediate Set emission - market entries) and by the pending store/arm pair
     (EnterAtStop/EnterAtLimit + printPendingSLPTArm), which need the raw value expression. -->
<#macro resolveSLPT block slptType slptParamName anchor="" atrBarsAgo="">
<#assign slptFkey = "" />
<#assign slptMode = "" />
<#assign slptVal = "" />
<#assign slptMmNote = "" />
<#list block.* as param>
	<#if param.@key == slptParamName>
		<#assign slptFkey = param.Formula[0].@key />
		<#local mode = "" />
		<#local val = "" />
		<#switch slptFkey>
			<#case "SQ.Formulas.SLPT.None"><#break>
			<#case "SQ.Formulas.SLPT.FixedValue">
				<#local mode = "CalculationMode.Ticks" />
				<#-- FixedValue is in SQX pips; convert to a tick count for CalculationMode.Ticks. -->
				<#local val><@compress_single_line>(<@printParameterValue param.Formula[0].Param />) * SqPipFactor</@compress_single_line></#local>
				<#break>
			<#case "SQ.Formulas.SLPT.PctValue">
				<#local mode = "CalculationMode.Percent" />
				<#-- NinjaScript's CalculationMode.Percent takes a FRACTION - 0.01 is one percent - while
				     the SQX PctValue is the percent itself, so the value has to be divided by 100 (a 0.30%
				     stop would otherwise be submitted as 30%). The Move SL/PT path below divides by 100
				     too when it turns the same formula into a price. -->
				<#-- 100.0, not 100: a whole-number percent is an int literal in C#, and (1) / 100 is 0 there. -->
				<#local val><@compress_single_line>(<@printParameterValue param.Formula[0].Param />) / 100.0</@compress_single_line></#local>
				<#break>
			<#case "SQ.Formulas.SLPT.ATRBasedValue">
				<#local mode = "CalculationMode.Ticks" />
				<@useAtrRuntime /><#local val>sqAtrTicks(<@compress_single_line><@printParameterValue param.Formula[0].Param[0] /></@compress_single_line>, <@compress_single_line><@printParameterValue param.Formula[0].Param[1] /></@compress_single_line><#if atrBarsAgo != "">, ${atrBarsAgo}</#if>)</#local>
				<#break>
			<#case "SQ.Formulas.SLPT.ValueFromFormula">
				<#local mode = "CalculationMode.Ticks" />
				<#-- "Value from formula (in pips)" (ValueFromFormula.java): the value is an arbitrary nested
				     block expression in SQX pips (valueInPips -> convertPipsToRealPrice). Same pip->tick
				     conversion as FixedValue, but the operand is a block, not a literal -
				     rendered via printBlock like the PriceLevel case. Mirrors MT5/JForex/EasyLanguage, which
				     all handle SLPT.ValueFromFormula (pip-valued formula). -->
				<#local val><@compress_single_line>(<@printBlock param.Formula[0]?children[0] />) * SqPipFactor</@compress_single_line></#local>
				<#break>
			<#case "SQ.Formulas.SLPT.PriceLevel">
				<#local mode = "CalculationMode.Price" />
				<#local val><@compress_single_line><@printBlock param.Formula[0]?children[0] /></@compress_single_line></#local>
				<#break>
		</#switch>
		<#-- MinMaxSLPT: clamp the tick distance at placement (mirrors MT5 SQ.mqh).
		     Percent/Price modes carry no pre-entry pip distance -> documented, not silently skipped. -->
		<#if tradingOptionUsed("MinMaxSLPT") && mode == "CalculationMode.Ticks">
			<#local val>sqClampSLPT(${val}, <#if slptType == "SL">true<#else>false</#if>)</#local>
		<#elseif tradingOptionUsed("MinMaxSLPT") && (mode == "CalculationMode.Percent" || mode == "CalculationMode.Price")>
			<#-- A Percent or Price mode has no pre-entry pip distance for MinMaxSLPT to clamp. --><#assign slptMmNote> /* no MinMaxSLPT clamp */</#assign>
		</#if>
		<#-- Decision-close anchoring: tick distances on market entries become
		     absolute prices from Close[0]. SL sits against the direction, PT with it. -->
		<#if anchor == "close" && (mode == "CalculationMode.Ticks" || mode == "CalculationMode.Percent")>
			<#local dir = getParam(block, "#Direction#", "1") />
			<#if (slptType == "SL" && dir != "-1") || (slptType == "PT" && dir == "-1")><#local sign = "-" /><#else><#local sign = "+" /></#if>
			<#-- sqRoundPrice: SQX rounds the level with a +1e-10 epsilon (SQUtils.round) - a level on
			     exactly half a tick rounds UP, NinjaTrader's own tick rounding resolves it lower.
			     A PERCENT level is anchored and rounded here for the same reason a tick distance is.
			     Left to CalculationMode.Percent, NinjaTrader measures it off the FILL price and rounds
			     it its own way, which puts exits a tick or so away from StrategyQuant. -->
			<#if mode == "CalculationMode.Percent">
				<#local val>sqRoundPrice(Close[0] * (1 ${sign} (${val})))</#local>
			<#else>
				<#local val>sqRoundPrice(Close[0] ${sign} (${val}) * TickSize)</#local>
			</#if>
			<#local mode = "CalculationMode.Price" />
		</#if>
		<#assign slptMode = mode />
		<#assign slptVal = val />
	</#if>
</#list>
</#macro>

<#macro printSetSLPT block slptType slptParamName anchor="" suffix="" atrBarsAgo="">
<@resolveSLPT block slptType slptParamName anchor atrBarsAgo /><#t>
<#if slptFkey == "SQ.Formulas.SLPT.None" || slptFkey == ""><#-- no SL/PT to set -->
<#elseif slptMode == "">/* ${slptType} formula ${slptFkey} not supported yet */
<#elseif slptType == "SL" && slptFkey == "SQ.Formulas.SLPT.PriceLevel" && slptMode == "CalculationMode.Price"><#-- A price level
     that is not a price at the entry (the block read 0) gives the position no stop in StrategyQuant. NinjaTrader
     does not submit a long stop at 0, and a stop that was never submitted is not created by a later SetStopLoss,
     so a timed exit or a stop move would find nothing to amend: such a level is set out of reach instead - one
     tick for a long, 1e9 for a short. -->SetStopLoss(<@printSignalName block suffix />, ${slptMode}, (${slptVal} > 0 ? ${slptVal} : <#if getParam(block, "#Direction#", "1") != "-1">TickSize<#else>1e9</#if>), false);${slptMmNote}<#elseif slptType == "SL">SetStopLoss(<@printSignalName block suffix />, ${slptMode}, ${slptVal}, false);${slptMmNote}<#else>SetProfitTarget(<@printSignalName block suffix />, ${slptMode}, ${slptVal});${slptMmNote}</#if>
</#macro>

<#-------------------------------------------------------------->
<#-- RangeLevel/Range formula -> a price distance, for MoveSL2BE threshold and add-pips.
     FixedValue -> <value> * SqPip; ATRBasedValue -> sqRound(SqATR(Close, period).Values[0][1], 6) * <mult>
     (the SQX formulas round the ATR to 6 decimals before applying the multiplier, and read Indicators.ATR
     = the ATR.java replay the installed SqATR carries, not the native NT ATR); PctValue -> Close[0]*<v>/100;
     PriceLevel -> the price expression; RangeLevel.PriceRange -> (<expr>) * SqPip; Range.PriceRange ->
     (<expr>). Mirrors the printSetTrailStop RangeLevel handling. -->
<#macro printRangeLevelPrice block paramName><@compress_single_line>
<#local out = "0" />
<#list block.* as param>
  <#if param.@key == paramName && param.Formula[0]??>
    <#switch param.Formula[0].@key>
      <#case "SQ.Formulas.RangeLevel.FixedValue"><#case "SQ.Formulas.Range.FixedValue"><#-- pips -> price distance via SqPip. --><#local out><@printParameterValue param.Formula[0].Param /> * SqPip</#local><#break>
      <#-- barsAgo 1, not 0: Range/ATRBasedValue.java and RangeLevel/ATRBasedValue.java both read
           getATRValue(chart, period, 1), the same shift the SL/PT formula uses - and at decision time
           NinjaScript's [1] IS that bar. -->
      <#case "SQ.Formulas.RangeLevel.ATRBasedValue"><#case "SQ.Formulas.Range.ATRBasedValue"><#global sqUsesIndicatorPackage = true><#local out>sqRound(<@printSeriesAtOffset block "1" "0">SqATR(Close, <@printParameterValue param.Formula[0].Param[1] />).Values[0]</@printSeriesAtOffset>, 6) * <@printParameterValue param.Formula[0].Param[0] /></#local><#break>
      <#case "SQ.Formulas.RangeLevel.PctValue"><#case "SQ.Formulas.Range.PctValue"><#local out>Close[0] * <@printParameterValue param.Formula[0].Param /> / 100</#local><#break>
      <#case "SQ.Formulas.RangeLevel.PriceLevel"><#local out><@printBlock param.Formula[0]?children[0] /></#local><#break>
      <#-- "Range in pips" with a block as the value. The RangeLevel variant converts the pips to a price
           distance (RangeLevel/PriceRange.java: convertPipsToRealPrice). The Range variant returns the
           block value as it is, without a pip conversion (Range/PriceRange.java), and is rendered the
           same way so the export computes what the backtest computes. -->
      <#case "SQ.Formulas.RangeLevel.PriceRange"><#local out>(<@printBlock param.Formula[0]?children[0] />) * SqPip</#local><#break>
      <#case "SQ.Formulas.Range.PriceRange"><#local out>(<@printBlock param.Formula[0]?children[0] />)</#local><#break>
      <#-- SLPT.* is the StopLoss/ProfitTarget namespace. Needed because the trailing-stop management
           has to know the fixed stop distance to avoid ever widening the stop, and a stop loss
           carries SLPT formulas, not RangeLevel ones - without these cases a StopLoss would render
           a silent "0" and the floor would collapse onto the entry price. -->
      <#case "SQ.Formulas.SLPT.FixedValue"><#local out><@printParameterValue param.Formula[0].Param /> * SqPip</#local><#break>
      <#case "SQ.Formulas.SLPT.ATRBasedValue"><#global sqUsesIndicatorPackage = true><#local out>sqRound(<@printSeriesAtOffset block "1" "0">SqATR(Close, <@printParameterValue param.Formula[0].Param[1] />).Values[0]</@printSeriesAtOffset>, 6) * <@printParameterValue param.Formula[0].Param[0] /></#local><#break>
      <#case "SQ.Formulas.SLPT.PctValue"><#local out>Close[0] * <@printParameterValue param.Formula[0].Param /> / 100</#local><#break>
      <#case "SQ.Formulas.SLPT.ValueFromFormula"><#local out>(<@printBlock param.Formula[0]?children[0] />) * SqPip</#local><#break>
      <#-- An absolute level, not a distance: expressed as the distance from the entry so callers can
           keep treating the result as one. -->
      <#case "SQ.Formulas.SLPT.PriceLevel"><#local out>Math.Abs(Position.AveragePrice - (<@printBlock param.Formula[0]?children[0] />))</#local><#break>
    </#switch>
  </#if>
</#list>
${out}</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- SL distance in ticks from #StopLoss.StopLoss#, for risk-based money management.
     FixedValue -> the value (ticks); ATRBasedValue -> sqAtrTicks(mult, period); PctValue -> the percentage
     of priceRef; otherwise 0 (the MM helper falls back to LotsIfNoMM / StopLossInPips). A known distance goes
     through sqSLTicksAtLevel and, with MinMaxSLPT, sqClampSLPT. -->
<#macro printSLTicks block priceRef="Close[0]"><@compress_single_line>
<#local t = "0" />
<#list block.* as param>
  <#if param.@key == "#StopLoss.StopLoss#">
    <#switch param.Formula[0].@key>
      <#case "SQ.Formulas.SLPT.FixedValue"><#-- pips -> tick count via SqPipFactor. --><#local t>(<@printParameterValue param.Formula[0].Param />) * SqPipFactor</#local><#break>
      <#case "SQ.Formulas.SLPT.ATRBasedValue"><@useAtrRuntime /><#local t>sqAtrTicks(<@printParameterValue param.Formula[0].Param[0] />, <@printParameterValue param.Formula[0].Param[1] />)</#local><#break>
      <#case "SQ.Formulas.SLPT.PctValue"><#local t>${priceRef} * (<@printParameterValue param.Formula[0].Param />) / 100.0 / TickSize</#local><#break>
    </#switch>
  </#if>
</#list>
<#if t != "0">
  <#global sqUsesSLTicksAtLevel = true>
  <#local t>sqSLTicksAtLevel(${t}, <#if getParam(block, "#Direction#", "1") == "-1">false<#else>true</#if>)</#local>
  <#if tradingOptionUsed("MinMaxSLPT")><#local t>sqClampSLPT(${t}, true)</#local></#if>
</#if>
${t}</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Emit the entry-side note for the TrailingStop exit method.

  It emits no call. A native SetTrailStop here would be ignored - NinjaTrader does not honour it
  alongside SetStopLoss on the same signal - so the trailing stop is managed per bar in OnBarUpdate
  (printTrailStopManage) and this macro only records why nothing is set inline. What the formula is
  therefore does not matter, only whether it is one the export knows: None emits nothing, the four
  known RangeLevel formulas emit the note, and anything else emits the unsupported marker so a new
  formula cannot pass silently.

  @param block        the entry action block.
  @param tsParamName  the trailing-stop parameter key ("#TrailingStop.TrailingStop#").
-->
<#macro printSetTrailStop block tsParamName>
<#list block.* as param>
	<#if param.@key == tsParamName>
		<#local fkey = param.Formula[0].@key />
		<#local supported = fkey == "SQ.Formulas.RangeLevel.FixedValue"
				|| fkey == "SQ.Formulas.RangeLevel.ATRBasedValue"
				|| fkey == "SQ.Formulas.RangeLevel.PctValue"
				|| fkey == "SQ.Formulas.RangeLevel.PriceLevel" />
		<#if fkey == "SQ.Formulas.RangeLevel.None"><#-- no trailing stop -->
		<#elseif !supported>/* TrailingStop formula ${fkey} not supported yet */
		<#-- A SetTrailStop here would be ignored: NinjaTrader does not honour it alongside SetStopLoss on the same
		     signal, and the stop loss wins - the trail is managed per bar (printTrailStopManage). -->
		<#else>/* the trailing stop is managed per bar */</#if>
	</#if>
</#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  Emit a SetStopLoss / SetProfitTarget call for a STANDALONE "Move SL/PT" action block
  (SQX SetStopLoss / SetProfitTarget) - adjusting the SL/PT of an already-open position
  during the trade, as opposed to printSetSLPT which sets it inline at entry.

  In NinjaScript (Managed Approach) "moving" the SL/PT is simply re-calling SetStopLoss /
  SetProfitTarget for the same signal name in OnBarUpdate; NinjaScript updates the existing
  order and places the level on the correct side of the position automatically (no sign
  handling needed for Ticks/Price/Percent).

  These blocks use the SQX RangeLevel formula (keys SQ.Formulas.RangeLevel.*), not the SLPT
  formula. SetStopLoss.OnAction() evaluates the formula against
  order.getOpenPrice() (the ENTRY price), not the current price - so a RANGE offset is measured
  from entry, which maps exactly to NinjaScript CalculationMode.Ticks (offset from the entry
  fill). Hence Move is almost identical to the inline printSetSLPT.

  @param block          the Move SL/PT action block.
  @param slptType       "SL" or "PT".
  @param slptParamName  the RangeLevel parameter key (e.g. "#StopLoss.StopLoss#").
  Generates one NinjaScript statement:
    None          -> (nothing)
    FixedValue    -> CalculationMode.Ticks, <pips>           (offset from entry)
    PriceRange    -> CalculationMode.Ticks, <offset expr>    (offset from entry)
    PctValue      -> CalculationMode.Percent, <value>
    ATRBasedValue -> CalculationMode.Ticks, sqAtrTicks(mult, period)
    PriceLevel    -> CalculationMode.Price, <absolute price>
    ValueFromFormula / other -> "/* ... not supported yet */"
-->
<#--
  Signal name for a Move stop loss / Move profit target ACTION.

  Not the same problem as an entry's signal name. An entry block declares #Direction# as
  "Long=1,Short=-1" - two values - so the binary printDirectionValue is exact there, and the four
  Enter* templates keep using it. SetStopLoss.java / SetProfitTarget.java declare
  "Long=1,Short=-1,Any=0" and DEFAULT to Any, with showIfDefault=false, so the parameter is usually
  absent from the XML entirely. Through the binary macro Any would collapse onto "LE", and a Move
  action on a short position would address the long entry's signal.

  Any is therefore resolved at runtime against the open position - the same test sqOpenPLInPips uses.
  Long and Short stay literal.

  @param block  the SetStopLoss / SetProfitTarget action block.
  Generates: "LE" | "SE" | (Position.MarketPosition == MarketPosition.Short ? "SE" : "LE")
-->
<#macro printMoveSignalName block><@compress_single_line>
<#local dir = getParam(block, "#Direction#", "0") />
<#if dir == "1">"LE"<#elseif dir == "-1">"SE"<#else>(Position.MarketPosition == MarketPosition.Short ? "SE" : "LE")</#if>
</@compress_single_line></#macro>

<#macro printMoveSLPT block slptType slptParamName>
<#list block.* as param>
	<#if param.@key == slptParamName>
		<#local fkey = param.Formula[0].@key />
		<#-- Resolve CalculationMode + value into locals, then emit one clean line. -->
		<#local mode = "" />
		<#local val = "" />
		<#switch fkey>
			<#case "SQ.Formulas.RangeLevel.None"><#break>
			<#case "SQ.Formulas.RangeLevel.FixedValue">
				<#--
				  FixedValue is the ONE member of the RangeLevel family that is market-relative.
				  Its siblings use the price they are handed - which the Move
				  SL/PT blocks pass as the order's ENTRY price - so CalculationMode.Ticks is the
				  right mapping for them:

				    PriceRange.java    : direction == Long ? openPrice - v : openPrice + v
				    ATRBasedValue.java : direction == Long ? price - ATR*v : price + ATR*v

				  FixedValue.java discards that argument and reads the live market instead:

				    direction == Long ? Chart.Bid() - v : Chart.Ask() + v

				  Re-evaluated every bar by an ActionOnly "Move SL" rule that is a TRAILING stop,
				  while N ticks from entry re-set every bar is a FIXED one. So the level is computed
				  from the current bar, the way the trailing-stop emitter in ExitMethods.inc does it
				  (CalculationMode.Price + a price expression).

				  ONLY for the stop. StrategyQuant branches on the block's #Direction#, which is
				  also the order filter, so a TARGET computed this way lands on the stop side - a
				  long position gets its profit target BELOW the market, where it never triggers.
				  There is nothing there worth being faithful to, so PT keeps the entry-relative
				  reading, where NinjaScript puts the level on the correct side itself.

				  Close[0] rather than Bid: the export equates them and assumes no spread.
				-->
				<#if slptType == "SL">
					<#local mode = "CalculationMode.Price" />
					<#local dir = getParam(block, "#Direction#", "0") />
					<#local off><@compress_single_line>(<@printParameterValue param.Formula[0].Param />) * SqPip</@compress_single_line></#local>
					<#-- Direction Any takes StrategyQuant's SHORT branch, which puts a LONG position's
					     stop above the market. Not replicated: the export is not obliged to reproduce a
					     simulator outcome a real platform would reject, and the
					     divergence is bounded to this one parameter value. -->
					<#if dir == "1"><#local val>Close[0] - ${off}</#local>
					<#elseif dir == "-1"><#local val>Close[0] + ${off}</#local>
					<#else><#local val>(Position.MarketPosition == MarketPosition.Short ? Close[0] + ${off} : Close[0] - ${off})</#local></#if>
				<#else>
					<#local mode = "CalculationMode.Ticks" />
					<#-- FixedValue is in SQX pips; convert to a tick count for CalculationMode.Ticks. -->
					<#local val><@compress_single_line>(<@printParameterValue param.Formula[0].Param />) * SqPipFactor</@compress_single_line></#local>
				</#if>
				<#break>
			<#case "SQ.Formulas.RangeLevel.PriceRange">
				<#local mode = "CalculationMode.Ticks" />
				<#local val><@compress_single_line><@printBlock param.Formula[0]?children[0] /></@compress_single_line></#local>
				<#break>
			<#case "SQ.Formulas.RangeLevel.PctValue">
				<#-- UNREACHABLE: there is no Formulas/RangeLevel/PctValue.java (nor a
				     Range/ one). The family ships ATRBasedValue, FixedValue, None, PriceLevel and
				     PriceRange; PctValue exists only under Formulas/SLPT/, which this macro never sees.
				     Kept rather than deleted - it costs nothing and is right if the class is ever added -
				     but do not read its presence as evidence that the case is exercised. -->
				<#local mode = "CalculationMode.Percent" />
				<#local val><@compress_single_line><@printParameterValue param.Formula[0].Param /></@compress_single_line></#local>
				<#break>
			<#case "SQ.Formulas.RangeLevel.ATRBasedValue">
				<#local mode = "CalculationMode.Ticks" />
				<@useAtrRuntime /><#local val>sqAtrTicks(<@compress_single_line><@printParameterValue param.Formula[0].Param[0] /></@compress_single_line>, <@compress_single_line><@printParameterValue param.Formula[0].Param[1] /></@compress_single_line>)</#local>
				<#break>
			<#case "SQ.Formulas.RangeLevel.PriceLevel">
				<#local mode = "CalculationMode.Price" />
				<#local val><@compress_single_line><@printBlock param.Formula[0]?children[0] /></@compress_single_line></#local>
				<#break>
		</#switch>
		<#-- The level is STORED, not submitted, and only while a position is OPEN. Both halves matter:

		     * FLAT guard - SQX's SetStopLoss.OnAction walks getOpenOrdersCount() and modifies what it
		       finds, so with nothing open the block is a no-op. NinjaTrader is not: a Set call issued
		       while flat is remembered and attached to the next entry using that signal name, so the
		       stop would go live with the fill.
		     * DEFERRAL - printMoveSLPTApply hands the level to NinjaTrader at the top of the NEXT bar.
		       Submitting it here would fill inside the same bar, which StrategyQuant cannot do: its
		       action only calls order.setSL() and the simulator materializes the exit order on the
		       following bar. Same deferral and the same reason as the pending SL/PT arming.

		     Stored as an absolute PRICE whatever the formula's mode, because one double has to carry it:
		     a Ticks distance is measured off Position.AveragePrice, the same anchor SetStopLoss(Ticks)
		     uses, and a Percent one off the same price. -->
		<#local moveDir = getParam(block, "#Direction#", "0") />
		<#local moveSign><#if slptType == "SL"><#if moveDir == "-1">+<#else>-</#if><#else><#if moveDir == "-1">-<#else>+</#if></#if></#local>
		<#local moveLevel><#if mode == "CalculationMode.Price">${val}<#elseif mode == "CalculationMode.Percent">sqRoundPrice(Position.AveragePrice * (1 ${moveSign} (${val}) / 100))<#else>sqRoundPrice(Position.AveragePrice ${moveSign} (${val}) * TickSize)</#if></#local>
		<#if fkey == "SQ.Formulas.RangeLevel.None"><#-- no SL/PT to move -->
		<#elseif mode == "">/* ${slptType} formula ${fkey} not supported yet */
		<#elseif slptType == "SL">if (Position.MarketPosition != MarketPosition.Flat)
					sqMoveSL = ${moveLevel};<#else>if (Position.MarketPosition != MarketPosition.Flat)
					sqMovePT = ${moveLevel};</#if>
	</#if>
</#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  Render the FORMULA sub-tree of a named parameter to a NinjaScript expression. Used by
  AssignVariable (variable = <formula>) where the value is an arbitrary formula (arithmetic,
  indicators, variables) rather than a single literal/variable/formula-key.

  Delegates the rendering to printBlock (Blocks.inc), which dispatches to the operand block
  templates and degrades gracefully (/* ... not supported */) for operands outside the current
  block set. Mirrors JForex Parameters.inc printFormulaParam.

  @param block      the action block whose <Param> children are scanned.
  @param paramName  the parameter key holding the formula (e.g. "#Value#").
  Generates: the C# expression of the formula's first operand sub-tree.
-->
<#macro printFormulaParam block paramName><@compress_single_line>
<#list block.* as param>
	<#if param.@key == paramName>
      <@printBlock param.Formula[0]?children[0] />
   </#if>
</#list>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#--
  Declare every strategy variable as a private field of the class, mapping the
  SQX variable type to its C# type: "int" -> int, "boolean" -> bool, "string" -> string,
  everything else -> double.
  The boolean branch is required for Signal rules (Blocks.inc), which assign a boolean condition
  to the variable (var = (SMA(...) > SMA(...));) - declaring such a signal/flag variable as double
  would not compile (CS0029: cannot implicitly convert 'bool' to 'double'). Mirrors the MT5 export,
  which likewise maps var.type == "boolean" to bool.
  The field is INITIALIZED to the variable's actual <value> (via printVariableInit), NOT hardcoded
  to 0/false. This is critical: builder strategies bind an indicator's numeric parameters (period,
  deviation, ...) to strategy variables so they can be optimized; the variable carries the chosen
  value in <value>. Hardcoding 0 would make every variable-bound parameter evaluate as 0 at runtime
  (e.g. "KeltnerChannel(Close, 1.5, KCPeriod)" with "KCPeriod = 0" -> a period-0 indicator that NT8
  refuses to backtest). Mirrors the MT5 export, which initializes to ${var.value}.
  Variables are read from doc.StrategyFile.Strategy.Variables; each C# name is sanitized via
  csVariableName (consistent with printVariableName). Emitted in the class body (Main.tpl) so
  AssignVariable and variable-bound parameters can use them. Note: TradingOptions variables are
  already removed upstream (SourceCodeGenerator.getSource), so the list contains only user/strategy
  variables.
-->
<#macro printVariableDeclarations>
<#list doc.StrategyFile.Strategy.Variables.* as var>
<#local ctype><#if var.type == "int">int<#elseif var.type == "boolean">bool<#elseif var.type == "string">string<#else>double</#if></#local>
<#if (var.makeExternal[0]!"false") == "true">
		<#-- A makeExternal variable becomes a public [NinjaScriptProperty] - settable and optimizable
		     in the NT8 UI, the counterpart of an MT input/extern. Its default is NOT a field
		     initializer but an assignment in State.SetDefaults (printExternalVariableDefaults), which
		     is the NinjaScript convention. References through printVariableName -> csVariableName are
		     unaffected: a property of the same name reads and writes like a field. -->
		[NinjaScriptProperty]
<@printVariableRange var ctype />		[Display(Name="${var.name?j_string}", GroupName="Strategy Parameters", Order=${var?index})]
		public ${ctype} ${csVariableName(var)} { get; set; }
<#else>
		private ${ctype} ${csVariableName(var)} = <@printVariableInit var />;
</#if>
</#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  The [Range] validation attribute for a numeric [NinjaScriptProperty]. Emitted ONLY when the
  variable carries both <min> and <max>.
  int -> Range(int,int), double -> Range(double,double). Bool and string have no Range.
-->
<#macro printVariableRange var ctype><#if (ctype == "int" || ctype == "double") && var.min[0]?? && var.max[0]??>		[Range(${var.min}, ${var.max})]
</#if></#macro>

<#-------------------------------------------------------------->
<#--
  Defaults of the external variables, emitted in State.SetDefaults (Main.tpl), because a
  [NinjaScriptProperty] property has no field initializer. The value comes from <value> through
  printVariableInit, the same path the private fields use. Non-external variables are not handled
  here - they carry a field initializer.
-->
<#macro printExternalVariableDefaults>
<#list doc.StrategyFile.Strategy.Variables.* as var>
<#if (var.makeExternal[0]!"false") == "true">
				${csVariableName(var)} = <@printVariableInit var />;
</#if>
</#list>
</#macro>

<#-------------------------------------------------------------->
<#--
  Defaults of the COTSymbol inputs (global/cotSymbols.inc), emitted in State.SetDefaults: the market each
  input held at export, and an empty COTLicenseCode. The properties themselves are declared by SqCOTBlocks.inc.
-->
<#macro printCotSymbolDefaults>
<#list cotSymbols as cotSymbol>
				${cotSymbolInput(cotSymbol)} = "${cotSymbol?j_string}";
</#list>
<#if cotCheckedSymbols?has_content>
				COTLicenseCode = "";
</#if>
</#macro>

<#-------------------------------------------------------------->
<#--
  Emit the C# initializer literal for a strategy variable from its <value>, per declared type:
    boolean -> true/false (SQX stores lowercase "true"/"false"; "1" and any case of "true" also
              accepted - a silent false on a case variant would be a value change). A bool field
              cannot be initialized with 0. Empty/absent -> false.
    string  -> the value in double quotes, Java-escaped (?j_string: \" \\ \n... are valid C# escapes
              too), so a quote/backslash in the value cannot break the literal.
    int     -> the value with a redundant TRAILING ".0" stripped so it stays an int literal. The
              ?ends_with guard (same idiom as printParameterValue above) is required: an unguarded
              ?replace(".0", "") replaces ALL occurrences and would silently corrupt a malformed
              value like "10.05" -> "105"; with the guard such a value passes through verbatim and
              fails C# compilation NOISILY instead. Empty/absent -> 0.
    double  -> the value verbatim. Empty/absent -> 0.
  The value text is captured into a plain string first so it can be compared/manipulated safely
  (?has_content / ?ends_with) regardless of the underlying XML node model. The [0] index on
  var.value is REQUIRED for the absent-<value> default to work: in the FreeMarker DOM model a
  missing child returns an EMPTY NODE SEQUENCE (a defined value), so a bare (var.value)!"" never
  falls back and ${...} throws on the empty sequence; (var.value[0])!"" is the working idiom
  (same as param.@variable[0]?? / param.Formula[0]?? used elsewhere in this file).
  @param var  the <variable> node (with <type> and <value> children).
-->
<#macro printVariableInit var><@compress_single_line>
<#local raw>${(var.value[0])!""}</#local>
<#if var.type == "boolean"><#if raw?lower_case == "true" || raw == "1">true<#else>false</#if><#elseif var.type == "string">"${raw?j_string}"<#elseif var.type == "int"><#if raw?has_content><#if raw?ends_with(".0")>${raw?replace(".0", "")}<#else>${raw}</#if><#else>0</#if><#else><#if raw?has_content>${raw}<#else>0</#if></#if>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     INDICATOR VARIANT macros
     Mechanical comparisons of a native NT indicator's value at different bars/levels.
     `ind` is the NinjaScript method name (e.g. "ATR"); the block carries #Period#,
     optional #Level# and #Shift#. Used by blocks/<Ind><Variant>.tpl (ATR/CCI/StdDev).
     ============================================================ -->

<#--
  Emit one indicator value at a given bar offset:  <ind>(<input>, <period>)[<shift>].
  @param block  the variant block (carries #Period#/#Shift#).
  @param ind    NinjaScript indicator method name (e.g. "ATR").
  @param shift  extra bar offset (e.g. "0"/"1"/"2"), combined with the block's #Shift#.

  These indicator names do NOT map to the like-named native NT indicator, because the native
  calculation differs from the SQX Java snippet (the other platforms use their own Sq*
  implementations too):
    - "Momentum": SQX Momentum is a RATIO (Input[0]*100/Input[Period]), not the native NT
      absolute Momentum (Close - Close[n]). Emitted inline as the ratio expression, with the
      divisor index clamped to the bars available so far (warm-up: min(Period, CurrentBar)),
      mirroring Momentum.java's Math.min(Period, CurrentBar) guard. NT-safe (no div-by-zero:
      Input[...] is a price, never 0).
    - "CCI": SQX CCI is the Lambert CCI computed on the #ComputedFrom# series with a plain
      rolling SMA and mean-deviation divisor (CCI.java), which differs from native NT CCI.
      Computed by the installed SqCCI indicator.
    - "ATR": SQX ATR (ATR.java) seeds bar 0 with High-Low and divides by min(CurrentBar+1, period)
      over the warm-up. Computed by the installed SqATR indicator. ATR has no #ComputedFrom#, so
      printInput only binds the indicator to the block's chart.
    - "ADX": SQX ADX (ADX.java OnBarUpdateStandard) uses Wilder running sums with SQUtils.round-to-8;
      the native NT ADX seeds its Wilder smoothing differently, and the double smoothing amplifies
      the difference. Computed by the installed SqADX indicator (Values[0] = the ADX line). ADX has
      no #ComputedFrom# (it reads High/Low/Close directly); printInput only binds the chart.
    - "ROC": SQX ROC (ROC.java, Close only, 0 before bar period), routed to the installed SqROC indicator
      and rounded to 6 decimals as the ROC condition blocks read it.
    - "HMA": SQX Hull MA (HullMovingAverage.java, three AverageCalculator LWMAs), routed to
      the installed SqHullMovingAverage like the plain value block, rounded to 6
      decimals as the HMA condition blocks read it (getRounded).
  All other names keep the native ${ind}(input, period)[barsAgo] form.
-->
<#macro printIndValueAt block ind shift><@compress_single_line>
<#if ind == "Momentum">
<#-- SQX ratio Momentum: Input[shift]*100/Input[shift + min(Period, CurrentBar - shift)].
     The divisor index is clamped exactly like Momentum.java (Math.min(Period, CurrentBar)),
     evaluated at the bar 'shift' bars back (its CurrentBar was CurrentBar - shift). -->
(<@printSeriesAt block shift><@printInput block /></@printSeriesAt> * 100.0 / <@printInput block />[<@printCIShift block shift /> + Math.Min(<@printParam block "#Period#" />, CurrentBar - (<@printCIShift block shift />))])
<#elseif ind == "CCI">
<#-- SQX Lambert CCI on #ComputedFrom# (the installed SqCCI indicator); native NT CCI is numerically different. -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqCCI(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
<#elseif ind == "ADX">
<#-- SQX standard ADX line from the installed SqADX indicator; native NT ADX is numerically different. -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqADX(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
<#elseif ind == "ATR">
<#-- SQX ATR (ATR.java: bar-0 seed High-Low, warm-up divisor min(CurrentBar+1, period)) from the
     installed SqATR indicator, as the plain ATR value block reads it. -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqATR(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>
<#elseif ind == "ROC">
<#-- The ROC condition blocks compare Value.getRounded(...), 6 decimals. -->
<#global sqUsesIndicatorPackage = true>sqRound(<@printSeriesAt block shift>SqROC(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>, 6)
<#elseif ind == "HMA">
<#-- The HMA condition blocks compare Value.getRounded(...), 6 decimals. -->
<#global sqUsesIndicatorPackage = true>sqRound(<@printSeriesAt block shift>SqHullMovingAverage(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt>, 6)
<#else>
<@printSeriesAt block shift>${ind}(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>
</#if>
</@compress_single_line></#macro>

<#-- Rising: value one bar ago is below the current value (indicator increasing). -->
<#macro printIndRising block ind>(<@printIndValueAt block ind "1"/> < <@printIndValueAt block ind "0"/>)</#macro>
<#-- Falling: value one bar ago is above the current value (indicator decreasing). -->
<#macro printIndFalling block ind>(<@printIndValueAt block ind "1"/> > <@printIndValueAt block ind "0"/>)</#macro>
<#-- Higher: current value is above #Level#. -->
<#macro printIndHigher block ind>(<@printIndValueAt block ind "0"/> > <@printParam block "#Level#" />)</#macro>
<#-- Lower: current value is below #Level#. -->
<#macro printIndLower block ind>(<@printIndValueAt block ind "0"/> < <@printParam block "#Level#" />)</#macro>
<#-- CrossUp: value crossed above #Level# between the previous and the current bar. -->
<#macro printIndCrossUp block ind>(<@printIndValueAt block ind "1"/> < <@printParam block "#Level#" /> && <@printIndValueAt block ind "0"/> > <@printParam block "#Level#" />)</#macro>
<#-- CrossDown: value crossed below #Level# between the previous and the current bar. -->
<#macro printIndCrossDown block ind>(<@printIndValueAt block ind "1"/> > <@printParam block "#Level#" /> && <@printIndValueAt block ind "0"/> < <@printParam block "#Level#" />)</#macro>
<#-- ChangesUp: local minimum (was falling, now rising) - direction change upwards. -->
<#macro printIndChangesUp block ind>(<@printIndValueAt block ind "2"/> > <@printIndValueAt block ind "1"/> && <@printIndValueAt block ind "1"/> < <@printIndValueAt block ind "0"/>)</#macro>
<#-- ChangesDown: local maximum (was rising, now falling) - direction change downwards. -->
<#macro printIndChangesDown block ind>(<@printIndValueAt block ind "2"/> < <@printIndValueAt block ind "1"/> && <@printIndValueAt block ind "1"/> > <@printIndValueAt block ind "0"/>)</#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     KAMA macro
     Kaufman Adaptive Moving Average has 3 distinct period params
     (#ShortPeriod#/#ERPeriod#/#LongPeriod#), so it cannot reuse the generic
     printIndValueAt (which assumes a single #Period#).
     SQX parameters:
       #ShortPeriod# = min smoothing (fast length)
       #ERPeriod#    = efficiency ratio period
       #LongPeriod#  = max smoothing (slow length)
     @param block  the KAMA block (carries the 3 periods + #Shift#).
     @param shift  extra bar offset ("0"/"1"), combined with the block's #Shift#.
     ============================================================ -->
<#-- KAMA -> the installed SqKAMA indicator, not the native NinjaScript KAMA. The native accepts Fast 1..125
     while SQX's ShortPeriod goes to 500, so a strategy the Builder considers valid could compile and
     then fail to RUN, NinjaTrader refusing the indicator and leaving an empty data series.
     Argument order is SQX's (ER, Short, Long), not the native's (fast, period, slow). -->
<#macro printKamaValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqKAMA(<@printInput block />, <@printParam block "#ERPeriod#" />, <@printParam block "#ShortPeriod#" />, <@printParam block "#LongPeriod#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     BULLS/BEARS POWER macro
     SQX BullsPower.java = Input.High[0] - EMA(ComputedFrom, Period);
         BearsPower.java = Input.Low[0]  - EMA(ComputedFrom, Period).
     The value is a composite (price - EMA), not a single IND(input,period) call,
     so it cannot reuse the generic printIndValueAt. NT has native EMA(input, period),
     so this maps natively (no SQIndicators.inc) - like SMMA/MA.
     The price term is ALWAYS the bar High/Low (independent of #ComputedFrom#, which selects
     only the EMA source); both terms get the SAME shift, so the value holds at #Shift# != 0.
     The price term goes through printSeries, so it follows the block's #Chart# just like the
     EMA input does - a raw "High[k]" would read the PRIMARY chart while the EMA computed from
     the subchart.
     @param block  the BullsPower/BearsPower block (carries #Period#/#ComputedFrom#/#Shift#).
     @param price  the bar price series: "High" (BullsPower) or "Low" (BearsPower).
     @param shift  extra bar offset ("0"/"1"), combined with the block's #Shift#.
     ============================================================ -->
<#macro printBullsBearsValueAt block price shift><@compress_single_line>(<@printSeriesAt block shift><@printSeries block price /></@printSeriesAt> - <@printSeriesAt block shift>EMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt>)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     MULTI-OUTPUT INDICATOR macros
     Map the SQX #Line# parameter to the matching native NinjaScript output property.
     #Line# values come from the SQX catalog (TA-Lib convention): MACD 0=main/1=signal/2=hist,
     Bollinger 0=upper/1=middle/2=lower, Stochastic 0=%K/1=%D, ADX 0=ADX/1=+DI/2=-DI.
     NT parameter ORDER differs from SQX: Bollinger(input, numStdDev, period) - handled per
     macro below. Stochastic maps to the installed SqStochastic indicator, not native NT.
     ============================================================ -->

<#--
  MACD line from the installed SqMACD indicator, not the native NinjaScript MACD(...): the native
  MACD.Avg is an EMA of the MACD line, while MACD.java's signal is the simple moving average of the main
  line, and SqMACD computes it that way.
  #Line# 0 -> main (Values[0]), 1 -> signal (Values[1]), 2 -> histogram (main - signal).
  Output e.g.: SqMACD(Close, 12, 26, 9).Values[0][0] (main) / SqMACD(Close, 12, 26, 9).Values[1][0] (signal) /
               (SqMACD(Close, 12, 26, 9).Values[0][0] - SqMACD(Close, 12, 26, 9).Values[1][0]) (histogram).
-->
<#macro printMACDLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#switch line>
<#case "1"><@printMACDCall block "1" shift /><#break>
<#case "2">(<@printMACDCall block "0" shift /> - <@printMACDCall block "1" shift />)<#break>
<#default><@printMACDCall block "0" shift />
</#switch>
</@compress_single_line></#macro>

<#--
  One SqMACD line. @param which "0" = main line, "1" = signal line. @param shift extra bar offset.
  Output e.g.: SqMACD(Close, 12, 26, 9).Values[0][0]
-->
<#macro printMACDCall block which shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqMACD(<@printInput block />, <@printParam block "#Fast#" />, <@printParam block "#Slow#" />, <@printParam block "#Smooth#" />).Values[${which}]</@printSeriesAt></@compress_single_line></#macro>

<#--
  WaveTrend line selected by #Line#: 0 -> WT1 (Main), 1 -> WT2 (Signal).
  WaveTrend.java declares exactly the two outputs, so #Line# is only ever 0 or 1.
  Output e.g.: SqWaveTrend(Close, 10, 21).Values[0][0]
-->
<#macro printWaveTrendLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#switch line>
<#case "1"><@printWaveTrendCall block "1" shift /><#break>
<#default><@printWaveTrendCall block "0" shift />
</#switch>
</@compress_single_line></#macro>

<#--
  One SqWaveTrend line. @param which "0" = WT1 (Main), "1" = WT2 (Signal). @param shift extra bar offset.
-->
<#macro printWaveTrendCall block which shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqWaveTrend(<@printInput block />, <@printParam block "#ChannelLength#" />, <@printParam block "#AverageLength#" />).Values[${which}]</@printSeriesAt></@compress_single_line></#macro>

<#--
  Anchored VWAP line selected by #Line#: 0 -> VWAP, 1 -> Upper band, 2 -> Lower band
  (the AnchoredVWAP.java output order), from the installed SqAnchoredVWAP indicator.
  Output e.g.: SqAnchoredVWAP(Close, 1, 2.0).Values[0][0]
-->
<#macro printAnchoredVWAPLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#switch line>
<#case "1"><@printAnchoredVWAPCall block "1" shift /><#break>
<#case "2"><@printAnchoredVWAPCall block "2" shift /><#break>
<#default><@printAnchoredVWAPCall block "0" shift />
</#switch>
</@compress_single_line></#macro>

<#--
  One SqAnchoredVWAP line. @param which "0" = VWAP, "1" = Upper, "2" = Lower. @param shift extra bar offset.
-->
<#macro printAnchoredVWAPCall block which shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAnchoredVWAP(<@printInput block />, <@printParam block "#SessionType#" />, <@printParam block "#StdDevMult#" "1.0" />).Values[${which}]</@printSeriesAt></@compress_single_line></#macro>

<#-- One WaveTrend line value at a bar offset (variant blocks; the printMACDValueAt pattern).
     @param line "MAIN" (WT1, which 0) or "SIGNAL" (WT2, which 1). @param shift extra bar offset.
     The value is the raw indicator value, as the MACD family macros also emit it. -->
<#macro printWaveTrendValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqWaveTrend(<@printInput block />, <@printParam block "#ChannelLength#" />, <@printParam block "#AverageLength#" />).Values[<#if line == "SIGNAL">1<#else>0</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#-- One Anchored VWAP line value at a bar offset (variant blocks). @param line "VWAP"/"UPPER"/"LOWER".
     @param shift extra bar offset. Same raw-value family convention as printWaveTrendValueAt. -->
<#macro printAnchoredVWAPValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAnchoredVWAP(<@printInput block />, <@printParam block "#SessionType#" />, <@printParam block "#StdDevMult#" "1.0" />).Values[<#if line == "UPPER">1<#elseif line == "LOWER">2<#else>0</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#--
  The VolumeProfile block itself is not offered for NinjaTrader (see VolumeProfile.java), so there
  is no VolumeProfile line macro here. The installed SqVolumeProfile and SqVPSignal indicators serve
  the VP* variant blocks, which do render for NinjaTrader.
-->

<#--
  TPO Profile line selected by #Line#: Java @Output order 0..22 == the SqTPOProfile Values
  1:1. The UseCustomHours window is passed through to the indicator (printTPOProfileCall).
-->
<#macro printTPOProfileLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<@printTPOProfileCall block line shift />
</@compress_single_line></#macro>

<#-- One SqTPOProfile line (which 0..22). UseCustomHours and its StartHour/StartMinute ->
     EndHour/EndMinute window are passed through to the indicator. Defaults match the Java
     @Parameter defaults: UseCustomHours=false, 0:00 -> 23:59.
     Output e.g.: SqTPOProfile(Close, 1, 150, 2, 1, 70, 30, 240, 720, 720, 0, false, 0, 0, 23, 59).Values[0][0] -->
<#macro printTPOProfileCall block which shift><@compress_single_line>
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqTPOProfile(<@printInput block />, <@printParam block "#SessionType#" "1" />, <@printParam block "#ProfileRows#" "150" />, <@printParam block "#BinSizeMode#" "2" />, <@printParam block "#TicksPerBin#" "1" />, <@printParam block "#ValueAreaPct#" "70" />, <@printParam block "#BracketMinDaily#" "30" />, <@printParam block "#BracketMinWeekly#" "240" />, <@printParam block "#BracketMinMonthly#" "720" />, <@printParam block "#BracketMinYearly#" "720" />, 0, <@printTPOCustomHours block />).Values[${which}]</@printSeriesAt>
</@compress_single_line></#macro>

<#-- The UseCustomHours window as five C# arguments. Kept as its own macro so the boolean is
     normalised in one place: the strategy XML writes "true"/"false", C# needs a bare literal. -->
<#macro printTPOCustomHours block><@compress_single_line>
<#local custom = getParam(block, "#UseCustomHours#", "false") />
<#if custom == "true">true<#else>false</#if>, <@printParam block "#StartHour#" "0" />, <@printParam block "#StartMinute#" "0" />, <@printParam block "#EndHour#" "23" />, <@printParam block "#EndMinute#" "59" />
</@compress_single_line></#macro>

<#-- One Anchored VWAP line value of the FAST/SLOW instance (AVWAPFast/Slow comparison blocks).
     @param prefix "Fast" or "Slow" - selects the #FastSessionType#/#FastStdDevMult# (resp. Slow)
     parameter pair; both instances read the VWAP line. @param shift extra bar offset. -->
<#macro printAnchoredVWAPFastSlowAt block prefix shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAnchoredVWAP(<@printInput block />, <@printParam block "#${prefix}SessionType#" />, <@printParam block "#${prefix}StdDevMult#" "1.0" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#--
  "No duplicate trades" guard for entry actions.

  EnterAtMarket.java / EnterAtStop.java / EnterAtLimit.java declare #AllowDuplicateTrades# with a
  default of false, and the engine then refuses a new entry while a live order exists, in EITHER
  direction (Java: checkLiveOrderExists(0, true); MT5 runtime: sqSelectPosition(magic, symbol, 0)).
  Without this NinjaTrader happily takes the opposite entry and REVERSES the open position, which it
  reports as a trade closed with exit name "Close position".

  Emitted as an extra term on the openingOrdersAllowed condition. EnterReverseAtMarket deliberately
  does NOT use this: reversing is the whole point of that block. Mirrors EasyLanguage's
  printAllowDuplicateTradesCondition, which prefixes the action with `if(MarketPosition = 0)`.

  UNCONDITIONAL, whatever #AllowDuplicateTrades# says. Keying it on the flag would be right on an
  engine where the flag decides something. On this one it never does:

    // EnterAtMarket.OnAction
    if ((!AllowDuplicateTrades || !engineSupportsDuplicateTrades()) && checkLiveOrderExists(0, true) != null)
        return;

  NinjaTraderSimulator extends BarCloseSimulator, whose supportsDuplicateTrades() returns FALSE, so the
  left side is true whatever the flag says and StrategyQuant refuses the second entry either way.
  (The flag ALSO makes openNormalOrder clone the exit methods per order, which changes trailing-stop
  behaviour - a second effect that cannot produce a second position.)

  Keying the guard on the flag would therefore remove it exactly when a user asks for duplicates, and
  leave the exported strategy entering while a position is open when StrategyQuant would not.
-->
<#macro printNoDuplicateGuard block> && Position.MarketPosition == MarketPosition.Flat</#macro>

<#-------------------------------------------------------------->
<#--
  The same-bar rule for market entry blocks of one direction.

  NinjaScript ignores a second EnterLong / EnterShort of the same signal name on a bar: the first one
  has not filled, so the Flat guard lets every later block through, and each of them would still run
  its SetStopLoss / SetProfitTarget and overwrite the levels the first entry fills with. StrategyQuant
  refuses the second entry (EnterAtMarket.OnAction on the NinjaTrader engine). So when a strategy has
  more than one EnterAtMarket block of a direction, each of them checks that no market entry of that
  direction was submitted on the bar, and records its own submission.

  countMarketEntries - number of EnterAtMarket actions of the direction ("1" long, "-1" short) in the
                       OnBarUpdate rules.
  printSameBarMarketGuard - " && sqLongMarketEntryBar != CurrentBar", or nothing for a single block.
  printSameBarMarketRecord - "sqLongMarketEntryBar = CurrentBar;", or nothing for a single block.
-->
<#function countMarketEntries dir>
  <#local n = 0 />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#local a = action />
            <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
            <#if a.@key?string == "EnterAtMarket" && marketEntryDir(a) == dir><#local n = n + 1 /></#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#return n />
</#function>

<#--
  Entry ownership for strategies with several market entry blocks of one direction.

  StrategyQuant attaches exit methods (ExitAfterBars, MoveSL2BE, TrailingStop) to the order their
  block opened; the export emits them per direction and they act on any position of it. When a
  direction has more than one EnterAtMarket block, the export records which block entered
  (sqLongEntryOwner / sqShortEntryOwner, the block's 1-based position among the direction's market
  blocks) and each exit-method block acts only on its own block's position. The same-bar rule above
  makes the recorded block the one that fills.

  Only when every entry block of the direction is a plain EnterAtMarket in an IfThen / ActionOnly
  rule: a pending entry fills bars after it was submitted, so the block recorded at submission is not
  necessarily the one that filled.

  entryOwnerMode(dir)  - true when ownership is tracked for the direction.
  entryOwnerField(dir) - "sqLongEntryOwner" / "sqShortEntryOwner".
-->
<#function entryOwnerMode dir>
  <#if (countMarketEntries(dir) < 2)><#return false /></#if>
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#list event.* as rule>
      <#list rule?children as part>
        <#if part?node_type == "element" && (part?node_name == "Then" || part?node_name == "Else")>
          <#list part?children as action>
            <#if action?node_type == "element">
              <#local a = action />
              <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
              <#local k = "" + a.@key />
              <#if (k == "EnterAtStop" || k == "EnterAtLimit" || k == "EnterReverseAtMarket") && marketEntryDir(a) == dir><#return false /></#if>
              <#if k == "EnterAtMarket" && marketEntryDir(a) == dir && (part?node_name == "Else" || event.@key != "OnBarUpdate")><#return false /></#if>
            </#if>
          </#list>
        </#if>
      </#list>
    </#list>
  </#list>
  <#return true />
</#function>

<#-- True when the strategy has a pending entry block (EnterAtStop / EnterAtLimit) of the direction, in
     any rule and event: then a market entry block of that direction can meet a working pending under
     its own signal name and needs the park-and-F branch. -->
<#function hasPendingEntryBlock dir>
  <#return hasPendingEntryBlockOfType(dir, "EnterAtStop") || hasPendingEntryBlockOfType(dir, "EnterAtLimit") />
</#function>

<#-- True when the strategy has both an EnterAtStop and an EnterAtLimit of the direction. Both go out
     under the direction's one signal name, and NinjaTrader ignores a second pending of a DIFFERENT order
     type submitted on the same bar - the first one stays. -->
<#function hasBothPendingTypes dir>
  <#return hasPendingEntryBlockOfType(dir, "EnterAtStop") && hasPendingEntryBlockOfType(dir, "EnterAtLimit") />
</#function>

<#-- The gate a pending block of a direction with both types carries: once the bar queued a pending of
     the other type for the direction, the block does nothing - no stop state, no reset, no queue - so the
     level, the type and the stop that go out stay the first one's, the pending NinjaTrader keeps. Unless
     its own level is already through the market: then it is a market entry, which withdraws the queued
     pending (sqNoteMarketEntry) exactly as the backtest's market entry withdraws the bar's pendings. -->
<#macro printOtherPendingTypeGuard block isLimit><#local d = marketEntryDir(block) /><#if hasBothPendingTypes(d)><#local side = (d == "-1")?then("Short", "Long") /><#local crossed = ((d == "-1") == isLimit)?then("<=", ">=") /> && (!(sq${side}PendTakenThisBar && <#if isLimit>!</#if>sq${side}PendIsLimit) || sqRoundPrice(sqRound(<@printPrice block "#Price#" />, 5)) ${crossed} Close[0])</#if></#macro>

<#function hasPendingEntryBlockOfType dir key>
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#list event.* as rule>
      <#list rule?children as part>
        <#if part?node_type == "element" && (part?node_name == "Then" || part?node_name == "Else")>
          <#list part?children as action>
            <#if action?node_type == "element">
              <#local a = action />
              <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
              <#local k = "" + a.@key />
              <#if k == key && marketEntryDir(a) == dir><#return true /></#if>
            </#if>
          </#list>
        </#if>
      </#list>
    </#list>
  </#list>
  <#return false />
</#function>

<#-- True when a reverse market entry of the direction may re-enter on the bar its timed exit fires. The
     timed exit closes the position by pushing its stop through the market, so the position is still
     open when the entry rule runs on that bar close; StrategyQuant's reverse entry closes it at the next
     open and opens the new one at the same open. A plain market entry does not: StrategyQuant refuses it
     while the position is open, and it enters on a later signal. The re-entry goes under a second signal
     name (EntryHandling.UniqueEntries allows one entry per name), so the pushed stop and the new market
     entry fill at the same open. Limited to a direction without pending entries and not tracked by
     owner, where the entry name is the direction's one base name. -->
<#function timedExitReentry dir>
  <#if hasPendingEntryBlock(dir) || entryOwnerMode(dir)><#return false /></#if>
  <#local hasTimedExit = false />
  <#local hasMarketEntry = false />
  <#list doc.StrategyFile.Strategy.Rules.Events.* as event>
    <#if event.@key == "OnBarUpdate">
      <#list event.* as rule>
        <#if rule.Then[0]??>
          <#list rule.Then.* as action>
            <#local a = action />
            <#if a?node_name == "Block"><#local a = a?children[0] /></#if>
            <#local k = "" + a.@key />
            <#if k == "EnterReverseAtMarket" && marketEntryDir(a) == dir>
              <#local hasMarketEntry = true />
              <#if hasExitMethod(a, "#ExitAfterBars.ExitAfterBars#")><#local hasTimedExit = true /></#if>
            </#if>
          </#list>
        </#if>
      </#list>
    </#if>
  </#list>
  <#return hasTimedExit && hasMarketEntry />
</#function>

<#-- The re-entry branch of a market entry block, appended after its own if-block (see timedExitReentry).
     The old position keeps its own stop and target untouched - the timed exit has just pushed them - and
     the new entry alternates between the base name and the R-suffixed one. -->
<#macro printTimedExitReentry block>
<#local d = marketEntryDir(block) />
<#if timedExitReentry(d)><#local side = (d == "-1")?then("Short", "Long") />
			else if (openingOrdersAllowed && Position.MarketPosition == MarketPosition.${side} && sq${side}TimedExitBar == CurrentBar<@printSameBarMarketGuard block />)
			{
				sq${side}PendOrigin = false;
				<@printSameBarMarketRecord block />
				if (sq${side}EntrySignal == <@printSignalName block />)
				{
					<@printEntrySLPT block "close" "R" />
					sqNoteMarketEntry();
					Enter${side}(<@printSizeMethod block "#Size#" />, <@printSignalName block "R" />);
				}
				else
				{
					<@printEntrySLPT block "close" />
					sqNoteMarketEntry();
					Enter${side}(<@printSizeMethod block "#Size#" />, <@printSignalName block />);
				}
			}
</#if>
</#macro>

<#function entryOwnerField dir>
  <#if dir == "-1"><#return "sqShortEntryOwner" /></#if>
  <#return "sqLongEntryOwner" />
</#function>

<#function sameBarMarketField block>
  <#if marketEntryDir(block) == "-1"><#return "sqShortMarketEntryBar" /></#if>
  <#return "sqLongMarketEntryBar" />
</#function>

<#function marketEntryDir block>
  <#if ("" + getParam(block, "#Direction#", "1")) == "-1"><#return "-1" /></#if>
  <#return "1" />
</#function>

<#macro printSameBarMarketGuard block><#if (countMarketEntries(marketEntryDir(block)) > 1)> && ${sameBarMarketField(block)} != CurrentBar</#if></#macro>

<#-- The line break and indentation are part of the output: the caller's line holds only this macro
     call, and FreeMarker strips such a line's own break, which would put the next statement on it. -->
<#macro printSameBarMarketRecord block><#local d = marketEntryDir(block) /><#if (countMarketEntries(d) > 1)>${sameBarMarketField(block)} = CurrentBar;
				<#if entryOwnerMode(d)><#if d == "-1"><#assign sqShortMarketIdx = (sqShortMarketIdx!0) + 1 /><#local idx = sqShortMarketIdx /><#else><#assign sqLongMarketIdx = (sqLongMarketIdx!0) + 1 /><#local idx = sqLongMarketIdx /></#if>${entryOwnerField(d)} = ${idx};
				</#if></#if></#macro>

<#--
  Bollinger band line. NT order is Bollinger(input, numStdDev, period).
  Docs: https://ninjatrader.com/support/helpGuides/nt8/bollinger_bands.htm
  #Line# 1 -> .Lower, anything else -> .Upper.
-->
<#macro printBollingerLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#switch line>
<#case "1"><@printSeriesAt block shift>Bollinger(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).Lower</@printSeriesAt><#break>
<#default><@printSeriesAt block shift>Bollinger(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).Upper</@printSeriesAt>
</#switch>
</@compress_single_line></#macro>

<#--
  Stochastic line from the installed SqStochastic indicator, not the native NinjaScript
  Stochastics(), which is SMA-only and Low/High-only and would drop the SQX #MAMethod#
  (SMA/EMA/SMMA/LWMA) and #PriceField# (Low/High or Close/Close) choices. The indicator reads the
  High/Low/Close of the chart printInput binds it to.
  #Line# 0 -> %K (Values[0]), 1 -> %D (Values[1]).
  Output e.g.: SqStochastic(Close, 9, 3, 3, 0, 0).Values[0][0]
-->
<#macro printStochLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#-- MAMethod/PriceField default to 0 - strategies saved before the params existed omit them. -->
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqStochastic(<@printInput block />, <@printParam block "#KPeriod#" />, <@printParam block "#DPeriod#" />, <@printParam block "#Slowing#" />, <@printParam block "#MAMethod#" "0" />, <@printParam block "#PriceField#" "0" />).Values[<#if line == "1">1<#else>0</#if>]</@printSeriesAt>
</@compress_single_line></#macro>

<#--
  ADX / Directional Movement line from the installed SqADX indicator, NOT native NinjaScript
  ADX()/DM(). Native NT ADX/DM seed their Wilder smoothing differently from ADX.java (and the
  double Wilder smoothing of ADX amplifies the difference). SqADX computes ADX.java's
  OnBarUpdateStandard (Wilder running sums with SQUtils.round-to-8) from the chart's
  High/Low/Close; #ComputedFrom# is not used, printInput only binds the chart.
  @param block  the ADX block (carries #Period#/#Line#/#Shift#).
  @param shift  extra bar offset, combined with the block's #Shift#.
  #Line# 0 -> Values[0] (ADX); 1 -> Values[1] (+DI); 2 -> Values[2] (-DI).
  Output e.g.: SqADX(Close, 14).Values[0][0]
-->
<#macro printADXLine block shift><@compress_single_line>
<#local line = getParam(block, "#Line#", "0") />
<#global sqUsesIndicatorPackage = true><@printSeriesAt block shift>SqADX(<@printInput block />, <@printParam block "#Period#" />).Values[<#if line == "1">1<#elseif line == "2">2<#else>0</#if>]</@printSeriesAt>
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     DM (Directional Movement) VARIANT macros
     +DI / -DI variant blocks. The value comes from the installed SqADX indicator (ADX.java +DI/-DI;
     native NT DM differs). Used by blocks/DIPlus*.tpl / DIMinus*.tpl.
     ============================================================ -->

<#-- One DM line value at a bar offset from the installed SqADX indicator (ADX.java +DI/-DI).
     @param prop "DiPlus" (-> Values[1]) or "DiMinus" (-> Values[2]).
     Output e.g.: SqADX(Close, 14).Values[1][0] (+DI) / SqADX(Close, 14).Values[2][1] (-DI one bar back). -->
<#macro printDMValueAt block prop shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqADX(<@printInput block />, <@printParam block "#Period#" />).Values[<#if prop == "DiPlus">1<#else>2</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#-- DI line rising / falling (value[1] vs value[0]), on values rounded to 6 decimals as the blocks' getRounded. -->
<#macro printDMRising block prop>(sqRound(<@printDMValueAt block prop "1"/>, 6) < sqRound(<@printDMValueAt block prop "0"/>, 6))</#macro>
<#macro printDMFalling block prop>(sqRound(<@printDMValueAt block prop "1"/>, 6) > sqRound(<@printDMValueAt block prop "0"/>, 6))</#macro>
<#-- DI line direction change (local min / max). -->
<#macro printDMChangesUp block prop>(sqRound(<@printDMValueAt block prop "2"/>, 6) > sqRound(<@printDMValueAt block prop "1"/>, 6) && sqRound(<@printDMValueAt block prop "1"/>, 6) < sqRound(<@printDMValueAt block prop "0"/>, 6))</#macro>
<#macro printDMChangesDown block prop>(sqRound(<@printDMValueAt block prop "2"/>, 6) < sqRound(<@printDMValueAt block prop "1"/>, 6) && sqRound(<@printDMValueAt block prop "1"/>, 6) > sqRound(<@printDMValueAt block prop "0"/>, 6))</#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     MACD VARIANT value macro
     MACD variant blocks compare a specific MACD line at given bar offsets / against a level,
     zero, or the signal line. This macro emits one MACD line value; the blocks/MACD*.tpl
     templates build the inline comparison (rising/higher/cross/...). Docs:
     https://ninjatrader.com/support/helpGuides/nt8/moving_average_convergence-divergence_macd.htm
     ============================================================ -->

<#-- One MACD line value at a bar offset from the installed SqMACD indicator.
     @param line "MAIN" (Values[0]) or "SIGNAL" (Values[1], the SMA of the main line).
     Output e.g.: sqRound(SqMACD(Close, 12, 26, 9).Values[0][0], 6) -->
<#-- sqRound(..., 6): every MACD comparison block reads indicator.Main/Signal.getRounded(shift)
     (6 decimals, e.g. MACDMainChangesUp.java) - comparing RAW values flips a strict inequality
     when two neighbours differ only past the 6th decimal, creating patterns SQX's rounded
     comparison does not see. Same rule as printMAValueAt / printStochValueAt. -->
<#macro printMACDValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line>sqRound(<@printSeriesAt block shift>SqMACD(<@printInput block />, <@printParam block "#Fast#" />, <@printParam block "#Slow#" />, <@printParam block "#Smooth#" />).Values[<#if line == "SIGNAL">1<#else>0</#if>]</@printSeriesAt>, 6)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     STOCHASTIC VARIANT value macro
     Stochastic variant blocks compare a specific line (%K / %D) at bar offsets / against a
     level, or K vs D. This macro emits one Stochastic line value from the installed SqStochastic
     indicator, with #MAMethod#/#PriceField# (the native NinjaScript Stochastics would drop both).
     The blocks/Stoch*.tpl templates build the inline comparison.
     ============================================================ -->

<#-- One Woodies CCI operand at a bar offset: the WoodiesCCI*.java patterns read the CCI
     series exclusively through DataSeries.getRounded (half-up to 6 decimals, epsilon 1e-10) before
     EVERY comparison - sqRound(x, 6) reproduces that rounding exactly (same contract the
     comparison-block layer relies on). Factor/level literals stay raw (plain numbers in Java). -->
<#macro printWoodiesCCI block shift><@compress_single_line>sqRound(<@printIndValueAt block "CCI" shift />, 6)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- One Stochastic line value at a bar offset.  @param line  "K" (%K) or "D" (%D).
     MAMethod/PriceField default to 0 - strategies saved before the params existed omit them. -->
<#-- Rounded to 6 decimals: every Stoch* comparison block reads getRounded(Shift) in the Java
     (StochFastKUp/StochSlowDRising/...), and the raw C# value flips ties the 6dp value does not. -->
<#macro printStochValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line>sqRound(<@printSeriesAt block shift>SqStochastic(<@printInput block />, <@printParam block "#KPeriod#" />, <@printParam block "#DPeriod#" />, <@printParam block "#Slowing#" />, <@printParam block "#MAMethod#" "0" />, <@printParam block "#PriceField#" "0" />).Values[<#if line == "D">1<#else>0</#if>]</@printSeriesAt>, 6)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     BOLLINGER VARIANT value macro
     Bollinger variant blocks compare a band line (Upper/Lower) at bar offsets, or the bar's
     Close against a band (BarCloses). This macro emits one Bollinger band value; the
     blocks/BB*.tpl templates build the inline comparison. NT order: Bollinger(input, numStdDev,
     period); NT Bollinger has no .Middle -> Middle is SMA(input, period).
     Docs: https://ninjatrader.com/support/helpGuides/nt8/bollinger_bands.htm
     ============================================================ -->

<#-- One Bollinger band value at a bar offset.  @param line  "Upper" / "Lower" / "Middle". -->
<#macro printBollingerValueAt block line shift><@compress_single_line><#if line == "Middle"><@printSeriesAt block shift>SMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt><#else><@printSeriesAt block shift>Bollinger(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).${line}</@printSeriesAt></#if></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     AROON macros (the installed SqAroon indicator)
     Aroon is multi-output: AroonUp + AroonDown. SQX selects via #Line#; per Aroon.java
     (@Output Up green / Down red, AroonUpFallFromTop uses line 0 = Up) the convention is
     #Line# 0 -> Up, 1 -> Down. Aroon has no #ComputedFrom# (computed from High/Low).
     SQX Aroon uses an EXACTLY Period-bar window (Aroon.java), unlike native NT Aroon's Period+1
     window, so it is computed by SqAroon: Values[0] = Up, Values[1] = Down.
     ============================================================ -->

<#-- Aroon value for the value block: map the #Line# param (0 -> Up, 1 -> Down).
     SQX Aroon uses an EXACTLY Period-bar window (Aroon.java + Highest/LowestCalculator), while the
     native NT Aroon scans a Period+1-bar window, so it is numerically different (the other
     platforms use their own Sq* impl). Computed by the installed SqAroon indicator, the line selected
     by #Line# (0 = Up over Highs, 1 = Down over Lows).
     @param shift  bar offset, combined with the block's #Shift#.
     Output e.g.: SqAroon(Close, 14).Values[0][0] -->
<#macro printAroonLine block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAroon(<@printInput block />, <@printParam block "#Period#" />).Values[<@printParam block "#Line#" "0" />]</@printSeriesAt></@compress_single_line></#macro>

<#-- Aroon value at a fixed line (Up/Down) and shift, for inline variant blocks (the installed SqAroon).
     @param line   literal "Up" / "Down" (Up -> Values[0], Down -> Values[1]).  @param shift  bar offset.
     Output e.g.: SqAroon(Close, 14).Values[1][1] -->
<#macro printAroonValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAroon(<@printInput block />, <@printParam block "#Period#" />).Values[<#if line == "Down">1<#else>0</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     VOLUME / VORTEX macros
     - Volume: NT VOL() takes neither input nor period (uses the primary data series).
     - AvgVolume: the installed SqAvgVolume indicator, the SMA of the chart's Volume (AvgVolume.java).
     - Vortex: multi-output (VIPlus/VIMinus); #Line# 0 -> .VIPlus, 1 -> .VIMinus
       (per Vortex.java: @Output VIPlusSumRge=0, VIMinusSumRge=1).
     Docs: https://ninjatrader.com/support/helpguides/nt8/volume.htm ,
           https://ninjatrader.com/support/helpguides/nt8/vortex.htm
     ============================================================ -->

<#-- Volume value at a bar offset (NT VOL has no input/period). -->
<#macro printVolumeValueAt block shift><@compress_single_line><#local ci = getParam(block, "#Chart#", "0") /><#local series><#if ci == "0">VOL()<#else>Volumes[${ci}]</#if></#local><@printSeriesAt block shift>${series}</@printSeriesAt></@compress_single_line></#macro>

<#-- Average Volume value at a bar offset: AverageCalculator SMA of the chart's Volume (AvgVolume.java),
     from the installed SqAvgVolume indicator.
     Output e.g.: SqAvgVolume(Close, 20).Values[0][0] -->
<#macro printAvgVolumeValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAvgVolume(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-- Vortex value for the value block through the installed SqVortex indicator: #Line# 0 -> VI+, 1 -> VI-. -->
<#macro printVortexLine block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqVortex(<@printInput block />, <@printParam block "#Period#" />).Values[<#if getParam(block, "#Line#", "0") == "1">1<#else>0</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#-- Vortex value at a fixed line (VIPlus/VIMinus) and shift, for the inline condition blocks,
     rounded to 6 decimals as the Java reads getRounded.
     @param line   literal "VIPlus" / "VIMinus".  @param shift  bar offset. -->
<#macro printVortexValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line>sqRound(<@printSeriesAt block shift>SqVortex(<@printInput block />, <@printParam block "#Period#" />).Values[<#if line == "VIMinus">1<#else>0</#if>]</@printSeriesAt>, 6)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     KELTNER CHANNEL macros
     Multi-output (Upper/Lower; default = Midline). SQX selects via #Line#; per
     KeltnerChannel.java (@Output Upper/Lower) + JForex blocks (KCUpperRising -> #Line# 0,
     KCLowerRising -> #Line# 1) the convention is #Line# 0 -> .Upper, 1 -> .Lower, 2 -> Midline.
     NT signature: KeltnerChannel(input, offsetMultiplier, period) -> offsetMultiplier=#Deviation#,
     period=#Period# (order reversed vs SQX, same as Bollinger). Default (no property) = Midline.
     Docs: https://ninjatrader.com/support/helpguides/nt8/keltner_channel.htm
     ============================================================ -->

<#-- KC value for the value block: map #Line# (0 -> .Upper, 1 -> .Lower, 2 -> Midline default). -->
<#macro printKCLine block shift><@compress_single_line><#local line = getParam(block, "#Line#", "0") /><#if line == "1"><@printSeriesAt block shift>KeltnerChannel(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).Lower</@printSeriesAt><#elseif line == "2"><@printSeriesAt block shift>KeltnerChannel(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />)</@printSeriesAt><#else><@printSeriesAt block shift>KeltnerChannel(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).Upper</@printSeriesAt></#if></@compress_single_line></#macro>

<#-- KC value at a fixed line (Upper/Lower) and shift, for inline variant blocks.
     @param line   literal "Upper" / "Lower".  @param shift  bar offset. -->
<#macro printKCValueAt block line shift><@compress_single_line><@printSeriesAt block shift>KeltnerChannel(<@printInput block />, <@printParam block "#Deviation#" />, <@printParam block "#Period#" />).${line}</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     PARABOLIC SAR macro - the installed SqParabolicSAR indicator, replaying
     ParabolicSAR.java's MetaTrader path with #Step# (initial factor and increment) and
     #Maximum# (ceiling).
     ============================================================ -->
<#macro printPSARValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line>SqParabolicSAR(<@printInput block />, <@printParam block "#Step#" />, <@printParam block "#Maximum#" />).FinalValue(0, <@printCIShift block shift />)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     MA GENERIC macro
     The generic Moving Average blocks (MARising/MAFalling/MABarCloses*) carry a #Type# selector
     (Simple=0, Exponential=1, Smoothed=2, Linear weighted=3):
       0 -> SMA(input, period)
       1 -> EMA(input, period)
       2 -> SqSMMA(input, period)   (AverageCalculator SMMA, the installed indicator)
       3 -> SqLWMA(input, period)   (AverageCalculator LWMA, the installed indicator)
     A variable/non-literal #Type# falls back to SMA (the builder emits a literal type).
     ============================================================ -->
<#-- Rounded to 6 decimals: every MA* comparison block reads Value.getRounded(Shift) in the Java
     (MABarClosesAbove/MARising/...; the price side stays RAW there, matching Chart.Close(Shift)),
     and the raw C# value flips ties the 6dp value does not. -->
<#macro printMAValueAt block shift><@compress_single_line>
<#local type = getParam(block, "#Type#", "0") />
<#if type == "2" || type == "3"><#global sqUsesIndicatorPackage = true></#if>sqRound(<#if type == "1"><@printSeriesAt block shift>EMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt><#elseif type == "2"><@printSeriesAt block shift>SqSMMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt><#elseif type == "3"><@printSeriesAt block shift>SqLWMA(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt><#else><@printSeriesAt block shift>SMA(<@printInput block />, <@printParam block "#Period#" />)</@printSeriesAt></#if>, 6)
</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     VWAP macro - the installed SqVWAP indicator.
     NinjaTrader has no native Managed VWAP. SqVWAP computes VWAP.java's rolling volume-weighted mean of
     (O+H+L+C)/4 over #VWAPPeriod# bars.
     Output e.g.: SqVWAP(Close, 10).Values[0][0]
     ============================================================ -->
<#macro printVWAPValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqVWAP(<@printInput block />, <@printParam block "#VWAPPeriod#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     DeMarker macro - the installed SqDeMarker indicator.
     NinjaTrader has no native Managed DeMarker. DeMarker.java uses the bar High/Low directly (not
     #ComputedFrom#): printInput only binds the indicator to the block's chart, and #Period# is the
     one parameter.
     ============================================================ -->
<#macro printDeMarkerValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqDeMarker(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     LinReg value macro - custom indicator.
     NinjaTrader's native LinReg returns the regression value at the CURRENT bar, whereas SQX
     (LinearRegression.java) evaluates the line at x=period-1 (the OLDEST bar of the window), which is
     what the installed SqLinReg indicator computes. #ComputedFrom# selects the price series via
     printInput (Close/Open/High/Low/Median/Typical/Weighted, all ISeries<double>).
     ============================================================ -->
<#macro printLinRegValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqLinReg(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     Reflex value macro - the installed SqReflex indicator.
     NinjaTrader has no native Ehlers Reflex. SqReflex computes Reflex.java's MetaTrader engine branch
     (recursive IIR filter) from the bar Close (not #ComputedFrom#): printInput only binds it to the
     block's chart, and #Period# is the one parameter.
     ============================================================ -->
<#macro printReflexValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqReflex(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     QQE value macros - the installed SqQQE indicator.
     NinjaTrader has no native QQE. SqQQE computes QQE.java (Wilder RSI -> EMA(sF) = Value1, Values[0];
     EMA(WildersPeriod) chain -> trailing line = Value2, Values[1]) from the bar Close (not
     #ComputedFrom#); params are #RSIPeriod#, #sF#, #wF#.
     ============================================================ -->
<#macro printQQEValue1At block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqQQE(<@printInput block />, <@printParam block "#RSIPeriod#" />, <@printParam block "#sF#" />, <@printParam block "#wF#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>
<#macro printQQEValue2At block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqQQE(<@printInput block />, <@printParam block "#RSIPeriod#" />, <@printParam block "#sF#" />, <@printParam block "#wF#" />).Values[1]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     Ichimoku value macro - the installed SqIchimoku indicator.
     NinjaTrader has no native Managed Ichimoku. SqIchimoku computes Ichimoku.java (forward-shifted
     cloud + median warm-up). line: 0=Tenkan, 1=Kijun, 2=SenkouA, 3=SenkouB; a higher line (Chikou,
     which the indicator does not produce) reads SenkouB. Params #TenkanPeriod#/#KijunPeriod#/#SenkouPeriod#.
     Output e.g.: SqIchimoku(Close, 9, 26, 52).Values[2][0]
     ============================================================ -->
<#macro printIchimokuValueAt block line shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqIchimoku(<@printInput block />, <@printParam block "#TenkanPeriod#" />, <@printParam block "#KijunPeriod#" />, <@printParam block "#SenkouPeriod#" />).Values[<#if line?number gt 3>3<#else>${line}</#if>]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     GannHiLo / KER value macros - the installed SqGannHiLo (stateful trend-switch activator) and
     SqKaufmanEfficiencyRatio indicators. NinjaTrader has neither natively. Both use the bar
     Close/High/Low directly (not #ComputedFrom#); param #Period#.
     ============================================================ -->
<#macro printGannHiLoValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqGannHiLo(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>
<#-- KER block value through the installed SqKaufmanEfficiencyRatio indicator, which replays KaufmanEfficiencyRatio.java's SumCalculator. -->
<#macro printKERValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqKaufmanEfficiencyRatio(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     Heiken Ashi value macro - the installed SqHeikenAshi indicator.
     NinjaTrader has no native Heiken Ashi. SqHeikenAshi computes the HA candle from the bar OHLC
     (HAOpen recursive). which: 0=HAOpen, 1=HAClose, 2=HAHigh, 3=HALow. No #ComputedFrom# (uses the
     bar OHLC directly).
     Output e.g.: SqHeikenAshi(Close).Values[1][0]
     ============================================================ -->
<#macro printHeikenAshiValueAt block which shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqHeikenAshi(<@printInput block />).Values[${which}]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     Schaff Trend Cycle value macro - the installed SqSTC indicator.
     NinjaTrader has no native STC. SqSTC computes SchaffTrendCycle.java (MACD -> double stochastic)
     from the bar Close (no #ComputedFrom#); params #StochPeriod#/#FastPeriod#/#SlowPeriod#.
     ============================================================ -->
<#macro printSTCValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqSTC(<@printInput block />, <@printParam block "#StochPeriod#" />, <@printParam block "#FastPeriod#" />, <@printParam block "#SlowPeriod#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     Ulcer Index value macro - custom indicator.
     NinjaTrader has no native Ulcer Index; the installed SqUlcerIndex indicator computes the RMS of percent
     drawdowns from the highest (#Mode#=1) / lowest (#Mode#=2) Close over #Period#. barsAgo via printCIShift
     (argument, not a [] index). Uses Close directly (no #ComputedFrom#).
     ============================================================ -->
<#macro printUlcerIndexValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqUlcerIndex(<@printInput block />, <@printParam block "#Mode#" />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     RSI value macro - the installed SqRSI indicator, replaying RSI.java /
     RSICalculator. Used by RSI.tpl and the RSI variants (which round it to 6 decimals, as the Java
     reads getRounded).
     @param block  the RSI block (carries #Period#/#ComputedFrom#/#Shift#).
     @param shift  extra bar offset ("0"/"1"/"2"), combined with the block's #Shift#.
     ============================================================ -->
<#macro printRSIValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqRSI(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     AwesomeOscillator macro - the installed SqAwesomeOscillator indicator.
     AwesomeOscillator.java = SMA(Median, 5) - SMA(Median, 34), Median = (High+Low)/2, fixed periods
     (no #Period#/#ComputedFrom#). The helper replays its AverageCalculator warm-up: bar 0 is never
     fed.

     The Median series follows #Chart#: the AWO blocks are on CHART_ROUTED_BLOCKS, so printSeries
     emits Median on the primary chart and Medians[ci] on a subchart, and the helper runs on the
     same chart index.
     @param block  the AWO block, carrying an optional #Chart# and #Shift#.
     @param shift  extra bar offset, combined with the block's #Shift#.
     Output e.g.: SqAwesomeOscillator(Close).Values[0][0]
     ============================================================ -->
<#macro printAOValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqAwesomeOscillator(<@printInput block />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     OSMA macro - the installed SqMACD indicator.
     SQX OSMA.java = macd - SMA(macd, SignalPeriod), where macd = EMA(in, FastEMA) - EMA(in, SlowEMA)
     and the signal SMA uses AverageCalculator.SMA. That is exactly SqMACD main - SqMACD signal, so OSMA
     reads the same indicator as MACD rather than the native MACD(...).Default, whose seeding differs.
     Both terms get the same shift, so the value holds at #Shift# != 0:
       (SqMACD(in, fast, slow, signal).Values[0][s] - SqMACD(in, fast, slow, signal).Values[1][s])
     @param block  the OSMA block (carries #FastEMA#/#SlowEMA#/#SignalPeriod#/#ComputedFrom#/#Shift#).
     @param shift  extra bar offset ("0"/"1"/"2"), combined with the block's #Shift#.
     ============================================================ -->
<#macro printOSMAValueAt block shift><@compress_single_line>(<@printOSMACall block "0" shift /> - <@printOSMACall block "1" shift />)</@compress_single_line></#macro>

<#-- One SqMACD line for OSMA (OSMA uses #FastEMA#/#SlowEMA#/#SignalPeriod#, not #Fast#/#Slow#/#Smooth#).
     @param which "0" = main line (macd), "1" = signal line (SMA of macd).
     Output e.g.: SqMACD(Close, 12, 26, 9).Values[0][0] -->
<#macro printOSMACall block which shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqMACD(<@printInput block />, <@printParam block "#FastEMA#" />, <@printParam block "#SlowEMA#" />, <@printParam block "#SignalPeriod#" />).Values[${which}]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     LaguerreRSI macro - the installed SqLaguerreRSI indicator.
     NinjaTrader has no native LaguerreRSI. LaguerreRSI.java uses a fixed Close source and a single
     #Gamma# param (double): printInput only binds the indicator to the block's chart.
     ============================================================ -->
<#macro printLaguerreRSIValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqLaguerreRSI(<@printInput block />, <@printParam block "#Gamma#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     SuperTrend macro - the installed SqSuperTrend indicator.
     NinjaTrader has no native Managed SuperTrend. SqSuperTrend computes SuperTrend.java's MetaTrader
     branch with #ATRPeriod#/#ATRMult#, its ATR being the simple-mean MetaTrader ATR rounded to 6
     decimals; #Mode# (Basic=1) has no effect and is not passed.
     Output e.g.: SqSuperTrend(Close, 24, 3).Values[0][0]
     ============================================================ -->
<#macro printSuperTrendValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqSuperTrend(<@printInput block />, <@printParam block "#ATRPeriod#" />, <@printParam block "#ATRMult#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     FRACTAL / PIVOTS / SR PERCENT RANK value macros.
     All three read installed indicators (SqFractal, SqPivots, SqSRPercentRank).
     ============================================================ -->
<#-- Fractal pivot value: SqFractal(input, fractal).Values[#Line#]. #Line# 0 = Up, 1 = Down. -->
<#macro printFractalValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqFractal(<@printInput block />, <@printParam block "#Fractal#" />).Values[<@printParam block "#Line#" "0" />]</@printSeriesAt></@compress_single_line></#macro>

<#-- Pivot level: SqPivots(input, startHour, startMinute, SqSourceEndOfBar).Values[#Line#], 0..6 = PP/R1/R2/R3/S1/S2/S3. -->
<#macro printPivotsValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqPivots(<@printInput block />, <@printParam block "#StartHour#" />, <@printParam block "#StartMinute#" />, SqSourceEndOfBar).Values[<@printParam block "#Line#" "0" />]</@printSeriesAt></@compress_single_line></#macro>

<#-- SR percent rank: SqSRPercentRank(input, mode, length, atrPeriod).Values[0]. -->
<#macro printSRPercRankValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqSRPercentRank(<@printInput block />, <@printParam block "#Mode#" />, <@printParam block "#Length#" />, <@printParam block "#ATRPeriod#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     MTATR / MTKeltnerChannel value macros - the installed SqMTATR and SqMTKeltnerChannel indicators.
     MTATR = MetaTrader simple-mean ATR (not Wilder); MTKeltner = SMA(Close) +/- SMA(High-Low)*Dev.
     Output e.g.: SqMTATR(Close, 14).Values[0][0]
     ============================================================ -->
<#macro printMTATRValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqMTATR(<@printInput block />, <@printParam block "#Period#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-- MT Keltner Channel band: SqMTKeltnerChannel(input, period, deviation).Values[#Line#], 0 = Upper, 1 = Lower.
     Output e.g.: SqMTKeltnerChannel(Close, 20, 1.5).Values[0][0] -->
<#macro printMTKeltnerValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqMTKeltnerChannel(<@printInput block />, <@printParam block "#Period#" />, <@printParam block "#Deviation#" />).Values[<@printParam block "#Line#" "0" />]</@printSeriesAt></@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- Multi-TF OHLC value (BAR-DERIVED, calendar period).
     Emits SqCalendarOHLC(series, tf).PeriodValue(ohlc, periodShift) - the installed package
     indicator - instead of a native Opens/Highs/Lows/Closes[idx][barsAgo] secondary-series read.
     NinjaTrader's native AddDataSeries(Day/Week/Month) buckets bars by the instrument SESSION (FX
     close ~22:00 UTC), which disagrees with the SQX calendar day/week/month
     (SQTime.isSameDay/isSameWeek/isSameMonth, midnight). SqCalendarOHLC groups the bars of the
     block's chart by the calendar period, so an exported strategy trades on the SAME periods as the
     SQX backtest, and these blocks need no secondary AddDataSeries (see Functions.inc
     printMultiTfDataSeries).

       tf          : 1 = Day, 2 = Week, 3 = Month (caller passes a literal).
       ohlc        : 0 = Open, 1 = High, 2 = Low, 3 = Close (caller passes a literal).
       basePeriodShift : the per-component base periods-back - 0 for EVERY component (Open AND
                     High/Low/Close). SQX's D/W/M series are per-DATA-period records with index 0 =
                     the RUNNING period updated intrabar (ChartData.java:1933 `HighD.set(0, tickBid)`),
                     so Chart.HighD(Shift) is exactly Shift data-periods back with no completed-period
                     offset - an extra +1 for H/L/C would pick the period before the one SQX reads.
                     The block's own #Shift# and the caller's comparison offset are ADDED, exactly as
                     SQX evaluates Chart.CloseD(Shift + relativeShift) etc. (CloseD.java:98).
       shift       : the CALLER's extra offset, from a multi-bar comparison such as IsRising, which
                     renders its operand at k and k+1 and compares the two. It has to be summed in as
                     well - `relativeShift` in the Java is exactly this. Without it every k renders
                     the SAME expression and `IsRising(CloseD)` becomes `x > x`, which is never true
                     (guarded by testCalendarPeriodBlockFollowsTheComparisonOffset). -->
<#macro printMultiTfOhlcValueAt block tf ohlc basePeriodShift shift><@compress_single_line>
<#-- Both offsets are plain integers at every call site; the guard keeps a non-numeric caller shift
     rendering as a readable sum instead of failing generation. -->
<#local extra><#if basePeriodShift?matches(r"-?[0-9]+") && shift?matches(r"-?[0-9]+")>${(basePeriodShift?number + shift?number)?c}<#else>${basePeriodShift}+${shift}</#if></#local>
<#global sqUsesIndicatorPackage = true>SqCalendarOHLC(<@printSeries block "Close" />, ${tf}).PeriodValue(${ohlc}, <@printCIShift block extra />)</@compress_single_line></#macro>

<#-------------------------------------------------------------->
<#-- ============================================================
     HighestInRange / LowestInRange / Fibo value macros - the installed SqHighestInRange,
     SqLowestInRange and SqFibo indicators.
     ============================================================ -->
<#-- Highest High of the last completed daily window; SqSourceEndOfBar tells the indicator how the
     source data labels its bars.
     Output e.g.: SqHighestInRange(Close, 930, 1600, SqSourceEndOfBar).Values[0][0] -->
<#macro printHighestInRangeValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqHighestInRange(<@printInput block />, <@printParam block "#TimeFrom#" />, <@printParam block "#TimeTo#" />, SqSourceEndOfBar).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#macro printLowestInRangeValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqLowestInRange(<@printInput block />, <@printParam block "#TimeFrom#" />, <@printParam block "#TimeTo#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>

<#-- Fibo: the installed SqFibo indicator. The previous completed calendar day/week/month is taken
     from the chart's own bars; no native secondary series. The shift reads the Fibo series bars
     back, as Fibo.java's Value does.
     Output e.g.: SqFibo(Close, 1, 61.8).Values[0][0] -->
<#macro printFiboValueAt block shift><#global sqUsesIndicatorPackage = true><@compress_single_line><@printSeriesAt block shift>SqFibo(<@printInput block />, <@printParam block "#FiboRange#" />, <@printParam block "#FiboLevel#" />).Values[0]</@printSeriesAt></@compress_single_line></#macro>
