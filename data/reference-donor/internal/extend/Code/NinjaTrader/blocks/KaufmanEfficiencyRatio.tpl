<#-- Kaufman Efficiency Ratio value from the installed SqKaufmanEfficiencyRatio indicator. NinjaTrader has no native KER. -->
<#-- The caller's `shift` MUST be passed on: comparisons such as IsRising or CrossesAbove
     render the same operand at shift and shift+1, so a fixed shift makes them compare a
     value with itself. -->
<@compress_single_line><@printKERValueAt block shift /></@compress_single_line>