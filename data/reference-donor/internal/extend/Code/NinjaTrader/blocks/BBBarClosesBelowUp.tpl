<#-- Bar closes below the upper band (Close < Upper). Close and band via printShift
     (respects #Shift#, parity with other platforms). -->
(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printBollingerValueAt block "Upper" shift />, 6))