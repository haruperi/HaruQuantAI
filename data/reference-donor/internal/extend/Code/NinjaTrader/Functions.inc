<#--
  ============================================================================
  Functions.inc - NinjaTrader-specific FreeMarker helper macros.
  ============================================================================
  Parameter printers (printParam/printInput/
  printShift) live in Parameters.inc; rule traversal and per-block rendering
  (printRulesForEvent/printBlock/printBlockChild) live in Blocks.inc.
  Cross-platform helpers (compress_single_line, getOptions, getRulesCountForEvent,
  ...) come from /global/globalFunctions.inc.
-->

<#-------------------------------------------------------------->
<#-- The C# keywords: none of them can name a class or a field. -->
<#assign csKeywords = ["abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char", "checked", "class",
  "const", "continue", "decimal", "default", "delegate", "do", "double", "else", "enum", "event", "explicit", "extern",
  "false", "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit", "in", "int", "interface",
  "internal", "is", "lock", "long", "namespace", "new", "null", "object", "operator", "out", "override", "params",
  "private", "protected", "public", "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof", "stackalloc",
  "static", "string", "struct", "switch", "this", "throw", "true", "try", "typeof", "uint", "ulong", "unchecked",
  "unsafe", "ushort", "using", "virtual", "void", "volatile", "while"] />

<#-- NinjaTrader and .NET names the generated code uses without a qualifier; a class or variable of such a name would
     hide them. The trading options' fields are not listed: strategies declare them as variables of those names. -->
<#assign csReservedNames = ["Account", "AccountItem", "AddDataSeries", "ArgumentOutOfRangeException", "Array",
  "Bars", "BarsArray", "BarsInProgress", "BarsPeriod", "BarsPeriodType", "BarsPeriods", "BarsRequiredToTrade",
  "BarsSinceEntryExecution", "BarsSinceExitExecution", "Bollinger", "Calculate", "CalculationMode", "CancelOrder",
  "Cbi", "Close", "Closes", "Core", "CultureInfo", "CurrentBar", "CurrentBars", "Data", "Date", "DateTime",
  "DateTimeKind", "DayOfWeek", "Description", "Dictionary", "Display", "DrawingTools", "EMA", "EnterLong",
  "EnterLongLimit", "EnterLongStopMarket", "EnterShort", "EnterShortLimit", "EnterShortStopMarket",
  "EntriesPerDirection", "Entry", "EntryHandling", "Environment", "ErrorCode", "Exception", "Execution", "Exit",
  "ExitLong", "ExitLongLimit", "ExitLongStopMarket", "ExitShort", "ExitShortLimit", "ExitShortStopMarket", "File",
  "Func", "GeneralOptions", "Generic", "GetCurrentAsk", "GetCurrentBid", "Globals", "GroupName", "HashSet", "High",
  "Highs", "ICollection", "ISeries", "Indicator", "Indicators", "Input", "Instrument", "InstrumentType",
  "IsExitOnSessionCloseStrategy", "IsFillLimitOnTouch", "KeltnerChannel", "KeyValuePair", "List", "Low", "Lows",
  "MAX", "MIN", "MarketPosition", "Math", "MaximumBarsLookBack", "Media", "Median", "Name", "NinjaScript",
  "NinjaScriptBase", "NinjaScriptProperty", "NinjaTrader", "OnBarUpdate", "OnExecutionUpdate", "OnOrderUpdate",
  "OnStateChange", "Open", "Opens", "Order", "OrderAction", "OrderState", "OrderType", "Orders", "ParabolicSAR",
  "Path", "PerformanceUnit", "Position", "Print", "Range", "RangeLevel", "SMA", "SQ", "SendMail", "Series",
  "SetProfitTarget", "SetStopLoss", "State", "StdDev", "Strategies", "Strategy", "System", "SystemPerformance",
  "TEMA", "TickSize", "Time", "TimeSeries", "TimeSpan", "TimeZoneInfo", "Times", "Trade", "TradesPerformance",
  "Typical", "VOL", "Volume", "Volumes", "Weighted", "WilliamsR"] />

<#--
  Sanitize arbitrary text into a valid C# identifier that names nothing the generated code already uses.
  @param text  the source string (e.g. a strategy name that may contain spaces).
  Returns: the text with every char outside [A-Za-z0-9_] replaced by '_'; a leading '_' when it starts with a digit
  or is empty; a trailing '_' when it is a C# keyword, a reserved name or starts with sq, Sq or mm and a capital.
