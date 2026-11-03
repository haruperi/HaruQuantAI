<#-- QQE value from the installed SqQQE indicator (Value1 = smoothed RSI line, the primary output).
     NinjaTrader has no native QQE. -->
<#-- The caller's `shift` MUST be passed on: comparisons such as IsRising or CrossesAbove
     render the same operand at shift and shift+1, so a fixed shift makes them compare a value
     with itself. -->
<@compress_single_line><@printQQEValue1At block shift /></@compress_single_line>