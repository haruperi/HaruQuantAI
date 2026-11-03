<#-- Linear Regression value from the installed SqLinReg indicator. SQX evaluates the regression at
     x=period-1 (oldest bar of the window), so native NT LinReg is NOT used.

     The caller's shift MUST be passed through: the Indicator*MA lambda walks a window with
     f(shift+i), so a child that ignores the offset returns a constant, the MA of that constant
     equals it, and the crosses-MA test can never fire. -->
<@compress_single_line><@printLinRegValueAt block shift /></@compress_single_line>