-->
<#function csIdentifierOf text>
  <#local s = "${text}"?replace("[^a-zA-Z0-9_]", "_", "r") />
  <#if s == "" || s?matches("[0-9].*")><#local s = "_" + s /></#if>
  <#if csKeywords?seq_contains(s) || csReservedNames?seq_contains(s) || s?matches("(sq|Sq|mm)[A-Z].*")>
    <#local s = s + "_" />
  </#if>
  <#return s />
</#function>

<#-- Emit csIdentifierOf(text). Used for the generated class name. -->
<#macro csIdentifier text><@compress_single_line>${csIdentifierOf(text)}</@compress_single_line></#macro>

<#--
  The C# names of the strategy's variables, by variable id: csIdentifierOf each name, with "_2", "_3", ... appended
  where it equals the class name or an earlier variable's name. Computed once per export.
  Returns: a hash of variable id -> C# name.
-->
<#function csVariableNames>
  <#if !(sqCsVariableNames??)>
    <#local used = [csIdentifierOf(sqStrategyName(getOptions("StrategyName")))] />
    <#local names = {} />
    <#list doc.StrategyFile.Strategy.Variables.* as var>
      <#local base = csIdentifierOf(var.name) />
      <#local n = base />
      <#local i = 2 />
      <#list 1..1000 as attempt>
        <#if !used?seq_contains(n)><#break></#if>
        <#local n = base + "_" + i />
        <#local i = i + 1 />
      </#list>
      <#local used = used + [n] />
      <#local names = names + {"${var.id}": n} />
    </#list>
    <#global sqCsVariableNames = names />
  </#if>
  <#return sqCsVariableNames />
</#function>

<#-- The C# name of a strategy variable. @param var  a node of doc.StrategyFile.Strategy.Variables. -->
<#function csVariableName var>
  <#return csVariableNames()["${var.id}"] />
</#function>

<#-------------------------------------------------------------->
<#-- ============================================================
     MULTI-TF OHLC detection + data-series setup.
     A block that needs native daily/weekly/monthly secondary data series gets them added in
     State.Configure only when the strategy actually uses it, so plain strategies are unchanged.
     When any is used ALL THREE are added so the series indices are fixed: Day = 1, Week = 2,
     Month = 3 (primary series is index 0).
     ============================================================ -->
<#-- The trigger list is EMPTY: the multi-TF OHLC blocks (Open/High/Low/Close x D/W/M) and Fibo are
     BAR-DERIVED (the installed SqCalendarOHLC and SqFibo indicators group the chart's own bars by
     the calendar period), so no block needs a native secondary
     series and printMultiTfDataSeries emits nothing. A native multi-TF block enables the plumbing
     just by adding its key here. -->
<#assign multiTfOhlcKeys = [] />

<#-- Recursively check whether any element under `node` is a multi-TF OHLC block. With an empty
     multiTfOhlcKeys this always returns false (no key ever matches). -->
<#function nodeUsesMultiTf node>
  <#list node?children as c>
    <#if c?node_type == "element">
      <#if c?node_name == "Item" && c.@key[0]?? && multiTfOhlcKeys?seq_contains("${c.@key}")>
        <#return true />
      </#if>
      <#if nodeUsesMultiTf(c)>
        <#return true />
      </#if>
    </#if>
  </#list>
  <#return false />
</#function>

<#-- True when the strategy uses any block that needs a native secondary series (currently none). -->
<#function usesMultiTfOhlc>
  <#return nodeUsesMultiTf(doc) />
</#function>

<#-- Emitted in State.Configure: would add Day/Week/Month series (idx 1/2/3) only when used. Currently
     no block triggers it, so this emits nothing. -->
<#macro printMultiTfDataSeries><#if usesMultiTfOhlc()>
				AddDataSeries(BarsPeriodType.Day, 1);
				AddDataSeries(BarsPeriodType.Week, 1);
				AddDataSeries(BarsPeriodType.Month, 1);
</#if></#macro>

