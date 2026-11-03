<#-- Bar closes below the upper Keltner band (Close < Upper). Close and band via printShift
     (respects #Shift#, parity with other platforms). -->
(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printKCValueAt block "Upper" shift />, 6))