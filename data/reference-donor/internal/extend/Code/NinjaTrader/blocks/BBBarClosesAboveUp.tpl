<#-- Bar closes above the upper band (Close > Upper). Close and band via printShift
     (respects #Shift#, parity with other platforms; Java: Close(Shift) > Upper.getRounded(Shift)). -->
(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> > sqRound(<@printBollingerValueAt block "Upper" shift />, 6))