<#--
  ============================================================
   SECONDARY CHART SERIES
  ============================================================
  A strategy can be built over several charts. `<Datas>` lists them:

      <data><id>0</id><symbol>NULL</symbol><chart>Main chart</chart><timeFrame>0</timeFrame></data>
      <data><id>1</id><symbol>NULL</symbol><chart>Subchart 1</chart><timeFrame>60</timeFrame></data>

  `id` 0 is the primary series; every further id is an extra NinjaScript data series, added in
  State.Configure in id order so that AddDataSeries call N lands on BarsArray index N. Blocks pick
  their chart through a `#Chart#` parameter (controlType="dataVar") holding that id - see
  getChartIndex / printComputedFrom in Parameters.inc.

  `timeFrame` is expressed in MINUTES (TimeframeManager: 60 = H1, 1440 = D1, 10080 = weekly,
  43200 = monthly), which is what MetaTrader5 emits verbatim as Subchart<N>Timeframe.
-->

<#-- Number of chart series the strategy declares (1 = primary only). -->
<#function dataSeriesCount>
  <#local n = 0 />
  <#list doc.StrategyFile.Strategy.Datas.* as data>
    <#local n = n + 1 />
  </#list>
  <#return n />
</#function>

<#-- Map an SQX timeframe in minutes to a NinjaScript BarsPeriodType + value pair,
     e.g. 60 -> "BarsPeriodType.Minute, 60", 1440 -> "BarsPeriodType.Day, 1". -->
<#function barsPeriodOf minutes>
  <#local m = minutes?number />
  <#if m == 43200><#return "BarsPeriodType.Month, 1" />
  <#elseif m == 10080><#return "BarsPeriodType.Week, 1" />
  <#elseif m == 1440><#return "BarsPeriodType.Day, 1" />
  <#elseif m gt 0><#return "BarsPeriodType.Minute, " + m?c />
  <#else><#return "" />
  </#if>
</#function>

<#-- Whether a chart reads the main chart's symbol. SQX writes it as NULL, "Main chart symbol", Current or
     "Same as main chart" - or, after the project's chart settings were applied, as the main chart's own symbol,
     which the export passes as the mainSymbol attribute of Datas. -->
<#function isMainSymbol data>
  <#local s = (data.symbol[0]!"")?string?trim />
  <#local main = (doc.StrategyFile.Strategy.Datas.@mainSymbol[0]!"")?string?trim />
  <#return s == "" || s == "NULL" || s == "Main chart symbol" || s == "Current" || s == "Same as main chart" || (main != "" && s == main) />
</#function>

<#-- The input holding the symbol of a subchart on another symbol, e.g. "Subchart1Symbol". -->
<#function subchartSymbolInput data><#return "Subchart" + data.id?string?trim + "Symbol" /></#function>

<#-- The input holding a subchart's timeframe in minutes, e.g. "Subchart1Timeframe". -->
<#function subchartTimeframeInput data><#return "Subchart" + data.id?string?trim + "Timeframe" /></#function>

<#-- Emitted in State.Configure: one AddDataSeries per secondary chart, in id order, at the period of its
     Subchart<N>Timeframe input. A subchart on another symbol reads the instrument its Subchart<N>Symbol input names. -->
<#macro printSecondaryDataSeries><#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0">
    <#local bp = barsPeriodOf(data.timeFrame) />
    <#if bp != "">
    <#local tf = subchartTimeframeInput(data) />
    <#if isMainSymbol(data)>
				AddDataSeries(SqPeriodType(${tf}), SqPeriodValue(${tf}));   // ${data.chart} (SQX timeFrame ${data.timeFrame} min) -> BarsArray[${data.id}]
    <#else>
				AddDataSeries(${subchartSymbolInput(data)}, SqPeriodType(${tf}), SqPeriodValue(${tf}));   // ${data.chart} on ${data.symbol} (SQX timeFrame ${data.timeFrame} min) -> BarsArray[${data.id}]
    </#if>
    </#if>
</#if></#list></#macro>

<#-- A subchart whose Subchart<N>Timeframe is one day (1440) is read on StrategyQuant's calendar day
     (SqCalendarDayOHLC, SqHigherTimeframeMA), built from intraday bars: on the main symbol the primary bars, on
     another symbol a companion series of that instrument at the primary period. The companion is added only when
     the input asks for a day, after every subchart, so its BarsArray index is known only at run time and lives in
     the field sqDayBars<N>. Any other timeframe reads NinjaTrader's own series of that period. -->
<#function dayBarsSeries ci>
  <#list doc.StrategyFile.Strategy.Datas.* as data>
    <#if data.id?string?trim == ci && !isMainSymbol(data)><#return "Closes[sqDayBars" + ci + "]" /></#if>
  </#list>
  <#return "Close" />
