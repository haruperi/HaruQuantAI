<#-- Data logging indicator: a debug-only OHLCV CSV logger whose value output equals Close.
     NT maps the value to Close[shift]; the CSV side-effect is not replicated.
     Mirrors SQ.Blocks.Indicators.Other.DataLoggingIndy.java.      IGNORES #Tinput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
     IGNORES #Oinput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
     IGNORES #Hinput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
     IGNORES #Linput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
     IGNORES #Cinput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
     IGNORES #Vinput#: a logging indicator: the exported expression is the value, the log itself is GUI-side.
-->
<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt>
