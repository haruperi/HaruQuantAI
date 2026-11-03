<#-- Bar closes below the Moving Average (Close < MA). Close via printSeries+printShift (honours #Chart#), MA uses
     ComputedFrom input and #Type#. Parity with other platforms (Close(Shift) < MA(Shift)). -->
(<@printSeriesAt block shift><@printSeries block "Close" /></@printSeriesAt> < <@printMAValueAt block shift />)