</#function>

<#-- The run-time test that a subchart is read on calendar days, e.g. "Subchart1Timeframe == 1440". -->
<#function isDayRead ci><#return "Subchart" + ci + "Timeframe == 1440" /></#function>

<#-- Emitted in State.Configure after the subcharts: the companion series of each subchart on another symbol whose
     timeframe input is one day. -->
<#macro printDayCompanionSeries><#local first = true /><#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && !isMainSymbol(data) && barsPeriodOf(data.timeFrame) != ""><#if first>
				int sqNextSeries = ${dataSeriesCount()?c};
<#local first = false /></#if>
				if (${isDayRead(data.id?string?trim)})
				{
					sqDayBars${data.id?string?trim} = sqNextSeries++;
					AddDataSeries(${subchartSymbolInput(data)}, BarsPeriod.BarsPeriodType, BarsPeriod.Value);   // calendar days of ${data.chart} on ${data.symbol}
				}
</#if></#list></#macro>

<#-- Emitted in State.Configure before the data series: a Subchart<N>Symbol NinjaTrader does not know stops the strategy
     instead of letting AddDataSeries fail or read nothing. -->
<#macro printSubchartSymbolCheck><#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && !isMainSymbol(data) && barsPeriodOf(data.timeFrame) != "">
				if (string.IsNullOrEmpty(${subchartSymbolInput(data)}) || NinjaTrader.Cbi.Instrument.GetInstrument(${subchartSymbolInput(data)}, false) == null)
					throw new Exception("${subchartSymbolInput(data)} '" + ${subchartSymbolInput(data)} + "' is not a NinjaTrader instrument. Set the ${subchartSymbolInput(data)} input to the instrument ${data.chart?j_string} reads, as NinjaTrader names it (StrategyQuant symbol: ${data.symbol?j_string}).");
</#if></#list></#macro>

<#-- Emitted in State.SetDefaults: each Subchart<N>Symbol input starts as the symbol the subchart has in StrategyQuant,
     each Subchart<N>Timeframe as its timeframe in minutes. -->
<#macro printSubchartSymbolDefaults><#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && barsPeriodOf(data.timeFrame) != "">
<#if !isMainSymbol(data)>
				${subchartSymbolInput(data)} = "${data.symbol?j_string}";
</#if>
				${subchartTimeframeInput(data)} = ${data.timeFrame?string?trim?number?c};
</#if></#list></#macro>

<#-- The Subchart<N>Symbol and Subchart<N>Timeframe inputs, and the period helpers they need, in the strategy
     fields region. -->
<#macro printSubchartSymbolProperties><#local any = false /><#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && barsPeriodOf(data.timeFrame) != ""><#local any = true />
<#if !isMainSymbol(data)>
		[NinjaScriptProperty]
		[Display(Name="${subchartSymbolInput(data)}", Description="The NinjaTrader instrument ${data.chart?j_string} reads", GroupName="Subcharts", Order=${(data.id?string?trim?number * 2 - 1)?c})]
		public string ${subchartSymbolInput(data)} { get; set; }

</#if>
		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name="${subchartTimeframeInput(data)}", Description="The timeframe of ${data.chart?j_string} in minutes (60 = H1, 240 = H4, 1440 = D1)", GroupName="Subcharts", Order=${(data.id?string?trim?number * 2)?c})]
		public int ${subchartTimeframeInput(data)} { get; set; }

</#if></#list><#if any>
<#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && !isMainSymbol(data) && barsPeriodOf(data.timeFrame) != "">
		private int sqDayBars${data.id?string?trim} = -1;   // BarsArray index of ${data.chart}'s calendar-day companion, -1 when it reads another timeframe
</#if></#list>
		// A timeframe in minutes as NinjaTrader's bar period: whole months, weeks and days, otherwise minutes.
		private static BarsPeriodType SqPeriodType(int minutes)
		{
			if (minutes % 43200 == 0) return BarsPeriodType.Month;
			if (minutes % 10080 == 0) return BarsPeriodType.Week;
			if (minutes % 1440 == 0) return BarsPeriodType.Day;
			return BarsPeriodType.Minute;
		}

		// The bar period value that goes with SqPeriodType.
		private static int SqPeriodValue(int minutes)
		{
			if (minutes % 43200 == 0) return minutes / 43200;
			if (minutes % 10080 == 0) return minutes / 10080;
			if (minutes % 1440 == 0) return minutes / 1440;
			return minutes;
		}

