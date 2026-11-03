<#-- Is uptrend (Method 0 = price above SMA200, the only defined method). Mirrors
     SQ.Blocks.Indicators.Trend.IsUptrend.java: price = Chart.Close(1) and sma200 =
     SMA(...).getRounded(1) - BOTH evaluated on the PREVIOUS bar (shift 1), so NinjaScript must use
     [1] on both operands (SQX bar k -> NT [k]). Using [0] would read one bar ahead.      IGNORES #Method#: values="Price above SMA200=0" - one declared value.
-->
(<@printSeriesAtOffset block "1"><@printSeries block "Close" /></@printSeriesAtOffset> > sqRound(<@printSeriesAtOffset block "1">SMA(<@printSeries block "Close" />, 200)</@printSeriesAtOffset>, 6))
