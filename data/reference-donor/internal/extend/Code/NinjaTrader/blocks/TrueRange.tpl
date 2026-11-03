<#-- True Range: TrueHigh - TrueLow, where TrueHigh = max(Close[shift+1], High[shift]) and
     TrueLow = min(Close[shift+1], Low[shift]). Parity with TrueRange.java, an indicator block whose series
     is read at the caller's offset too (a multi-bar comparison steps it back bar by bar). -->
<#assign trShift1><#if shift?matches(r"-?[0-9]+")>${(shift?number + 1)?c}<#else>${shift}+1</#if></#assign>
<@compress_single_line>(Math.Max(<@printSeriesAt block trShift1><@printSeries block "Close" /></@printSeriesAt>, <@printSeriesAt block shift><@printSeries block "High" /></@printSeriesAt>) - Math.Min(<@printSeriesAt block trShift1><@printSeries block "Close" /></@printSeriesAt>, <@printSeriesAt block shift><@printSeries block "Low" /></@printSeriesAt>))</@compress_single_line>
