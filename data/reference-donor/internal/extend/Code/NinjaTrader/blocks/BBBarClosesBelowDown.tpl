<#-- Bar closes below the lower band (Close < Lower). Close and band via printShift
     (respects #Shift#, parity with other platforms). -->
(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> < sqRound(<@printBollingerValueAt block "Lower" shift />, 6))