</#if></#macro>

<#-- True when the strategy adds any data series beyond the primary one. -->
<#function usesSecondarySeries>
  <#if usesMultiTfOhlc()><#return true /></#if>
  <#list doc.StrategyFile.Strategy.Datas.* as data>
    <#if data.id?string != "0" && barsPeriodOf(data.timeFrame) != ""><#return true /></#if>
  </#list>
  <#return false />
</#function>

<#-- The bars since the position's last entry (or exit) on the primary series. With a secondary series
     NinjaTrader throws on the parameterless overloads - they must name the series - and terminates the
     strategy on its first position; a single-series strategy keeps the plain call. -->
<#function barsSinceEntryCall>
  <#return usesSecondarySeries()?then("BarsSinceEntryExecution(0, \"\", 0)", "BarsSinceEntryExecution()") />
</#function>
<#function barsSinceExitCall>
  <#return usesSecondarySeries()?then("BarsSinceExitExecution(0, \"\", 0)", "BarsSinceExitExecution()") />
</#function>

<#--
  The strategy name without a file extension, for the class name and the NinjaScript Name property.

  StrategyXMLModifier.addOptions stamps the StrategyName option with the file name AS GIVEN, while
  SourceCode.generate passes the stripped name to getSource - and the templates read the option, not
  the argument. On the CLI a name like "Strategy 1.1.179.sqx" therefore reaches the template with its
  extension, which would end up in the class name. The GUI path stamps a databank name that has no
  extension.

  Stripped HERE, in the NinjaTrader templates only, rather than in addOptions - that call is shared by
  every generator and changing it would rename the exported class on all of them at once.

  Only a KNOWN extension is stripped. A blanket "cut at the last dot" would turn the perfectly legal
  name "Strategy 1.1.179" into "Strategy 1.1", because these names are full of dots.
-->
<#function sqStrategyName name>
  <#list [".sqx", ".str", ".xml"] as ext>
    <#if name?lower_case?ends_with(ext)>
      <#return name?substring(0, name?length - ext?length)>
    </#if>
  </#list>
  <#return name>
</#function>

<#-- Emitted at the top of OnBarUpdate: history guard for EVERY series.
     The scalar `CurrentBar` only covers the primary series, so on a multi-chart strategy the
     secondary series is still short and any indicator over it reads out of range. -->
<#-- A Day subchart is counted in StrategyQuant's completed calendar days (SqCalendarDayOHLC counts the day
     in progress too), which is what StrategyQuant waits on before it trades; its own series only has to
     exist. An intraday subchart is counted in StrategyQuant's bars of its period (SqTimeframeBarCount counts its completed
     bars, the one completing on this bar included): StrategyQuant trades once the chart holds MORE of them than the
     reserved ones, and NinjaTrader's own series of that period, cut by the trading hours, can count more.
     An intraday subchart on another symbol is counted on its own series: the primary bars say nothing about
     how many bars the other instrument holds. -->
<#macro printBarsGuard><#if dataSeriesCount() gt 1>
			if (<#list doc.StrategyFile.Strategy.Datas.* as data><#if data.id?string != "0" && barsPeriodOf(data.timeFrame) != ""><#local ci = data.id?string?trim /><#local tf = subchartTimeframeInput(data) /><#global sqUsesIndicatorPackage = true>(${tf} == 1440 ? (CurrentBars[${ci}] < 0 || <#if !isMainSymbol(data)>CurrentBars[sqDayBars${ci}] < 0 || </#if>SqCalendarDayOHLC(${dayBarsSeries(ci)}, 0).Values[4][0] - 2 < BarsRequiredToTrade) : <#if isMainSymbol(data)>${tf} < 1440 ? (CurrentBars[${ci}] < 0 || SqTimeframeBarCount(Close, ${tf}).Values[0][0] - 1 < BarsRequiredToTrade) : </#if>CurrentBars[${ci}] < BarsRequiredToTrade)<#else>CurrentBars[${data.id}] < BarsRequiredToTrade</#if><#if data_has_next> || </#if></#list>)
			return;
<#else>
			if (CurrentBar < BarsRequiredToTrade)
			return;
</#if></#macro>
